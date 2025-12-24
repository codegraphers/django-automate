import logging
from collections.abc import Iterable
from typing import Any

import requests

from automate_modal.contracts import Capability, ExecutionCtx, ModalResult, ModalTaskType, StreamEvent
from automate_modal.registry import ProviderBase
from automate_modal.security.ssrf import safe_download

logger = logging.getLogger(__name__)

class VideoSTTCapability(Capability):
    def __init__(self, parent: 'VideoPipelineProvider'):
        self.task_type = ModalTaskType.VIDEO_STT
        self.parent = parent

    def validate(self, req: dict[str, Any]) -> None:
        if "url" not in req:
            raise ValueError("Request must contain 'url'")

    def run(self, req: dict[str, Any], ctx: ExecutionCtx) -> ModalResult:
        url = req["url"]

        # 1. Download
        # TODO: Check cache or existing artifacts?
        artifact = safe_download(url, ctx.blob)

        # OpenAI Whisper API limit is 25MB
        if artifact.size_bytes > 25 * 1024 * 1024:
            raise ValueError(f"Video size {artifact.size_bytes} exceeds OpenAI Whisper limit of 25MB. Chunking not yet implemented.")

        # 2. Transcribe
        # We use a simplified Whisper call here directly, reusing OpenAI key
        # In a generic pipeline, we'd call engine.execute("whisper-endpoint", ...)

        api_key = self.parent.resolve_api_key(ctx)
        transcribe_url = "https://api.openai.com/v1/audio/transcriptions"

        # Re-open artifact
        # Note: LocalBlobStore returns file handle.
        # But requests.post files needs a tuple or handle.
        # We need to ensure we read it or pass handle.
        file_obj = ctx.blob.open(artifact.uri)

        files = {
            "file": ("video.mp4", file_obj, "application/octet-stream") # Whisper handles video formats usually
        }
        data = {"model": "whisper-1", "response_format": "verbose_json"}
        headers = {"Authorization": f"Bearer {api_key}"}

        response = requests.post(transcribe_url, headers=headers, files=files, data=data)
        response.raise_for_status()
        result = response.json()

        # Transcript Artifact
        text = result.get("text", "")
        trans_artifact = ctx.blob.put_bytes(
            data=text.encode("utf-8"),
            mime="text/plain",
            filename=f"{ctx.request_id}_transcript.txt",
            meta={"source_video": url}
        )

        return ModalResult(
            task_type=self.task_type,
            outputs={"text": text, "video_size": artifact.size_bytes},
            artifacts=[artifact, trans_artifact],
            usage={"duration": result.get("duration")},
            raw_provider_meta=result
        )

    def stream(self, req: dict[str, Any], ctx: ExecutionCtx) -> Iterable[StreamEvent]:
        # Emulate progress
        # Since we do sync steps (download, transcribe), we can't easily stream progress
        # unless we break it down or use callbacks.
        # For job execution, the engine might poll?
        pass

class VideoPipelineProvider(ProviderBase):
    key = "video-pipeline"
    display_name = "Video Processing Pipeline"
    config = {}

    @classmethod
    def config_schema(cls) -> dict:
        return {
            "type": "object",
            "required": ["api_key_ref"], # Reusing OpenAI key for STT
            "properties": {
                "api_key_ref": {"type": "string"},
            }
        }

    @property
    def capabilities(self) -> list[Capability]:
        return [
            VideoSTTCapability(self),
        ]

    def build_client(self, cfg: dict, ctx: ExecutionCtx) -> Any:
        pass

    def resolve_api_key(self, ctx: ExecutionCtx) -> str:
        ref = self.config.get("api_key_ref")
        return ctx.secrets.resolve(ref)
