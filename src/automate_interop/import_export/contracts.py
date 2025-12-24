from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict

class WorkflowSanitizer(ABC):
    @abstractmethod
    def sanitize(self, workflow_json: Dict[str, Any]) -> Dict[str, Any]:
        """Strip credentials and unsafe data."""
        raise NotImplementedError

class Importer(ABC):
    @abstractmethod
    def parse(self, external_json: Dict[str, Any]) -> Dict[str, Any]:
        """Convert external JSON to internal model structure."""
        raise NotImplementedError

class Exporter(ABC):
    @abstractmethod
    def dump(self, internal_model: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal model to external JSON."""
        raise NotImplementedError
