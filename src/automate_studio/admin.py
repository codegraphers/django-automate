from django.contrib import admin
from django.urls import path

from .views.explorer import ExecutionExplorerView
from .views.tester import RuleTesterView
from .views.wizard import AutomationWizardView


class AutomateAdminSite(admin.AdminSite):
    site_header = "Automate Studio"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("studio/wizard/", AutomationWizardView.as_view(), name="studio_wizard"),
            path("studio/tester/", RuleTesterView.as_view(), name="studio_tester"),
            path("studio/explorer/<str:run_id>/", ExecutionExplorerView.as_view(), name="studio_explorer_detail"),
        ]
        return custom_urls + urls


# We hook into standard admin for now, or replace it.
# For plugin style, we might just register views in urls.py of the project
