# LLM Subsystem

The LLM subsystem provides a structured, safe, and efficient way to integrate Large Language Models into your workflows.

## Architecture

The system is built on four core components:

1.  **Backends (`automate.llm.providers`)**: Adapters for specific providers (OpenAI, Anthropic, Gemini).
2.  **Configuration (`LLMModelConfig`)**: Defines model parameters (temperature, max_tokens) and links to a provider.
3.  **Router (`LLMRouter`)**: Determines the active configuration based on precedence rules.
4.  **Engine (`LLMEngine`)**: Orchestrates the generation process, including template rendering and backend dispatch.

## Configuration Precedence

When an `LLM` node executes, the configuration is resolved in the following order:

1.  **Workflow/Runtime Override**: Explicit configuration passed to the execution (highest priority).
2.  **Environment Override (`PromptRelease`)**: Configuration specific to the deployment environment (e.g., use `gpt-4` in Prod, `gpt-3.5` in Dev).
3.  **Default Configuration (`PromptVersion`)**: The base configuration defined by the prompt author.

## Safety Features

### Jinja2 Sandboxing
All prompt templates are rendered using a **Sandboxed Environment**. This prevents malicious templates from accessing internal Python objects or executing unsafe code.
We also enforce `StrictUndefined`, meaning any variable used in a template *must* be provided in the input context, effectively preventing silent failures.

### Log Redaction
By default, raw prompts and completions are **Redacted** in logs to prevent accidental leakage of PII or sensitive data.
To enable full logging for debugging, set `AUTOMATE_LLM_LOG_PROMPTS = True` in your Django settings.

## Adding a New Provider

To add a custom provider:

1.  Create a subclass of `BaseLLMBackend` in `src/automate/llm/backend.py`.
2.  Implement the `complete()` method.
3.  Register it in the `LLMEngine` backend map.

```python
class MyCustomBackend(BaseLLMBackend):
    def complete(self, config, messages, **kwargs):
        # Implementation
        return {"content": "..."}
```
