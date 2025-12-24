from __future__ import annotations

from typing import Any

from .engine import RuleNode


class RuleCompiler:
    """
    Analyzes rules to extract indexable terms for DB capabilities.
    Example: {"==": [{"var": "event.type"}, "order.created"]}
    -> index_terms: ["event.type=order.created"]
    """

    def extract_index_terms(self, rule: RuleNode) -> list[str]:
        terms: set[str] = set()
        self._visit(rule, terms)
        return sorted(list(terms))

    def _visit(self, node: RuleNode, terms: set[str]) -> None:
        if not isinstance(node, dict):
            return

        # Check for simple equality: { "==": [ {"var": "path"}, "literal" ] }
        # Or { "==": [ "literal", {"var": "path"} ] }
        if "==" in node:
            args = node["=="]
            if isinstance(args, list) and len(args) == 2:
                path = self._get_var_path(args[0])
                val = args[1]
                if path and self._is_literal(val):
                    terms.add(f"{path}={val}")
                else:
                    path = self._get_var_path(args[1])
                    val = args[0]
                    if path and self._is_literal(val):
                        terms.add(f"{path}={val}")

        # Recurse
        for key, val in node.items():
            if isinstance(val, list):
                for item in val:
                    self._visit(item, terms)
            elif isinstance(val, dict):
                self._visit(val, terms)

    def _get_var_path(self, node: Any) -> str | None:
        if isinstance(node, dict) and "var" in node:
            return str(node["var"])
        return None

    def _is_literal(self, node: Any) -> bool:
        return isinstance(node, (str, int, float, bool))
