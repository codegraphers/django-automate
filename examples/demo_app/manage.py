#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""

    # Add package source to path for easy dev
    curr_dir = Path(__file__).resolve().parent
    sys.path.append(str(curr_dir.parent / "packages" / "django_automate" / "src"))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'example_project.settings')

    # Add the package source to sys.path so we can run without installing
    # This simulates "editable" install
    BASE_DIR = Path(__file__).resolve().parent
    PACKAGE_DIR = BASE_DIR.parent / "packages" / "django_automate" / "src"
    sys.path.insert(0, str(PACKAGE_DIR))

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
