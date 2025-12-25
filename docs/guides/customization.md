# Customization & Integration Guide

This guide covers all customization points for administrators and developers.

---

## Part 1: Admin Customizations (No Code)

All these can be configured directly in Django Admin.

### 1.1 LLM Providers
**Location**: Admin → Automate → LLM Providers

| Field | Description |
|-------|-------------|
| Slug | Unique key (e.g., `openai`) |
| Name | Display name |
| Base URL | API endpoint (optional, defaults to provider's standard) |
| API Key Env Var | Environment variable name (e.g., `OPENAI_API_KEY`) |

### 1.2 Model Configurations
**Location**: Admin → Automate → LLM Model Configs

| Field | Description |
|-------|-------------|
| Provider | FK to LLMProvider |
| Name | Model name (e.g., `gpt-4o`) |
| Is Default | ✓ = Used by DataChat |
| Temperature | 0.0-2.0 |
| Max Tokens | Response limit |

### 1.3 MCP Server Integration
**Location**: Admin → Automate → MCP Servers

1. **Add Server**: Enter name, slug, endpoint URL
2. **Configure Auth**: Bearer token or API key
3. **Sync Tools**: Select server → Actions → "Sync tools"

### 1.4 Prompts
**Location**: Admin → Automate → Prompts

Create versioned, environment-promoted prompts:

| Field | Description |
|-------|-------------|
| Slug | Unique key (e.g., `datachat_sql_generator`) |
| System Template | Jinja2 template for system prompt |
| User Template | Jinja2 template for user message |
| Status | draft → approved → archived |

**Template Variables:**
```jinja2
{{ schema }}    {# Database schema #}
{{ history }}   {# Conversation history #}
{{ question }}  {# User's question #}
{{ tools }}     {# Available MCP tools #}
{{ context }}   {# Session context (user, time, etc.) #}
```

### 1.5 Budget Policies
**Location**: Admin → Automate → Budget Policies

Limit LLM usage per scope (global, user, automation).

### 1.6 Connection Profiles
**Location**: Admin → Automate → Connection Profiles

Store connector credentials scoped by environment (dev/staging/prod).

---

## Part 2: Developer Integration (Code)

### 2.1 DataChat Table Registration

**Option A: In apps.py (recommended)**
```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'myapp'
    
    def ready(self):
        from automate_datachat.registry import DataChatRegistry
        from .models import Product, Order
        
        DataChatRegistry.register(
            Product,
            include_fields=["id", "name", "price"],
            exclude_fields=["internal_notes"],
            tags=["inventory", "products"]
        )
```

**Option B: Decorator**
```python
# myapp/models.py
from automate_datachat.registry import register_model

@register_model(tags=["sales"])
class Order(models.Model):
    ...
```

### 2.2 Custom Connectors

**Step 1: Create the adapter**
```python
# myapp/adapters.py
from automate_connectors.adapters.base import ConnectorAdapter

class ERPConnector(ConnectorAdapter):
    code = "erp"
    name = "My ERP System"
    
    def execute(self, action: str, params: dict, context: dict):
        if action == "create_order":
            return self._create_order(params)
        raise NotImplementedError(f"Unknown action: {action}")
    
    def _create_order(self, params):
        # Your implementation
        return {"order_id": "12345"}
```

**Step 2: Register via entrypoints**
```toml
# pyproject.toml
[project.entry-points."django_automate.connectors"]
erp = "myapp.adapters:ERPConnector"
```

### 2.3 Custom Secrets Backend

```python
# myapp/secrets.py
from automate_governance.secrets.interfaces import SecretsBackend

class VaultBackend(SecretsBackend):
    def get_secret(self, key: str) -> str:
        # Fetch from HashiCorp Vault
        return vault_client.read(f"secret/data/{key}")
```

Register in `pyproject.toml`:
```toml
[project.entry-points."django_automate.secrets.backends"]
vault = "myapp.secrets:VaultBackend"
```

### 2.4 Custom LLM Provider

```python
# myapp/llm.py
from automate_llm.providers.base import BaseLLMProvider

class AnthropicProvider(BaseLLMProvider):
    slug = "anthropic"
    
    def chat_complete(self, request):
        # Call Anthropic API
        return CompletionResponse(content=...)
```

Register in settings:
```python
AUTOMATE_LLM_PROVIDERS = {
    "anthropic": "myapp.llm.AnthropicProvider",
}
```

### 2.5 Extending Admin Templates

Override Django Admin templates in your app:

```
myapp/
  templates/
    admin/
      index.html          # Custom admin home
      base_site.html      # Custom header/footer
      myapp/
        mymodel/
          change_form.html  # Custom edit form
```

### 2.6 Adding Custom Studio Views

```python
# myapp/views.py
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

@method_decorator(staff_member_required, name='dispatch')
class MyDashboardView(TemplateView):
    template_name = "myapp/dashboard.html"
```

```python
# automate_studio/urls.py (or your own urls.py)
path("studio/my-dashboard/", MyDashboardView.as_view(), name="my_dashboard"),
```

---

## Part 3: API Integration

### 3.1 REST API

**Authentication**: Bearer token
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/jobs/
```

**Endpoints:**
| Resource | Methods |
|----------|---------|
| `/api/v1/jobs/` | GET, POST |
| `/api/v1/executions/` | GET |
| `/api/v1/events/` | POST |
| `/api/v1/providers/` | GET |
| `/api/v1/endpoints/` | GET |

### 3.2 DataChat API

```python
import requests

response = requests.post(
    "http://localhost:8000/datachat/api/chat/",
    json={"message": "How many orders this month?"},
    headers={"Authorization": "Bearer <token>"}
)
print(response.json())
# {"answer": "...", "sql": "SELECT ...", "data": [...]}
```

### 3.3 MCP Tool Execution

```python
from automate_llm.mcp_client import MCPClient
from automate.models import MCPServer

server = MCPServer.objects.get(slug="shopify-mcp")
client = MCPClient(server)

# Discover tools
tools = client.discover_tools()

# Execute a tool
result = client.execute_tool("getProducts", {"limit": 10})
```

---

## Part 4: Configuration Reference

### 4.1 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `DATABASE_URL` | PostgreSQL URL | SQLite |
| `REDIS_URL` | Redis for Celery | memory:// |
| `CELERY_BROKER_URL` | Task broker | Redis |
| `DEBUG` | Debug mode | False |

### 4.2 Django Settings

```python
# Celery
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_TASK_ALWAYS_EAGER = False  # True for testing

# DataChat
DATACHAT_CONFIG = {
    "max_results": 1000,
    "default_provider": "openai",
}

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "automate_api.v1.auth.BearerTokenAuthentication",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "tenant": "120/min",
        "token": "60/min",
    },
}
```

---

## Part 5: Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| "No tables exposed" | Register models in `DataChatRegistry` |
| MCP tools not syncing | Run `python manage.py sync_mcp_tools` |
| 401 on DataChat | Set `OPENAI_API_KEY` in `.env` |
| Chat returns SQL for greetings | Create `datachat_sql_generator` Prompt with MCP tool instructions |
