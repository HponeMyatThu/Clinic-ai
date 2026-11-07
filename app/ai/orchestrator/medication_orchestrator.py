"""Medication suggestion orchestrator linking AI, SDD matching, and safety checks."""

from __future__ import annotations

import logging
from typing import Any

from app.ai.base_provider import BaseAIProvider
from app.ai.orchestrator.structured_output import StructuredOutputParser
from app.ai.prompts.medication_prompt import MedicationPrompt
from app.clinical_safety.safety_orchestrator import SafetyOrchestrator
from app.privacy.context_minimizer import ContextMinimizer
from app.privacy.pii_filter import PIIFilter
from app.schemas.common import MappingStatus, ReviewStatus, generate_request_id
from app.schemas.consultation import ConsultationContext
from app.schemas.medication import (
    MedicationSuggestionResponse,
    MedicationSuggestionResult,
    SelectedDiagnosis,
)
from app.services.sdd_service import SDDService

logger = logging.getLogger("gcms.ai.medication")


class MedicationOrchestrator:
    """Coordinates evidence-based medication suggestions with SDD catalog matching and safety rules."""

    def __init__(
        self,
        ai_provider: BaseAIProvider,
        sdd_service: SDDService,
        safety_orchestrator: SafetyOrchestrator | None = None,
    ) -> None:
        self.ai = ai_provider
        self.sdd = sdd_service
        self.safety = safety_orchestrator or SafetyOrchestrator()
        self.prompt_template = MedicationPrompt()
        self.pii_filter = PIIFilter()

    async def suggest_medications(
        self,
        selected_diagnosis: SelectedDiagnosis,
        context: ConsultationContext,
        request_id: str | None = None,
    ) -> MedicationSuggestionResponse:
        req_id = request_id or generate_request_id()

        # Step 1: Minimum-necessary context minimization
        minimized = ContextMinimizer.prepare_for_medications(
            context=context,
            selected_diagnosis=selected_diagnosis.display,
        )

        # Step 2: Scrub direct PII identifiers
        sanitized = self.pii_filter.sanitize_context_dict(minimized)

        # Step 3: Render versioned medication prompt
        system_prompt = self.prompt_template.get_system_prompt()
        user_prompt = self.prompt_template.render(
            selected_diagnosis=selected_diagnosis.display,
            context_dict=sanitized,
        )

        # Step 4: AI Model Inference directly through Ollama (no hardcoded fallback)
        warnings: list[str] = []
        model_name = self.ai.get_model_name()

        ai_resp = await self.ai.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.0,
            json_mode=True,
        )
        raw_candidates = StructuredOutputParser.parse_medications(ai_resp.parsed_json)
        if not raw_candidates:
            warnings.append(f"Model {model_name} returned a response, but no structured medication candidates were parsed.")

        # Step 5: Match candidate medications against local SDD database & run Safety Checks
        suggestions: list[MedicationSuggestionResult] = []
        all_safety_summaries: list[str] = []

        for cand in raw_candidates:
            # Search local SDD catalog
            search_term = cand.generic_name or cand.display
            sdd_matches, _ = await self.sdd.search(
                query=search_term,
                active_only=True,
                page=1,
                page_size=3,
            )

            matched_id: str | None = None
            matched_name: str | None = None
            dosage_form = cand.dosage_form
            strength = cand.strength
            route = cand.route
            active_ingredients: list[str] = []
            mapping_status = MappingStatus.UNRESOLVED

            if sdd_matches:
                top_sdd = sdd_matches[0]
                matched_id = top_sdd.medication_id
                matched_name = top_sdd.name
                dosage_form = top_sdd.dosage_form or dosage_form
                strength = top_sdd.strength or strength
                route = top_sdd.route or route
                active_ingredients = [ing.ingredient_name for ing in top_sdd.active_ingredients]
                mapping_status = MappingStatus.VERIFIED if top_sdd.relevance_score >= 0.5 else MappingStatus.AMBIGUOUS

            # Step 6: Independent Clinical Safety Evaluation
            safety_report = self.safety.evaluate_medication(
                medication_name=matched_name or cand.display,
                generic_name=cand.generic_name,
                active_ingredients=active_ingredients,
                context=context,
            )

            all_safety_summaries.append(safety_report.summary)

            suggestions.append(
                MedicationSuggestionResult(
                    candidate_id=cand.candidate_id,
                    display=cand.display,
                    generic_name=cand.generic_name,
                    medication_id=matched_id,
                    sdd_match_status=mapping_status,
                    matched_sdd_name=matched_name,
                    dosage_form=dosage_form,
                    strength=strength,
                    route=route,
                    clinical_rationale=cand.clinical_rationale,
                    safety_status=safety_report.overall_status,
                    allergy_warnings=safety_report.allergy_warnings,
                    interaction_warnings=safety_report.interaction_warnings,
                    contraindication_warnings=safety_report.contraindication_warnings,
                    missing_information=safety_report.missing_information,
                    requires_doctor_review=True,
                )
            )

        combined_safety_summary = "; ".join(set(all_safety_summaries)) if all_safety_summaries else "Review required"

        return MedicationSuggestionResponse(
            request_id=req_id,
            status=ReviewStatus.REVIEW_REQUIRED,
            model_used=model_name,
            prompt_version=self.prompt_template.version,
            selected_diagnosis=selected_diagnosis,
            suggestions=suggestions,
            safety_summary=combined_safety_summary,
            warnings=warnings,
        )

