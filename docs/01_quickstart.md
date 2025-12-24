# Getting Started with Django Automate

**Django Automate** is a production-grade workflow automation platform for Django. It provides a control plane (Studio) and execution plane (Rules Engine, Outbox) to build reliable, auditable, and secure automation workflows.

### What is it?
Think of it as "Zapier inside your Django app", but built for developers who need:
*   **Idempotency**: Guaranteed exactly-once processing intent.
*   **Audit Trails**: Every action, rule check, and external call is logged.
*   **Security**: Secret redaction, policy engines, and execution sandboxing.
*   **Observability**: OpenTelemetry-compatible tracing and structured logging.

### Compatibility
*   **Python**: 3.10+
*   **Django**: 4.2+
*   **Databases**: Postgres (Recommended), SQLite (Dev), MySQL 8+

---

## 5-Minute Quickstart

### 1. Installation

Install the package:
```bash
pip install django-automate
```

Add to `INSTALLED_APPS` in your `settings.py`:
```python
INSTALLED_APPS = [
    # ... django apps ...
    'automate', 
    'automate_core',
    'automate_governance',
    'automate_llm',
    'automate_studio', # Optional: Admin UI
    'automate_observability',
    'rest_framework',
]
```

### 2. Minimal Configuration

Set the basic configuration in `settings.py`:

```python
DJANGO_AUTOMATE = {
    "ENABLED": True,
    "SECRET_KEY_PREFIX": "AUTOMATE_", # For env-based secrets
    "EXECUTION": {
        "timeout_seconds": 60,
        "max_retries": 3,
    }
}
```

Run migrations:
```bash
python manage.py migrate
```

### 3. Create Your First Workflow

You can define workflows via code (JSON) or the Visual Studio. Let's create a simple JSON workflow that logs a message when a user is created.

Go to `http://localhost:8000/studio/wizard/` (if running locally) or define it programmatically:

```python
from automate_core.models import Workflow

Workflow.objects.create(
    name="Welcome New User",
    trigger_spec={
        "type": "signal",
        "config": {
            "model": "auth.User",
            "signal": "post_save",
            "condition": "created == true"
        }
    },
    steps=[
        {
            "id": "log_action",
            "action": "core.log",
            "config": {
                "level": "INFO",
                "message": "New user registered: {{ event.instance.username }}"
            }
        }
    ]
)
```

### 4. Run the Worker

In development, you can run the simplified management command worker:

```bash
python manage.py automate_worker
```

Trigger the workflow by creating a new User in Django Admin. You should see the log output in your worker console.

### 5. Inspect the Run

Visit the **Execution Explorer** at `http://localhost:8000/studio/explorer/` to see the timeline of your execution, verify inputs/outputs, and check audit logs.
