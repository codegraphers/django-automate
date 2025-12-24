# Your First Automation

Let's build a simple automation that logs a message when you trigger it manually.

## 1. Create Automation
1. Go to **Admin > Automations**.
2. Click **Add Automation**.
3. **Name**: `Hello World`
4. **Slug**: `hello-world`
5. **Enabled**: Checked.
6. Click **Save**.

## 2. Add Trigger
1. On the Automation page, scroll to **Trigger Specs**.
2. Click **Add another Trigger Spec**.
3. **Type**: `Manual`
4. **Config**: `{}` (Empty JSON)
5. **Enabled**: Checked.
6. Click **Save**.

## 3. Define Workflow
1. Go to **Admin > Workflows**.
2. Click **Add Workflow**.
3. **Automation**: Select `Hello World`.
4. **Version**: `1`
5. **Is Live**: Checked.
6. **Graph**: Paste the following JSON:
   ```json
   {
     "nodes": [
       {
         "id": "step1",
         "type": "logging",
         "config": {
           "msg": "Hello from Django Automate! Payload: {{ event.payload }}"
         },
         "next": []
       }
     ],
     "edges": []
   }
   ```
7. Click **Save**.

## 4. Test It
1. Use the **Manual Trigger API** (via Swagger or curl):
   ```bash
   curl -X POST http://localhost:8000/automate/manual \
     -H "Content-Type: application/json" \
     -d '{"event": "hello-world", "payload": {"name": "User"}}'
   ```
2. Check **Admin > Executions**. You should see a successful execution!
