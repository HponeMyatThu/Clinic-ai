"""Unit tests for Privacy Boundary and PII filtering engine using standard library unittest."""

import unittest
from app.privacy.pii_filter import PIIFilter


class TestPIIFilter(unittest.TestCase):
    def setUp(self):
        self.pii_filter = PIIFilter()

    def test_redact_singapore_nric(self):
        text = "Patient John Tan NRIC S1234567A presented with fever."
        cleaned = self.pii_filter.redact_text(text)
        self.assertNotIn("S1234567A", cleaned)
        self.assertIn("[NRIC_REDACTED]", cleaned)

    def test_redact_phone_numbers(self):
        text = "Contact patient at 91234567 or +65 67891234."
        cleaned = self.pii_filter.redact_text(text)
        self.assertNotIn("91234567", cleaned)
        self.assertNotIn("67891234", cleaned)
        self.assertIn("[PHONE_REDACTED]", cleaned)

    def test_redact_email_addresses(self):
        text = "Send lab report to test.patient@example.com immediately."
        cleaned = self.pii_filter.redact_text(text)
        self.assertNotIn("test.patient@example.com", cleaned)
        self.assertIn("[EMAIL_REDACTED]", cleaned)

    def test_sanitize_context_dict_removes_forbidden_keys(self):
        data = {
            "chief_complaint": "Persistent cough",
            "nric": "S9876543Z",
            "patient_name": "Alice Wong",
            "phone": "98765432",
            "symptoms": ["Fever S7654321A", "Chills"],
        }
        sanitized = self.pii_filter.sanitize_context_dict(data)

        self.assertNotIn("nric", sanitized)
        self.assertNotIn("patient_name", sanitized)
        self.assertNotIn("phone", sanitized)
        self.assertIn("chief_complaint", sanitized)
        self.assertIn("[NRIC_REDACTED]", sanitized["symptoms"][0])


if __name__ == "__main__":
    unittest.main()
