"""Missing clinical information detector."""

from __future__ import annotations

from app.schemas.consultation import ConsultationContext


class MissingInformationChecker:
    """Flags critical missing data required for clinical decision safety."""

    @staticmethod
    def check_for_diagnosis(context: ConsultationContext) -> list[str]:
        missing: list[str] = []
        if not context.symptom_duration:
            missing.append("Symptom duration (onset timing is critical for acute vs chronic differential)")
        if not context.vital_signs:
            missing.append("Baseline vital signs (BP, heart rate, temperature, SpO2)")
        if not context.examination_findings:
            missing.append("Physical examination findings (system-focused examination not documented)")
        if not context.medical_history:
            missing.append("Past medical history / comorbidities")
        return missing

    @staticmethod
    def check_for_medications(context: ConsultationContext) -> list[str]:
        missing: list[str] = []
        if not context.allergies:
            missing.append("Allergy status (drug allergy documentation missing or unverified)")
        if not context.current_medications:
            missing.append("Current medication list (required to rule out drug-drug interactions)")
        if not context.renal_function:
            missing.append("Renal function documentation (eGFR / Serum Creatinine)")
        if context.patient_age is None:
            missing.append("Patient age (required for pediatric / geriatric dosage safety)")
        return missing

