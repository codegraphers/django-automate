import uuid

import pytest
from django.contrib.auth.models import User
from django.test import Client

from automate.models import LLMProvider


@pytest.fixture
def admin_user():
    return User.objects.create_superuser("admin", "admin@test.com", "password")

@pytest.fixture
def provider():
    return LLMProvider.objects.create(
        slug="test-provider",
        name="Test Provider"
    )

from django.urls import reverse


@pytest.mark.django_db
def test_provider_console_access(admin_user, provider):
    client = Client()
    client.force_login(admin_user)

    # Resolving via admin namespace
    url = reverse("admin:automate_llmprovider_test", args=[provider.pk])
    print(f"DEBUG: Resolved URL: {url}")

    response = client.get(url)

    assert response.status_code == 200
    assert "Test Provider" in response.content.decode()
    assert "Test Input" in response.content.decode()

@pytest.mark.django_db
def test_provider_console_run(admin_user, provider):
    client = Client()
    client.force_login(admin_user)

    url = reverse("admin:automate_llmprovider_test", args=[provider.pk])
    response = client.post(url, {"input": "Hello"}, headers={"HX-Request": "true"})

    assert response.status_code == 200
    content = response.content.decode()
    assert "Result: Success" in content
    assert "Echo: Hello" in content
