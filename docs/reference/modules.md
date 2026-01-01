# Modules Overview

Django Automate is organized into **Core** modules (always needed) and **Suite** modules (add what you need).

---

## Core Modules

These modules form the foundation of every Django Automate installation.

| Module | Description |
|--------|-------------|
| `automate` | Main app, admin integration, settings |
| `automate_core` | Execution engine, workflows, jobs, outbox |
| `automate_api` | REST API v1 endpoints |

```python
INSTALLED_APPS = [
    # Core - Always Required
    "automate",
    "automate_core",
    "automate_api",
]
```

---

## Suite Modules

Add these modules based on your needs.

### LLM & AI

| Module | Description | Extra |
|--------|-------------|-------|
| `automate_llm` | LLM provider abstraction | `[llm-openai]` |
| `automate_datachat` | NL2SQL chat interface | - |
| `rag` | RAG endpoints, embeddings | `[rag-milvus]` |

### Integrations

| Module | Description | Extra |
|--------|-------------|-------|
| `automate_connectors` | External service adapters | `[connectors-slack]` |
| `automate_interop` | n8n, Zapier webhooks | - |

### Operations

| Module | Description | Extra |
|--------|-------------|-------|
| `automate_studio` | Visual workflow builder | - |
| `automate_governance` | Audit logs, policies | - |
| `automate_observability` | OpenTelemetry tracing | `[observability]` |
| `automate_modal` | Multi-modal processing | - |

---

## Full Suite Install

```python
INSTALLED_APPS = [
    # Core
    "automate",
    "automate_core",
    "automate_api",
    
    # Suite - LLM
    "automate_llm",
    "automate_datachat",
    "rag",
    
    # Suite - Integrations
    "automate_connectors",
    "automate_interop",
    
    # Suite - Operations
    "automate_studio",
    "automate_governance",
    "automate_observability",
    "automate_modal",
]
```

---

## Decision Guide

| Need | Recommended Modules |
|------|---------------------|
| Just workflows | Core only |
| LLM chatbot | Core + `automate_llm` |
| RAG pipeline | Core + `rag` + `automate_llm` |
| Slack integration | Core + `automate_connectors[connectors-slack]` |
| Full AI agent | Full suite |
