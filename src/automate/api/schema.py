from django.apps import apps
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse


@staff_member_required
def list_apps_and_models(request):
    """
    GET /api/automate/schema/
    Returns a hierarchical list of apps and their models.
    Structure:
    [
        {
            "app_label": "auth",
            "verbose_name": "Authentication and Authorization",
            "models": [
                {
                    "name": "User",
                    "verbose_name": "User",
                    "db_table": "auth_user"
                },
                ...
            ]
        },
        ...
    ]
    """
    data = []

    for app_config in apps.get_app_configs():
        # Optional: Filter out internal or unwanted apps?
        # For now, let's expose everything but maybe we can add a simple exclude list
        if app_config.label in ["admin", "contenttypes", "sessions", "messages", "staticfiles"]:
            continue

        app_data = {"app_label": app_config.label, "verbose_name": app_config.verbose_name, "models": []}

        for model in app_config.get_models():
            app_data["models"].append(
                {
                    "name": model.__name__,
                    "verbose_name": str(model._meta.verbose_name),
                    "db_table": model._meta.db_table,
                }
            )

        if app_data["models"]:
            data.append(app_data)

    return JsonResponse({"apps": data})
