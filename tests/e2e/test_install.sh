#!/bin/bash
set -e

# Smoke Test for Wheel Installation
# Usage: ./tests/e2e/test_install.sh

echo "Building wheel..."
(cd packages/django_automate && rm -rf dist && hatch build -t wheel)

WHEEL_FILE=$(find packages/django_automate/dist -name "*.whl" | head -n 1)
# Make absolute
WHEEL_FILE="$PWD/$WHEEL_FILE"
echo "Found wheel: $WHEEL_FILE"

TEST_DIR=$(mktemp -d)
echo "Created temp dir: $TEST_DIR"

# Cleanup on exit
function cleanup {
  rm -rf "$TEST_DIR"
  echo "Cleaned up."
}
trap cleanup EXIT

cd "$TEST_DIR"

echo "Creating venv..."
python3 -m venv venv
source venv/bin/activate

echo "Installing wheel..."
pip install "$WHEEL_FILE"
pip install django

echo "Creating Django project..."
django-admin startproject smoketest .

echo "Configuring installed apps..."
# Add 'automate' to INSTALLED_APPS in settings.py
sed -i.bak "s/'django.contrib.staticfiles',/'django.contrib.staticfiles', 'automate',/" smoketest/settings.py

echo "Running migrate..."
python manage.py migrate

echo "Running check..."
python manage.py check

echo "Smoke test PASSED!"
