"""Unit tests for AI Diagnosis Orchestrator."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.ai.base_provider import AIResponse, BaseAIProvider
from app.ai.orchestrator.diagnosis_orchestrator import DiagnosisOrchestrator
from app.schemas.common import MappingStatus
from app.schemas.consultation import ConsultationContext
from app.schemas.snomed import SnomedConceptResult


class MockAIProvider(BaseAIProvider):
    async def generate(self, prompt, system_prompt=None, temperature=0.0, max_tokens=4096, json_mode=False):
        return AIResponse(
            raw_text='{"suggestions": [{"candidate_id": "dx-01", "display": "Acute upper respiratory tract infection", "supporting_factors": ["Cough", "Fever"], "contradicting_factors": [], "missing_information": [], "clinical_reasoning_summary": "Classic viral presentation."}]}',
            parsed_json={
                "suggestions": [
                    {
                        "candidate_id": "dx-01",
                        "display": "Acute upper respiratory tract infection",
                        "supporting_factors": ["Cough", "Fever"],
                        "contradicting_factors": [],
                        "missing_information": [],
                        "clinical_reasoning_summary": "Classic viral presentation.",
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
async def test_diagnosis_orchestrator_maps_verified_snomed(sample_consultation_context):
    mock_snomed = AsyncMock()
    mock_snomed.search.return_value = (
        [
            SnomedConceptResult(
                concept_id="386661006",
                display="Acute upper respiratory tract infection",
                preferred_term="Acute upper respiratory tract infection",
                synonyms=["URTI"],
                active=True,
                match_type="exact",
                relevance_score=1.0,
            )
        ],
        1,
    )

    orchestrator = DiagnosisOrchestrator(
        ai_provider=MockAIProvider(),
        snomed_service=mock_snomed,
    )

    response = await orchestrator.suggest_diagnoses(sample_consultation_context)

    assert len(response.suggestions) == 1
    sug = response.suggestions[0]
    assert sug.snomed_concept_id == "386661006"
    assert sug.mapping_status == MappingStatus.VERIFIED
    assert sug.requires_doctor_review is True

