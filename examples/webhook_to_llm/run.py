import os
import sys
import time

import django
import requests

# Setup Django (for seeding/verification)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings") # Using test settings for standalone run if needed
# But realistically, if running against docker stack, we might not have access to DB port easily unless exposed.
# The prompt says "Examples are executable... CI enforcement... run example scripts".

# Strategy:
# 1. Use API to provision if possible, or Django ORM if running in same env.
# 2. Trigger webhook via HTTP.
# 3. Poll API/DB.

def run():
    print("Initializing Django SDK...")
    django.setup()

    from automate_core.jobs.models import Job
    from automate_core.models import Automation, Trigger, TriggerTypeChoices, Workflow

    print("Seeding Data...")
    tenant_id = "demo_tenant"

    # Cleaning up old run
    Automation.objects.filter(tenant_id=tenant_id).delete()

    # 1. Create Automation
    auto = Automation.objects.create(
        tenant_id=tenant_id,
        name="Webhook -> Log",
        slug="webhook-log"
    )

    # 2. Add Trigger
    Trigger.objects.create(
        automation=auto,
        type=TriggerTypeChoices.WEBHOOK,
        event_type="test.event",
        is_active=True
    )

    # 3. Add Workflow (Simple Logic)
    Workflow.objects.create(
        automation=auto,
        version=1,
        is_live=True,
        graph={
            "steps": [
                {
                    "id": "step_1",
                    "action": "log",
                    "params": {"message": "Hello from {{ event.payload.name }}"}
                }
            ]
        }
    )

    print("Triggering Webhook...")
    # Using 'web' service if in docker, or localhost if running locally against docker
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    webhook_url = f"{base_url}/api/v1/webhooks/{tenant_id}/test.event"

    try:
        # Mocking signature for now (or assuming no-verify for dev)
        resp = requests.post(webhook_url, json={"name": "Developer"}, timeout=5)
        print(f"Webhook Status: {resp.status_code}")
        if resp.status_code not in [200, 202]:
            print(f"Failed to trigger: {resp.text}")
            sys.exit(1)
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Ensure server is running (make dev)")
        sys.exit(1)

    print("Waiting for execution...")
    # Poll DB for Job completion
    for i in range(10):
        jobs = Job.objects.filter(tenant_id=tenant_id)
        if jobs.exists():
            status = jobs.first().status
            print(f"Job Status: {status}")
            if status == "succeeded":
                print("SUCCESS: Automation executed successfully.")
                sys.exit(0)
            if status == "failed":
                print("FAILURE: Job failed.")
                sys.exit(1)
        time.sleep(1)

    print("TIMEOUT: Job did not complete in time.")
    sys.exit(1)

if __name__ == "__main__":
    run()
