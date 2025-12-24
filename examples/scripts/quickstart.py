import django
from django.conf import settings

# 1. Minimal Configuration
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="demo-secret",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "automate",
            "automate_modal",
        ],
        TIME_ZONE="UTC",
        USE_TZ=True,
    )
    django.setup()

# 2. Setup DB
from django.core.management import call_command  # noqa: E402

print("⚡ Initializing Database...")
call_command("migrate", verbosity=0)

# 3. Create Demo Data
from automate_modal.models import ModalEndpoint, ModalProviderConfig  # noqa: E402
from automate_modal.providers.echo import EchoProvider  # noqa: E402

print("⚡ Creating Configuration...")
config = ModalProviderConfig.objects.create(name="Echo Provider", provider_key=EchoProvider.key, enabled=True)

endpoint = ModalEndpoint.objects.create(
    name="Test API", slug="test-echo", provider_config=config, enabled=True, allowed_task_types=["llm.chat"]
)

# 4. Run Task
from automate_modal.engine import engine  # noqa: E402

print(f"⚡ Executing Task on endpoint: {endpoint.slug}...")
result = engine.execute(
    endpoint_slug="test-echo",
    task_type="llm.chat",
    req={"model": "gpt-4", "messages": [{"role": "user", "content": "Hello!"}]},
    actor_id="demo-script",
)

print("\n✅ Result:")
print(f"Output: {result.outputs['echo']}")
print(f"Usage: {result.usage}")
