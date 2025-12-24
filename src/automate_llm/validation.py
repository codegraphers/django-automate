from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json

@dataclass
class ValidationResult:
    ok: bool
    errors: List[str]

class OutputValidator:
    def validate_structure(self, response_text: str, schema: Optional[Dict[str, Any]]) -> ValidationResult:
        """
        Validate that the response text conforms to the expected JSON schema.
        Future: Integrate with jsonschema library.
        """
        if not schema:
            return ValidationResult(ok=True, errors=[])

        try:
            # 1. Parse JSON
            data = json.loads(response_text)
            
            # 2. Schema check (stub for now, assuming jsonschema package available)
            # from jsonschema import validate, ValidationError
            # try:
            #     validate(instance=data, schema=schema)
            # except ValidationError as e:
            #     return ValidationResult(ok=False, errors=[str(e)])

            return ValidationResult(ok=True, errors=[])
        except json.JSONDecodeError as e:
             return ValidationResult(ok=False, errors=[f"Invalid JSON: {str(e)}"])

    def validate_tool_calls(self, tool_calls: List[Any], allowed_tools: List[str]) -> ValidationResult:
        """
        Ensure tool calls are within the allowed list.
        """
        errors = []
        for tc in tool_calls:
            if tc.name not in allowed_tools:
                errors.append(f"Tool {tc.name} not permitted.")
        
        return ValidationResult(ok=len(errors) == 0, errors=errors)
