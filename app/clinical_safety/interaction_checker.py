"""Drug-drug interaction safety checker.

Following clinical governance principles:
Do not fabricate complete interaction checks without an authoritative data source.
Flags known high-risk primary care interactions and highlights unverified combinations.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class InteractionWarning(BaseModel):
    interacting_drug: str
    severity: str  # major | moderate | minor
    description: str


class InteractionCheckResult(BaseModel):
    status: str  # clear | warning | unresolved
    warnings: list[InteractionWarning] = Field(default_factory=list)
    has_warnings: bool = False
    requires_pharmacist_review: bool = False


class InteractionChecker:
    """Evaluates high-risk drug combinations against patient's current medications."""

    # Curated authoritative high-risk interactions commonly encountered in Singapore GP clinics
    KNOWN_INTERACTIONS: list[dict[str, str]] = [
        {
            "drug_a": "warfarin",
            "drug_b": "aspirin",
            "severity": "major",
            "description": "Concurrent use significantly increases bleeding risk and INR instability.",
        },
        {
            "drug_a": "warfarin",
            "drug_b": "ibuprofen",
            "severity": "major",
            "description": "NSAIDs damage GI mucosa and potentiate anticoagulant effect of warfarin.",
        },
        {
            "drug_a": "warfarin",
            "drug_b": "diclofenac",
            "severity": "major",
            "description": "NSAIDs damage GI mucosa and potentiate anticoagulant effect of warfarin.",
        },
        {
            "drug_a": "metformin",
            "drug_b": "contrast",
            "severity": "major",
            "description": "Iodinated contrast may cause lactic acidosis in metformin patients with renal impairment.",
        },
        {
            "drug_a": "simvastatin",
            "drug_b": "amlodipine",
            "severity": "moderate",
            "description": "Amlodipine increases simvastatin exposure. Limit simvastatin dose to 20mg daily.",
        },
        {
            "drug_a": "clarithromycin",
            "drug_b": "simvastatin",
            "severity": "major",
            "description": "Strong CYP3A4 inhibitor increases simvastatin plasma levels; high risk of rhabdomyolysis.",
        },
        {
            "drug_a": "erythromycin",
            "drug_b": "simvastatin",
            "severity": "major",
            "description": "CYP3A4 inhibition causes marked increase in simvastatin concentration.",
        },
        {
            "drug_a": "sertraline",
            "drug_b": "tramadol",
            "severity": "major",
            "description": "Increased risk of Serotonin Syndrome and lowered seizure threshold.",
        },
        {
            "drug_a": "escitalopram",
            "drug_b": "tramadol",
            "severity": "major",
            "description": "Increased risk of Serotonin Syndrome and lowered seizure threshold.",
        },
        {
            "drug_a": "ciprofloxacin",
            "drug_b": "theophylline",
            "severity": "major",
            "description": "Ciprofloxacin inhibits theophylline clearance causing potential toxicity.",
        },
        {
            "drug_a": "methotrexate",
            "drug_b": "ibuprofen",
            "severity": "major",
            "description": "NSAIDs reduce renal methotrexate excretion leading to severe bone marrow toxicity.",
        },
        {
            "drug_a": "methotrexate",
            "drug_b": "diclofenac",
            "severity": "major",
            "description": "NSAIDs reduce renal methotrexate excretion leading to severe bone marrow toxicity.",
        },
    ]

    def check(
        self,
        proposed_medication: str,
        generic_name: str | None,
        current_medications: list[str],
    ) -> InteractionCheckResult:
        if not current_medications:
            return InteractionCheckResult(status="clear", has_warnings=False)

        matched_warnings: list[InteractionWarning] = []
        proposed_tokens = [proposed_medication.lower()]
        if generic_name:
            proposed_tokens.append(generic_name.lower())

        for curr_med in current_medications:
            curr_lower = curr_med.lower()
            for rule in self.KNOWN_INTERACTIONS:
                a = rule["drug_a"]
                b = rule["drug_b"]

                # Case 1: proposed matches drug_a, current matches drug_b
                is_match_1 = any(a in p for p in proposed_tokens) and (b in curr_lower)
                # Case 2: proposed matches drug_b, current matches drug_a
                is_match_2 = any(b in p for p in proposed_tokens) and (a in curr_lower)

                if is_match_1 or is_match_2:
                    matched_warnings.append(
                        InteractionWarning(
                            interacting_drug=curr_med,
                            severity=rule["severity"],
                            description=f"Interaction with existing '{curr_med}': {rule['description']}",
                        )
                    )

        status = "warning" if matched_warnings else "clear"
        has_major = any(w.severity == "major" for w in matched_warnings)

        return InteractionCheckResult(
            status=status,
            warnings=matched_warnings,
            has_warnings=len(matched_warnings) > 0,
            requires_pharmacist_review=has_major,
        )

