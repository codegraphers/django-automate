# REST API Reference

Complete reference for all Django Automate REST API endpoints.

## Table of Contents

1. [Authentication](#authentication)
2. [Common Headers](#common-headers)
3. [Error Responses](#error-responses)
4. [Workflow API](#workflow-api)
5. [Execution API](#execution-api)
6. [Event API](#event-api)
7. [DataChat API](#datachat-api)
8. [RAG API](#rag-api)
9. [Embed API](#embed-api)

---

## Authentication

All API requests require authentication via one of the following methods:

### Bearer Token
```http
Authorization: Bearer <TOKEN>
```

### API Key
```http
X-API-Key: <API_KEY>
```

### Session Cookie
For admin users with active Django session.

### Obtaining Tokens

```http
POST /api/auth/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "secret"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 3600
}
```

---

## Common Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes* | Bearer token or API key |
| `Content-Type` | Yes | `application/json` for POST/PUT |
| `X-Tenant-ID` | Optional | Multi-tenant identifier |
| `X-Trace-ID` | Optional | Correlation ID for tracing |
| `X-Request-ID` | Optional | Idempotency key for mutations |

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {
        "field": "name",
        "message": "This field is required"
      }
    ],
    "trace_id": "abc123-def456"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request body |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Workflow API

### List Workflows

```http
GET /api/automate/workflows/
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 25 | Results per page (max 100) |
| `enabled` | bool | - | Filter by enabled status |
| `search` | string | - | Search by name/slug |
| `ordering` | string | `-created_at` | Sort field |

**Response:**
```json
{
  "count": 42,
  "next": "/api/automate/workflows/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Slack Notification",
      "slug": "slack-notification",
      "enabled": true,
      "trigger_type": "webhook",
      "workflow_version": 3,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-20T14:45:00Z"
    }
  ]
}
```

### Get Workflow

```http
GET /api/automate/workflows/{id}/
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Slack Notification",
  "slug": "slack-notification",
  "description": "Send notifications to Slack on new orders",
  "enabled": true,
  "trigger_type": "webhook",
  "trigger_config": {
    "event_type": "order.created",
    "source": "stripe"
  },
  "workflow_version": 3,
  "graph": {
    "nodes": [
      {
        "id": "step_1",
        "type": "slack.send_message",
        "config": {
          "channel": "#orders",
          "message": "{{ event.payload.customer_name }}"
        }
      }
    ],
    "edges": []
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T14:45:00Z"
}
```

### Create Workflow

```http
POST /api/automate/workflows/
Content-Type: application/json

{
  "name": "Order Processor",
  "slug": "order-processor",
  "description": "Process incoming orders",
  "enabled": true,
  "trigger_type": "webhook",
  "trigger_config": {
    "event_type": "order.created"
  },
  "graph": {
    "nodes": [
      {
        "id": "step_1",
        "type": "logging",
        "config": {
          "message": "Order received: {{ event.payload.order_id }}"
        }
      }
    ]
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Order Processor",
  "slug": "order-processor",
  ...
}
```

### Update Workflow

```http
PUT /api/automate/workflows/{id}/
Content-Type: application/json

{
  "name": "Updated Name",
  "enabled": false
}
```

### Delete Workflow

```http
DELETE /api/automate/workflows/{id}/
```

**Response:** `204 No Content`

---

## Execution API

### List Executions

```http
GET /api/automate/executions/
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workflow` | uuid | - | Filter by workflow ID |
| `status` | string | - | Filter by status (QUEUED, RUNNING, SUCCESS, FAILED) |
| `since` | datetime | - | Filter by created_at >= since |
| `until` | datetime | - | Filter by created_at <= until |

**Response:**
```json
{
  "count": 156,
  "results": [
    {
      "id": "exec-001",
      "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
      "workflow_name": "Slack Notification",
      "status": "SUCCESS",
      "attempt": 1,
      "started_at": "2024-01-20T14:45:00Z",
      "finished_at": "2024-01-20T14:45:02Z",
      "duration_ms": 2000,
      "trigger_event_id": "evt-001"
    }
  ]
}
```

### Get Execution Detail

```http
GET /api/automate/executions/{id}/
```

**Response:**
```json
{
  "id": "exec-001",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_name": "Slack Notification",
  "status": "SUCCESS",
  "attempt": 1,
  "context": {
    "source": "stripe",
    "event_type": "order.created"
  },
  "steps": [
    {
      "id": "step-001",
      "node_key": "step_1",
      "status": "SUCCESS",
      "input_data": {"channel": "#orders", "message": "***REDACTED***"},
      "output_data": {"ok": true, "ts": "1234567890.123456"},
      "started_at": "2024-01-20T14:45:00Z",
      "finished_at": "2024-01-20T14:45:02Z",
      "duration_ms": 2000
    }
  ],
  "error_summary": null,
  "started_at": "2024-01-20T14:45:00Z",
  "finished_at": "2024-01-20T14:45:02Z"
}
```

### Replay Execution

Re-run a failed execution with the same input.

```http
POST /api/automate/executions/{id}/replay/
```

**Response:** `202 Accepted`
```json
{
  "execution_id": "exec-002",
  "message": "Execution queued for replay",
  "trace_id": "abc123"
}
```

---

## Event API

### Ingest Webhook Event

```http
POST /api/automate/webhooks/{source}/
Content-Type: application/json
X-Webhook-Signature: sha256=abc123...

{
  "event_type": "order.created",
  "data": {
    "order_id": "ORD-123",
    "amount": 99.99,
    "customer_name": "John Doe"
  }
}
```

**Response:** `202 Accepted`
```json
{
  "event_id": "evt-001",
  "trace_id": "abc123-def456",
  "message": "Event accepted for processing"
}
```

### Emit Event Programmatically

```http
POST /api/automate/events/
Content-Type: application/json

{
  "type": "custom.event",
  "payload": {
    "key": "value"
  },
  "dedupe_key": "unique-key-123"
}
```

**Response:** `201 Created`
```json
{
  "event_id": "evt-002",
  "trace_id": "abc123"
}
```

---

## DataChat API

### Send Chat Message

```http
POST /api/datachat/chat/
Content-Type: application/json

{
  "question": "How many orders were placed last week?",
  "session_id": "optional-session-uuid",
  "context": {
    "tables": ["orders", "customers"]
  }
}
```

**Response:**
```json
{
  "answer": "There were 156 orders placed last week, totaling $15,432.50 in revenue.",
  "sql": "SELECT COUNT(*) as count, SUM(amount) as total FROM orders WHERE created_at >= NOW() - INTERVAL '7 days'",
  "data": {
    "columns": ["count", "total"],
    "rows": [[156, 15432.50]]
  },
  "session_id": "sess-001",
  "message_id": "msg-001",
  "trace_id": "abc123"
}
```

### Get Chat History

```http
GET /api/datachat/chat/history/
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | uuid | - | Filter by session |
| `page` | int | 1 | Page number |
| `limit` | int | 15 | Messages per page |

**Response:**
```json
{
  "session_id": "sess-001",
  "messages": [
    {
      "id": "msg-001",
      "role": "user",
      "content": "How many orders last week?",
      "created_at": "2024-01-20T10:00:00Z"
    },
    {
      "id": "msg-002",
      "role": "assistant",
      "content": "There were 156 orders...",
      "sql": "SELECT COUNT(*) ...",
      "created_at": "2024-01-20T10:00:02Z"
    }
  ],
  "has_more": false
}
```

---

## RAG API

### Query RAG Endpoint

```http
POST /api/rag/endpoints/{slug}/query/
Content-Type: application/json

{
  "query": "What is our refund policy?",
  "top_k": 5,
  "filters": {
    "category": "support"
  }
}
```

**Response:**
```json
{
  "query": "What is our refund policy?",
  "results": [
    {
      "id": "doc-001",
      "content": "Our refund policy allows returns within 30 days...",
      "score": 0.92,
      "metadata": {
        "source": "support-docs",
        "category": "support",
        "last_updated": "2024-01-15"
      }
    },
    {
      "id": "doc-002",
      "content": "Exceptions to the refund policy include...",
      "score": 0.87,
      "metadata": {
        "source": "support-docs",
        "category": "support"
      }
    }
  ],
  "latency_ms": 145,
  "trace_id": "abc123"
}
```

### Check RAG Endpoint Health

```http
GET /api/rag/endpoints/{slug}/health/
```

**Response:**
```json
{
  "status": "healthy",
  "endpoint": "support-docs",
  "provider": "pinecone",
  "document_count": 1523,
  "last_sync": "2024-01-20T00:00:00Z",
  "latency_ms": 23
}
```

---

## Embed API

### Get Widget JavaScript

```http
GET /api/embed/{embed_id}/widget.js
```

Returns JavaScript code to embed the chat widget.

### Embed Chat Message

```http
POST /api/embed/{embed_id}/chat/
Content-Type: application/json
X-API-Key: <EMBED_API_KEY>
Origin: https://allowed-domain.com

{
  "message": "Hello, I need help"
}
```

**Response:**
```json
{
  "response": "Hello! I'd be happy to help. What can I assist you with?",
  "session_id": "sess-embed-001"
}
```

### Get Embed Configuration

```http
GET /api/embed/{embed_id}/config/
X-API-Key: <EMBED_API_KEY>
```

**Response:**
```json
{
  "title": "Support Chat",
  "primary_color": "#667EEA",
  "welcome_message": "Hi! How can I help you today?",
  "placeholder": "Type your question...",
  "rate_limit": 60
}
```

---

## Rate Limiting

All endpoints are rate-limited. Limits are returned in headers:

```http
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 115
X-RateLimit-Reset: 1705747200
```

Default limits:

| Endpoint Type | Rate Limit |
|---------------|------------|
| Standard API | 120/minute |
| DataChat | 30/minute |
| RAG Query | 60/minute |
| Embed Widget | 60/minute per embed |

---

## OpenAPI Schema

Full OpenAPI 3.0 specification is available at:

- **Swagger UI:** `/api/schema/swagger-ui/`
- **ReDoc:** `/api/schema/redoc/`
- **OpenAPI JSON:** `/api/schema/`

## See Also

- [Python API Reference](../python-api/index.md)
- [Authentication Guide](../../guides/customization.md#configuration-via-settings)
- [API Base Classes](../api-base-classes.md)
