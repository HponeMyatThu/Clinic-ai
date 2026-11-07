"""Deterministic allergy cross-check engine."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AllergyCheckResult(BaseModel):
    has_conflict: bool
    warnings: list[str] = Field(default_factory=list)
    allergy_data_recorded: bool = True


class AllergyChecker:
    """Checks proposed medications against known patient drug allergies."""

    # Cross-reactivity mapping (e.g. penicillin allergy cross-reacts with amoxicillin, augmentin, ampicillin)
    ALLERGY_CROSS_REACTIONS: dict[str, list[str]] = {
        "penicillin": [
            "amoxicillin", "ampicillin", "augmentin", "co-amoxiclav",
            "piperacillin", "cloxacillin", "penicillin",
        ],
        "sulfa": [
            "sulfamethoxazole", "bactrim", "septrin", "sulfasalazine",
            "dapsone", "furosemide", "hydrochlorothiazide",
        ],
        "nsaid": [
            "aspirin", "ibuprofen", "diclofenac", "naproxen", "mefenamic acid",
            "meloxicam", "celecoxib", "ketorolac", "etoricoxib",
        ],
        "aspirin": [
            "aspirin", "ibuprofen", "diclofenac", "naproxen", "mefenamic acid",
        ],
        "cephalosporin": [
            "cephalexin", "cefuroxime", "ceftriaxone", "ceftazidime", "cefazolin",
        ],
        "macrolide": [
            "azithromycin", "clarithromycin", "erythromycin", "roxithromycin",
        ],
        "statin": [
            "simvastatin", "atorvastatin", "rosuvastatin", "pravastatin",
        ],
    }

    def check(
        self,
        medication_name: str,
        generic_name: str | None,
        active_ingredients: list[str],
        patient_allergies: list[str],
    ) -> AllergyCheckResult:
        if not patient_allergies:
            return AllergyCheckResult(
                has_conflict=False,
                warnings=["Notice: No known allergies recorded in patient profile. Verify allergy status with patient."],
                allergy_data_recorded=False,
            )

        warnings: list[str] = []
        med_tokens = [medication_name.lower()]
        if generic_name:
            med_tokens.append(generic_name.lower())
        for ing in active_ingredients:
            med_tokens.append(ing.lower())

        for allergy in patient_allergies:
            allergy_clean = allergy.strip().lower()
            if not allergy_clean or allergy_clean in ("nil", "none", "nka", "nkda"):
                continue

            # 1. Direct name match
            for token in med_tokens:
                if allergy_clean in token or token in allergy_clean:
                    warnings.append(
                        f"CRITICAL ALLERGY ALERT: Patient has documented allergy to '{allergy}'. "
                        f"Matches proposed medication/ingredient '{token}'."
                    )
                    break

            # 2. Cross-reactivity class match
            for drug_class, related_drugs in self.ALLERGY_CROSS_REACTIONS.items():
                if drug_class in allergy_clean or any(rd in allergy_clean for rd in related_drugs):
                    for token in med_tokens:
                        if any(rd in token for rd in related_drugs):
                            msg = (
                                f"CROSS-REACTIVITY WARNING: Patient allergic to '{allergy}'. "
                                f"Proposed drug '{token}' carries known cross-reactivity risk with {drug_class}s."
                            )
                            if msg not in warnings:
                                warnings.append(msg)

        return AllergyCheckResult(
            has_conflict=len(warnings) > 0,
            warnings=warnings,
            allergy_data_recorded=True,
        )

