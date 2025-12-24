from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EvalResult:
    ok: bool
    summary: dict[str, Any]
    scores: list[dict[str, Any]]

class EvalService:
    def run_dataset(self, *, prompt_key: str, prompt_version: str, dataset_id: int, mode: str = "async") -> dict[str, Any]:
        # TODO: create EvalRun, enqueue or execute sync
        raise NotImplementedError
