# Installation & Configuration

## 1. What you'll build
A properly configured Django project ready for automation, with the database schema and admin interface enabled.

## 2. Prerequisites
*   Python 3.10+
*   Django 4.2+ project
*   (Recommended) Postgres database

## 3. Steps

### Install the Package
```bash
pip install django-automate
```

### Configure Settings
Add the apps to your `INSTALLED_APPS` in `settings.py`:
```python
INSTALLED_APPS = [
    # ... django apps ...
    'automate', 
    'automate_core',
    'automate_governance',
    'automate_llm',
    'automate_studio',
    'automate_observability',
    'rest_framework',
]
```

Add the minimal configuration:
```python
DJANGO_AUTOMATE = {
    "ENABLED": True,
    "SECRET_KEY_PREFIX": "AUTOMATE_", 
    "EXECUTION": {
        "timeout_seconds": 60,
        "max_retries": 3,
    }
}
```

### URL Routing
Add the studio and API routes to `urls.py`:
```python
from django.urls import path, include

urlpatterns = [
    # ...
    path('studio/', include('automate_studio.urls')),
    path('api/automate/', include('automate_core.urls')),
]
```

### Run Migrations
```bash
python manage.py migrate
```

## 4. Expected Output
Run the server:
```bash
python manage.py runserver
```
Visit `http://localhost:8000/studio/wizard/`. You should see the Automation Studio.

## 5. Next Steps
*   [Create your first automation](first-automation.md)
