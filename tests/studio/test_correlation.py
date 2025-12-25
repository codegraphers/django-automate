import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from automate.models import Automation, Event, Execution
from automate_governance.models import AuditLog


@pytest.fixture
def admin_user():
    return User.objects.create_superuser("admin", "admin@test.com", "password")

import uuid


@pytest.fixture
def correlation_data():
    cid = str(uuid.uuid4())

    # 1. Create AuditLog
    AuditLog.objects.create(
        tenant_id="t1",
        actor={"id": "admin"},
        action="POST /api/test",
        resource={"id": "1"},
        result="success",
        correlation_id=cid,
        occurred_at=timezone.now()
    )

    # 2. Create Execution
    auto = Automation.objects.create(name="Test Auto", slug="test-auto", tenant_id="t1")
    event = Event.objects.create(
        tenant_id="t1",
        event_type="test",
        source="manual",
        payload={},
        status="processed",
        occurred_at=timezone.now()
    )
    Execution.objects.create(
        automation=auto,
        event=event,
        correlation_id=cid,
        status="completed",
        started_at=timezone.now(),
        tenant_id="t1"
    )

    return cid

@pytest.mark.django_db
def test_correlation_explorer_search(admin_user, correlation_data):
    client = Client()
    client.force_login(admin_user)

    url = "/admin/automate/studio/correlation/"
    response = client.get(url, {"q": correlation_data})

    assert response.status_code == 200
    content = response.content.decode()

    # Check for presence of both types
    assert "AuditLog" in content # From table
    assert "Execution" in content # From table
    assert correlation_data in content # Input value matches
