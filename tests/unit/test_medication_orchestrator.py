"""Unit tests for AI Medication Orchestrator."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock
from app.ai.base_provider import AIResponse, BaseAIProvider
from app.ai.orchestrator.medication_orchestrator import MedicationOrchestrator
from app.schemas.common import MappingStatus, SafetyStatus
from app.schemas.consultation import ConsultationContext
from app.schemas.medication import SelectedDiagnosis
from app.schemas.sdd import SDDMedicationResult, SDDIngredientResult


class MockMedicationAI(BaseAIProvider):
    async def generate(self, prompt, system_prompt=None, temperature=0.0, max_tokens=4096, json_mode=False):
        return AIResponse(
            raw_text="{}",
            parsed_json={
                "suggestions": [
                    {
                        "candidate_id": "med-01",
                        "display": "Panadol 500mg Tablet",
                        "generic_name": "Paracetamol",
                        "strength": "500mg",
                        "dosage_form": "Tablet",
                        "route": "Oral",
                        "clinical_rationale": "Analgesic and antipyretic for fever.",
                    }
                ]
            },
            model="mock-qwen3:8b",
        )

    async def health_check(self):
        return True

    def get_model_name(self):
        return "mock-qwen3:8b"


@pytest.mark.asyncio
async def test_medication_orchestrator_matches_sdd():
    mock_sdd = AsyncMock()
    mock_sdd.search.return_value = (
        [
            SDDMedicationResult(
                medication_id="SDD-000001",
                name="Panadol 500mg Tablet",
                generic_name="Paracetamol",
                brand_name="Panadol",
                active_ingredients=[
                    SDDIngredientResult(ingredient_name="Paracetamol", strength_value="500", strength_unit="mg")
                ],
                strength="500mg",
                dosage_form="Tablet",
                route="Oral",
                active=True,
                match_type="exact",
                relevance_score=1.0,
            )
        ],
        1,
    )

    orchestrator = MedicationOrchestrator(
        ai_provider=MockMedicationAI(),
        sdd_service=mock_sdd,
    )

    diagnosis = SelectedDiagnosis(display="Acute upper respiratory tract infection", snomed_concept_id="386661006")
    context = ConsultationContext(
        chief_complaint="Fever",
        allergies=[],
        current_medications=[],
    )

    response = await orchestrator.suggest_medications(
        selected_diagnosis=diagnosis,
        context=context,
    )

    assert len(response.suggestions) == 1
    med = response.suggestions[0]
    assert med.medication_id == "SDD-000001"
    assert med.sdd_match_status == MappingStatus.VERIFIED
    assert med.safety_status in (SafetyStatus.SAFE, SafetyStatus.UNRESOLVED)
    assert med.requires_doctor_review is True

