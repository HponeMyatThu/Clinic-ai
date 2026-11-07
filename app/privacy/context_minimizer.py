"""Context minimization to enforce 'minimum-necessary' healthcare data egress."""

from __future__ import annotations

from typing import Any
from app.schemas.consultation import ConsultationContext


class ContextMinimizer:
    """Enforces minimum-necessary context selection for AI tasks."""

    @staticmethod
    def prepare_for_diagnosis(context: ConsultationContext) -> dict[str, Any]:
        """Extract only fields relevant for differential diagnosis."""
        return {
            "chief_complaint": context.chief_complaint,
            "history_of_present_illness": context.history_of_present_illness,
            "symptoms": context.symptoms,
            "symptom_duration": context.symptom_duration,
            "medical_history": context.medical_history,
            "vital_signs": context.vital_signs.model_dump() if hasattr(context.vital_signs, "model_dump") else context.vital_signs,
            "examination_findings": context.examination_findings,
            "investigation_results": context.investigation_results,
            "patient_age": context.patient_age,
            "patient_gender": context.patient_gender,
        }

    @staticmethod
    def prepare_for_medications(
        context: ConsultationContext,
        selected_diagnosis: str,
    ) -> dict[str, Any]:
        """Extract only fields relevant for medication recommendations."""
        return {
            "selected_diagnosis": selected_diagnosis,
            "chief_complaint": context.chief_complaint,
            "symptoms": context.symptoms,
            "allergies": context.allergies,
            "current_medications": context.current_medications,
            "medical_history": context.medical_history,
            "pregnancy_status": context.pregnancy_status,
            "renal_function": context.renal_function,
            "hepatic_function": context.hepatic_function,
            "patient_age": context.patient_age,
        }

