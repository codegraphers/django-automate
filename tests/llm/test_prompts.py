import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from automate_llm.models import Prompt, PromptStatus, PromptVersion


@pytest.mark.django_db
def test_prompt_versioning():
    p = Prompt.objects.create(tenant_id="t1", key="test.prompt")

    # Create valid version
    v1 = PromptVersion.objects.create(
        prompt=p,
        version=1,
        system_template="You are a bot.",
        status=PromptStatus.DRAFT
    )
    assert v1.prompt == p
    assert v1.version == 1

    # Test Unique Constraint (prompt + version)
    try:
        from django.db import transaction
        with transaction.atomic():
            PromptVersion.objects.create(
                prompt=p,
                version=1, # Duplicate
                system_template="Diff"
            )
        pytest.fail("Should have raised IntegrityError")
    except IntegrityError:
        pass

    # Create v2
    v2 = PromptVersion.objects.create(
        prompt=p,
        version=2,
        system_template="New sys"
    )
    assert v2.version == 2
    assert p.versions.count() == 2

@pytest.mark.django_db
def test_prompt_unique_key_per_tenant():
    from django.db import transaction
    Prompt.objects.create(tenant_id="t1", key="uniq.key")

    try:
        with transaction.atomic():
            Prompt.objects.create(tenant_id="t1", key="uniq.key")
        pytest.fail("Should have raised IntegrityError")
    except IntegrityError:
        pass

    # Different tenant ok
    Prompt.objects.create(tenant_id="t2", key="uniq.key")
