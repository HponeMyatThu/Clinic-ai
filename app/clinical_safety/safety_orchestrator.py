"""Clinical Safety Orchestrator — coordinates all independent safety engines."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.clinical_safety.allergy_checker import AllergyChecker
from app.clinical_safety.contraindication_checker import ContraindicationChecker
from app.clinical_safety.duplicate_therapy_checker import DuplicateTherapyChecker
from app.clinical_safety.interaction_checker import InteractionChecker
from app.clinical_safety.missing_information import MissingInformationChecker
from app.schemas.common import SafetyStatus
from app.schemas.consultation import ConsultationContext


class MedicationSafetyReport(BaseModel):
    overall_status: SafetyStatus
    allergy_warnings: list[str] = Field(default_factory=list)
    interaction_warnings: list[str] = Field(default_factory=list)
    contraindication_warnings: list[str] = Field(default_factory=list)
    duplicate_warnings: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    summary: str = ""


class SafetyOrchestrator:
    """Evaluates safety rules independently from the LLM."""

    def __init__(self) -> None:
        self.allergy_checker = AllergyChecker()
        self.interaction_checker = InteractionChecker()
        self.contraindication_checker = ContraindicationChecker()
        self.duplicate_checker = DuplicateTherapyChecker()
        self.missing_info_checker = MissingInformationChecker()

    def evaluate_medication(
        self,
        medication_name: str,
        generic_name: str | None,
        active_ingredients: list[str],
        context: ConsultationContext,
    ) -> MedicationSafetyReport:
        # 1. Allergy check
        allergy_res = self.allergy_checker.check(
            medication_name=medication_name,
            generic_name=generic_name,
            active_ingredients=active_ingredients,
            patient_allergies=context.allergies,
        )

        # 2. Interaction check
        interaction_res = self.interaction_checker.check(
            proposed_medication=medication_name,
            generic_name=generic_name,
            current_medications=context.current_medications,
        )

        # 3. Contraindications
        contraindication_res = self.contraindication_checker.check(
            medication_name=medication_name,
            generic_name=generic_name,
            patient_conditions=context.medical_history,
            pregnancy_status=context.pregnancy_status,
            renal_function=context.renal_function,
            hepatic_function=context.hepatic_function,
        )

        # 4. Duplicate therapy
        duplicate_res = self.duplicate_checker.check(
            proposed_medication=medication_name,
            generic_name=generic_name,
            active_ingredients=active_ingredients,
            current_medications=context.current_medications,
        )

        # 5. Missing safety info
        missing_info = self.missing_info_checker.check_for_medications(context)
        missing_info.extend(contraindication_res.missing_critical_labs)

        # Combine warnings
        interaction_desc_list = [w.description for w in interaction_res.warnings]

        # Determine overall safety status
        if allergy_res.has_conflict or any("CRITICAL" in c for c in contraindication_res.warnings):
            overall_status = SafetyStatus.BLOCKED
            summary = "BLOCKED: Critical allergy or contraindication detected."
        elif interaction_res.has_warnings or duplicate_res.is_duplicate or contraindication_res.has_contraindication:
            overall_status = SafetyStatus.REQUIRES_REVIEW
            summary = "REQUIRES REVIEW: Drug interaction, duplicate therapy, or precaution identified."
        elif not allergy_res.allergy_data_recorded:
            overall_status = SafetyStatus.UNRESOLVED
            summary = "UNRESOLVED: Allergy documentation missing."
        else:
            overall_status = SafetyStatus.SAFE
            summary = "PASS: No contraindications or documented interactions identified."

        return MedicationSafetyReport(
            overall_status=overall_status,
            allergy_warnings=allergy_res.warnings,
            interaction_warnings=interaction_desc_list,
            contraindication_warnings=contraindication_res.warnings,
            duplicate_warnings=duplicate_res.warnings,
            missing_information=list(set(missing_info)),
            summary=summary,
        )

