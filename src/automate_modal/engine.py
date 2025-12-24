"""
Core Execution Engine.

Orchestrates:
1. Endpoint & Provider resolution
2. Context creation (Secrets, Blob)
3. Policy checks
4. Capability execution (Sync/Async/Stream)
5. Result persistence
"""
import logging
import time
import uuid
from collections.abc import Generator
from typing import Any

from django.utils import timezone

from .blob.local import LocalBlobStore
from .contracts import ArtifactRef, ExecutionCtx, ModalResult, StreamEvent
from .models import ModalAuditEvent, ModalEndpoint, ModalJob
from .queue.celery import CeleryJobQueue
from .registry import ProviderRegistry
from .secrets.env import EnvSecretsResolver

logger = logging.getLogger(__name__)

class ExecutionEngine:

    def __init__(self):
        # In a real app, these would be injected or loaded from settings
        self.secrets = EnvSecretsResolver()
        self.blob = LocalBlobStore()
        self.queue = CeleryJobQueue()

    def execute(self, *, endpoint_slug: str, task_type: str, req: dict[str, Any], actor_id: str | None = None) -> ModalResult:
        """
        Synchronous execution.
        """
        start_ts = time.time()
        endpoint = self._get_endpoint(endpoint_slug, task_type)
        provider, capability = self._get_capability(endpoint, task_type)

        ctx = self._build_ctx(endpoint, actor_id=actor_id)

        try:
            # 1. Validate
            capability.validate(req)

            # 2. Check Policy/Budget (TODO)
            # self.policy_engine.check(...)

            # 3. Run
            result = capability.run(req, ctx)

            # 4. Audit
            self._audit_log(endpoint, task_type, ctx, "success", start_ts)

            # 5. Persist standalone artifacts if needed
            # (Providers usually return ArtifactRefs that are already "persisted" in blob,
            # but we might want to track them in ModalArtifact table explicitly here?)
            self._persist_artifacts(result.artifacts)

            return result

        except Exception as e:
            logger.exception(f"Execution failed: {e}")
            self._audit_log(endpoint, task_type, ctx, "error", start_ts, error=str(e))
            raise

    def stream(self, *, endpoint_slug: str, task_type: str, req: dict[str, Any], actor_id: str | None = None) -> Generator[StreamEvent, None, None]:
        """
        Streaming execution generator.
        """
        endpoint = self._get_endpoint(endpoint_slug, task_type)
        provider, capability = self._get_capability(endpoint, task_type)
        ctx = self._build_ctx(endpoint, actor_id=actor_id)

        try:
            capability.validate(req)
            iterator = capability.stream(req, ctx)

            for event in iterator:
                yield event

        except Exception as e:
            logger.exception("Stream failed")
            yield StreamEvent(type="error", data={"message": str(e)}, ts=time.time())

    def submit_job(self, *, endpoint_slug: str, task_type: str, req: dict[str, Any], actor_id: str | None = None) -> str:
        """
        Submit async job. Returns job_id.
        """
        endpoint = self._get_endpoint(endpoint_slug, task_type)

        # Create Job Record
        job = ModalJob.objects.create(
            endpoint=endpoint,
            task_type=task_type,
            state=ModalJob.State.QUEUED,
            scheduled_at=timezone.now(),
            # TODO: Redact payload
            payload_redacted=req,
            correlation_id=str(uuid.uuid4()) # or from trace context
        )

        # Enqueue
        self.queue.enqueue(
            job_name="automate_modal.tasks.execute_job",
            payload={"job_id": job.job_id}
        )

        return job.job_id

    # --- Internals ---

    def _get_endpoint(self, slug: str, task_type: str) -> ModalEndpoint:
        try:
            endpoint = ModalEndpoint.objects.get(slug=slug, enabled=True)
        except ModalEndpoint.DoesNotExist:
            raise ValueError(f"Endpoint '{slug}' not found or disabled")

        if task_type not in endpoint.allowed_task_types:
             raise ValueError(f"Task '{task_type}' not allowed for endpoint '{slug}'")

        return endpoint

    def _get_capability(self, endpoint: ModalEndpoint, task_type: str) -> tuple:
        provider_cls = ProviderRegistry.get(endpoint.provider_config.provider_key)
        provider_instance = provider_cls()

        # Inject configuration
        provider_instance.configure(endpoint.provider_config.config)

        # Find capability
        for cap in provider_instance.capabilities:
            if cap.task_type == task_type:
                return provider_instance, cap

        raise ValueError(f"Provider {provider_cls.key} does not support task {task_type}")

    def _build_ctx(self, endpoint: ModalEndpoint, actor_id: str = None) -> ExecutionCtx:
        return ExecutionCtx(
            request_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()), # TODO: propagation
            actor_id=actor_id,
            tenant_id=None,
            policy=endpoint.access_policy,
            secrets=self.secrets,
            blob=self.blob,
            logger=logger,
            now_ts=time.time()
        )

    def _audit_log(self, endpoint, task_type, ctx, outcome, start_ts, error=None):
        ModalAuditEvent.objects.create(
            actor_id=ctx.actor_id,
            action="run.execute",
            target_type="endpoint",
            target_id=endpoint.slug,
            correlation_id=ctx.correlation_id,
            request_id=ctx.request_id,
            meta={
                "task_type": task_type,
                "outcome": outcome,
                "duration_ms": int((time.time() - start_ts) * 1000),
                "error": error
            }
        )

    def _persist_artifacts(self, refs: list[ArtifactRef]):
        # Optional: verify blob existence or create DB records
        pass

# Singleton
engine = ExecutionEngine()
