# Serializers Reference

Complete reference for all Django Automate serializers.

## Table of Contents

1. [Base Classes](#base-classes)
2. [Mixins](#mixins)
3. [Serializers by Module](#serializers-by-module)
4. [Customization Guide](#customization-guide)

---

## Base Classes

**Import:** `from automate_core.base import BaseSerializer, BaseModelSerializer`

### BaseSerializer

Base serializer with context awareness and validation.

```python
from automate_core.base import BaseSerializer
from rest_framework import serializers

class MySerializer(BaseSerializer):
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    
    def validate_name(self, value):
        if value.lower() == 'admin':
            raise serializers.ValidationError("Reserved name")
        return value
```

**Features:**
- `self.request` - Access request object
- `self.current_user` - Access current user
- `self.tenant_id` - Access tenant context
- `self.view` - Access parent view

---

### BaseModelSerializer

Model serializer with enhanced features.

```python
from automate_core.base import BaseModelSerializer

class MyModelSerializer(BaseModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'
        exclude_fields = ['internal_notes']
        readonly_fields = ['created_at']
```

| Attribute | Default | Description |
|-----------|---------|-------------|
| `exclude_fields` | `[]` | Always exclude these fields |
| `readonly_fields` | `[]` | Always read-only fields |
| `auto_include_timestamps` | True | Include timestamp fields |

---

### TenantScopedSerializer

Auto-inject tenant on creation.

```python
from automate_core.base import TenantScopedSerializer

class MyTenantSerializer(TenantScopedSerializer):
    class Meta:
        model = MyTenantModel
        fields = '__all__'
```

| Attribute | Default | Description |
|-----------|---------|-------------|
| `tenant_field` | `'tenant_id'` | Tenant field name |
| `auto_set_tenant` | True | Auto-set from context |

---

### AuditableSerializer

Auto-set audit fields (created_by, modified_by).

```python
from automate_core.base import AuditableSerializer

class MyAuditableSerializer(AuditableSerializer):
    class Meta:
        model = MyAuditableModel
        fields = '__all__'
```

---

### NestedWritableSerializer

Handle nested create/update automatically.

```python
from automate_core.base import NestedWritableSerializer

class OrderSerializer(NestedWritableSerializer):
    items = OrderItemSerializer(many=True)
    
    nested_fields = {
        'items': {'serializer': OrderItemSerializer, 'many': True}
    }
    
    class Meta:
        model = Order
        fields = '__all__'
```

---

### ReadOnlySerializer

All fields automatically read-only.

```python
from automate_core.base import ReadOnlySerializer

class StatsSerializer(ReadOnlySerializer):
    total_count = serializers.IntegerField()
    avg_duration = serializers.FloatField()
```

---

## Mixins

### ValidationMixin

Enhanced validation with custom error messages.

```python
from automate_core.base import ValidationMixin

class MySerializer(ValidationMixin, serializers.Serializer):
    error_messages = {
        'name': {'required': 'Name is mandatory'},
    }
    strict_validation = True  # Fail on unknown fields
```

---

### ContextMixin

Easy access to request context.

```python
class MySerializer(ContextMixin, serializers.Serializer):
    def validate_owner(self, value):
        if value != self.current_user.id:
            raise ValidationError("Not your resource")
        return value
```

**Properties:**
- `self.request` - Request object
- `self.current_user` - User object
- `self.tenant_id` - Tenant identifier
- `self.view` - Parent view

---

### DynamicFieldsMixin

Request-based field selection.

```python
class MySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'

# Usage: GET /api/items/?fields=id,name,email
```

---

### ExpandableMixin

Expand nested relations on request.

```python
class OrderSerializer(ExpandableMixin, serializers.ModelSerializer):
    expandable_fields = {
        'customer': CustomerSerializer,
        'items': OrderItemSerializer,
    }
    
    class Meta:
        model = Order
        fields = '__all__'

# Usage: GET /api/orders/1/?expand=customer,items
```

---

### PaginationMixin

Add pagination fields to response.

```python
class MyListSerializer(PaginationMixin, serializers.Serializer):
    items = MyItemSerializer(many=True)
    # Automatically includes: page, page_size, total_count, has_next, has_previous
```

---

### CacheMixin

Response caching support.

```python
class MySerializer(CacheMixin, serializers.ModelSerializer):
    cache_timeout = 300  # 5 minutes
    cache_key_prefix = 'mymodel'
```

---

## Serializers by Module

### automate_datachat (8 serializers)

| Serializer | Type | Key Fields | Validation |
|------------|------|------------|------------|
| `ChatRequestSerializer` | Request | `question`, `context` | Min 1, max 2000 chars |
| `ChatResponseSerializer` | Response | `answer`, `sql`, `data`, `chart`, `error` | - |
| `HistoryMessageSerializer` | Nested | `id`, `role`, `content`, `sql`, `data`, `created_at` | - |
| `HistoryResponseSerializer` | Response | `messages`, `has_more`, `total`, `page` | - |
| `EmbedChatRequestSerializer` | Request | `question` | Max 1000 chars |
| `EmbedChatResponseSerializer` | Response | `answer`, `sql`, `error` | - |
| `EmbedConfigSerializer` | Response | `theme`, `welcome_message`, `require_auth` | - |

### automate/api/serializers/workflows.py (8 serializers)

| Serializer | Type | Key Fields | Validation |
|------------|------|------------|------------|
| `WorkflowNodeSerializer` | Nested | `id`, `type`, `config`, `position` | Type in choices |
| `WorkflowEdgeSerializer` | Nested | `source`, `target`, `condition` | - |
| `WorkflowGraphSerializer` | Nested | `nodes`, `edges` | Graph structure valid |
| `WorkflowCreateRequestSerializer` | Request | `name`, `graph` | Name max 200 |
| `WorkflowCreateResponseSerializer` | Response | `id`, `slug`, `workflow_version`, `message` | - |
| `WorkflowDetailSerializer` | Response | `id`, `name`, `slug`, `graph` | - |
| `WorkflowUpdateRequestSerializer` | Request | `name`, `graph` | - |
| `WorkflowUpdateResponseSerializer` | Response | `id`, `message` | - |

### automate/api/serializers/zapier.py (4 serializers)

| Serializer | Type | Key Fields | Validation |
|------------|------|------------|------------|
| `TriggerSerializer` | Response | `key`, `label` | - |
| `SubscribeRequestSerializer` | Request | `target_url`, `event` | Valid URL |
| `SubscribeResponseSerializer` | Response | `id`, `status` | - |
| `UnsubscribeResponseSerializer` | Response | `status` | - |

### automate_api/v1/serializers/ (10 serializers)

| Serializer | Type | Model/Key Fields | Description |
|------------|------|------------------|-------------|
| `ProviderSerializer` | ModelSerializer | LLMProvider | Full provider config |
| `EndpointSerializer` | ModelSerializer | Endpoint | Endpoint definition |
| `EndpointRunRequest` | Request | `input`, `async` | Run request |
| `EndpointRunResponse` | Response | `id`, `status`, `output` | Run result |
| `JobSerializer` | ModelSerializer | Job | Job details |
| `CancelResponse` | Response | `cancelled`, `message` | Cancel result |
| `ExecutionSerializer` | ModelSerializer | Execution | Execution details |
| `ArtifactSerializer` | ModelSerializer | Artifact | Artifact metadata |
| `IngestEventSerializer` | Request | `type`, `payload`, `source` | Event ingest |
| `IngestEventResponse` | Response | `id`, `status` | Ingest result |

### rag/api/serializers.py (4 serializers)

| Serializer | Type | Key Fields | Validation |
|------------|------|------------|------------|
| `RAGQueryRequestSerializer` | Request | `query`, `top_k`, `filters` | Query 1-2000, top_k 1-100 |
| `RAGResultSerializer` | Nested | `text`, `score`, `source_id`, `metadata` | - |
| `RAGQueryResponseSerializer` | Response | `results`, `trace_id`, `latency_ms` | - |
| `RAGHealthResponseSerializer` | Response | `healthy`, `message`, `status` | - |

### automate/api/viewsets/ (4 serializers)

| Serializer | Type | Key Fields | Description |
|------------|------|------------|-------------|
| `PromptTestRequestSerializer` | Request | `prompt_slug`, `version`, `variables` | Test prompt |
| `PromptTestResponseSerializer` | Response | `system_prompt`, `user_prompt`, `status` | Test result |
| `PromptMetricsSerializer` | Response | `daily_stats`, `recent_failures` | Metrics |
| `ManualTriggerSerializer` | Request | `automation_slug`, `payload` | Manual trigger |

### automate_llm/api/serializers.py (1 serializer)

| Serializer | Type | Key Fields | Description |
|------------|------|------------|-------------|
| `LlmRunCreateSerializer` | Request | `prompt_slug`, `variables`, `model` | LLM run request |

### automate_modal/api/serializers.py (4 serializers)

| Serializer | Type | Key Fields | Description |
|------------|------|------------|-------------|
| `ModalRunRequestSerializer` | Request | `endpoint_slug`, `input`, `async` | Modal run |
| `ModalArtifactSerializer` | Response | `id`, `type`, `path`, `size`, `url` | Artifact info |
| `ModalResultSerializer` | Response | `output`, `artifacts`, `cost`, `duration` | Run result |
| `ModalJobSerializer` | Response | `id`, `status`, `endpoint`, `created_at` | Job info |

---

## Customization Guide

### Extending a Serializer

```python
from automate_datachat.serializers import ChatRequestSerializer

class ExtendedChatRequestSerializer(ChatRequestSerializer):
    session_id = serializers.UUIDField(required=False)
    
    def validate_question(self, value):
        # Additional validation
        if 'DROP TABLE' in value.upper():
            raise serializers.ValidationError("Invalid query")
        return super().validate_question(value)
```

### Adding Custom Fields

```python
from automate_api.v1.serializers.jobs import JobSerializer

class ExtendedJobSerializer(JobSerializer):
    owner_name = serializers.SerializerMethodField()
    
    class Meta(JobSerializer.Meta):
        fields = JobSerializer.Meta.fields + ['owner_name']
    
    def get_owner_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None
```

### Custom Validation

```python
from automate_core.base import BaseSerializer

class MySerializer(BaseSerializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    def validate(self, attrs):
        attrs = super().validate(attrs)
        
        if attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })
        
        return attrs
```

### Dynamic Field Selection

```python
class FlexibleSerializer(DynamicFieldsMixin, BaseModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'

# In view:
serializer = FlexibleSerializer(
    queryset,
    many=True,
    fields=['id', 'name']  # Only these fields
)
```

### Nested Create/Update

```python
from automate_core.base import NestedWritableSerializer

class ParentSerializer(NestedWritableSerializer):
    children = ChildSerializer(many=True)
    
    nested_fields = {
        'children': {
            'serializer': ChildSerializer,
            'many': True
        }
    }
    
    class Meta:
        model = Parent
        fields = '__all__'

# POST /api/parents/
# {
#     "name": "Parent",
#     "children": [
#         {"name": "Child 1"},
#         {"name": "Child 2"}
#     ]
# }
```

### Using in ViewSets

```python
from rest_framework import viewsets
from automate_core.base import BaseModelSerializer

class MyModelSerializer(BaseModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'

class MyViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['tenant_id'] = self.request.user.tenant_id
        return context
```
