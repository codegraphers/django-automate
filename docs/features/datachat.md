# Data Chat (NL2SQL)

An AI-powered natural language interface for querying your Django database directly from the admin.

## Overview

Data Chat allows staff users to ask questions in plain English and receive SQL-backed answers. The system:

1. **Converts natural language to SQL** using an LLM
2. **Validates queries** against a security policy (read-only, allowed tables)
3. **Executes** the query and returns results
4. **Summarizes** results in natural language

## Quick Setup

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "automate_datachat",
]
```

### 2. Register Models

In your app's `apps.py`:

```python
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'myapp'
    
    def ready(self):
        from automate_datachat.registry import DataChatRegistry
        from .models import Product, Order, Customer
        
        DataChatRegistry.register(
            Product,
            include_fields=["id", "name", "price", "category", "created_at"],
            tags=["inventory"]
        )
        
        DataChatRegistry.register(
            Order,
            include_fields=["id", "customer_id", "total", "status", "created_at"],
            tags=["sales"]
        )
```

### 3. Run Migrations

```bash
python manage.py migrate automate_datachat
```

## Admin Widget

The chat widget appears automatically in Django Admin for staff users (bottom-right corner).

### Features
- **Conversational**: Maintains context across questions
- **SQL Display**: Shows generated SQL for transparency
- **History**: Persists messages across sessions

## Prompt Management

Prompts are stored in the database and editable via Admin.

### Default Prompts
- `datachat_sql_generator` - Converts natural language to SQL
- `datachat_summarizer` - Summarizes query results

### Template Variables
Prompts use Jinja2 templating:

| Variable | Description |
|----------|-------------|
| `{{ schema }}` | Database schema (tables, columns) |
| `{{ history }}` | Conversation history |
| `{{ question }}` | User's current question |
| `{{ results }}` | Query results (for summarizer) |

## LLM Logging

All LLM interactions are logged to `LLMRequest`:

| Field | Description |
|-------|-------------|
| `input_payload` | Full messages sent to LLM |
| `output_content` | Raw LLM response |
| `input_tokens` | Tokens consumed |
| `latency_ms` | Response time |
| `cost_usd` | Cost (if provider returns it) |

View logs in Admin → Automate LLM → LLM Requests.

## Security

### Read-Only Queries
Only `SELECT` statements are allowed. `INSERT`, `UPDATE`, `DELETE` are blocked.

### Table Whitelisting
Only registered models are exposed. Unregistered tables cannot be queried.

### SQL Validation
All generated SQL is validated before execution using `SQLPolicy`.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/datachat/api/chat/` | POST | Send a question |
| `/datachat/api/history/` | GET | Get message history |

## Configuration

```python
# settings.py
DATACHAT_CONFIG = {
    "max_results": 1000,  # Max rows returned
    "default_provider": "openai",  # LLM provider to use
}
```
