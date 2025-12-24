from __future__ import annotations

import re


class PIIScanner:
    """
    Regex-based PII scanner.
    Used to block or redact sensitive data before sending to LLM.
    """

    # Example heuristic patterns (Simple)
    PATTERNS = {
        "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    }

    def scan(self, text: str) -> list[str]:
        """Return list of detected PII types."""
        detected = []
        for label, pattern in self.PATTERNS.items():
            if re.search(pattern, text):
                detected.append(label)
        return detected

    def redact(self, text: str) -> str:
        """Replace detected PII with [REDACTED:TYPE]."""
        redacted = text
        for label, pattern in self.PATTERNS.items():
            redacted = re.sub(pattern, f"[REDACTED:{label}]", redacted)
        return redacted
