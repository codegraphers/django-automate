# Django Automate

A production-grade, event-driven automation platform for Django applications.

## 📚 Documentation

*   [**0. Getting Started**](packages/django_automate/docs/01_getting_started.md): Quickstart guide (5 mins).
*   [**1. Core Concepts**](packages/django_automate/docs/02_concepts.md): Mental model (Events, Rules, Workflows).
*   [**2. Tutorials**](packages/django_automate/docs/03_tutorials.md): Step-by-step guides (Signals, Webhooks, LLMs).
*   [**3. How-To Guides**](packages/django_automate/docs/04_how_to_guides.md): Common tasks (Secrets, Connector Authoring).
*   [**4. Reference**](packages/django_automate/docs/05_reference.md): API endpoint & Settings spec.
*   [**5. Extending**](packages/django_automate/docs/06_extending.md): Plugin system & Internals.
*   [**6. Operations**](packages/django_automate/docs/07_operations.md): Deployment checklist & Security.
*   [**7. Examples**](packages/django_automate/docs/08_examples.md): Copy-paste workflow templates.
*   [**Changelog**](packages/django_automate/docs/09_changelog.md): Version history.

## 🚀 Quick Install

```bash
pip install django-automate
```

## ✨ Features
all definable from the Django Admin.

![CI](https://github.com/example/django-automate/actions/workflows/main.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-90%25-green)
![PyPI](https://img.shields.io/pypi/v/django-automate.svg)


*   **Workflow Engine**: Versioned graph workflows with robust retry logic and exponential backoff.
*   **Event Driven**: Transactional Outbox pattern ensures 100% reliability (no lost signals).
*   **LLM Ops Inside**: Prompt registry, versioning, evaluation gates, and provider switching.
*   **Plugins & Connectors**: Slack, Webhooks, OpenAI, and a strict SDK for building your own.
*   **Ecosystem Ready**: First-class interoperability with **n8n** (export/import) and **Zapier** (API hooks).
*   **Enterprise Governance**: Validation rules, secret redaction, and audit logging built-in.

---

## ⚡ Quickstart

### 1. Installation

```bash
pip install django-automate
```

Add to `INSTALLED_APPS` and middleware:

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "automate",
]
```

Run migrations:

```bash
python manage.py migrate
```

### 2. Running the Demo (Local Development)

The fastest way to try it out is using the included **Docker Compose** setup.

1.  **Clone & Setup Env**:
    ```bash
    cp .env.example .env
    ```

2.  **Start Services**:
    ```bash
    docker-compose up -d --build
    ```

3.  **Seed Data**:
    ```bash
    docker-compose exec web python example_project/manage.py seed_automations
    ```

4.  **Login**:
    Visit `http://localhost:8000/admin/`. Default user: `admin` / `password` (if seeded via script usage).
    *(Note: You may need to create a superuser manually if using a fresh DB volume)*
    ```bash
    docker-compose exec web python example_project/manage.py createsuperuser
    ```

---

## 🏗 Architecture

### 1. The Core Engine
*   **Event Ingestion**: Signals or API calls create an immutable `Event` record alongside an `Outbox` entry inside a single transaction.
*   **Dispatcher**: A background worker (Celery) picks up `Outbox` items, locks them, and routes them to Automations.
*   **Runtime**: The Executor creates an `Execution` run, traversing the `Workflow` graph and invoking `Connectors`.

### 2. Connectors
Connectors are Python classes that implement the `BaseConnector` protocol. They handle the "side effects" (Slack, HTTP, etc.).
*   **Location**: `src/automate/connectors/`
*   **Registry**: Connectors are pluggable. Register them in `AppConfig.ready()`.

### 3. LLM Ops
We treat Prompts as code.
*   **Prompt Registry**: Store templated prompts in the DB.
*   **Versioning**: Iterate safely. Pin automations to specific versions.
*   **Providers**: Swap between OpenAI, Anthropic, or Local LLMs via config.

---

## 💬 Data Chat (NL2SQL)

An AI-powered natural language interface for querying your Django database.

### Features
- **Natural Language Queries**: Ask questions like "How many users signed up this week?"
- **SQL Generation**: LLM generates secure, read-only SQL
- **Schema Awareness**: Auto-exposes registered Django models
- **Conversation Memory**: Context-aware follow-up questions
- **Result Summarization**: LLM explains query results in plain language

### Quick Setup

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "automate_datachat",
]

# apps.py - Register models for Data Chat
from automate_datachat.registry import DataChatRegistry
from myapp.models import Product, Order

