# LLM Providers & Profiles

Manage how you connect to AI models.

## Provider Adapters
We support:
*   `openai`
*   `anthropic`
*   `gemini` (Google)

## Connection Profiles
A **Connection Profile** stores the configuration (model name, temperature) and secrets (API Key) separately.
1.  Go to Admin > Governance > Connection Profiles.
2.  Create new profile "Production GPT-4".
3.  **Config**: `{"model": "gpt-4-turbo", "temperature": 0.0}`.
4.  **Secrets**: `{"api_key": "sk-..."}` (Redacted).

## Using Profiles
In your workflow or prompt configuration, reference the profile by name:
`"profile": "production-gpt-4"`

This allows you to switch models globally without editing 100 different workflows.
