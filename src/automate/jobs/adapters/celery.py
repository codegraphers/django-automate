from datetime import datetime

from celery import current_app
from django.utils import timezone

from automate_core.jobs.queue import CancelResult, JobQueue, QueueReceipt


class CeleryJobQueue(JobQueue):
    """
    Celery implementation of the JobQueue interface.
    """
    def __init__(self, task_name: str = "django_automate.execute_job"):
        self.task_name = task_name

    def submit(
        self,
        *,
        job_id: str,
        queue: str,
        eta: datetime | None = None,
        priority: int | None = None,
        dedupe_key: str | None = None,
    ) -> QueueReceipt:
        # Celery options
        options = {
            "queue": queue,
            "priority": priority,
        }
        if eta:
            options["eta"] = eta

        # If dedupe_key is supported by a custom Task class or backend, passing it here
        # standard Celery doesn't use it directly without plugins, but passing explicitly helper.
        if dedupe_key:
            options["task_id"] = dedupe_key  # Using dedupe_key as task_id enforces strict de-duplication if supported

        # Send
        # Payload is JUST the job_id
        async_result = current_app.send_task(
            self.task_name,
            args=[job_id],
            **options
        )

        return QueueReceipt(
            backend="celery",
            backend_task_id=async_result.id,
            queue=queue,
            enqueued_at=timezone.now(),
        )

    def cancel(self, *, job_id: str, backend_task_id: str | None = None) -> CancelResult:
        if not backend_task_id:
            return CancelResult(
                job_id=job_id,
                canceled_in_db=False,  # Managed by caller (Service) usually, but protocol allows return status
                backend_revoked=False,
                message="No backend task id provided"
            )

        current_app.control.revoke(backend_task_id, terminate=True)

        return CancelResult(
            job_id=job_id,
            canceled_in_db=True,  # Caller sets DB status, we confirm backend action
            backend_revoked=True,
            message=f"Revoked Celery task {backend_task_id}"
        )

    def health(self) -> dict:
        return {
            "backend": "celery",
            "broker_connection": "unknown", # Could check ping
        }
