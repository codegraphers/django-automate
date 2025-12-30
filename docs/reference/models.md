# Models Reference

Complete reference for all Django Automate models, organized by module.

## Table of Contents

1. [Base Classes](#base-classes)
2. [automate Module](#automate-module)
3. [automate_core Module](#automate_core-module)
4. [automate_datachat Module](#automate_datachat-module)
5. [automate_llm Module](#automate_llm-module)
6. [automate_modal Module](#automate_modal-module)
7. [rag Module](#rag-module)
8. [Other Modules](#other-modules)

---

## Base Classes

All models should inherit from these abstract base classes for consistency.

**Import:** `from automate_core.base import TimeStampedModel, TenantScopedModel`

### TimeStampedModel

Automatic `created_at` and `updated_at` timestamps.

```python
from automate_core.base import TimeStampedModel

class MyModel(TimeStampedModel):
    name = models.CharField(max_length=200)
```

| Field | Type | Description |
|-------|------|-------------|
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-set on save |

---

### UUIDModel

UUID primary key for globally unique identifiers.

```python
from automate_core.base import UUIDModel

class MyModel(UUIDModel):
    name = models.CharField(max_length=200)
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUIDField | UUID4 primary key |

---

### TenantScopedModel

Multi-tenant isolation with automatic filtering.

```python
from automate_core.base import TenantScopedModel

class MyModel(TenantScopedModel):
    name = models.CharField(max_length=200)

# Query for specific tenant
MyModel.objects.for_tenant('tenant-123')
```

| Field | Type | Description |
|-------|------|-------------|
| `tenant_id` | CharField | Tenant identifier |

| Attribute | Default | Description |
|-----------|---------|-------------|
| `tenant_field` | `'tenant_id'` | Name of tenant field (override) |

**Manager:** `TenantManager` with `for_tenant(tenant_id)` method

---

### AuditableModel

Track who created/modified records.

```python
from automate_core.base import AuditableModel

class MyModel(AuditableModel):
    name = models.CharField(max_length=200)
```

| Field | Type | Description |
|-------|------|-------------|
| `created_by` | CharField | Username of creator |
| `modified_by` | CharField | Username of last modifier |

**Override:** `get_current_user()` to customize user resolution

---

### SoftDeleteModel

Soft deletion instead of permanent delete.

```python
from automate_core.base import SoftDeleteModel

class MyModel(SoftDeleteModel):
    name = models.CharField(max_length=200)

obj.delete()    # Soft delete
obj.restore()   # Restore
obj.hard_delete()  # Permanent delete
```

| Field | Type | Description |
|-------|------|-------------|
| `is_deleted` | BooleanField | Whether deleted |
| `deleted_at` | DateTimeField | When deleted |
| `deleted_by` | CharField | Who deleted |

**Manager:** `SoftDeleteManager` (excludes deleted by default)

---

### SluggedModel

Auto-generated URL-friendly slugs.

```python
from automate_core.base import SluggedModel

class MyModel(SluggedModel):
    name = models.CharField(max_length=200)
    # slug auto-generated from name
```

| Field | Type | Description |
|-------|------|-------------|
| `slug` | SlugField | URL-friendly identifier |

| Attribute | Default | Description |
|-----------|---------|-------------|
| `slug_source_field` | `'name'` | Field to generate slug from |

---

### StatusModel

State machine with status transitions.

```python
from automate_core.base import StatusModel

class Job(StatusModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
    ]
    INITIAL_STATUS = 'pending'
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | CharField | Current status |
| `status_changed_at` | DateTimeField | When status changed |

**Manager:** `StatusManager` with `by_status(status)` and `active()` methods

---

### MetadataModel

Flexible JSON metadata storage.

```python
from automate_core.base import MetadataModel

class MyModel(MetadataModel):
    name = models.CharField(max_length=200)

obj.set_meta('key', 'value')
obj.set_meta('nested.key', 'value')
value = obj.get_meta('key', default='fallback')
```

| Field | Type | Description |
|-------|------|-------------|
| `metadata` | JSONField | Flexible JSON storage |

---

### OrderedModel

Position-based ordering.

```python
from automate_core.base import OrderedModel

class Step(OrderedModel):
    name = models.CharField(max_length=200)

step.move_up()
step.move_down()
step.move_to(5)
```

| Field | Type | Description |
|-------|------|-------------|
| `position` | PositiveIntegerField | Position for ordering |

**Manager:** `OrderedManager` (auto-orders by position)

---

## automate Module

### LLMProvider

LLM provider configuration.

**Location:** `automate/models.py`

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | Provider name |
| `provider_type` | CharField | Type (openai, anthropic, etc.) |
| `config` | JSONField | Provider configuration |
| `is_default` | BooleanField | Default provider flag |

**Override Points:**
- `get_client()`: Return provider client instance
- `validate_config()`: Validate provider configuration

---

### LLMModelConfig

Model-specific configuration.

| Field | Type | Description |
|-------|------|-------------|
| `provider` | ForeignKey | Parent provider |
| `model_id` | CharField | Model identifier |
| `max_tokens` | IntegerField | Token limit |
| `temperature` | FloatField | Sampling temperature |
| `params` | JSONField | Additional parameters |

---

### Prompt

Prompt template definition.

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | Prompt name |
| `slug` | SlugField | URL identifier |
| `description` | TextField | Description |
| `category` | CharField | Category tag |

**Related:** `versions` - PromptVersion queryset

---

### PromptVersion

Version of a prompt template.

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | ForeignKey | Parent prompt |
| `version` | IntegerField | Version number |
| `system_template` | TextField | System prompt template |
| `user_template` | TextField | User prompt template |
| `variables` | JSONField | Required variables |

**Override Points:**
- `render(variables)`: Render templates with variables

---

### ConnectionProfile

External service connection credentials.

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | Connection name |
| `provider` | CharField | Provider type |
| `credentials` | JSONField | Encrypted credentials |
| `config` | JSONField | Connection config |

**Override Points:**
- `get_client()`: Return service client
- `test_connection()`: Test connectivity

---

### MCPServer

MCP (Model Context Protocol) server.

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | Server name |
| `url` | URLField | Server URL |
| `auth_config` | JSONField | Authentication |
| `status` | CharField | Connection status |

**Related:** `tools` - MCPTool queryset

**Override Points:**
- `sync_tools()`: Sync available tools
- `health_check()`: Check server health

---

### MCPTool

Tool available from MCP server.

| Field | Type | Description |
|-------|------|-------------|
| `server` | ForeignKey | Parent server |
| `name` | CharField | Tool name |
| `schema` | JSONField | Input schema |
| `description` | TextField | Tool description |

**Override Points:**
- `execute(input)`: Execute tool with input

---

## automate_core Module

### Automation

Top-level automation definition.

**Location:** `automate_core/workflows/models.py`

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | Automation name |
| `slug` | SlugField | URL identifier |
| `enabled` | BooleanField | Active flag |
| `config` | JSONField | Configuration |

**Related:** `triggers`, `workflows`

---

### Workflow

Workflow graph definition.

| Field | Type | Description |
|-------|------|-------------|
| `automation` | ForeignKey | Parent automation |
| `version` | IntegerField | Version number |
| `graph` | JSONField | Workflow graph |
| `is_live` | BooleanField | Active version flag |

**Override Points:**
- `compile()`: Compile graph to executable
- `validate()`: Validate graph structure

---

### Trigger (TriggerSpec)

Event trigger configuration.

| Field | Type | Description |
|-------|------|-------------|
| `automation` | ForeignKey | Parent automation |
| `type` | CharField | Trigger type |
| `config` | JSONField | Trigger configuration |
| `filters` | JSONField | Event filters |

**Override Points:**
- `matches(event)`: Check if event matches
- `extract_payload(event)`: Extract payload from event

---

### Event

Captured event record.

**Location:** `automate_core/events/models.py`

| Field | Type | Description |
|-------|------|-------------|
| `type` | CharField | Event type |
| `payload` | JSONField | Event data |
| `source` | CharField | Event source |
| `trace_id` | UUIDField | Trace identifier |

---

### Execution

Workflow execution instance.

**Location:** `automate_core/executions/models.py`

| Field | Type | Description |
|-------|------|-------------|
| `workflow` | ForeignKey | Executed workflow |
| `event` | ForeignKey | Triggering event |
| `status` | CharField | Execution status |
| `started_at` | DateTimeField | Start time |
| `ended_at` | DateTimeField | End time |
| `context` | JSONField | Execution context |

**Related:** `steps` - StepRun queryset

---

### StepRun

Individual step execution.

| Field | Type | Description |
|-------|------|-------------|
| `execution` | ForeignKey | Parent execution |
| `step_id` | CharField | Step identifier |
| `status` | CharField | Step status |
| `input` | JSONField | Step input |
| `output` | JSONField | Step output |
| `error` | TextField | Error message |
| `duration_ms` | IntegerField | Execution time |

---

### Job

Async job record.

**Location:** `automate_core/jobs/models.py`

| Field | Type | Description |
|-------|------|-------------|
| `type` | CharField | Job type |
| `status` | CharField | Job status |
| `params` | JSONField | Job parameters |
| `result` | JSONField | Job result |
| `priority` | IntegerField | Queue priority |
| `scheduled_at` | DateTimeField | Scheduled time |

**Override Points:**
- `execute()`: Run job logic
- `cancel()`: Cancel job
- `get_progress()`: Get progress info

---

## automate_datachat Module

### DataChatSession

Chat session for data queries.

**Location:** `automate_datachat/models.py`

| Field | Type | Description |
|-------|------|-------------|
| `user` | CharField | Username |
| `context` | JSONField | Session context |
| `expires_at` | DateTimeField | Expiration time |

**Related:** `messages` - DataChatMessage queryset

---

### DataChatMessage

Individual chat message.

| Field | Type | Description |
|-------|------|-------------|
| `session` | ForeignKey | Parent session |
| `role` | CharField | Message role (user/assistant) |
| `content` | TextField | Message text |
| `sql` | TextField | Generated SQL |
| `data` | JSONField | Query results |
| `chart` | JSONField | Chart configuration |

---

### ChatEmbed

Embeddable widget configuration.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUIDField | Embed identifier |
| `name` | CharField | Widget name |
| `api_key` | CharField | API key for auth |
| `allowed_domains` | ArrayField | Allowed origins |
| `theme` | JSONField | Widget styling |
| `rate_limit` | IntegerField | Requests per minute |

**Override Points:**
- `validate_origin(origin)`: Validate request origin
- `check_rate_limit(key)`: Check rate limit

---

## automate_llm Module

### LLMUsage

LLM usage tracking.

**Location:** `automate_llm/models.py`

| Field | Type | Description |
|-------|------|-------------|
| `tenant_id` | CharField | Tenant identifier |
| `model` | CharField | Model used |
| `tokens_in` | IntegerField | Input tokens |
| `tokens_out` | IntegerField | Output tokens |
| `cost` | DecimalField | Estimated cost |

---

### LLMRequest

LLM request audit log.

**Location:** `automate_llm/governance/models.py`

| Field | Type | Description |
|-------|------|-------------|
| `prompt_slug` | CharField | Prompt used |
| `model` | CharField | Model used |
| `latency_ms` | IntegerField | Response time |
| `success` | BooleanField | Success flag |
| `error` | TextField | Error message |

---

## automate_modal Module

### ModalEndpoint

Modal function endpoint.

**Location:** `automate_modal/models.py`

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | Endpoint name |
| `slug` | SlugField | URL identifier |
| `function_name` | CharField | Modal function |
| `gpu` | CharField | GPU type |
| `timeout` | IntegerField | Timeout seconds |

**Override Points:**
- `invoke(input)`: Invoke function
- `get_logs()`: Get execution logs

---

### ModalJob

Modal function execution.

| Field | Type | Description |
|-------|------|-------------|
| `endpoint` | ForeignKey | Parent endpoint |
| `status` | CharField | Job status |
| `input` | JSONField | Job input |
| `output` | JSONField | Job output |
| `cost` | DecimalField | Execution cost |

**Related:** `artifacts` - ModalArtifact queryset

---

## rag Module

### RAGEndpoint

RAG retrieval endpoint.

**Location:** `rag/models.py`

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | Endpoint name |
| `slug` | SlugField | URL identifier |
| `source` | ForeignKey | Knowledge source |
| `retrieval_config` | JSONField | Retrieval settings |
| `access_policy` | JSONField | Access control |

**Override Points:**
- `query(text, top_k)`: Execute retrieval
- `health_check()`: Check endpoint health

---

### KnowledgeSource

RAG knowledge source.

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | Source name |
| `type` | CharField | Source type |
| `config` | JSONField | Source configuration |
| `credentials_ref` | CharField | Credentials reference |
| `sync_status` | CharField | Sync status |

**Override Points:**
- `sync()`: Sync from source
- `get_documents()`: Get document list

---

### EmbeddingModel

Embedding model configuration.

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | Model name |
| `provider` | CharField | Provider (openai, etc.) |
| `model_id` | CharField | Model identifier |
| `dimensions` | IntegerField | Vector dimensions |

**Override Points:**
- `embed(text)`: Embed single text
- `batch_embed(texts)`: Embed batch

---

## Other Modules

### automate_governance

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `AuditLog` | Audit trail | `actor`, `action`, `target`, `changes` |
| `RuleSpec` | Business rule | `expression`, `action` |
| `ConnectionProfile` | Credentials | `provider`, `credentials` |
| `StoredSecret` | Encrypted secret | `key`, `encrypted_value` |
| `ThrottleBucket` | Rate limit state | `key`, `count`, `window` |

### automate_interop

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `InteropMapping` | Platform mapping | `source_platform`, `target`, `transform` |
| `TemplateCollection` | Template group | `name`, `description` |
| `TemplateWorkflow` | Workflow template | `collection`, `graph`, `variables` |

### automate_observability

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `AuditLogEntry` | Log entry | `level`, `message`, `context`, `trace_id` |

### automate_connectors

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `ConnectorInstance` | External connector | `connector_type`, `config`, `credentials` |

---

## Customization Guide

### Extending a Model

```python
from automate_core.base import TimeStampedModel, TenantScopedModel

class MyCustomModel(TenantScopedModel, TimeStampedModel):
    """Custom model with tenant isolation and timestamps."""
    
    name = models.CharField(max_length=200)
    
    class Meta:
        # Override default ordering
        ordering = ['name']
    
    @classmethod
    def get_current_tenant(cls):
        # Custom tenant resolution
        from myapp.middleware import get_current_tenant
        return get_current_tenant()
```

### Adding Custom Fields

```python
from automate.models import Automation

class ExtendedAutomation(Automation):
    """Automation with additional fields."""
    
    department = models.CharField(max_length=100)
    cost_center = models.CharField(max_length=50)
    
    class Meta:
        proxy = True  # Use proxy for same table
        # Or remove proxy for separate table
```

### Custom Manager

```python
from automate_core.base import TimeStampedModel

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class MyModel(TimeStampedModel):
    is_active = models.BooleanField(default=True)
    
    objects = models.Manager()
    active = ActiveManager()
```
