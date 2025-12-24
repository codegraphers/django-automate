import logging
import uuid
import datetime
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from .models import Outbox, OutboxStatusChoices, TriggerSpec, Execution, ExecutionStatusChoices, Event

logger = logging.getLogger(__name__)

LOCK_TTL = getattr(settings, "AUTOMATE_OUTBOX_LOCK_TTL", 60) # seconds

class Dispatcher:
    """
    Process outbox entries with safe concurrency.
    P0.3: Robust Implementation.
    """
    
    def dispatch_batch(self, batch_size=50, worker_id=None):
        if not worker_id:
            worker_id = str(uuid.uuid4())
            
        candidates = self._fetch_candidates(batch_size, worker_id)
        
        for entry in candidates:
            try:
                self._dispatch_event(entry)
            except Exception as e:
                # _dispatch_event should handle its own errors and state updates.
                # If we get here, it's a critical crash in the dispatcher logic itself.
                logger.critical(f"CRITICAL: Unhandled dispatcher error for {entry.id}: {e}")
                
    def _fetch_candidates(self, batch_size, worker_id):
        """
        Uses SELECT FOR UPDATE SKIP LOCKED to verify availability.
        Implements Lock Stealing (TTL).
        """
        now = timezone.now()
        ttl_cutoff = now - datetime.timedelta(seconds=LOCK_TTL)
        
        with transaction.atomic():
            # Filter logic: 
            # 1. PENDING
            # 2. LOCKED but expired (Steal)
            # 3. FAILED with retry due (Not implemented fully in P0, sticking to PENDING/LOCKED)
            
            qs = Outbox.objects.filter(
                Q(status=OutboxStatusChoices.PENDING) | 
                Q(status=OutboxStatusChoices.LOCKED, locked_at__lt=ttl_cutoff) |
                Q(status=OutboxStatusChoices.FAILED, next_attempt_at__lte=now)
            ).select_for_update(skip_locked=True).order_by("created_at")[:batch_size]
            
            locked_entries = list(qs)
            
            if locked_entries:
                Outbox.objects.filter(
                    id__in=[e.id for e in locked_entries]
                ).update(
                    locked_at=now,
                    lock_owner=worker_id,
                    status=OutboxStatusChoices.LOCKED
                )
                
            return locked_entries

    def _dispatch_event(self, entry: Outbox):
        event = entry.event
        try:
            # P0.4: Use Strict Matching Service
            from .services.trigger import TriggerMatchingService
            matcher = TriggerMatchingService()
            
            triggers = TriggerSpec.objects.filter(enabled=True)
            matched_automations = {} # Deduplicate by ID
            
            for trigger in triggers:
                if matcher.matches(trigger, event):
                    matched_automations[trigger.automation.id] = trigger.automation
            
            if not matched_automations:
                logger.debug(f"No automations found for event {event.id}")
                entry.status = OutboxStatusChoices.PROCESSED
                entry.processed_at = timezone.now()
                entry.save()
                return

            # P0.2: Deduplicated Execution Creation with Version Snapshot
            for automation in matched_automations.values():
                # Resolve workflow
                workflow = automation.workflows.filter(is_live=True).first()
                if not workflow:
                    # Fallback to latest
                    workflow = automation.workflows.order_by("-version").first()
                
                if workflow:
                     # P0.2: Snapshot workflow.version
                     Execution.objects.get_or_create(
                        event=event,
                        automation=automation,
                        workflow_version=workflow.version,
                        defaults={
                            "status": ExecutionStatusChoices.QUEUED,
                        }
                    )
                else:
                    logger.warning(f"Automation {automation.id} matched but has no workflows.")
            
            entry.status = OutboxStatusChoices.PROCESSED
            entry.processed_at = timezone.now()
            entry.save()
            logger.info(f"Dispatched event {event.id} to {len(matched_automations)} automations")
            
        except Exception as e:
            logger.exception(f"Failed to dispatch event {event.id}")
            
            # P0.3: Retry Logic (Backoff + DLQ)
            entry.attempts += 1
            MAX_RETRIES = getattr(settings, "AUTOMATE_MAX_RETRIES", 3)
            
            if entry.attempts >= MAX_RETRIES:
                logger.error(f"Event {event.id} exhausted retries. Moving to DEAD.")
                entry.status = OutboxStatusChoices.DEAD
                entry.save()
                
                # Create DeadLetter
                from .dlq import DeadLetter
                DeadLetter.objects.create(
                    outbox=entry,
                    reason_code="dispatch_failed",
                    last_error_redacted=str(e)
                )
            else:
                entry.status = OutboxStatusChoices.FAILED
                
                # Exponential Backoff + Jitter
                import random
                backoff = 2 ** (entry.attempts - 1) # 1, 2, 4
                jitter = random.uniform(0, 1)
                delay = backoff + jitter
                
                entry.next_attempt_at = timezone.now() + datetime.timedelta(seconds=delay)
                entry.save()
                logger.info(f"Scheduled retry {entry.attempts} for event {event.id} in {delay:.2f}s")

    def _matches(self, trigger: TriggerSpec, event: Event):
        # Deprecated by TriggerMatchingService
        return False
