from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class QueueReceipt:
    backend: str                # celery, rq, outbox-db
    backend_task_id: str | None  # celery task id if exists
    queue: str
    enqueued_at: datetime


@dataclass
class CancelResult:
    job_id: str
    canceled_in_db: bool
    backend_revoked: bool
    message: str


class JobQueue(Protocol):
    """
    Contract for a job queue backend.
    """
    def submit(
        self,
        *,
        job_id: str,
        queue: str,
        eta: datetime | None = None,
        priority: int | None = None,
        dedupe_key: str | None = None,
    ) -> QueueReceipt:
        """Enqueue delivery of execute_job(job_id). Returns receipt with backend task id."""
        ...

    def cancel(self, *, job_id: str, backend_task_id: str | None = None) -> CancelResult:
        """Best-effort. Marks canceled in DB; may revoke backend task if supported."""
        ...

    def health(self) -> dict:
        """Basic info: backend type, broker url masked, queue names, status."""
        ...
