from collections.abc import Iterable
from typing import Any

from automate_modal.contracts import Capability, ExecutionCtx, ModalResult, ModalTaskType, StreamEvent
from automate_modal.registry import ProviderBase


class EchoCapability(Capability):
    def __init__(self, task_type):
        self.task_type = task_type

    def validate(self, req: dict[str, Any]) -> None:
        if not req:
            raise ValueError("Request cannot be empty")

    def run(self, req: dict[str, Any], ctx: ExecutionCtx) -> ModalResult:
        return ModalResult(
            task_type=self.task_type, outputs={"echo": req, "msg": "Echo from provider"}, usage={"units": 1}
        )

    def stream(self, req: dict[str, Any], ctx: ExecutionCtx) -> Iterable[StreamEvent]:
        # Emulate stream
        import time

        prompt = req.get("prompt", "echo")
        for _i, char in enumerate(prompt):
            yield StreamEvent(type="token", data={"text": char}, ts=time.time())
            time.sleep(0.01)


class EchoProvider(ProviderBase):
    key = "echo"
    display_name = "Echo (Test) Provider"

    @property
    def capabilities(self) -> list[Capability]:
        return [
            EchoCapability(ModalTaskType.LLM_CHAT),
            EchoCapability(ModalTaskType.AUDIO_TTS),
        ]

    @classmethod
    def config_schema(cls) -> dict:
        return {"type": "object", "properties": {}}

    def build_client(self, cfg: dict, ctx: ExecutionCtx) -> Any:
        return None
