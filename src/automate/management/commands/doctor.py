import sys

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.utils import OperationalError

from automate_core.providers.registry import registry


class Command(BaseCommand):
    help = "Diagnose system health and configuration"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Django Automate Doctor"))
        self.stdout.write("Checking system health...\n")

        has_errors = False

        # 1. Database
        self.stdout.write("Database... ", ending="")
        try:
            connection = connections[DEFAULT_DB_ALIAS]
            connection.ensure_connection()
            self.stdout.write(self.style.SUCCESS("OK"))
        except OperationalError:
            self.stdout.write(self.style.ERROR("FAIL"))
            self.stdout.write(f"  Could not connect to database at {settings.DATABASES['default']['NAME']}")
            has_errors = True
        except Exception as e:
            self.stdout.write(self.style.ERROR("FAIL"))
            self.stdout.write(f"  {e}")
            has_errors = True

        # 2. Redis/Cache
        self.stdout.write("Cache/Redis... ", ending="")
        try:
            cache.set("doctor_check", "ok", 10)
            val = cache.get("doctor_check")
            if val == "ok":
                self.stdout.write(self.style.SUCCESS("OK"))
            else:
                self.stdout.write(self.style.ERROR("FAIL"))
                self.stdout.write("  Cache read/write mismatch")
                has_errors = True
        except Exception as e:
            self.stdout.write(self.style.ERROR("FAIL"))
            self.stdout.write(f"  {e}")
            has_errors = True

        # 3. Providers
        self.stdout.write("Providers... ", ending="")
        try:
            reg = registry()
            count = len(reg.list())
            if count > 0:
                self.stdout.write(self.style.SUCCESS(f"OK ({count} found)"))
            else:
                self.stdout.write(self.style.WARNING("WARNING"))
                self.stdout.write("  No providers registered. Check INSTALLED_APPS or AUTOMATE_PROVIDERS.")
        except Exception as e:
            self.stdout.write(self.style.ERROR("FAIL"))
            self.stdout.write(f"  {e}")
            has_errors = True

        # 4. Secrets
        self.stdout.write("Secrets Engine... ", ending="")
        try:
            from automate.secrets_backend import SecretsManager
            SecretsManager.get_backend()
            self.stdout.write(self.style.SUCCESS("OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR("FAIL"))
            self.stdout.write(f"  {e}")
            has_errors = True

        self.stdout.write("\n")
        if has_errors:
            self.stdout.write(self.style.ERROR("System has issues. See details above."))
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("System is healthy and ready for automation."))
