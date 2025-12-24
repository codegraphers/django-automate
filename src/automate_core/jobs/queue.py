from datetime import datetime
from dataclasses import dataclass
from typing import Protocol, Optional

@dataclass
class QueueReceipt:
    backend: str                # celery, rq, outbox-db
    backend_task_id: str | None # celery task id if exists
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
        eta: Optional[datetime] = None,
        priority: Optional[int] = None,
        dedupe_key: Optional[str] = None,
    ) -> QueueReceipt:
        """Enqueue delivery of execute_job(job_id). Returns receipt with backend task id."""
        ...

    def cancel(self, *, job_id: str, backend_task_id: Optional[str] = None) -> CancelResult:
        """Best-effort. Marks canceled in DB; may revoke backend task if supported."""
        ...

    def health(self) -> dict:
        """Basic info: backend type, broker url masked, queue names, status."""
        ...
