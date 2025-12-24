from typing import Any

from jinja2 import Undefined
from jinja2.sandbox import SandboxedEnvironment


class StrictUndefined(Undefined):
    def __str__(self):
        raise ValueError(f"Undefined variable in prompt: {self._undefined_name}")

class PromptRenderer:
    """
    Renders prompts using a secured Jinja2 environment.
    Prevents access to unsafe internals (SandboxedEnvironment defaults).
    """

    def __init__(self):
        self.env = SandboxedEnvironment(
            undefined=StrictUndefined,
            autoescape=False # Prompts are text, usually don't need HTML escaping unless for web view
        )

    def render(self, template_text: str, variables: dict[str, Any]) -> str:
        template = self.env.from_string(template_text)
        return template.render(**variables)
