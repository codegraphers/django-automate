"""
Management command to reap stale outbox items.

Recovers items stuck in RUNNING status after worker crashes.

Usage:
    python manage.py outbox_reap
    python manage.py outbox_reap --stale-threshold=600 --dry-run
"""

from django.core.management.base import BaseCommand

from automate_core.outbox.reaper import OutboxReaper


class Command(BaseCommand):
    help = "Reap stale outbox items that are stuck in RUNNING status"

    def add_arguments(self, parser):
        parser.add_argument(
            "--stale-threshold",
            type=int,
            default=300,
            help="Seconds after lease expiry to consider stale (default: 300)",
        )
        parser.add_argument(
            "--max-batch",
            type=int,
            default=100,
            help="Maximum items to reap per run (default: 100)",
        )
        parser.add_argument(
            "--retry-delay",
            type=int,
            default=60,
            help="Seconds before reaped items can be retried (default: 60)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be reaped without actually reaping",
        )

    def handle(self, *args, **options):
        reaper = OutboxReaper(
            stale_threshold_seconds=options["stale_threshold"],
            max_reap_batch=options["max_batch"],
            retry_delay_seconds=options["retry_delay"],
        )

        if options["dry_run"]:
            stale_count = reaper.get_stale_count()
            self.stdout.write(
                f"🔍 Dry run: Found {stale_count} stale items that would be reaped"
            )
            return

        reaped_count = reaper.reap_stale_items()

        if reaped_count > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Reaped {reaped_count} stale outbox items")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ No stale outbox items found")
            )
