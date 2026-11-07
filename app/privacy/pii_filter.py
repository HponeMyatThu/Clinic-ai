"""Privacy Boundary & PII Filtering Engine.

Enforces Section 5 of the GCMS Architecture Specification:
Patient name, NRIC/FIN, contact details remain inside trusted CMS/BFF.
Direct identifiers are scrubbed before any transmission to AI models.
"""

from __future__ import annotations

import re
from typing import Any


class PIIFilter:
    """Detects and redacts direct patient identifiers."""

    # Singapore NRIC / FIN pattern (e.g. S1234567A, T1234567B, F1234567C, G1234567D, M1234567E)
    NRIC_PATTERN = re.compile(r"\b[STFGMstfgm]\d{7}[A-Za-z]\b")

    # Singapore phone numbers (8-digit starting with 6, 8, 9, optionally prefixed with +65)
    PHONE_PATTERN = re.compile(r"(?:\+65\s?)?[689]\d{3}[-\s]?\d{4}\b")

    # Standard email addresses
    EMAIL_PATTERN = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")

    # Postal codes (Singapore 6-digit)
    POSTAL_PATTERN = re.compile(r"\bSingapore\s+\d{6}\b|\b\d{6}\b(?=\s*(?:singapore|sg))", re.IGNORECASE)

    # Common name prefixes/labels
    NAME_PREFIXES = re.compile(
        r"\b(?:patient(?:\s+name)?|pt|name|mr|mrs|ms|mdm|dr)\s*[:\-]?\s*([A-Za-z\s]{3,30})(?=[,\n\.;]|$)",
        re.IGNORECASE,
    )

    def redact_text(self, text: str | None) -> str:
        """Redact direct PII patterns from unstructured clinical text."""
        if not text:
            return ""

        cleaned = text

        # 1. Redact NRIC / FIN
        cleaned = self.NRIC_PATTERN.sub("[NRIC_REDACTED]", cleaned)

        # 2. Redact Phone numbers
        cleaned = self.PHONE_PATTERN.sub("[PHONE_REDACTED]", cleaned)

        # 3. Redact Email addresses
        cleaned = self.EMAIL_PATTERN.sub("[EMAIL_REDACTED]", cleaned)

        # 4. Redact Singapore postal codes
        cleaned = self.POSTAL_PATTERN.sub("[POSTAL_REDACTED]", cleaned)

        # 5. Redact explicit patient name patterns
        def _redact_name(match: re.Match) -> str:
            prefix = match.group(0).split(":")[0] if ":" in match.group(0) else "Patient"
            return f"{prefix}: [NAME_REDACTED]"

        cleaned = self.NAME_PREFIXES.sub(_redact_name, cleaned)

        return cleaned

    def sanitize_context_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively scrub all string values in a clinical context payload."""
        sanitized: dict[str, Any] = {}
        # Keys to discard outright
        forbidden_keys = {
            "nric", "fin", "patient_name", "full_name", "first_name", "last_name",
            "phone", "mobile", "email", "address", "postal_code", "mrn",
        }

        for key, value in data.items():
            if key.lower() in forbidden_keys:
                continue

            if isinstance(value, str):
                sanitized[key] = self.redact_text(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.redact_text(item) if isinstance(item, str)
                    else self.sanitize_context_dict(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_context_dict(value)
            else:
                sanitized[key] = value

        return sanitized

    def contains_pii(self, text: str) -> bool:
        """Check if raw text contains any identifiable NRIC, phone, or email."""
        if not text:
            return False
        return bool(
            self.NRIC_PATTERN.search(text)
            or self.PHONE_PATTERN.search(text)
            or self.EMAIL_PATTERN.search(text)
        )

