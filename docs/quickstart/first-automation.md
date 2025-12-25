# Your First Automation

In this guide, we will build a simple "Webhook -> LLM -> Log" automation.

## Prerequisites

Ensure you have a running stack:
```bash
make dev
```

## Step 1: Create Automation

1. Open **Admin Studio**: [http://localhost:8000/admin/](http://localhost:8000/admin/)
2. Navigate to **Automations** > **Add Automation**.
3. Name: `Welcome Bot`, Slug: `welcome-bot`.
4. Tenant ID: `default`.

## Step 2: Add Trigger

1. Navigate to **Triggers** > **Add Trigger**.
2. Automation: `Welcome Bot`.
3. Type: `Webhook`.
4. Event Type: `user.signup`.
5. Save.

## Step 3: Define Workflow

1. Navigate to **Workflows** > **Add Workflow**.
2. Automation: `Welcome Bot`.
3. Version: `1`.
4. Graph (JSON):
   ```json
   {
     "steps": [
       {
         "id": "stats",
         "action": "llm.chat",
         "params": {
           "prompt": "Say hello to {{ event.payload.name }}",
           "model": "gpt-4"
         }
       }
     ]
   }
   ```
5. Check `Is Live` and Save.

## Step 4: Test

Send a webhook:
```bash
curl -X POST http://localhost:8000/api/v1/webhooks/default/user.signup \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'
```

Check the **Dashboard** or **Executions** tab in Admin Studio to see the result!
