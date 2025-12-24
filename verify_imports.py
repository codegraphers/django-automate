import sys
import os
import django
from django.conf import settings

# Ensure src is in path
sys.path.insert(0, os.path.join(os.getcwd(), "packages/django_automate/src"))

# Configure minimal Django settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "automate",
            "automate_governance",
            "automate_core",
            "automate_llm",
            "automate_connectors",
            "automate_interop",
            "automate_observability",
            "automate_studio",
        ],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        SECRET_KEY="test",
    )
    django.setup()

modules = [
    "automate_llm.types",
    "automate_llm.errors",
    "automate_llm.conf",
    "automate_llm.registry",
    "automate_llm.policy",
    "automate_llm.redaction",
    "automate_llm.adapters.base",
    "automate_llm.adapters.openai",
    "automate_llm.prompts.renderers.base",
    "automate_llm.prompts.renderers.chat_messages",
    "automate_llm.prompts.renderers.jinja_renderer",
    "automate_llm.prompts.compiler",
    "automate_llm.runs.store",
    "automate_llm.runs.executor",
    "automate_llm.runs.service",
    "automate_llm.evals.service",
    "automate_llm.api.permissions",
    "automate_llm.api.serializers",
    "automate_llm.api.views",
    "automate_llm.api.urls",
    "automate_llm.tools",
    "automate_llm.pricing",
    "automate_llm.validation",
    
    # Connectors Framework
    "automate_connectors.errors",
    "automate_connectors.types",
    "automate_connectors.adapters.base",
    "automate_connectors.profiles",
    # Connectors
    "automate_connectors.execution",
    "automate_connectors.registry",
    
    # LLM Integrations
    "automate_llm.tools.http",
    "automate_llm.tools.bridge",
    "automate_llm.tools.executor",
    "automate_llm.tools.types",
    "automate_llm.adapters.anthropic",
    "automate_llm.adapters.gemini",
    
    # Interop
    "automate_interop.flags",
    "automate_interop.orchestrators.contracts",
    "automate_interop.orchestrators.n8n.adapter",
    "automate_interop.import_export.contracts",
    "automate_interop.import_export.sanitizer",
    "automate_interop.import_export.n8n_json",
    "automate_interop.templates_host.api",
    "automate_interop.sync.drift",
    "automate_interop.models",
    "automate_interop.admin",

    # Connectors
    "automate_connectors.adapters.slack",

    # Observability
    "automate_observability.context",
    "automate_observability.middleware",
    "automate_observability.logging",
    "automate_observability.models",
    "automate_observability.metrics",
    "automate_observability.service",
    
    # Authoring Studio
    "automate_studio.views.wizard",
    "automate_studio.views.tester",
    "automate_studio.views.explorer",
    "automate_studio.admin",
]

print("Verifying imports...")
failed = []
for mod in modules:
    try:
        __import__(mod)
        print(f"OK: {mod}")
    except Exception as e:
        print(f"FAIL: {mod} -> {e}")
        failed.append(mod)

if failed:
    print(f"\nFAILED MODULES: {len(failed)}")
    sys.exit(1)

print("\nAll modules imported successfully.")
