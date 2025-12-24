# First Automation

## 1. What you'll build
A simple "Welcome User" workflow that logs a message when a new User is created in Django.

## 2. Prerequisites
*   Usage of `auth.User` model in your project.
*   Completed [Installation](install.md).

## 3. Steps

### Create the Workflow (JSON)
You can define workflows programmatically. Create a script or run in `python manage.py shell`:

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

### Run the Worker
Open a terminal and start the development worker:
```bash
python manage.py automate_worker
```

### Trigger the Event
In a separate terminal or the Django Admin:
1.  Create a new User.
2.  The `post_save` signal triggers the workflow.

## 4. Expected Output
In the worker console, you should see:
```text
[INFO] New user registered: myuser123
```

In the [Execution Explorer](../../studio/execution-explorer.md), you will see a green "COMPLETED" run.

## 5. Next Steps
*   [Add a Webhook Trigger](../tutorials/triggers/inbound-webhooks.md)
*   [Configure Secrets](../how-to/secrets/secretref.md)
