import logging
import random
import time
import traceback
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Job, JobEvent, JobEventTypeChoices, JobStatusChoices

logger = logging.getLogger(__name__)

LEASE_TTL = getattr(settings, "AUTOMATE_JOB_LEASE_TTL", 300)  # 5 minutes

class JobExecutionError(Exception):
    """Wraps errors occurring during job execution."""
    pass

class TransientError(JobExecutionError):
    """Errors that are potentially temporary (network, timeout)."""
    pass

class PermanentError(JobExecutionError):
    """Errors that are fatal (validation, logic)."""
    pass


def execute_job(job_id: str, worker_id: str = "worker-default", handler: Callable[[Job], Any] = None):
    """
    The Single Worker Entrypoint.
    Executes a job by ID, managing DB state, locking, and retries.

    Args:
        job_id: The UUID of the job to execute.
        worker_id: Identifier for the worker (pod name, process id).
        handler: Optional callable to actually run the logic. If None, uses internal dispatcher (stub).
    """

    # 1. Acquire Job & Lease
    # Robust acquisition for SQLite/Postgres
    job = _acquire_job_lease(job_id, worker_id)
    if not job:
        # Job not found, locked, or already finished/owned
        return

    try:
        # 2. Transition to RUNNING
        _start_job(job, worker_id)

        # 3. Execute
        result = None
        result = handler(job) if handler else _dispatch_internal(job)

        # 4. Success
        _finish_job(job, JobStatusChoices.SUCCEEDED, result=result)

    except Exception as e:
        # 5. Handle Error (Retry vs Fail)
        _handle_job_error(job, e)

    finally:
        # 6. Cleanup Lease
        _release_lease(job_id)


def _acquire_job_lease(job_id: str, worker_id: str) -> Job | None:
    """
    Selects job for update, checks status/lease availability.
    """
    # Simply using transaction.atomic + select_for_update
    # For SQLite, we might need the retry wrapper similar to Dispatcher

    is_sqlite = "sqlite" in settings.DATABASES["default"]["ENGINE"]
    max_retries = 5 if is_sqlite else 1

    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                qs = Job.objects.select_for_update(skip_locked=not is_sqlite).filter(id=job_id)
                if is_sqlite:
                    qs = Job.objects.select_for_update().filter(id=job_id)

                job = qs.first()
                if not job:
                    return None

                # Check terminal states
                if job.status in (
                    JobStatusChoices.SUCCEEDED,
                    JobStatusChoices.FAILED,
                    JobStatusChoices.DLQ,
                    JobStatusChoices.CANCELED
                ):
                    return None

                # Check valid lease
                now = timezone.now()
                if job.lease_expires_at and job.lease_expires_at > now and job.lease_owner != worker_id:
                    return None # Owned by someone else

                return job

        except Exception as e:
            if is_sqlite and "database table is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(random.uniform(0.05, 0.2))
                continue
            # For other errors or exhausted retries
            logger.warning(f"Failed to acquire lock for job {job_id}: {e}")
            return None
    return None

def _start_job(job: Job, worker_id: str):
    now = timezone.now()
    job.status = JobStatusChoices.RUNNING
    job.lease_owner = worker_id
    job.lease_expires_at = now + timedelta(seconds=LEASE_TTL)
    job.heartbeat_at = now

    # Reset result/error
    job.result_summary = {}
    job.error_redacted = {}

    job.save()

    JobEvent.objects.create(
        job=job,
        seq=_next_seq(job),
        type=JobEventTypeChoices.PROGRESS,
        data={"message": "Job started", "worker": worker_id}
    )

def _dispatch_internal(job: Job) -> Any:
    """
    Mock dispatcher. Real implementation would route based on job.topic.
    """
    logger.info(f"Executing job {job.id} topic={job.topic} payload={job.payload_redacted.keys()}")

    # Simulate work
    # In real world, this calls service layer
    if job.topic == "test.fail":
        raise ValueError("Simulated Failure")

    return {"status": "ok", "executed": True}

def _finish_job(job: Job, status: str, result: dict = None):
    job.status = status
    job.lease_owner = None
    job.lease_expires_at = None
    if result:
        job.result_summary = result
    job.save()

    JobEvent.objects.create(
        job=job,
        seq=_next_seq(job),
        type=JobEventTypeChoices.FINAL,
        data={"status": status}
    )

def _handle_job_error(job: Job, error: Exception):
    # Determine if retry
    job.attempts += 1

    # Default Retry Policy: Max 3 attempts, exponential backoff
    should_retry = job.attempts < job.max_attempts

    # Could check for PermanentError to force fail
    if isinstance(error, PermanentError):
        should_retry = False

    error_data = {
        "type": type(error).__name__,
        "message": str(error),
        "traceback": traceback.format_exc()[-1000:] # Redact/truncate
    }

    if should_retry:
        job.status = JobStatusChoices.RETRY_SCHEDULED

        # Exponential backoff: 2^(attempt-1) * 10s
        delay = 10 * (2 ** (job.attempts - 1))
        # Add Jitter
        delay += random.uniform(0, 5)

        job.next_attempt_at = timezone.now() + timedelta(seconds=delay)
        job.lease_owner = None
        job.lease_expires_at = None
        job.error_redacted = error_data
        job.save()

        JobEvent.objects.create(
            job=job,
            seq=_next_seq(job),
            type=JobEventTypeChoices.ERROR,
            data={"message": f"Retry scheduled in {delay:.1f}s", "error": str(error)}
        )

    else:
        # DLQ / Failed
        job.status = JobStatusChoices.FAILED
        job.lease_owner = None
        job.lease_expires_at = None
        job.error_redacted = error_data
        job.save()

        JobEvent.objects.create(
            job=job,
            seq=_next_seq(job),
            type=JobEventTypeChoices.ERROR,
            data={"message": "Max attempts reached. Job failed.", "error": str(error)}
        )

def _release_lease(job_id: str):
    # Usually handled in finish/error, but strict cleanup here if needed
    # (Optional if we trust logic above)
    pass

def _next_seq(job: Job) -> int:
    # Get max seq + 1. Optimization: could be cached or use Count
    last = job.events.order_by("-seq").first()
    return (last.seq + 1) if last else 1
