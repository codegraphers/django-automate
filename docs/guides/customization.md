# Customization Guide

This guide covers how to customize and extend Django Automate components.

## Table of Contents

1. [Configuration via Settings](#configuration-via-settings)
2. [Extending Base Classes](#extending-base-classes)
3. [Custom ViewSets](#custom-viewsets)
4. [Custom Serializers](#custom-serializers)
5. [Custom Permissions](#custom-permissions)
6. [Service Layer Customization](#service-layer-customization)
7. [Custom Providers](#custom-providers)

---

## Configuration via Settings

All Django Automate components are configurable via Django settings.

### API Settings

```python
# settings.py

AUTOMATE_API = {
    # Pagination
    'PAGINATION_PAGE_SIZE': 50,
    
    # Rate Limiting
    'RATE_LIMIT_PER_MINUTE': 120,
    
    # CORS
    'CORS_ALLOWED_ORIGINS': ['https://example.com'],
    'CORS_ALLOWED_METHODS': ['GET', 'POST', 'PUT', 'DELETE'],
    'CORS_ALLOWED_HEADERS': ['Content-Type', 'Authorization', 'X-API-Key'],
    
    # Authentication
    'API_KEY_HEADER': 'X-API-Key',
    'BEARER_TOKEN_HEADER': 'Authorization',
    
    # Schema Inspection
    'SCHEMA_EXCLUDED_APPS': ['admin', 'contenttypes', 'sessions'],
    
    # Throttling
    'THROTTLE_RATES': {
        'tenant': '120/min',
        'token': '60/min',
    },
}
```

### DataChat Settings

```python
AUTOMATE_DATACHAT = {
    'HISTORY_PAGE_SIZE': 20,
    'EMBED_RATE_LIMIT': 60,
    'EMBED_MAX_MESSAGE_LENGTH': 1000,
}
```

### RAG Settings

```python
AUTOMATE_RAG = {
    'DEFAULT_TOP_K': 5,
    'MAX_TOP_K': 100,
    'QUERY_TIMEOUT_SECONDS': 30,
}
```

### LLM Settings

```python
AUTOMATE_LLM = {
    'DEFAULT_PROVIDER': 'openai',
    'DEFAULT_MODEL': 'gpt-4',
    'MAX_RETRIES': 3,
    'TIMEOUT_SECONDS': 60,
}
```

---

## Extending Base Classes

### BaseViewSet

All ViewSets inherit from configurable base classes.

```python
from automate_api.v1.base import BaseViewSet

class MyCustomViewSet(BaseViewSet):
    """
    Custom ViewSet with inherited:
    - Authentication
    - Permission checking
    - Rate limiting
    - Tenant filtering
    - Pagination
    """
    pass
```

### Available Base Classes

| Class | Purpose | Features |
|-------|---------|----------|
| `BaseAPIView` | Single-endpoint views | Auth, permissions, throttling |
| `BaseViewSet` | ViewSet operations | + pagination, tenant filter |
| `BaseModelViewSet` | CRUD operations | + queryset, serializer |
| `BaseReadOnlyViewSet` | Read-only resources | List and retrieve only |

### Mixins

```python
from automate_api.v1.base import CORSMixin, TenantFilterMixin, RateLimitMixin

class MyAPIView(CORSMixin, BaseAPIView):
    """View with CORS support."""
    cors_allowed_origins = ['https://mysite.com']

class MyViewSet(TenantFilterMixin, BaseViewSet):
    """ViewSet with automatic tenant filtering."""
    tenant_field = 'organization_id'  # Custom field name

class RateLimitedView(RateLimitMixin, BaseAPIView):
    """View with custom rate limiting."""
    rate_limit_per_minute = 30
```

---

## Custom ViewSets

### Overriding ChatViewSet

```python
from automate_datachat.viewsets import ChatViewSet
from myapp.orchestrators import MyOrchestrator

class MyChatViewSet(ChatViewSet):
    """Custom chat with different orchestrator."""
    
    # Override orchestrator
    orchestrator_class = MyOrchestrator
    
    # Override history page size
    history_page_size = 25
    
    def get_orchestrator_class(self):
        """Dynamic orchestrator selection."""
        if self.request.user.is_superuser:
            return SuperOrchestrator
        return self.orchestrator_class
```

### Overriding WorkflowViewSet

```python
from automate.api.viewsets import WorkflowViewSet
from myapp.services import MyWorkflowService

class MyWorkflowViewSet(WorkflowViewSet):
    """Custom workflow handling."""
    
    service_class = MyWorkflowService
    
    def create(self, request):
        """Add custom logic before creation."""
        # Pre-processing
        self.validate_quota(request.user)
        
        # Call parent
        return super().create(request)
```

### Overriding RAGQueryViewSet

```python
from rag.api.viewsets import RAGQueryViewSet

class MyRAGViewSet(RAGQueryViewSet):
    """Custom RAG with enhanced logging."""
    
    default_top_k = 10
    
    def build_query_context(self, request, endpoint, trace_id):
        """Add custom context fields."""
        ctx = super().build_query_context(request, endpoint, trace_id)
        ctx.custom_field = request.headers.get('X-Custom')
        return ctx
    
    def log_query(self, **kwargs):
        """Enhanced logging."""
        super().log_query(**kwargs)
        send_to_analytics(kwargs)
```

---

## Custom Serializers

### Extending Serializers

```python
from automate_datachat.serializers import ChatRequestSerializer

class ExtendedChatRequestSerializer(ChatRequestSerializer):
    """Chat request with additional fields."""
    
    session_id = serializers.UUIDField(required=False)
    metadata = serializers.DictField(required=False)
    
    def validate_question(self, value):
        """Custom validation."""
        if len(value) < 5:
            raise serializers.ValidationError("Question too short")
        return value
```

### Using Custom Serializers

```python
class MyChatViewSet(ChatViewSet):
    serializer_class = ExtendedChatRequestSerializer
```

---

## Custom Permissions

### Creating Permissions

```python
from rest_framework import permissions

class IsProjectMember(permissions.BasePermission):
    """Check if user is member of the project."""
    
    message = "Must be a project member."
    
    def has_permission(self, request, view):
        project_id = request.headers.get('X-Project-ID')
        return request.user.projects.filter(id=project_id).exists()

class HasPremiumPlan(permissions.BasePermission):
    """Check if user has premium plan."""
    
    def has_permission(self, request, view):
        return request.user.subscription.is_premium
```

### Using Custom Permissions

```python
class MyViewSet(BaseViewSet):
    permission_classes = [IsProjectMember, HasPremiumPlan]
```

### Composing Permissions

```python
from rest_framework.permissions import AND, OR

class MyViewSet(BaseViewSet):
    permission_classes = [
        (IsProjectMember & HasPremiumPlan) | IsSuperUser
    ]
```

---

## Service Layer Customization

### Custom Workflow Service

```python
from automate.services import WorkflowService

class MyWorkflowService(WorkflowService):
    """Custom workflow logic."""
    
    trigger_type_map = {
        **WorkflowService.trigger_type_map,
        'custom_event': 'custom',
    }
    
    def create_automation(self, name, slug):
        """Add custom fields to automation."""
        automation = super().create_automation(name, slug)
        automation.custom_field = 'value'
        automation.save()
        return automation
    
    def create_trigger(self, automation, trigger_config):
        """Custom trigger setup."""
        super().create_trigger(automation, trigger_config)
        
        if trigger_config.get('event_type') == 'custom_event':
            self.setup_custom_trigger(automation, trigger_config)
```

---

## Custom Providers

### LLM Provider

```python
from automate_llm.providers import BaseLLMProvider

class MyLLMProvider(BaseLLMProvider):
    """Custom LLM provider."""
    
    name = 'my_llm'
    
    def generate(self, prompt, **kwargs):
        """Generate completion."""
        return my_api.complete(prompt)
    
    def validate_config(self, config):
        """Validate provider config."""
        if 'api_key' not in config:
            raise ValueError("API key required")
```

### Registering Providers

```python
# In your app's apps.py
class MyAppConfig(AppConfig):
    def ready(self):
        from automate_llm.providers import register_provider
        from .providers import MyLLMProvider
        
        register_provider('my_llm', MyLLMProvider)
```

### Using Entry Points

```toml
# pyproject.toml
[project.entry-points."automate.llm_providers"]
my_llm = "myapp.providers:MyLLMProvider"
```

---

## URL Configuration

### Registering Custom ViewSets

```python
# urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from myapp.viewsets import MyChatViewSet, MyWorkflowViewSet

router = DefaultRouter()
router.register('chat', MyChatViewSet, basename='custom-chat')
router.register('workflows', MyWorkflowViewSet, basename='custom-workflows')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
```

---

## Examples

### Complete Custom Implementation

```python
# myapp/viewsets.py
from automate_api.v1.base import BaseViewSet, CORSMixin
from automate_datachat.viewsets import ChatViewSet

class EnterpriseDataChatViewSet(CORSMixin, ChatViewSet):
    """Enterprise DataChat with custom features."""
    
    # Configuration
    cors_allowed_origins = ['https://internal.company.com']
    history_page_size = 50
    
    # Custom orchestrator
    from myapp.orchestrators import EnterpriseOrchestrator
    orchestrator_class = EnterpriseOrchestrator
    
    def check_permissions(self, request):
        """Add IP whitelist check."""
        super().check_permissions(request)
        
        allowed_ips = ['10.0.0.0/8']
        client_ip = request.META.get('REMOTE_ADDR')
        
        if not is_in_cidr(client_ip, allowed_ips):
            self.permission_denied(request, message="IP not allowed")
```

### Settings-Driven Configuration

```python
# settings.py
AUTOMATE_API = {
    'CORS_ALLOWED_ORIGINS': os.environ.get('CORS_ORIGINS', '*').split(','),
    'RATE_LIMIT_PER_MINUTE': int(os.environ.get('RATE_LIMIT', 60)),
}

AUTOMATE_DATACHAT = {
    'HISTORY_PAGE_SIZE': int(os.environ.get('CHAT_HISTORY_SIZE', 15)),
}
```

All ViewSets will automatically use these settings without code changes.
