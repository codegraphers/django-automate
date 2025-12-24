from django.core.management.base import BaseCommand
from automate.dlq import DeadLetter
from automate.outbox import OutboxStatusChoices

class Command(BaseCommand):
    help = "Replay dead letters"

    def handle(self, *args, **options):
        dls = DeadLetter.objects.all()
        count = 0
        for dl in dls:
            if dl.outbox:
                dl.outbox.status = OutboxStatusChoices.PENDING
                dl.outbox.attempts = 0
                dl.outbox.next_attempt_at = None
                dl.outbox.save()
                dl.delete()
                count += 1
        self.stdout.write(f"Replayed {count} dead letters.")
