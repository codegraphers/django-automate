"""
Workflow Executor

Orchestrates the execution of a complete workflow by running steps in sequence.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from django.utils import timezone

from .base import (
    BaseStepExecutor, 
    StepContext, 
    StepResult, 
    get_step_executor,
    list_step_types
)

# Import executors to register them
from . import llm_executor
from . import action_executor
from . import filter_executor

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    Executes a workflow by running each step in sequence.
    
    Workflow Definition Format:
        {
            "steps": [
                {
                    "id": "step_1",
                    "type": "filter",
                    "name": "Check Order Value",
                    "config": {...}
                },
                {
                    "id": "step_2", 
                    "type": "llm",
                    "name": "Generate Summary",
                    "config": {"prompt_slug": "order_summarizer", ...}
                },
                {
                    "id": "step_3",
                    "type": "action",
                    "name": "Send to Slack",
                    "config": {"action_type": "slack", ...}
                }
            ]
        }
    """
    
    def __init__(self, execution: "Execution"):
        """
        Args:
            execution: The Execution model instance
        """
        self.execution = execution
        self.event = execution.event
        self.automation = execution.automation
        
    def run(self) -> bool:
        """
        Execute the workflow.
        
        Returns:
            True if workflow completed successfully, False otherwise
        """
        from automate.models import ExecutionStep, ExecutionStatusChoices, Workflow
        
        # Mark execution as running
        self.execution.status = ExecutionStatusChoices.RUNNING
        self.execution.started_at = timezone.now()
        self.execution.save(update_fields=["status", "started_at"])
        
        start_time = time.time()
        
        try:
            # Get workflow definition
            workflow = self._get_workflow()
            if not workflow:
                self._fail_execution("No workflow found for automation")
                return False
            
            steps_def = workflow.graph.get("nodes", []) or workflow.graph.get("steps", [])
            if not steps_def:
                logger.warning(f"Workflow {workflow.id} has no steps defined")
                self._complete_execution(start_time)
                return True
            
            # Build initial context
            context = StepContext(
                execution_id=str(self.execution.id),
                step_index=0,
                previous_outputs={},
                event_payload=self.event.payload or {},
                automation_config=workflow.graph.get("config", {})
            )
            
            # Execute each step
            for idx, step_def in enumerate(steps_def):
                step_id = step_def.get("id", f"step_{idx}")
                step_type = step_def.get("type", "action")
                step_name = step_def.get("name", f"Step {idx + 1}")
                step_config = step_def.get("config", {})
                
                logger.info(f"Executing step {idx + 1}/{len(steps_def)}: {step_name} ({step_type})")
                
                # Update context
                context.step_index = idx
                
                # Get executor
                executor = get_step_executor(step_type, step_config)
                if not executor:
                    self._fail_execution(f"Unknown step type: {step_type}")
                    return False
                
                # Execute step
                step_start = time.time()
                result = executor.execute(context)
                
                # Log step result
                ExecutionStep.objects.create(
                    execution=self.execution,
                    step_id=step_id,
                    step_name=step_name,
                    connector_slug=step_type,  # Use step type as connector slug
                    input_data={"config": step_config, "context_keys": list(context.previous_outputs.keys())},
                    output_data={"output": result.output, "metadata": result.metadata} if result.success else {},
                    status="success" if result.success else "failed",
                    duration_ms=result.duration_ms or int((time.time() - step_start) * 1000),
                    error_message=result.error or ""
                )
                
                # Check if step failed and should stop
                if not result.success:
                    # Check if it's a filter that stopped intentionally
                    if step_type == "filter" and result.output and result.output.get("action") == "stopped":
                        logger.info(f"Workflow stopped by filter at step {idx + 1}")
                        self._complete_execution(start_time, partial=True)
                        return True
                    else:
                        self._fail_execution(f"Step {step_name} failed: {result.error}")
                        return False
                
                # Check for branching (from filter steps)
                if step_type == "filter" and result.output:
                    if result.output.get("action") == "branch":
                        branch_to = result.output.get("branch_to")
                        # Find the branch step index
                        branch_idx = self._find_step_index(steps_def, branch_to)
                        if branch_idx is not None:
                            # Skip to branch (modify the loop by updating steps_def slice)
                            logger.info(f"Branching to step: {branch_to}")
                            # For now, we'll just log - proper branching requires more complex flow
                
                # Store output for next step
                context.previous_outputs[step_id] = result.output
            
            # All steps completed
            self._complete_execution(start_time)
            return True
            
        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            self._fail_execution(str(e))
            return False
    
    def _get_workflow(self) -> Optional["Workflow"]:
        """Get the workflow definition for this execution."""
        # Try to get specific version
        if self.execution.workflow_version:
            workflow = self.automation.workflows.filter(
                version=self.execution.workflow_version
            ).first()
            if workflow:
                return workflow
        
        # Fallback to live or latest
        workflow = self.automation.workflows.filter(is_live=True).first()
        if not workflow:
            workflow = self.automation.workflows.order_by("-version").first()
        
        return workflow
    
    def _complete_execution(self, start_time: float, partial: bool = False):
        """Mark execution as completed."""
        from automate.models import ExecutionStatusChoices
        
        self.execution.status = ExecutionStatusChoices.SUCCESS
        self.execution.finished_at = timezone.now()
        self.execution.duration_ms = int((time.time() - start_time) * 1000)
        if partial:
            self.execution.error_summary = "Completed (partial - stopped by filter)"
        self.execution.save()
        
        logger.info(f"Execution {self.execution.id} completed in {self.execution.duration_ms}ms")
    
    def _fail_execution(self, error: str):
        """Mark execution as failed."""
        from automate.models import ExecutionStatusChoices
        
        self.execution.status = ExecutionStatusChoices.FAILED
        self.execution.finished_at = timezone.now()
        self.execution.error_summary = error[:1000]
        self.execution.save()
        
        logger.error(f"Execution {self.execution.id} failed: {error}")
    
    def _find_step_index(self, steps: List[Dict], step_id: str) -> Optional[int]:
        """Find the index of a step by its ID."""
        for idx, step in enumerate(steps):
            if step.get("id") == step_id:
                return idx
        return None


def run_pending_executions(limit: int = 10):
    """
    Run pending executions. Called by management command or scheduler.
    """
    from automate.models import Execution, ExecutionStatusChoices
    
    pending = Execution.objects.filter(
        status=ExecutionStatusChoices.QUEUED
    ).select_related("event", "automation").order_by("id")[:limit]
    
    results = {"success": 0, "failed": 0}
    
    for execution in pending:
        try:
            executor = WorkflowExecutor(execution)
            if executor.run():
                results["success"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            logger.exception(f"Failed to run execution {execution.id}: {e}")
            results["failed"] += 1
    
    return results
