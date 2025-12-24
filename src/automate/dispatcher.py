import datetime
import logging
import uuid

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import Event, Execution, ExecutionStatusChoices, Outbox, OutboxStatusChoices, TriggerSpec

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
            # 2. RUNNING but lease expired (Steal)
            # 3. RETRY with upcoming attempt

            qs = Outbox.objects.filter(
                Q(status=OutboxStatusChoices.PENDING) |
                Q(status=OutboxStatusChoices.RUNNING, lease_expires_at__lt=now) |
                Q(status=OutboxStatusChoices.RETRY, next_attempt_at__lte=now)
            )

            # SQLite does not support skip_locked
            if "sqlite" in settings.DATABASES["default"]["ENGINE"]:
               qs = qs.select_for_update().order_by("priority", "created_at")[:batch_size]
            else:
               qs = qs.select_for_update(skip_locked=True).order_by("priority", "created_at")[:batch_size]

            locked_entries = list(qs)

            if locked_entries:
                Outbox.objects.filter(
                    id__in=[e.id for e in locked_entries]
                ).update(
                    lease_expires_at=now + datetime.timedelta(seconds=LOCK_TTL),
                    lease_owner=worker_id,
                    status=OutboxStatusChoices.RUNNING
                )

            return locked_entries

    def _dispatch_event(self, entry: Outbox):
        if entry.kind != "event":
             # Only dispatch events for now
             return
             
        event_id = entry.payload.get("event_id")
        if not event_id:
            logger.error(f"Outbox entry {entry.id} missing event_id in payload")
            entry.status = OutboxStatusChoices.DLQ
            entry.save()
            return

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            logger.error(f"Event {event_id} not found for outbox entry {entry.id}")
            entry.status = OutboxStatusChoices.DLQ
            entry.save()
            return
            
        try:
            # P0.4: Use Strict Matching Service
            from .services.trigger import TriggerMatchingService
            matcher = TriggerMatchingService()

            triggers = TriggerSpec.objects.filter(is_active=True)
            matched_automations = {} # Deduplicate by ID

            for trigger in triggers:
                if matcher.matches(trigger, event):
                    matched_automations[trigger.automation.id] = trigger.automation

            if not matched_automations:
                logger.debug(f"No automations found for event {event.id}")
            if not matched_automations:
                logger.debug(f"No automations found for event {event.id}")
                entry.status = OutboxStatusChoices.DONE
                entry.save()
                return

            # P0.2: Deduplicated Execution Creation with Version Snapshot
            count = 0
            for automation in matched_automations.values():
                # Resolve workflow
                workflow = automation.workflows.filter(is_live=True).first()
                if not workflow:
                    # Fallback to latest
                    workflow = automation.workflows.order_by("-version").first()

                if workflow:
                     # P0.2: Snapshot workflow.version
                     Execution.objects.get_or_create(
                        tenant_id=event.tenant_id,
                        event=event,
                        automation=automation,
                        workflow_version=workflow.version,
                        defaults={
                            "status": ExecutionStatusChoices.QUEUED,
                        }
                    )
                     count += 1
                else:
                    logger.warning(f"Automation {automation.id} matched but has no workflows.")

            entry.status = OutboxStatusChoices.DONE
            entry.updated_at = timezone.now() # Generic uses updated_at, kept processed_at removed?
            # OutboxItem doesn't have processed_at, using updated_at implicitly
            entry.save()
            logger.info(f"Dispatched event {event.id} to {count} automations")

        except Exception as e:
            logger.exception(f"Failed to dispatch event {event.id}")

            # P0.3: Retry Logic (Backoff + DLQ)
            entry.attempt_count += 1
            MAX_RETRIES = getattr(settings, "AUTOMATE_MAX_RETRIES", 3)

            if entry.attempt_count >= MAX_RETRIES:
                logger.error(f"Event {event.id} exhausted retries. Moving to DLQ.")
                entry.status = OutboxStatusChoices.DLQ
                entry.last_error_message = str(e)
                entry.save()

                # Legacy DLQ table removed. Using status+fields on item.
                pass
            else:
                entry.status = OutboxStatusChoices.RETRY

                # Exponential Backoff + Jitter
                import random
                backoff = 2 ** (entry.attempt_count - 1) # 1, 2, 4
                jitter = random.uniform(0, 1)
                delay = backoff + jitter

                entry.next_attempt_at = timezone.now() + datetime.timedelta(seconds=delay)
                entry.save()
                logger.info(f"Scheduled retry {entry.attempt_count} for event {event.id} in {delay:.2f}s")

    def _matches(self, trigger: TriggerSpec, event: Event):
        # Deprecated by TriggerMatchingService
        return False
