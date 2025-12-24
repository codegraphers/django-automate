from typing import Any, Dict
from hashlib import sha256
import json
from .contracts import Importer, Exporter
from .sanitizer import JsonSanitizer

class N8nJsonAdapter(Importer, Exporter):
    def __init__(self):
        self.sanitizer = JsonSanitizer()

    def parse(self, external_json: Dict[str, Any]) -> Dict[str, Any]:
        # Validate structure (nodes, connections)
        if "nodes" not in external_json or "connections" not in external_json:
             raise ValueError("Invalid n8n JSON: missing nodes/connections")
        
        safe_json = self.sanitizer.sanitize(external_json)
        
        # Canonical hash for drift detection
        drift_hash = self._compute_hash(safe_json)

        return {
            "source_type": "n8n",
            "safe_definition": safe_json,
            "drift_hash": drift_hash,
            # In a real impl, we'd map nodes to internal Steps here
        }

    def dump(self, internal_model: Dict[str, Any]) -> Dict[str, Any]:
        # Pass-through safe definition for MVP
        return internal_model.get("safe_definition", {})

    def _compute_hash(self, data: Dict[str, Any]) -> str:
        # Sort keys for stable hashing
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return sha256(serialized.encode("utf-8")).hexdigest()
