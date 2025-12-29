"""
DataChat URL Configuration.

Uses DRF router for class-based ViewSets.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import ChatViewSet, EmbedViewSet

router = DefaultRouter()
router.register(r'chat', ChatViewSet, basename='datachat')

urlpatterns = [
    # Chat API (ViewSet-based)
    path('api/', include(router.urls)),
    
    # Embed API (custom routing for embed_id)
    path(
        'embed/<uuid:pk>/widget.js',
        EmbedViewSet.as_view({'get': 'widget_js'}),
        name='embed_widget_js'
    ),
    path(
        'embed/<uuid:pk>/chat/',
        EmbedViewSet.as_view({'post': 'chat', 'options': 'chat'}),
        name='embed_chat'
    ),
    path(
        'embed/<uuid:pk>/config/',
        EmbedViewSet.as_view({'get': 'config'}),
        name='embed_config'
    ),
]
