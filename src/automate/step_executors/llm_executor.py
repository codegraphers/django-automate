"""
LLM Step Executor

Executes an LLM prompt and returns the generated content.
"""
import logging
import time

from .base import BaseStepExecutor, StepContext, StepResult, register_step_executor

logger = logging.getLogger(__name__)


@register_step_executor("llm")
class LLMStepExecutor(BaseStepExecutor):
    """
    Execute an LLM prompt step.
    
    Config:
        prompt_slug: str - The slug of the prompt to use
        prompt_version: int - Optional version (default: latest approved)
        variables: dict - Variables to pass to the prompt template
        model_override: str - Optional model name override
    """

    def validate_config(self) -> bool:
        return "prompt_slug" in self.config

    def execute(self, context: StepContext) -> StepResult:
        start_time = time.time()

        try:
            import json
            import os

            from jinja2 import Environment

            from automate.models import LLMModelConfig, Prompt
            from automate_governance.secrets.interfaces import SecretsBackend
            from automate_governance.secrets.refs import SecretRef
            from automate_governance.secrets.resolver import SecretResolver
            from automate_llm.provider.interfaces import CompletionRequest
            from automate_llm.registry import get_provider_class

            prompt_slug = self.config.get("prompt_slug")
            prompt_version = self.config.get("prompt_version")
            variables = self.config.get("variables", {})

            # Resolve template variables
            resolved_vars = {}
            for key, value in variables.items():
                if isinstance(value, str):
                    resolved_vars[key] = self._resolve_template(value, context)
                else:
                    resolved_vars[key] = value

            # Add event data as a variable
            resolved_vars["event"] = context.event_payload
            resolved_vars["previous"] = context.previous_outputs

            # Get prompt
            prompt = Prompt.objects.get(slug=prompt_slug)
            if prompt_version:
                version = prompt.versions.filter(version=prompt_version).first()
            else:
                version = prompt.versions.filter(status="approved").order_by("-version").first()

            if not version:
                return StepResult(
                    success=False,
                    output=None,
                    error=f"No approved version found for prompt: {prompt_slug}"
                )

            # Render templates
            env = Environment()

            # Safe tojson filter that handles non-serializable objects
            def safe_tojson(x):
                try:
                    return json.dumps(x)
                except (TypeError, ValueError):
                    return json.dumps(str(x))

            env.filters['tojson'] = safe_tojson
            system_tpl = env.from_string(version.system_template)
            user_tpl = env.from_string(version.user_template)

            system_prompt = system_tpl.render(**resolved_vars)
            user_prompt = user_tpl.render(**resolved_vars)

            # Get LLM provider
            model_config = LLMModelConfig.get_default()
            if not model_config:
                return StepResult(
                    success=False,
                    output=None,
                    error="No LLM model configured"
                )

            # Setup provider
            provider = model_config.provider
            provider_cls = get_provider_class(provider.slug)

            if not provider_cls:
                return StepResult(
                    success=False,
                    output=None,
                    error=f"Provider {provider.slug} not found"
                )

            # Resolve API key
            class EnvBackend(SecretsBackend):
                def resolve(self, ref: SecretRef) -> str:
                    return os.environ.get(ref.name, "")

            resolver = SecretResolver(backends={"env": EnvBackend()})

            api_key_source = provider.api_key_env_var
            if api_key_source.startswith("sk-"):
                class RawKeyResolver:
                    def __init__(self, key):
                        self._key = key
                    def resolve_value(self, ref, **kwargs):
                        return self._key
                resolver = RawKeyResolver(api_key_source)
                api_key_ref = api_key_source
            else:
                api_key_ref = f"secretref://env/llm/{api_key_source}"

            llm_provider = provider_cls(
                secret_resolver=resolver,
                api_key_ref=api_key_ref,
                org_id_ref=None
            )

            # Make the LLM call
            response = llm_provider.chat_complete(
                CompletionRequest(
                    model=model_config.name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return StepResult(
                success=True,
                output=response.content,
                duration_ms=duration_ms,
                metadata={
                    "prompt_slug": prompt_slug,
                    "model": model_config.name,
                    "tokens": response.usage if hasattr(response, 'usage') else None
                }
            )

        except Prompt.DoesNotExist:
            return StepResult(
                success=False,
                output=None,
                error=f"Prompt not found: {self.config.get('prompt_slug')}"
            )
        except Exception as e:
            logger.exception(f"LLM step execution failed: {e}")
            return StepResult(
                success=False,
                output=None,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )
