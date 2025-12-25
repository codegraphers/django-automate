import pytest
from rest_framework.test import APIClient

from automate_core.models import Automation
from automate_governance.models import AuditLog


@pytest.fixture
def api_client():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer test")
    return client

@pytest.mark.django_db
def test_audit_log_creation(api_client):
    """Verify modifying action creates AuditLog entry."""
    auto = Automation.objects.create(name="Test", slug="test", tenant_id="t1", is_active=True)
    url = f"/api/v1/endpoints/{auto.id}/run/"

    payload = {"input": "secret-value", "password": "s3cret-password"}
    response = api_client.post(url, {"payload": payload}, format="json")

    assert response.status_code == 202

    # Check Audit Log
    log = AuditLog.objects.last()
    assert log is not None
    assert log.action == f"POST {url}"
    assert log.tenant_id == "t1" # From Principal
    assert log.actor["id"] == "u_test"

    # Redaction Check
    redacted = log.payload_redacted
    print(f"DEBUG: Redacted Payload: {redacted}")
    assert redacted["payload"]["input"] == "secret-value" # Not redacted by key
    assert redacted["payload"]["password"] == "[REDACTED]" # Redacted by key

@pytest.mark.django_db
def test_audit_log_404_failure(api_client):
    """Verify error responses (404) are audited."""
    url = "/api/v1/jobs/nonexistent-id/"
    response = api_client.get(url) # GET is usually read-only, but 404 is error

    # Middleware filters: is_modifying OR is_error
    # GET 404 -> is_error=True -> Should audit

    log = AuditLog.objects.last()
    assert log is not None
    assert log.action == f"GET {url}"
    assert log.result == "failure"
