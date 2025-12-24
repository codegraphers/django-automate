from django.core.management.base import BaseCommand
from automate.models import Automation, TriggerSpec, Workflow, TriggerTypeChoices

class Command(BaseCommand):
    help = "Seeds a demo automation"

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")
        
        # 1. Automation
        auto, created = Automation.objects.get_or_create(
            name="Demo Workflow",
            defaults={
                "slug": "demo-workflow",
                "enabled": True,
                "environment": "dev"
            }
        )
        if not created:
            self.stdout.write("Demo automation already exists.")
            return

        # 2. Trigger (Manual)
        TriggerSpec.objects.create(
            automation=auto,
            type=TriggerTypeChoices.MANUAL,
            config={},
            enabled=True
        )
        
        # 3. Workflow
        Workflow.objects.create(
            automation=auto,
            version=1,
            is_live=True,
            graph={
                "nodes": [
                    {
                        "id": "step1",
                        "type": "logging",
                        "config": {"msg": "Hello from Demo!"},
                        "next": []
                    }
                ],
                "edges": []
            }
        )
        self.stdout.write(self.style.SUCCESS("Demo seeded successfully."))
