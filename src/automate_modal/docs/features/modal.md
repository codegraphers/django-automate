# Multi-Modal Gateway

The **Multi-Modal Gateway** (`automate_modal`) provides a unified runtime for connecting AI models (LLM, Audio, Video, Image) to your Django application and Automation Workflows.

## Core Concepts

1.  **Providers**: Wrappers for external APIs (OpenAI, ElevenLabs, Runway) or local models.
2.  **Endpoints**: Named configurations (slugs) that expose a specific Capability (e.g., `company-chatbot-v1` -> `OpenAI GPT-4`).
3.  **Caps/Policies**: Rate limits, RBAC, and budgets are enforced at the Endpoint level.
4.  **Jobs**: Heavy tasks run asynchronously on a queue (Celery).

## Workflow Integration

You can use the gateway inside Automate workflows using the `modal` step type.

```yaml
steps:
  - id: analyze_image
    type: modal
    config:
      endpoint: "vision-pro"
      task_type: "llm.chat"
      input:
        messages:
          - role: "user"
            content: "Describe this image"
            image: "{{ event.payload.image_url }}"
    
  - id: generate_speech
    type: modal
    config:
      endpoint: "tts-english"
      task_type: "audio.tts"
      input:
        text: "{{ previous.analyze_image.outputs.content }}"
      wait_for_completion: true
```

## Admin Features

-   **Test Console**: Try any endpoint directly from the Django Admin.
-   **Import/Export**: Bulk manage configurations.
-   **Audit Logs**: Full trace of every request and job.

## Adding Custom Providers

Create a class inheriting from `ProviderBase`:

```python
from automate_modal.registry import ProviderBase, ProviderRegistry

class MyCustomProvider(ProviderBase):
    key = "my-custom"
    # ... implement capabilities
    
ProviderRegistry.register(MyCustomProvider)
```
