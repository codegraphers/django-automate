import logging
from typing import Any

logger = logging.getLogger(__name__)

class WorkflowCompiler:
    """
    Validates and compiles workflow graphs.
    """

    def validate(self, graph: dict[str, Any]) -> list[str]:
        """
        Returns list of validation errors.
        """
        errors = []

        nodes = graph.get("nodes", [])
        if not isinstance(nodes, list):
            errors.append("graph.nodes must be a list")
            return errors

        node_ids = set()
        for node in nodes:
            nid = node.get("id")
            if not nid:
                errors.append("Checking node without ID")
                continue

            if nid in node_ids:
                errors.append(f"Duplicate node ID: {nid}")
            node_ids.add(nid)

            # Check type
            ntype = node.get("type")
            if not ntype:
                errors.append(f"Node {nid} missing type")

            # Check next pointers
            next_nodes = node.get("next", [])
            if not isinstance(next_nodes, list):
                errors.append(f"Node {nid} 'next' must be list")

        # Validate edges (references exist)
        for node in nodes:
            next_nodes = node.get("next", [])
            for target in next_nodes:
                if target not in node_ids:
                    errors.append(f"Node {node['id']} points to unknown node {target}")

        return errors

    def compile(self, graph: dict[str, Any]) -> dict[str, Any]:
        """
        Optimizes graph for execution (e.g. adjacency list).
        For now, returns as is if valid.
        """
        errors = self.validate(graph)
        if errors:
            raise ValueError(f"Invalid workflow: {'; '.join(errors)}")

        return graph
