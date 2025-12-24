"""
Management command to create a sample workflow for testing.

Usage:
    python manage.py create_sample_workflow
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a sample workflow for testing the execution system"

    def handle(self, *args, **options):
        from automate.models import Automation, Prompt, PromptVersion, Rule, TriggerSpec, Workflow  # noqa: PLC0415

        # 1. Create or get test automation
        automation, created = Automation.objects.get_or_create(
            slug="order-notification",
            defaults={"name": "High Value Order Notification", "enabled": True, "environment": "default"},
        )

        if created:
            self.stdout.write(f"Created automation: {automation.name}")
        else:
            self.stdout.write(f"Using existing automation: {automation.name}")

        # 2. Add trigger
        trigger, _ = TriggerSpec.objects.get_or_create(
            automation=automation, type="webhook", defaults={"config": {"event_type": "order.created"}, "enabled": True}
        )
        self.stdout.write(f"  Trigger: {trigger.type}")

        # 3. Add rule (amount >= 100)
        rule, _ = Rule.objects.get_or_create(
            automation=automation,
            defaults={"priority": 1, "conditions": {">=": [{"var": "event.payload.amount"}, 100]}, "enabled": True},
        )
        self.stdout.write("  Rule: amount >= 100")

        # 4. Create a simple summary prompt
        prompt, _ = Prompt.objects.get_or_create(
            slug="order_summarizer",
            defaults={"name": "Order Summarizer", "description": "Summarizes an order for notifications"},
        )

        PromptVersion.objects.update_or_create(
            prompt=prompt,
            version=1,
            defaults={
                "status": "approved",
                "system_template": "You are a helpful assistant that summarizes orders concisely.",
                "user_template": """Summarize this order in one sentence for a Slack notification:

Order ID: {{ event.order_id }}
Customer: {{ event.customer_name }}
Amount: ${{ event.amount }}
Items: {{ event.items | tojson }}

Keep it brief and professional.""",
            },
        )
        self.stdout.write("  Prompt: order_summarizer (v1)")

        # 5. Create workflow with steps
        workflow_graph = {
            "nodes": [
                {
                    "id": "filter_high_value",
                    "type": "filter",
                    "name": "Check High Value",
                    "config": {"condition": {">=": [{"var": "event.payload.amount"}, 100]}, "on_fail": "stop"},
                },
                {
                    "id": "llm_summarize",
                    "type": "llm",
                    "name": "Generate Summary",
                    "config": {
                        "prompt_slug": "order_summarizer",
                        "variables": {
                            "order_id": "{{ event.payload.order_id }}",
                            "customer_name": "{{ event.payload.customer_name }}",
                            "amount": "{{ event.payload.amount }}",
                            "items": "{{ event.payload.items }}",
                        },
                    },
                },
                {
                    "id": "slack_notify",
                    "type": "action",
                    "name": "Send to Slack",
                    "config": {
                        "action_type": "http",
                        "method": "POST",
                        "url": "https://httpbin.org/post",  # Test endpoint instead of real Slack
                        "headers": {"Content-Type": "application/json"},
                        "body": {"text": "{{ previous.llm_summarize }}", "channel": "#orders"},
                    },
                },
            ],
            "config": {"name": "High Value Order → LLM → Slack"},
        }

        workflow, created = Workflow.objects.update_or_create(
            automation=automation, version=1, defaults={"graph": workflow_graph, "is_live": True}
        )

        self.stdout.write(f"  Workflow: v{workflow.version} ({'created' if created else 'updated'})")

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("✅ Sample workflow created!"))
        self.stdout.write("")
        self.stdout.write("To test, create an event and execution:")
        self.stdout.write("")
        self.stdout.write("  from automate.models import Event, Execution")
        self.stdout.write("  ")
        self.stdout.write("  event = Event.objects.create(")
        self.stdout.write("      event_type='order.created',")
        self.stdout.write("      source='webhook',")
        self.stdout.write("      payload={")
        self.stdout.write("          'order_id': 'ORD-123',")
        self.stdout.write("          'customer_name': 'John Doe',")
        self.stdout.write("          'amount': 150,")
        self.stdout.write("          'items': ['Widget A', 'Widget B']")
        self.stdout.write("      }")
        self.stdout.write("  )")
        self.stdout.write("  ")
        self.stdout.write("  execution = Execution.objects.create(")
        self.stdout.write("      event=event,")
        self.stdout.write(f"      automation_id='{automation.id}',")
        self.stdout.write("      workflow_version=1,")
        self.stdout.write("      status='queued'")
        self.stdout.write("  )")
        self.stdout.write("")
        self.stdout.write("Then run: python manage.py run_executions")
