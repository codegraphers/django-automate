# Admin Customization Guide

Django Automate is built on the Django Admin, but deeply customized for production operations. We use standard Django patterns that are easy to extend.

## Key Features

1.  **JSON Editor**: We use `django-json-widget` for all JSON fields, providing a syntax-highlighted editor instead of a text area.
2.  **Autocomplete**: Foreign keys use `autocomplete_fields` to support large datasets (e.g., millions of jobs) without loading dropdowns.
3.  **Import/Export**: Most models support CSV/JSON import/export via `django-import-export`, useful for bulk configuration or analytics.
4.  **Test Consoles**: Custom actions (like "Test Console") are injected via `get_urls` and custom templates.

## How to Customize

### Overriding functionality
You can inherit from our Admin classes in your own app and unregister/register them.

```python
# your_app/admin.py
from django.contrib import admin
from automate_modal.models import ModalEndpoint
from automate_modal.admin import ModalEndpointAdmin

admin.site.unregister(ModalEndpoint)

@admin.register(ModalEndpoint)
class CustomEndpointAdmin(ModalEndpointAdmin):
    # Add your custom logic
    pass
```

### Adding new Actions
Use standard Django Admin actions.

```python
@admin.action(description='Reset rate limits')
def reset_limits(modeladmin, request, queryset):
    queryset.update(rate_limit={})
```

### Custom Views
Override `get_urls` to add custom operational views, as seen in `ModalEndpointAdmin` for the Test Console.
