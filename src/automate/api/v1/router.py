from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.endpoints import EndpointViewSet
from .views.executions import ExecutionViewSet
from .views.jobs import JobViewSet
from .views.providers import ProviderViewSet

# from .views.artifacts import ArtifactViewSet

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'executions', ExecutionViewSet, basename='execution')
router.register(r'providers', ProviderViewSet, basename='provider')
router.register(r'endpoints', EndpointViewSet, basename='endpoint')
# router.register(r'artifacts', ArtifactViewSet, basename='artifact')

urlpatterns = [
    path('', include(router.urls)),
]
