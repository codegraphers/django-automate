import logging
from collections.abc import Iterable
from typing import Any

import requests

from automate_modal.contracts import Capability, ExecutionCtx, ModalResult, ModalTaskType, StreamEvent
from automate_modal.registry import ProviderBase

logger = logging.getLogger(__name__)

class OpenAITTSCapability(Capability):
    def __init__(self, parent: 'OpenAIAudioProvider'):
        self.task_type = ModalTaskType.AUDIO_TTS
        self.parent = parent

    def validate(self, req: dict[str, Any]) -> None:
        if "text" not in req:
            raise ValueError("TTS request must contain 'text'")

    def run(self, req: dict[str, Any], ctx: ExecutionCtx) -> ModalResult:
        api_key = self.parent.resolve_api_key(ctx)

        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": req.get("model", "tts-1"),
            "input": req.get("text"),
            "voice": req.get("voice", "alloy"),
            "response_format": req.get("format", "mp3")
        }

        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()

        # Stream to BlobStore
        # For simplicity in sync run, we read content.
        # Ideally we stream this directly to blob if blob supports stream write.
        # Our LocalBlobStore.put_bytes takes bytes.

        audio_data = response.content
        mime_map = {"mp3": "audio/mpeg", "aac": "audio/aac", "flac": "audio/flac", "opus": "audio/opus"}
        mime = mime_map.get(payload["response_format"], "audio/mpeg")

        artifact = ctx.blob.put_bytes(
            data=audio_data,
            mime=mime,
            filename=f"{ctx.request_id}.{payload['response_format']}",
            meta={"provider": "openai", "task": "tts", "voice": payload["voice"]}
        )

        return ModalResult(
            task_type=self.task_type,
            outputs={"message": "Audio generated"},
            artifacts=[artifact],
            usage={"chars": len(payload["input"])},
            raw_provider_meta={}
        )

    def stream(self, req: dict[str, Any], ctx: ExecutionCtx) -> Iterable[StreamEvent]:
        # OpenAI supports chunked transfer encoding for audio
        raise NotImplementedError("Audio streaming not implemented yet")

class OpenAIWhisperCapability(Capability):
    def __init__(self, parent: 'OpenAIAudioProvider'):
        self.task_type = ModalTaskType.AUDIO_STT
        self.parent = parent

    def validate(self, req: dict[str, Any]) -> None:
        if "audio_artifact_uri" not in req and "audio_url" not in req:
            raise ValueError("STT request must contain 'audio_artifact_uri' or 'audio_url'")

    def run(self, req: dict[str, Any], ctx: ExecutionCtx) -> ModalResult:
        api_key = self.parent.resolve_api_key(ctx)

        # Resolve Input
        if "audio_artifact_uri" in req:
            file_obj = ctx.blob.open(req["audio_artifact_uri"])
            filename = "audio.mp3" # simplistic
        elif "audio_url" in req:
            # Download temp?
            # For simplicity let's assume artifact usage primarily
            raise NotImplementedError("Direct URL STT not supported yet, use Artifact")

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}

        # Multipart form data
        files = {
            "file": (filename, file_obj, "audio/mpeg")
        }
        data = {
            "model": req.get("model", "whisper-1"),
            "response_format": "verbose_json"
        }

        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        result_json = response.json()

        text = result_json.get("text", "")
        segments = result_json.get("segments", [])

        # Store transcript as artifact too?
        transcript_bytes = text.encode("utf-8")
        trans_artifact = ctx.blob.put_bytes(
            data=transcript_bytes,
            mime="text/plain",
            filename=f"{ctx.request_id}_transcript.txt",
            meta={"source": "whisper"}
        )

        return ModalResult(
            task_type=self.task_type,
            outputs={
                "text": text,
                "segments_count": len(segments),
                "duration": result_json.get("duration")
            },
            artifacts=[trans_artifact],
            usage={"duration": result_json.get("duration")},
            raw_provider_meta=result_json
        )

class OpenAIAudioProvider(ProviderBase):
    key = "openai-audio"
    display_name = "OpenAI Audio (TTS/Whisper)"
    config = {}

    @classmethod
    def config_schema(cls) -> dict:
        return {
            "type": "object",
            "required": ["api_key_ref"],
            "properties": {
                "api_key_ref": {"type": "string"},
            }
        }

    @property
    def capabilities(self) -> list[Capability]:
        return [
            OpenAITTSCapability(self),
            OpenAIWhisperCapability(self),
        ]

    def build_client(self, cfg: dict, ctx: ExecutionCtx) -> Any:
        pass

    def resolve_api_key(self, ctx: ExecutionCtx) -> str:
        ref = self.config.get("api_key_ref")
        return ctx.secrets.resolve(ref)
