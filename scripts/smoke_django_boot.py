#!/usr/bin/env python3
"""
Smoke test: boot Django with django-automate full-suite apps.

Usage (after installing the wheel or editable install):
  python scripts/smoke_django_boot.py
  AUTOMATE_SMOKE_SKIP_MIGRATE=1 python scripts/smoke_django_boot.py
  AUTOMATE_SMOKE_APPS="automate,automate_core,rag,automate_api" python scripts/smoke_django_boot.py
"""

from __future__ import annotations

import os
import sys
import traceback

DEFAULT_APPS: list[str] = [
    # Django essentials
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    # 3rd-party
    "rest_framework",
    # Django Automate suite
    "automate",
    "automate_core",
    "automate_governance",
    "automate_llm",
    "automate_modal",  # Required before automate_datachat (imports models)
    "automate_connectors",
    "automate_interop",
    "automate_observability",
    "automate_studio",
    "automate_datachat",
    "rag",
    "automate_api",
]


def _env_apps() -> list[str]:
    raw = os.getenv("AUTOMATE_SMOKE_APPS", "").strip()
    if not raw:
        return DEFAULT_APPS
    # Allow passing short list like: "automate,automate_core,rag,automate_api"
    apps = [a.strip() for a in raw.split(",") if a.strip()]
    # If user provides apps, still keep Django essentials + DRF unless they explicitly pass them.
    return apps


def main() -> int:
    try:
        from django.conf import settings
    except Exception as e:
        print("❌ Django is not importable. Is it installed in this environment?")
        print(repr(e))
        return 2

    installed_apps = _env_apps()
    skip_migrate = os.getenv("AUTOMATE_SMOKE_SKIP_MIGRATE", "0") in ("1", "true", "yes")

    if not settings.configured:
        settings.configure(
            SECRET_KEY=os.getenv("DJANGO_SECRET_KEY", "smoke"),
            DEBUG=False,
            USE_TZ=True,
            TIME_ZONE="UTC",
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=installed_apps,
            ROOT_URLCONF=os.getenv("AUTOMATE_SMOKE_ROOT_URLCONF", "automate.urls"),
            MIDDLEWARE=[
                "django.middleware.security.SecurityMiddleware",
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.middleware.common.CommonMiddleware",
                "django.middleware.csrf.CsrfViewMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
                "django.contrib.messages.middleware.MessageMiddleware",
            ],
            TEMPLATES=[
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "DIRS": [],
                    "APP_DIRS": True,
                    "OPTIONS": {
                        "context_processors": [
                            "django.template.context_processors.debug",
                            "django.template.context_processors.request",
                            "django.contrib.auth.context_processors.auth",
                            "django.contrib.messages.context_processors.messages",
                        ],
                    },
                }
            ],
            # Keep it explicit: tests should not depend on host networking.
            ALLOWED_HOSTS=["*"],
        )

    # Helpful: show which apps are being attempted.
    print("🔎 Smoke boot apps:")
    for a in installed_apps:
        print(f"  - {a}")

    try:
        import django
        django.setup()
    except Exception:
        print("\n❌ django.setup() failed. This is almost always an import error or AppConfig issue.")
        traceback.print_exc()
        return 3

    try:
        from django.core.management import call_command
        call_command("check", verbosity=0)
    except Exception:
        print("\n❌ Django system checks failed.")
        traceback.print_exc()
        return 4

    if not skip_migrate:
        try:
            from django.core.management import call_command
            call_command("migrate", verbosity=0)
        except Exception:
            print("\n❌ migrate failed. Usually indicates missing migrations in wheel or bad migration dependencies.")
            traceback.print_exc()
            return 5

    print("\n✅ Django Automate smoke boot OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
