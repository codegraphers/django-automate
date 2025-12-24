from django.core.management.base import BaseCommand

from automate.models import Automation, TriggerSpec, Workflow


class Command(BaseCommand):
    help = "Seeds the database with sample automations."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Automations...")

        # 1. Welcome Automation
        a1, _ = Automation.objects.get_or_create(
            slug="welcome-user",
            defaults={"name": "Welcome New User", "tenant_id": "default"}
        )

        from automate.models import TriggerTypeChoices
        TriggerSpec.objects.get_or_create(
            automation=a1,
            type=TriggerTypeChoices.MODEL_SIGNAL,
            defaults={
                "filter_config": {"model": "auth.User", "event": "created"}
            }
        )

        Workflow.objects.get_or_create(
            automation=a1,
            version=1,
            defaults={
                "is_live": True,
                "graph": {
                    "nodes": [
                        {"id": "log", "type": "logging", "config": {"message": "New User Created"}, "next": ["slack_notify"]},
                        {"id": "slack_notify", "type": "slack", "config": {"channel": "C123", "message": "User joined!"}, "next": []}
                    ]
                }
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded automations!"))
