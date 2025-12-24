from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class EvalResult:
    ok: bool
    summary: Dict[str, Any]
    scores: List[Dict[str, Any]]

class EvalService:
    def run_dataset(self, *, prompt_key: str, prompt_version: str, dataset_id: int, mode: str = "async") -> Dict[str, Any]:
        # TODO: create EvalRun, enqueue or execute sync
        raise NotImplementedError
