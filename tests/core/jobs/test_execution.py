import pytest
from django.utils import timezone

from automate_core.jobs.models import Job, JobEvent, JobStatusChoices
from automate_core.jobs.worker import JobExecutionError, execute_job


@pytest.mark.django_db(transaction=True)
def test_execute_job_success():
    """Verify happy path execution."""
    job = Job.objects.create(topic="test.success", payload_redacted={"foo": "bar"})

    def handler(j):
        assert j.status == JobStatusChoices.RUNNING
        assert j.lease_owner == "worker-1"
        return {"result": "ok"}

    execute_job(job_id=job.id, worker_id="worker-1", handler=handler)

    job.refresh_from_db()
    assert job.status == JobStatusChoices.SUCCEEDED
    assert job.result_summary == {"result": "ok"}
    assert job.lease_owner is None

    events = JobEvent.objects.filter(job=job).order_by("seq")
    assert events.count() == 2
    assert events[0].type == "progress"
    assert events[1].type == "final"

@pytest.mark.django_db(transaction=True)
def test_execute_job_retry():
    """Verify retry logic on failure."""
    job = Job.objects.create(topic="test.fail", max_attempts=3)

    def handler(j):
        raise ValueError("Boom")

    # Attempt 1
    execute_job(job_id=job.id, worker_id="worker-1", handler=handler)

    job.refresh_from_db()
    assert job.status == JobStatusChoices.RETRY_SCHEDULED
    assert job.attempts == 1
    assert job.next_attempt_at is not None
    assert job.error_redacted["message"] == "Boom"

    # Attempt 2 (Simulate time pass or forced run)
    # We force run by just calling execute again, normally checking next_attempt_at happens in poller
    execute_job(job_id=job.id, worker_id="worker-1", handler=handler)

    job.refresh_from_db()
    assert job.attempts == 2
    assert job.status == JobStatusChoices.RETRY_SCHEDULED

    # Attempt 3 (Final Retry)
    execute_job(job_id=job.id, worker_id="worker-1", handler=handler)

    # After 3 failed attempts (since max_attempts=3), it should technically still retry if < max?
    # Logic is `should_retry = job.attempts < job.max_attempts`.
    # 0 -> 1 < 3 (Retry)
    # 1 -> 2 < 3 (Retry)
    # 2 -> 3 < 3 (False -> Fail)

    # Wait, simple math check:
    # 1st run: attempts becomes 1. 1 < 3 is True. Retry.
    # 2nd run: attempts becomes 2. 2 < 3 is True. Retry.
    # 3rd run: attempts becomes 3. 3 < 3 is False. Fail.

    job.refresh_from_db()
    # It should be FAILED now
    assert job.status == JobStatusChoices.FAILED
    assert job.attempts == 3

@pytest.mark.django_db(transaction=True)
def test_execute_job_locking():
    """Verify locking prevents double execution."""
    job = Job.objects.create(topic="test.lock")

    # Manually lock it
    job.status = JobStatusChoices.RUNNING
    job.lease_owner = "other-worker"
    job.lease_expires_at = timezone.now() + timezone.timedelta(minutes=5)
    job.save()

    # Try to execute
    executed = False
    def handler(j):
        nonlocal executed
        executed = True

    execute_job(job_id=job.id, worker_id="worker-1", handler=handler)

    assert not executed
    job.refresh_from_db()
    assert job.lease_owner == "other-worker"
