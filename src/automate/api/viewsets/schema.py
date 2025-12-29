"""
Schema API ViewSet.

Provides schema inspection endpoints for the canvas UI.
"""

from django.apps import apps
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class SchemaViewSet(viewsets.ViewSet):
    """
    Schema Inspection ViewSet.
    
    Provides endpoints for introspecting Django apps and models.
    
    Class Attributes:
        excluded_apps: Apps to exclude from listing
        
    Endpoints:
        GET /api/schema/apps/ - List apps and their models
        
    Example - Customize excluded apps:
        class MySchemaViewSet(SchemaViewSet):
            excluded_apps = ['admin', 'auth', 'sessions']
    """
    
    authentication_classes = []
    permission_classes = []
    
    excluded_apps = [
        'admin',
        'contenttypes', 
        'sessions',
        'messages',
        'staticfiles',
    ]
    
    def get_excluded_apps(self):
        """Get list of excluded apps. Override to customize."""
        from django.conf import settings
        api_settings = getattr(settings, 'AUTOMATE_API', {})
        return api_settings.get('SCHEMA_EXCLUDED_APPS', self.excluded_apps)
    
    def check_staff(self, request):
        """Check that user is staff."""
        if not request.user or not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Staff access required')
    
    @extend_schema(
        responses={'200': {'type': 'object', 'properties': {'apps': {'type': 'array'}}}},
        description="List all apps and their models."
    )
    @action(detail=False, methods=['get'], url_path='apps')
    def list_apps(self, request):
        """
        List apps and models.
        
        Returns hierarchical structure of apps and their models
        for use in the canvas UI.
        """
        self.check_staff(request)
        
        excluded = self.get_excluded_apps()
        data = []
        
        for app_config in apps.get_app_configs():
            if app_config.label in excluded:
                continue
            
            app_data = {
                'app_label': app_config.label,
                'verbose_name': app_config.verbose_name,
                'models': []
            }
            
            for model in app_config.get_models():
                app_data['models'].append({
                    'name': model.__name__,
                    'verbose_name': str(model._meta.verbose_name),
                    'db_table': model._meta.db_table,
                })
            
            if app_data['models']:
                data.append(app_data)
        
        return Response({'apps': data})
