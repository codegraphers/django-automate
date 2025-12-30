# Views Reference

Complete reference for all Django Automate views and ViewSets.

## Table of Contents

1. [Base Classes](#base-classes)
2. [Mixins](#mixins)
3. [ViewSets by Module](#viewsets-by-module)
4. [Customization Guide](#customization-guide)

---

## Base Classes

**Import:** `from automate_api.v1.base import BaseAPIView, BaseViewSet, BaseModelViewSet`

### BaseAPIView

Base API view with common middleware.

```python
from automate_api.v1.base import BaseAPIView
from rest_framework.response import Response

class MyAPIView(BaseAPIView):
    def get(self, request):
        return Response({'status': 'ok'})
```

**Features:**
- Authentication integration
- Permission checking
- Rate limiting
- CORS support

---

### BaseViewSet

Base ViewSet with configuration support.

```python
from automate_api.v1.base import BaseViewSet

class MyViewSet(BaseViewSet):
    def list(self, request):
        return Response({'items': []})
```

**Mixins included:** ConfigurableMixin, CORSMixin

---

### BaseModelViewSet

Full CRUD ViewSet for models.

```python
from automate_api.v1.base import BaseModelViewSet

class MyModelViewSet(BaseModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
```

---

### BaseReadOnlyViewSet

Read-only ViewSet (list + retrieve).

```python
from automate_api.v1.base import BaseReadOnlyViewSet

class MyReadOnlyViewSet(BaseReadOnlyViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
```

---

## Mixins

### ConfigurableMixin

Access Django settings dynamically.

```python
class MyViewSet(ConfigurableMixin, viewsets.ViewSet):
    def list(self, request):
        page_size = self.get_setting('PAGE_SIZE', 25)
        # Uses AUTOMATE_API_PAGE_SIZE from settings
```

---

### CORSMixin

Add CORS headers to responses.

```python
class MyViewSet(CORSMixin, viewsets.ViewSet):
    cors_origins = ['https://example.com']
    cors_methods = ['GET', 'POST']
```

---

### TenantFilterMixin

Auto-filter by tenant.

```python
class MyViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    tenant_field = 'organization_id'
    
    # Queryset automatically filtered by tenant
```

---

### RateLimitMixin

Per-endpoint rate limiting.

```python
class MyViewSet(RateLimitMixin, viewsets.ViewSet):
    rate_limit = '100/hour'
    rate_limit_key = 'user'  # or 'ip'
```

---

### StaffOnlyMixin

Restrict to staff users.

```python
class MyViewSet(StaffOnlyMixin, viewsets.ViewSet):
    # Only staff can access
```

---

### PublicAPIMixin

Public endpoints with enhanced rate limiting.

```python
class PublicViewSet(PublicAPIMixin, viewsets.ViewSet):
    public_rate_limit = '10/minute'
```

---

## ViewSets by Module

### automate_datachat (2 ViewSets)

#### ChatViewSet

Staff chat interface for data queries.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat/` | POST | Send chat message |
| `/history/` | GET | Get chat history |

| Override Point | Default | Description |
|----------------|---------|-------------|
| `orchestrator_class` | ChatOrchestrator | Chat logic handler |
| `history_page_size` | 15 | Messages per page |

```python
from automate_datachat.viewsets import ChatViewSet

class CustomChatViewSet(ChatViewSet):
    orchestrator_class = MyCustomOrchestrator
    history_page_size = 25
```

#### EmbedViewSet

Embeddable widget API.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/widget.js` | GET | Widget JavaScript |
| `/chat/` | POST | Embed chat message |
| `/config/` | GET | Widget configuration |

| Override Point | Default | Description |
|----------------|---------|-------------|
| `embed_model` | ChatEmbed | Embed config model |
| `_get_widget_js()` | - | Widget JS generator |

---

### automate/api/viewsets/ (4 ViewSets)

#### WorkflowViewSet

Workflow CRUD operations.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workflows/` | POST | Create workflow |
| `/workflows/{id}/` | GET | Get workflow |
| `/workflows/{id}/` | PUT | Update workflow |

| Override Point | Default | Description |
|----------------|---------|-------------|
| `service_class` | WorkflowService | Business logic |

#### ZapierViewSet

Zapier integration webhooks.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/triggers/` | GET | List triggers |
| `/subscribe/` | POST | Subscribe webhook |
| `/unsubscribe/` | POST | Unsubscribe webhook |

| Override Point | Default | Description |
|----------------|---------|-------------|
| `available_triggers` | list | Trigger list |
| `validate_callback_url()` | - | SSRF protection |

#### SchemaViewSet

Database schema introspection.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/apps/` | GET | List apps and models |

| Override Point | Default | Description |
|----------------|---------|-------------|
| `excluded_apps` | list | Apps to hide |

#### PromptEvalViewSet

Prompt testing and metrics.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/{slug}/test/` | POST | Test prompt |
| `/{slug}/metrics/` | GET | Get metrics |

| Override Point | Default | Description |
|----------------|---------|-------------|
| `metrics_days` | 30 | Days of metrics |
| `render_template()` | - | Template rendering |

---

### automate_api/v1/views/ (6 ViewSets)

#### EventIngestView

Event ingestion endpoint.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/events/` | POST | Ingest event |

#### JobViewSet

Job management.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/jobs/` | GET | List jobs |
| `/jobs/{id}/` | GET | Get job |
| `/jobs/{id}/cancel/` | POST | Cancel job |

#### ArtifactViewSet

Artifact retrieval.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/artifacts/` | GET | List artifacts |
| `/artifacts/{id}/` | GET | Get artifact |

#### ProviderViewSet

LLM provider management.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/providers/` | GET/POST | List/Create |
| `/providers/{id}/` | GET/PUT/DELETE | CRUD |

#### EndpointViewSet

Endpoint management.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/endpoints/` | GET | List endpoints |
| `/endpoints/{id}/run/` | POST | Run endpoint |

#### ExecutionViewSet

Execution history.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/executions/` | GET | List executions |
| `/executions/{id}/` | GET | Get execution |

---

### rag/api/ (1 ViewSet)

#### RAGQueryViewSet

RAG query and health.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/{slug}/query/` | POST | Execute query |
| `/{slug}/health/` | GET | Health check |

| Override Point | Default | Description |
|----------------|---------|-------------|
| `get_retrieval_provider()` | - | Retrieval config |
| `build_query_context()` | - | Query context |
| `log_query()` | - | Query logging |

---

### automate_modal/api/ (6 Views)

| View | Endpoint | Description |
|------|----------|-------------|
| `EndpointRunView` | `POST /endpoints/{id}/run/` | Sync execution |
| `EndpointStreamView` | `POST /endpoints/{id}/stream/` | SSE stream |
| `EndpointJobView` | `POST /endpoints/{id}/job/` | Async job |
| `JobStatusView` | `GET /jobs/{id}/status/` | Job status |
| `JobEventsView` | `GET /jobs/{id}/events/` | Job events |
| `ArtifactDownloadView` | `GET /artifacts/{id}/download/` | Download |

---

### automate_studio/ (7 Views)

| View | URL | Description |
|------|-----|-------------|
| `DashboardView` | `/studio/dashboard/` | Main dashboard |
| `CorrelationExplorerView` | `/studio/correlation/` | Event correlation |
| `ExecutionExplorerView` | `/admin/.../explorer/` | Execution browser |
| `WizardView` | `/admin/.../wizard/` | Creation wizard |
| `RuleTesterView` | `/admin/.../tester/` | Rule testing |
| `TestProviderView` | `/studio/provider-test/` | Provider testing |
| `AutomationWizardView` | `/admin/.../wizard/` | Automation setup |

---

## Customization Guide

### Override Existing ViewSet

```python
from automate_datachat.viewsets import ChatViewSet

class CustomChatViewSet(ChatViewSet):
    orchestrator_class = MyOrchestrator
    history_page_size = 50
    
    def create(self, request):
        # Pre-processing
        log_chat_request(request)
        
        response = super().create(request)
        
        # Post-processing
        track_usage(request.user)
        
        return response
```

### Custom Permissions

```python
from rest_framework.permissions import BasePermission

class IsProjectMember(BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_id')
        return request.user.projects.filter(id=project_id).exists()

class MyViewSet(BaseModelViewSet):
    permission_classes = [IsProjectMember]
```

### Custom Actions

```python
from rest_framework.decorators import action
from rest_framework.response import Response

class MyViewSet(BaseModelViewSet):
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        obj = self.get_object()
        obj.status = 'active'
        obj.save()
        return Response({'status': 'activated'})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        return Response({
            'total': self.get_queryset().count(),
            'active': self.get_queryset().filter(status='active').count()
        })
```

### Custom Routing

```python
from rest_framework.routers import DefaultRouter
from automate.api.viewsets import WorkflowViewSet

class CustomWorkflowViewSet(WorkflowViewSet):
    # Custom implementation
    pass

router = DefaultRouter()
router.register('workflows', CustomWorkflowViewSet, basename='workflow')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
```

### Extend BaseViewSet

```python
from automate_api.v1.base import BaseViewSet, StaffOnlyMixin

class MyAppBaseViewSet(StaffOnlyMixin, BaseViewSet):
    """Custom base for my app's views."""
    
    def get_queryset(self):
        qs = super().get_queryset()
        # App-specific filtering
        return qs.filter(app='myapp')
```
