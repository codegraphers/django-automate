def test_smoke():
    assert 1 + 1 == 2

def test_import_models():
    """Verify we can import models without messing up app registry."""
    from automate.models import Automation
    assert Automation is not None
