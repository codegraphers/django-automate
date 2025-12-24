# Tutorials

Guided walkthroughs to build production workflows.

## 1. Trigger: Model Signals
**Goal**: Send a Welcome Email when a `User` model is created.

1.  **Define Trigger**:
    ```json
    {
      "type": "signal",
      "config": {
        "model": "auth.User",
        "signal": "post_save",
        "condition": "created == true" // Only on create, not update
      }
    }
    ```
2.  **Add Action**: Use the `smtp.send` or `http.post` connector (e.g., to SendGrid).
    ```json
    {
      "action": "http.post",
      "config": {
        "url": "https://api.sendgrid.com/v3/mail/send",
        "headers": {
            "Authorization": "Bearer {{$secret.SENDGRID_KEY}}"
        },
        "json": {
            "personalizations": [{"to": [{"email": "{{event.instance.email}}"}]}],
            "subject": "Welcome!"
        }
      }
    }
    ```

## 2. Trigger: Inbound Webhook (Stripe)
**Goal**: Provision access when a `checkout.session.completed` webhook arrives.

1.  **Configure Ingestion**:
    Set up a generic webhook endpoint `/api/automate/webhooks/stripe/`.
    Configure signature verification middleware in `settings.py`.
2.  **Define Rule**:
    ```json
    {
      "and": [
        { "==": [{ "var": "type" }, "checkout.session.completed"] },
        { "==": [{ "var": "data.object.payment_status" }, "paid"] }
      ]
    }
    ```
3.  **Add Action**: Call your internal API to provision access.

## 3. Human-in-the-loop Approval
**Goal**: Require admin approval for refunds > $500.

1.  **Step 1**: Check value.
    ```json
    { "if": [ { ">": [{ "var": "amount" }, 500] }, "needs_review", "auto_approve" ] }
    ```
2.  **Step 2 (Branch: needs_review)**: Send Slack notification with "Approve" button.
3.  **Step 3**: `core.wait_for_signal` (Pause execution).
    The workflow suspends until a specific callback signal is received from the Slack interaction.
4.  **Step 4**: Process Refund.

## 4. LLM Chaining
**Goal**: Summarize support ticket and suggest reply.

1.  **Step 1**: `llm.chat`.
    *   **Prompt**: "Summarize this ticket: {{event.payload.description}}"
    *   **Model**: `gpt-4o`
2.  **Step 2**: `llm.chat`.
    *   **Prompt**: "Draft a polite reply based on this summary: {{step.1.output.text}}"
    *   **JSON Schema**: Enforce output structure `{"subject": "...", "body": "..."}`.
3.  **Step 3**: Save draft to Zendesk/Freshdesk via HTTP.
