from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from .views.artifacts import ArtifactViewSet
from .views.endpoints import EndpointViewSet
from .views.events import EventIngestView
from .views.executions import ExecutionViewSet
from .views.jobs import JobViewSet
from .views.providers import ProviderViewSet

router = DefaultRouter()
router.register(r"providers", ProviderViewSet, basename="providers")
router.register(r"endpoints", EndpointViewSet, basename="endpoints")
router.register(r"jobs", JobViewSet, basename="jobs")
router.register(r"executions", ExecutionViewSet, basename="executions")
router.register(r"artifacts", ArtifactViewSet, basename="artifacts")

urlpatterns = [
    path("", include(router.urls)),
    path("events/ingest", EventIngestView.as_view(), name="events-ingest"),

    # Docs
    path("schema/", SpectacularAPIView.as_view(), name="schema-v1"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema-v1"), name="docs-v1"),
]
