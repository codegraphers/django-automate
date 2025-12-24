"""
Management command to run pending workflow executions.

Usage:
    python manage.py run_executions              # Run up to 10 pending
    python manage.py run_executions --limit=50   # Run up to 50 pending
    python manage.py run_executions --daemon     # Run continuously
"""
import time

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run pending workflow executions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum executions to process per batch"
        )
        parser.add_argument(
            "--daemon",
            action="store_true",
            help="Run continuously (poll every 5 seconds)"
        )
        parser.add_argument(
            "--poll-interval",
            type=int,
            default=5,
            help="Seconds between polls when in daemon mode"
        )

    def handle(self, *args, **options):
        from automate.step_executors.workflow_executor import run_pending_executions

        limit = options["limit"]
        daemon = options.get("daemon")
        poll_interval = options.get("poll_interval", 5)

        if daemon:
            self.stdout.write(self.style.SUCCESS(f"Starting execution daemon (poll every {poll_interval}s)..."))
            self.stdout.write("Press Ctrl+C to stop\n")

            try:
                while True:
                    results = run_pending_executions(limit=limit)

                    if results["success"] or results["failed"]:
                        self.stdout.write(
                            f"Processed: {results['success']} success, {results['failed']} failed"
                        )

                    time.sleep(poll_interval)

            except KeyboardInterrupt:
                self.stdout.write("\nDaemon stopped.")
        else:
            results = run_pending_executions(limit=limit)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Completed: {results['success']} success, {results['failed']} failed"
                )
            )
