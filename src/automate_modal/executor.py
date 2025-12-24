import logging
from typing import Any

from automate.step_executors.base import BaseStepExecutor, StepContext, StepResult, register_step_executor
from automate_modal.contracts import ArtifactRef, ModalResult
from automate_modal.engine import engine

logger = logging.getLogger(__name__)

@register_step_executor("modal")
class ModalExecuteStep(BaseStepExecutor):
    """
    Workflow step to execute a Multi-Modal Gateway task.
    
    Configuration:
        endpoint: str (slug)
        task_type: str (e.g. "llm.chat")
        input: Dict (the payload)
        wait_for_completion: bool (default True, if False submits async job)
    """

    def validate_config(self) -> bool:
        return "endpoint" in self.config and "task_type" in self.config

    def execute(self, context: StepContext) -> StepResult:
        try:
            endpoint_slug = self._resolve_template(self.config.get("endpoint"), context)
            task_type = self._resolve_template(self.config.get("task_type"), context)

            # Resolve input structure recursively
            raw_input = self.config.get("input", {})
            input_payload = self._resolve_nested(raw_input, context)

            wait = self.config.get("wait_for_completion", True)

            if wait:
                # Synchronous Execution
                result: ModalResult = engine.execute(
                    endpoint_slug=endpoint_slug,
                    task_type=task_type,
                    req=input_payload,
                    actor_id=f"workflow:{context.execution_id}"
                )

                # Convert artifacts to dicts for JSON serialization safety in workflow context
                artifacts_data = [self._artifact_to_dict(a) for a in result.artifacts]

                return StepResult(
                    success=True,
                    output={
                        "outputs": result.outputs,
                        "artifacts": artifacts_data,
                        "usage": result.usage
                    },
                    metadata={"provider": result.raw_provider_meta.get("provider", "unknown")}
                )
            else:
                # Async Job Submission
                job_id = engine.submit_job(
                    endpoint_slug=endpoint_slug,
                    task_type=task_type,
                    req=input_payload,
                    actor_id=f"workflow:{context.execution_id}"
                )

                return StepResult(
                    success=True,
                    output={"job_id": job_id, "status": "queued"},
                    metadata={"mode": "async"}
                )

        except Exception as e:
            logger.exception("Modal execution failed")
            return StepResult(
                success=False,
                output=None,
                error=str(e)
            )

    def _resolve_nested(self, data: Any, context: StepContext) -> Any:
        if isinstance(data, dict):
            return {k: self._resolve_nested(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._resolve_nested(v, context) for v in data]
        elif isinstance(data, str):
            return self._resolve_template(data, context)
        return data

    def _artifact_to_dict(self, artifact: ArtifactRef) -> dict:
        return {
            "kind": artifact.kind,
            "uri": artifact.uri,
            "mime": artifact.mime,
            "size_bytes": artifact.size_bytes,
            "meta": artifact.meta
        }
