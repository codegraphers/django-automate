# Golden Path Example

A complete example using Core + LLM + RAG + Connector.

## What It Does

1. Receives a webhook payload
2. Queries RAG for relevant context
3. Sends to LLM for response generation
4. Posts result to Slack

## Quick Start

```bash
cd examples/golden_path
docker-compose up -d
```

## Files

- `docker-compose.yml` - Runs Django + Postgres + Redis
- `workflow.json` - The automation definition
- `test_e2e.py` - End-to-end test

## Trigger

```bash
curl -X POST http://localhost:8000/automate/api/v1/events/ \
  -H "Content-Type: application/json" \
  -d '{"type": "question", "data": {"text": "What is Django Automate?"}}'
```
