"""
Base Step Executor

All workflow step executors inherit from this base class.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StepContext:
    """Context passed to each step executor."""

    execution_id: str
    step_index: int
    previous_outputs: dict[str, Any]  # {step_id: output}
    event_payload: dict[str, Any]
    automation_config: dict[str, Any]


@dataclass
class StepResult:
    """Result from executing a step."""

    success: bool
    output: Any
    error: str | None = None
    duration_ms: int | None = None
    metadata: dict[str, Any] | None = None


class BaseStepExecutor(ABC):
    """
    Abstract base class for all step executors.

    Each step type (LLM, Action, Filter, etc.) implements this interface.
    """

    step_type: str = "base"

    def __init__(self, config: dict[str, Any]):
        """
        Args:
            config: Step configuration from the workflow definition
        """
        self.config = config

    @abstractmethod
    def execute(self, context: StepContext) -> StepResult:
        """
        Execute the step.

        Args:
            context: Execution context with previous outputs and event data

        Returns:
            StepResult with success status, output, and optional error
        """
        pass

    def validate_config(self) -> bool:
        """Validate step configuration. Override in subclasses."""
        return True

    def _resolve_template(self, template: str, context: StepContext) -> str:
        """
        Resolve Jinja2 template variables in config values.

        Supports:
        - {{ event.payload.field }}
        - {{ previous.step_id.field }}
        - {{ env.VARIABLE }}
        """
        if not template or not isinstance(template, str):
            return template

        if "{{" not in template:
            return template

        try:
            import os

            from jinja2 import Template

            tpl = Template(template)
            return tpl.render(
                event={"payload": context.event_payload}, previous=context.previous_outputs, env=os.environ
            )
        except Exception as e:
            logger.warning(f"Template resolution failed: {e}")
            return template


# Step type registry
_step_executors: dict[str, type] = {}


def register_step_executor(step_type: str):
    """Decorator to register a step executor class."""

    def decorator(cls):
        _step_executors[step_type] = cls
        cls.step_type = step_type
        return cls

    return decorator


def get_step_executor(step_type: str, config: dict[str, Any]) -> BaseStepExecutor | None:
    """Get an executor instance for the given step type."""
    executor_cls = _step_executors.get(step_type)
    if executor_cls:
        return executor_cls(config)
    logger.error(f"Unknown step type: {step_type}")
    return None


def list_step_types() -> list:
    """List all registered step types."""
    return list(_step_executors.keys())
