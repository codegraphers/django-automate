from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .api import schema, workflows, zapier
from .views import manual

urlpatterns = [
    path("zapier/triggers", zapier.list_triggers, name="zapier_triggers"),
    path("zapier/subscribe", zapier.subscribe, name="zapier_subscribe"),
    path("zapier/unsubscribe", zapier.unsubscribe, name="zapier_unsubscribe"),
    path("manual", manual.ManualTriggerView.as_view(), name="manual_trigger"),
    # Workflow API
    path("workflows/", workflows.create_workflow, name="create_workflow"),
    path("workflows/<int:id>/", workflows.workflow_detail, name="workflow_detail"),
    # Metadata API
    path("schema/apps/", schema.list_apps_and_models, name="schema_apps"),
    # Swagger / Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
