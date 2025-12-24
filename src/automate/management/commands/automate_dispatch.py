import time

from django.core.management.base import BaseCommand

from automate.dispatcher import Dispatcher


class Command(BaseCommand):
    help = "Run the dispatcher loop"

    def handle(self, *args, **options):
        dispatcher = Dispatcher()
        self.stdout.write("Starting dispatcher loop...")
        while True:
            try:
                dispatcher.dispatch_batch()
                time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write("Stopping...")
                break
            except Exception as e:
                self.stderr.write(f"Error: {e}")
                time.sleep(5)
