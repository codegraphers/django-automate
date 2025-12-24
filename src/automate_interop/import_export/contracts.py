from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class WorkflowSanitizer(ABC):
    @abstractmethod
    def sanitize(self, workflow_json: dict[str, Any]) -> dict[str, Any]:
        """Strip credentials and unsafe data."""
        raise NotImplementedError

class Importer(ABC):
    @abstractmethod
    def parse(self, external_json: dict[str, Any]) -> dict[str, Any]:
        """Convert external JSON to internal model structure."""
        raise NotImplementedError

class Exporter(ABC):
    @abstractmethod
    def dump(self, internal_model: dict[str, Any]) -> dict[str, Any]:
        """Convert internal model to external JSON."""
        raise NotImplementedError
