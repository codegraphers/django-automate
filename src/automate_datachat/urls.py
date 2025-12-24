from django.urls import path
from . import views

urlpatterns = [
    path('api/chat/', views.chat_api, name='datachat_api'),
    path('api/history/', views.history_api, name='datachat_history'),
    
    # Embed API
    path('embed/v1/<uuid:embed_id>/widget.js', views.embed_widget_js, name='embed_widget_js'),
    path('embed/v1/<uuid:embed_id>/chat', views.embed_chat_api, name='embed_chat_api'),
    path('embed/v1/<uuid:embed_id>/config', views.embed_config_api, name='embed_config_api'),
]

