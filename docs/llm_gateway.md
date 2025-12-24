# LLM Gateway

## Overview
A vendor-agnostic gateway for LLM interactions with built-in governance, costing, and safety.

## Configuration
Configure providers in `settings.py`:

```python
AUTOMATE = {
    "LLM": {
        "PROVIDERS": {
            "default": "openai_main",
            "registry": {
                "openai_main": {
                    "BACKEND": "automate_llm.provider.openai.OpenAIProvider",
                    "API_KEY": "secretref://env/openai/api_key"
                }
            }
        }
    }
}
```

## Features

### 1. Prompt Management
- Store prompts in the DB (`PromptTemplate`).
- Use **Jinja2** syntax with strict sandboxing (no `__class__` access).
- Versioned templates.

### 2. Governance
- **Budget**: Daily spending limits per tenant.
- **Audit**: Every request logged to `LLMRequest` table with cost, token usage, and latency.
- **PII**: Automatic regex scanning for Email, Phone, SSN before sending to provider.

### 3. Usage
```python
from automate_llm.client import LLMClient

response = client.chat(
    template="summarize_email",
    inputs={"email_body": "..."}
)
print(response.content)
```
