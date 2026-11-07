"""CMS Adapter to map CMS encounter data into ConsultationContext."""

from __future__ import annotations

from typing import Any
from app.cms.client import CMSClient
from app.schemas.consultation import ConsultationContext


class CMSAdapter:
    """Translates CMS encounter JSON structures into validated ConsultationContext objects."""

    def __init__(self, client: CMSClient) -> None:
        self.client = client

    async def fetch_and_map_consultation(
        self,
        encounter_id: str,
        auth_token: str | None = None,
    ) -> ConsultationContext:
        raw_data = await self.client.get_consultation(encounter_id, auth_token)

        # Map typical CMS fields to ConsultationContext
        return ConsultationContext(
            consultation_id=str(raw_data.get("id") or encounter_id),
            chief_complaint=raw_data.get("chief_complaint") or raw_data.get("complaint", "General consultation"),
            history_of_present_illness=raw_data.get("history_of_present_illness") or raw_data.get("hpi"),
            symptoms=raw_data.get("symptoms", []),
            symptom_duration=raw_data.get("duration"),
            medical_history=raw_data.get("past_medical_history", []),
            current_medications=raw_data.get("medications", []),
            allergies=raw_data.get("allergies", []),
            vital_signs=raw_data.get("vitals"),
            examination_findings=raw_data.get("physical_exam", []),
            investigation_results=raw_data.get("labs", []),
            patient_age=raw_data.get("age"),
            patient_gender=raw_data.get("gender"),
            pregnancy_status=raw_data.get("pregnancy_status"),
            renal_function=raw_data.get("renal_function"),
            hepatic_function=raw_data.get("hepatic_function"),
        )

