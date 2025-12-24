import logging
import traceback

from django.utils import timezone

from ..chaos import ChaosModule
from ..context import set_current_correlation_id, set_current_tenant
from ..services.leases import LeaseManager
from ..services.side_effects import SideEffectManager
from ..workflows.models import Workflow
from .models import Execution, ExecutionStatusChoices, StepRun

logger = logging.getLogger(__name__)

class ExecutionEngine:
    """
    SRE-Grade Execution Worker.
    Responsible for:
    - Claiming Execution Leases (Concurrency Control)
    - Traversing the Graph
    - Executing Steps with SideEffect Protection
    - Handling Retries and Failures with Chaos Injection
    """

    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.leases = LeaseManager(worker_id)
        self.side_effects = SideEffectManager()

    def run_execution(self, execution_id: str):
        """
        Main entry point for Worker.
        Idempotent: Can be called multiple times for the same execution.
        """
        # 0. Context & locking check
        # We need to fetch basic info first to set context?
        # Ideally we load the execution first.
        try:
            execution = Execution.objects.get(id=execution_id)
        except Execution.DoesNotExist:
            logger.error(f"Execution {execution_id} not found.")
            return

        # Set Context
        set_current_tenant(execution.tenant_id)
        set_current_correlation_id(str(execution.correlation_id))

        # 1. Acquire Lease (D1)
        if not self.leases.acquire_execution(execution_id):
            logger.warning(f"Could not acquire lease for {execution_id}. Locked by another worker?")
            return

        logger.info(f"Worker {self.worker_id} acquired execution {execution_id}")

        try:
            # Refresh data after lock
            execution.refresh_from_db()

            # 2. Chaos Hook (Start) - D4
            ChaosModule.check_and_raise("execution:start", {"execution_id": execution_id})

            if execution.status in (ExecutionStatusChoices.SUCCESS, ExecutionStatusChoices.FAILED, ExecutionStatusChoices.CANCELED):
                logger.info(f"Execution {execution_id} already finished: {execution.status}")
                return

            # 3. Load Graph
            # In a real system, we'd cache this or fetch from Workflow model
            # For now, simplistic traversal stub.
            workflow = Workflow.objects.filter(
                automation=execution.automation,
                version=execution.workflow_version
            ).first()

            if not workflow:
                self._fail_execution(execution, "Workflow version not found")
                return

            graph = workflow.graph # Expected: {"nodes": [...], "edges": [...]}

            # 4. Determine Next Steps
            # Simple linear execution for MVP? Or finding pending steps?
            # Let's find pending steps based on `execution.steps`.

            runnable_nodes = self._get_runnable_nodes(execution, graph)

            if not runnable_nodes:
                # If no running/pending steps and we ran something, maybe we are done?
                # Check if all end nodes are done.
                if self._check_completion(execution, graph):
                    self._complete_execution(execution)
                return

            # 5. Execute Steps
            for node in runnable_nodes:
                self._execute_step(execution, node)

            # 6. Check Completion immediately
            if self._check_completion(execution, graph):
                self._complete_execution(execution)

        except Exception as e:
            logger.error(f"Engine Crash for {execution_id}: {traceback.format_exc()}")
            self._handle_crash(execution, e)
        finally:
            # 6. Release Lease (or let it expire?)
            # SRE Practice: Release if done, otherwise keep if long-running?
            # Usually release so others can pick up next retry or step.
            self.leases.release_execution(execution_id)

    def _execute_step(self, execution: Execution, node: dict):
        node_key = node["id"]

        # 1. Idempotency / Step Record
        step_run, created = StepRun.objects.get_or_create(
            execution=execution,
            node_key=node_key,
            defaults={
                "status": ExecutionStatusChoices.RUNNING,
                "input_data": {}, # Resolve inputs here
            }
        )

        if step_run.status == ExecutionStatusChoices.SUCCESS:
            return # Already done

        logger.info(f"Running step {node_key}")

        try:
            # Chaos Hook (Pre-Step)
            ChaosModule.check_and_raise("step:pre", {"node_key": node_key})

            # 2. Side Effect Check (D2)
            # Example: If node type is "stripe_charge", we check log.
            # action = node.get("type")
            # params = node.get("config")
            # se_key = self.side_effects.compute_key(execution.id, node_key, action, params)
            # cached = self.side_effects.check(execution.tenant_id, se_key)
            # if cached: return cached...

            # SIMULATION OF WORK
            # ... call provider ...

            # Chaos Hook (Provider Call)
            ChaosModule.check_and_raise("provider:call", {"node_key": node_key})

            output = {"result": "ok", "mock": True}

            # 3. Record Success
            step_run.status = ExecutionStatusChoices.SUCCESS
            step_run.output_data = output
            step_run.finished_at = timezone.now()
            step_run.save()

            # Chaos Hook (Post-Step)
            ChaosModule.check_and_raise("step:post", {"node_key": node_key})

        except Exception as e:
            logger.error(f"Step {node_key} failed: {e}")
            step_run.status = ExecutionStatusChoices.FAILED
            step_run.error_data = {"message": str(e)}
            step_run.save()
            # Retry logic would go here (Outbox reschedule)
            raise e # Bubble up for now to crash execution

    def _get_runnable_nodes(self, execution: Execution, graph: dict) -> list:
        # Stub: Just return first node if no steps, or next node.
        # This graph traversal logic is complex, simplifying for MVP structure.
        nodes = graph.get("nodes", [])
        if not nodes: return []

        # Check existing steps
        existing_keys = set(execution.steps.values_list("node_key", flat=True))

        # Return nodes not yet run (Linear assumption for MVP)
        for node in nodes:
            if node["id"] not in existing_keys:
                return [node]
        return []

    def _check_completion(self, execution: Execution, graph: dict) -> bool:
        # Check if all nodes run
        nodes = graph.get("nodes", [])
        existing_count = execution.steps.filter(status=ExecutionStatusChoices.SUCCESS).count()
        return existing_count >= len(nodes)

    def _complete_execution(self, execution: Execution):
        execution.status = ExecutionStatusChoices.SUCCESS
        execution.finished_at = timezone.now()
        execution.save()
        logger.info(f"Execution {execution.id} COMPLETED SUCCESS.")

    def _fail_execution(self, execution: Execution, reason: str):
        execution.status = ExecutionStatusChoices.FAILED
        execution.context["error"] = reason
        execution.finished_at = timezone.now()
        execution.save()

    def _handle_crash(self, execution: Execution, exception: Exception):
        """
        D3: Robust Retries & DLQ Logic
        """
        import traceback

        # Max constant for now (could be dynamic policy)
        MAX_RETRIES = 5

        execution.attempt += 1

        if execution.attempt > MAX_RETRIES:
            # DLQ / Permanent Fail
            logger.error(f"Execution {execution.id} exceeded max retries ({MAX_RETRIES}). Moving to FAILED (DLQ candidate).")
            execution.status = ExecutionStatusChoices.FAILED
            execution.context["last_error"] = str(exception)
            execution.context["traceback"] = traceback.format_exc()
            execution.finished_at = timezone.now()
            execution.save()
            return

        # Schedule Retry
        # Exponential Backoff: 2^attempt (seconds) + jitter
        import random
        backoff_seconds = (2 ** (execution.attempt - 1)) * 10
        jitter = random.randint(1, 5)
        delay = backoff_seconds + jitter

        next_attempt = timezone.now() + timezone.timedelta(seconds=delay)

        logger.warning(f"Execution {execution.id} crashed. Retrying in {delay}s (Attempt {execution.attempt})")

        # We don't have a "next_attempt_at" field on Execution (only on OutboxItem).
        # But we do have `lease_expires_at`.
        # We can simulate "sleeping" by setting the lease to expire in `delay`?
        # No, that invites stealing.
        # Efficient way: Set status=QUEUED, but we need a way to delay pick up.
        # Alternatively, create an OutboxItem "execution.resume" with `next_attempt_at` set.

        # SRE Approach: Use Outbox to schedule the retry reliably.
        from ..outbox.models import OutboxItem

        execution.status = ExecutionStatusChoices.QUEUED
        execution.context["last_error"] = str(exception)
        execution.save()

        OutboxItem.objects.create(
            tenant_id=execution.tenant_id,
            kind="execution_queued",
            payload={"execution_id": str(execution.id)},
            status="RETRY",
            next_attempt_at=next_attempt,
            attempt_count=execution.attempt
        )
