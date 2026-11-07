"""Diagnosis suggestion orchestrator uniting AI inference with SNOMED CT verification."""

from __future__ import annotations

import logging
from typing import Any

from app.ai.base_provider import BaseAIProvider
from app.ai.orchestrator.structured_output import StructuredOutputParser
from app.ai.prompts.diagnosis_prompt import DiagnosisPrompt
from app.privacy.context_minimizer import ContextMinimizer
from app.privacy.pii_filter import PIIFilter
from app.schemas.common import MappingStatus, ReviewStatus, generate_request_id
from app.schemas.consultation import ConsultationContext
from app.schemas.diagnosis import DiagnosisCandidateResult, DiagnosisSuggestionResponse
from app.services.snomed_service import SnomedService

logger = logging.getLogger("gcms.ai.diagnosis")


class DiagnosisOrchestrator:
    """Coordinates end-to-end differential diagnosis reasoning and SNOMED CT ground-truthing."""

    def __init__(
        self,
        ai_provider: BaseAIProvider,
        snomed_service: SnomedService,
    ) -> None:
        self.ai = ai_provider
        self.snomed = snomed_service
        self.prompt_template = DiagnosisPrompt()
        self.pii_filter = PIIFilter()

    async def suggest_diagnoses(
        self,
        context: ConsultationContext,
        max_suggestions: int = 5,
        request_id: str | None = None,
    ) -> DiagnosisSuggestionResponse:
        req_id = request_id or generate_request_id()

        # Step 1: Minimum-necessary context minimization
        minimized = ContextMinimizer.prepare_for_diagnosis(context)

        # Step 2: Scrub direct PII identifiers (NRIC, names, phones)
        sanitized = self.pii_filter.sanitize_context_dict(minimized)

        # Step 3: Render versioned clinical prompt
        system_prompt = self.prompt_template.get_system_prompt()
        user_prompt = self.prompt_template.render(sanitized, max_suggestions=max_suggestions)

        # Step 4: Call Ollama inference
        warnings: list[str] = []
        raw_candidates = []
        model_name = self.ai.get_model_name()

        try:
            ai_resp = await self.ai.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.0,
                json_mode=True,
            )
            raw_candidates = StructuredOutputParser.parse_diagnoses(ai_resp.parsed_json)
        except Exception as exc:
            logger.warning(f"Ollama inference error during diagnosis reasoning: {exc}")
            warnings.append(
                f"Notice: Local AI model ({model_name}) was unreachable or returned an error: {str(exc)}. "
                "Falling back to rule-based symptom differential."
            )
            # Rule-based fallback based on symptoms if Ollama is not yet started
            raw_candidates = self._rule_based_fallback(context)

        # Step 5: Terminology Ground-Truthing against SNOMED CT database
        suggestions: list[DiagnosisCandidateResult] = []
        unmapped_count = 0

        for cand in raw_candidates[:max_suggestions]:
            # Ground truth search against verified SNOMED CT database
            snomed_matches, _ = await self.snomed.search(
                query=cand.display,
                active_only=True,
                page=1,
                page_size=3,
            )

            matched_id: str | None = None
            matched_display: str | None = None
            status = MappingStatus.UNRESOLVED

            if snomed_matches:
                top_match = snomed_matches[0]
                # High-confidence exact or partial match
                if top_match.relevance_score >= 0.65 or top_match.match_type == "exact":
                    matched_id = top_match.concept_id
                    matched_display = top_match.preferred_term
                    status = MappingStatus.VERIFIED
                elif len(snomed_matches) > 1 and top_match.relevance_score > 0.4:
                    status = MappingStatus.AMBIGUOUS
                    matched_id = top_match.concept_id
                    matched_display = top_match.preferred_term
                else:
                    status = MappingStatus.UNRESOLVED
            else:
                unmapped_count += 1

            suggestions.append(
                DiagnosisCandidateResult(
                    candidate_id=cand.candidate_id,
                    display=cand.display,
                    snomed_concept_id=matched_id,
                    snomed_display=matched_display,
                    mapping_status=status,
                    supporting_factors=cand.supporting_factors,
                    contradicting_factors=cand.contradicting_factors,
                    missing_information=cand.missing_information,
                    clinical_reasoning_summary=cand.clinical_reasoning_summary,
                    requires_doctor_review=True,
                )
            )

        return DiagnosisSuggestionResponse(
            request_id=req_id,
            status=ReviewStatus.REVIEW_REQUIRED,
            model_used=model_name,
            prompt_version=self.prompt_template.version,
            suggestions=suggestions,
            unmapped_candidates_count=unmapped_count,
            warnings=warnings,
        )

    def _rule_based_fallback(self, context: ConsultationContext):
        """Clinical rule-based heuristic when Ollama is offline in development."""
        from app.ai.orchestrator.structured_output import RawDiagnosisCandidate

        symptoms_str = " ".join(context.symptoms + [context.chief_complaint]).lower()
        candidates = []

        if any(w in symptoms_str for w in ["cough", "fever", "throat", "runny nose", "cold"]):
            candidates.append(
                RawDiagnosisCandidate(
                    candidate_id="dx-01",
                    display="Acute upper respiratory tract infection",
                    supporting_factors=["Reported respiratory symptoms and fever"],
                    contradicting_factors=["No chronic dyspnea noted"],
                    missing_information=["Auscultation of chest", "COVID-19 swab"],
                    clinical_reasoning_summary="Acute onset of fever and respiratory symptoms strongly indicates viral URTI.",
                )
            )
            candidates.append(
                RawDiagnosisCandidate(
                    candidate_id="dx-02",
                    display="Acute bronchitis",
                    supporting_factors=["Cough presentation"],
                    contradicting_factors=[],
                    missing_information=["Sputum color assessment"],
                    clinical_reasoning_summary="Consider lower respiratory involvement if productive cough persists.",
                )
            )

        if any(w in symptoms_str for w in ["headache", "migraine"]):
            candidates.append(
                RawDiagnosisCandidate(
                    candidate_id="dx-03",
                    display="Migraine",
                    supporting_factors=["Headache symptoms"],
                    contradicting_factors=[],
                    missing_information=["Fundoscopic exam", "Blood pressure check"],
                    clinical_reasoning_summary="Episodic unilateral or throbbing cephalalgia.",
                )
            )

        if not candidates:
            candidates.append(
                RawDiagnosisCandidate(
                    candidate_id="dx-01",
                    display="Viral infection",
                    supporting_factors=[context.chief_complaint],
                    contradicting_factors=[],
                    missing_information=["Full blood count", "Vital signs trend"],
                    clinical_reasoning_summary="General viral syndrome pending focused clinical evaluation.",
                )
            )

        return candidates