DataChatRegistry.register(Product, include_fields=["id", "name", "price"])
DataChatRegistry.register(Order, include_fields=["id", "customer_id", "total", "created_at"])
```

### Admin Widget
The chat widget is automatically available in Django Admin for staff users.

### Prompt Management
Prompts are stored in the database and editable via Admin → Prompts. Uses Jinja2 templating.

### LLM Logging
All LLM interactions are logged to `LLMRequest` with:
- Input/output payloads
- Token usage & latency
- Cost tracking (if configured)

---

## 🔌 MCP Server Integration

Connect external MCP (Model Context Protocol) servers to expose tools in the chat assistant.

### Registering an MCP Server

```python
# Via Admin → MCP Servers, or programmatically:
from automate.models import MCPServer

MCPServer.objects.create(
    name="Shopify MCP",
    slug="shopify-mcp",
    endpoint_url="http://localhost:3000",
    auth_type="bearer",
    auth_secret_ref="env:SHOPIFY_MCP_TOKEN",
)
```

### Syncing Tools

```bash
# Sync all enabled servers
python manage.py sync_mcp_tools

# Sync specific server
python manage.py sync_mcp_tools --server=shopify-mcp
```

Or use the Admin action: Select servers → "Sync tools"

### Tool Execution
Tools are automatically discovered and can be invoked by the chat assistant. The assistant can call tools like:
```
TOOL_CALL: {"tool": "get_products", "args": {"limit": 10}}
```

---

## 🔍 RAG Subsystem (Retrieval-Augmented Generation)

Unified interface for managing knowledge sources and creating high-performance retrieval APIs (`/api/rag/{slug}/query`).

### Features
- **Dual Modes**: 
    - **External Gateway**: Secure proxy to 3rd-party RAG microservices.
    - **Local Indexing**: Native **Milvus** and **PGVector** support.
- **Embedding Models**: Configurable providers (OpenAI, Azure, HuggingFace).
- **Security First**: SSRF-safe client, RBAC policies, and SecretRef credential management.
- **Observability**: Full query audit logging with latency and trace IDs.

### 1. External Gateway (Proxy)
Connect to existing RAG services without migrating data.
- **SSRF Protection**: Blocks private IPs, redirects, and enforces timeouts.
- **Unified API**: Exposes a standard retrieval contract regardless of backend.

### 2. Local Indexing (Native)
Run RAG entirely within your infrastructure.
- **Embeddings**: Define models via Admin (e.g., `openai-ada-002`).
- **Vector Stores**:
    - **Milvus**: High-scale vector database support.
    - **PGVector**: Simple, transactional vector search within Postgres.

```python
# Create a Local Index Source via Admin or Code
source = KnowledgeSource.objects.create(
    name="Internal Docs",
    provider_key="local_index",
    config={
        "vector_store": "milvus",
        "collection_name": "company_docs",
        "embedding_model": "openai-v3"
    }
)
```

---

## 🌐 Embeddable Chat Widget

Embed the Data Chat widget on external websites with security controls.

### Creating an Embed

1. Go to Admin → Automate Datachat → Chat Embeds
2. Create new embed with:
   - **Allowed Domains**: e.g., `["example.com", "*.myapp.io"]`
   - **Rate Limiting**: Requests per minute
   - **Theme**: Custom colors and title

### Embed Code

```html
<script 
  src="https://yoursite.com/datachat/embed/v1/<embed-id>/widget.js" 
  data-key="dce_YOUR_API_KEY">
</script>
```

### Security Features
- **Domain Whitelisting**: Only allowed origins can embed
- **API Key Authentication**: Each embed has a unique key
- **Rate Limiting**: Prevents abuse
- **Table Restrictions**: Limit which tables can be queried

---

## 🔌 Interop (n8n & Zapier)

### n8n Integration
*   **Export**: Go to any Workflow in Admin -> "Export to n8n JSON".
*   **Import**: Paste n8n JSON to scaffold a graph (supported nodes map to ours).
*   **Connect**: Use the `N8nWebhookConnector` to offload complex flows to self-hosted n8n.

### Zapier Mode
*   **Triggers**: Applications can poll `/api/zapier/triggers` or subscribe via Webhooks.
*   **Auth**: Secure your endpoints with `AUTOMATE_ZAPIER_API_KEY`.

---

## 🛠 Development

### Running Tests
```bash
# Unit & Integration
pytest

# Contract Tests (Connectors)
pytest packages/django_automate/tests/contract/

# E2E Smoke Tests
pytest packages/django_automate/tests/e2e/
```

### Management Commands

```bash
# Sync MCP tools from external servers
python manage.py sync_mcp_tools

# (Other commands as applicable)
```

### Contributing
See `CONTRIBUTING.md` for details on how to build a new Connector.

