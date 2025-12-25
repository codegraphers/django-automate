import uuid

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from automate.models import Automation, Execution, ExecutionStatusChoices
from automate_core.jobs.models import Job, JobStatusChoices


@pytest.fixture
def admin_client():
    u = User.objects.create_superuser("admin", "admin@test.com", "pass")
    c = Client()
    c.force_login(u)
    return c

@pytest.mark.django_db
def test_dashboard_stats(admin_client):
    # Setup data
    Job.objects.create(
        id=uuid.uuid4(), tenant_id="t1", topic="test", status=JobStatusChoices.QUEUED, payload_redacted={}
    )
    Job.objects.create(
        id=uuid.uuid4(), tenant_id="t1", topic="test", status=JobStatusChoices.SUCCEEDED, payload_redacted={}
    )

    from django.utils import timezone

    from automate_core.events.models import Event
    e = Event.objects.create(
        id=uuid.uuid4(), tenant_id="t1", source="test", event_type="test",
        payload={}, occurred_at=timezone.now()
    )

    a = Automation.objects.create(id=uuid.uuid4(), name="Auto1", slug="auto1", tenant_id="t1")
    Execution.objects.create(
        id=uuid.uuid4(), tenant_id="t1", automation=a, event=e, status=ExecutionStatusChoices.RUNNING
    )

    url = reverse("studio_dashboard")
    resp = admin_client.get(url)

    assert resp.status_code == 200
    content = resp.content.decode()

    # Check stats presence
    assert "System Health" in content
    assert "queued" in content # Status string
    assert "1" in content # Count

    # Clean check
    ctx = resp.context
    assert ctx["jobs_stats"][JobStatusChoices.QUEUED] == 1
    assert ctx["jobs_stats"][JobStatusChoices.SUCCEEDED] == 1
    assert ctx["exec_stats"][ExecutionStatusChoices.RUNNING] == 1
