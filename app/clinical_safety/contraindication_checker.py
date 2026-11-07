"""Contraindication verification for organ function, pregnancy, and medical conditions."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContraindicationCheckResult(BaseModel):
    has_contraindication: bool = False
    warnings: list[str] = Field(default_factory=list)
    missing_critical_labs: list[str] = Field(default_factory=list)


class ContraindicationChecker:
    """Evaluates medical condition, pregnancy, and organ impairment contraindications."""

    def check(
        self,
        medication_name: str,
        generic_name: str | None,
        patient_conditions: list[str],
        pregnancy_status: str | None,
        renal_function: str | None,
        hepatic_function: str | None,
    ) -> ContraindicationCheckResult:
        warnings: list[str] = []
        missing_labs: list[str] = []
        med_lower = (generic_name or medication_name).lower()

        # 1. Pregnancy contraindications
        is_pregnant = pregnancy_status and "pregnant" in pregnancy_status.lower()
        if is_pregnant:
            teratogenic_drugs = [
                "methotrexate", "isotretinoin", "warfarin", "valproate",
                "losartan", "enalapril", "lisinopril", "ramipril",  # ACEi / ARBs
                "atorvastatin", "simvastatin", "rosuvastatin",     # Statins
                "doxycycline", "ciprofloxacin",                    # Antibiotics with fetal risks
            ]
            if any(drug in med_lower for drug in teratogenic_drugs):
                warnings.append(
                    f"CRITICAL CONTRAINDICATION: '{medication_name}' is contraindicated in pregnancy (Category X / D risk)."
                )

        # 2. Renal function checks
        if not renal_function:
            renal_sensitive_drugs = ["metformin", "gentamicin", "ciprofloxacin", "allopurinol", "methotrexate"]
            if any(drug in med_lower for drug in renal_sensitive_drugs):
                missing_labs.append(
                    f"Renal function (eGFR / Serum Creatinine) not documented for nephro-cleared drug '{medication_name}'."
                )
        elif "impaired" in renal_function.lower() or "ckd" in renal_function.lower():
            if "metformin" in med_lower:
                warnings.append("CONTRAINDICATION / CAUTION: Metformin dose reduction or withholding required if eGFR < 30-45 mL/min.")
            if "nsaid" in med_lower or "ibuprofen" in med_lower or "diclofenac" in med_lower:
                warnings.append("CONTRAINDICATION: NSAIDs can precipitate acute kidney injury in renal impairment.")

        # 3. Medical condition contraindications
        conditions_str = " ".join(patient_conditions).lower()
        if ("asthma" in conditions_str or "copd" in conditions_str) and ("propranolol" in med_lower or "atenolol" in med_lower or "metoprolol" in med_lower):
            warnings.append("CAUTION: Non-selective / beta-blockers may provoke severe bronchospasm in asthma / COPD.")

        if ("peptic ulcer" in conditions_str or "gastritis" in conditions_str or "gi bleed" in conditions_str):
            if any(nsaid in med_lower for nsaid in ["aspirin", "ibuprofen", "diclofenac", "naproxen"]):
                warnings.append("CONTRAINDICATION: NSAIDs contraindicated in active peptic ulcer disease or history of GI bleeding.")

        return ContraindicationCheckResult(
            has_contraindication=len(warnings) > 0,
            warnings=warnings,
            missing_critical_labs=missing_labs,
        )

