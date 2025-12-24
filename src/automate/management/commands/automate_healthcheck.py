from django.core.management.base import BaseCommand
from automate.models import Outbox, OutboxStatusChoices
from automate.dlq import DeadLetter

class Command(BaseCommand):
    help = "Healthcheck stats"

    def handle(self, *args, **options):
        pending = Outbox.objects.filter(status=OutboxStatusChoices.PENDING).count()
        failed = Outbox.objects.filter(status=OutboxStatusChoices.FAILED).count()
        dead = Outbox.objects.filter(status=OutboxStatusChoices.DEAD).count()
        dlq = DeadLetter.objects.count()
        
        self.stdout.write(f"Outbox Pending: {pending}")
        self.stdout.write(f"Outbox Failed: {failed}")
        self.stdout.write(f"Outbox Dead: {dead}")
        self.stdout.write(f"DLQ Size: {dlq}")
