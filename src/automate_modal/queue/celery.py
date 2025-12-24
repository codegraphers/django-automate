"""
Celery adapter for JobQueue.
"""
from typing import Any

from celery import current_app

from automate_modal.contracts import JobQueue


class CeleryJobQueue(JobQueue):
    """
    JobQueue implementation using Celery.
    Assumes a task named 'automate_modal.tasks.execute_job' exists.
    """

    def enqueue(self, job_name: str, payload: dict[str, Any], *, priority: int = 5, delay_s: int = 0) -> str:
        # job_name is effectively the task name if we were dynamic,
        # but here we fan-in to a single worker task

        # We pass job_id as the primary arg to the task
        job_id = payload.get("job_id")
        if not job_id:
             raise ValueError("Payload must contain job_id")

        # Signature
        sig = current_app.signature(
            job_name, # "automate_modal.tasks.execute_job"
            args=[job_id],
            priority=priority,
            immutable=True
        )

        if delay_s > 0:
            result = sig.apply_async(countdown=delay_s)
        else:
            result = sig.apply_async()

        return str(result.id) # This is celery task id, distinct from our internal job_id

    def cancel(self, job_id: str) -> None:
        # Canceling via celery usually requires the celery task ID, not our internal job ID.
        # This implies we need to store celery_task_id on the ModalJob model.
        # For v1, this might be best effort or omitted.
        current_app.control.revoke(job_id, terminate=True)
