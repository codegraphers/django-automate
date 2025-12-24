"""
Core Contracts for Multi-Modal Gateway

Defines the stable interfaces for:
- Task Types
- Execution Context
- Artifacts & Results
- Capabilities
- Platform Services
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class ModalTaskType:
    """Standardized task types."""
    LLM_CHAT = "llm.chat"
    LLM_EMBED = "llm.embed"
    AUDIO_TTS = "audio.tts"
    AUDIO_STT = "audio.stt"
    IMAGE_TEXT2IMG = "image.text2img"
    IMAGE_IMG2IMG = "image.img2img"
    VIDEO_TEXT2VIDEO = "video.text2video"
    VIDEO_DOWNLOAD = "video.download"
    VIDEO_STT = "video.stt"  # composite task

@dataclass
class ArtifactRef:
    """Reference to a heavy artifact stored in BlobStorage."""
    kind: str                       # "text", "audio", "image", "video", "json", "transcript"
    uri: str                        # blob://... or s3://... or https://...
    mime: str
    size_bytes: int
    sha256: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

@dataclass
class ModalResult:
    """Unified output for all modal tasks."""
    task_type: str
    outputs: dict[str, Any] = field(default_factory=dict) # small payload (text snippets, metadata)
    artifacts: list[ArtifactRef] = field(default_factory=list) # heavy payload references
    usage: dict[str, Any] = field(default_factory=dict)   # tokens/seconds/cost
    raw_provider_meta: dict[str, Any] = field(default_factory=dict)  # safe subset only

@dataclass
class StreamEvent:
    """Unified event for streaming responses and job progress."""
    type: str                       # "token", "audio_chunk", "progress", "artifact", "final", "error"
    data: dict[str, Any]
    ts: float

# --- Platform Services Protocols ---

@runtime_checkable
class SecretsResolver(Protocol):
    """Resolves SecretRef strings (e.g. env://API_KEY) to actual values."""
    def resolve(self, secret_ref: str) -> str: ...

@runtime_checkable
class BlobStore(Protocol):
    """Abstract storage for artifacts."""
    def put_bytes(self, *, data: bytes, mime: str, filename: str, meta: dict) -> ArtifactRef: ...
    def open(self, uri: str) -> Any: ...
    def generate_presigned_url(self, uri: str, expiration: int = 3600) -> str: ...

@runtime_checkable
class JobQueue(Protocol):
    """Abstract job queue for async execution."""
    def enqueue(self, job_name: str, payload: dict[str, Any], *, priority: int = 5, delay_s: int = 0) -> str:
        """Enqueue a job and return job_id."""
        ...

    def cancel(self, job_id: str) -> None:
        """Cancel a pending job."""
        ...

@dataclass
class ExecutionCtx:
    """Context passed to every capability execution."""
    request_id: str
    correlation_id: str
    actor_id: str | None
    tenant_id: str | None
    policy: dict[str, Any]         # RBAC decisions, budgets, constraints
    secrets: SecretsResolver       # resolves SecretRef
    blob: BlobStore                # store/retrieve files
    logger: Any
    now_ts: float

# --- Capability Protocol ---

@runtime_checkable
class Capability(Protocol):
    """A specific unit of work (e.g. OpenAI Chat, ElevenLabs TTS)."""
    task_type: str

    def validate(self, req: dict[str, Any]) -> None:
        """Validate request payload schema. Raise ValueError if invalid."""
        ...

    def run(self, req: dict[str, Any], ctx: ExecutionCtx) -> ModalResult:
        """Execute the task synchronously."""
        ...

    def stream(self, req: dict[str, Any], ctx: ExecutionCtx) -> Iterable[StreamEvent]:
        """
        Optional. Return an iterator of events.
        If not implemented, platform may emulate or fallback.
        """
        ...
