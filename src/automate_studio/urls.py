from django.urls import path

from .views import CorrelationExplorerView, DashboardView, TestProviderView, WizardView, RuleTesterView

urlpatterns = [
    path("studio/dashboard/", DashboardView.as_view(), name="studio_dashboard"),
    path("studio/correlation/", CorrelationExplorerView.as_view(), name="studio_correlation"),
    path("studio/wizard/", WizardView.as_view(), name="studio_wizard"),
    path("studio/tester/", RuleTesterView.as_view(), name="studio_tester"),
    # Redirect sample explorer link to main correlation view for now
    path("studio/explorer/run-123/", CorrelationExplorerView.as_view()), 
    path("providers/<uuid:provider_id>/test/", TestProviderView.as_view(), name="studio_provider_test"),
]
