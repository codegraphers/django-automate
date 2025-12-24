from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.artifacts import ArtifactViewSet
from .views.endpoints import EndpointViewSet
from .views.executions import ExecutionViewSet
from .views.ingestion import EventIngestionView
from .views.jobs import JobViewSet
from .views.providers import ProviderViewSet

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'executions', ExecutionViewSet, basename='execution')
router.register(r'providers', ProviderViewSet, basename='provider')
router.register(r'endpoints', EndpointViewSet, basename='endpoint')
router.register(r'artifacts', ArtifactViewSet, basename='artifact')

urlpatterns = [
    # Router endpoints (CRUD / ViewSets)
    path('', include(router.urls)),

    # Singular endpoints
    path('events/ingest', EventIngestionView.as_view(), name='event-ingest'),
]
