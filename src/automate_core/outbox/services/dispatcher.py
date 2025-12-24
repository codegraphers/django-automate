import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from ..models import OutboxItem

# from ...executions.tasks import run_execution # To be implemented/shimmed

logger = logging.getLogger(__name__)

class OutboxDispatcher:
    """
    Service to reliably process the Outbox table and push tasks to async workers.
    Ensures 'At-Least-Once' delivery of side effects.
    """

    def process_pending(self, batch_size=50):
        # 1. Claim items (Lease pattern or Select For Update)
        # Using select_for_update with skip_locked is standard for PG.

        now = timezone.now()

        # Items ready to run (Pending or Retry due)
        qs = OutboxItem.objects.filter(
            status__in=["PENDING", "RETRY"],
            next_attempt_at__lte=now
        ).select_for_update(skip_locked=True).order_by("priority", "created_at")[:batch_size]

        success_count = 0

        with transaction.atomic():
            for item in qs:
                try:
                    self._dispatch_item(item)
                    item.status = "DONE"
                    item.save(update_fields=["status", "updated_at"])
                    success_count += 1
                except Exception as e:
                    logger.error(f"Outbox dispatch failed for {item.id}: {str(e)}")
                    item.attempt_count += 1
                    item.last_error_message = str(e)

                    if item.attempt_count >= item.max_attempts:
                        item.status = "DLQ"
                    else:
                        item.status = "RETRY"
                        # Exponential backoff
                        delay = 10 * (2 ** (item.attempt_count - 1))
                        item.next_attempt_at = now + timedelta(seconds=delay)

                    item.save()

        return success_count

    def _dispatch_item(self, item: OutboxItem):
        """
        Route the item to the correct handler.
        """
        if item.kind == "execution_queued":
            logger.info(f"Dispatching execution {item.payload['execution_id']}")
            # In a real app, this pushes to Celery/SQS.
            # Lazy import to avoid cycle if tasks import services
            # from ...executions.tasks import run_execution
            # run_execution.delay(item.payload["execution_id"])
            pass
        elif item.kind == "webhook":
            # Future: specialized webhook sending
            pass
        else:
            logger.warning(f"Unknown outbox kind: {item.kind}")
