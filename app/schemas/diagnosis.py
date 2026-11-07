"""Pydantic schemas for AI diagnosis suggestion API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import MappingStatus, ReviewStatus
from app.schemas.consultation import ConsultationContext


class DiagnosisSuggestionRequest(BaseModel):
    """Request payload for AI diagnosis suggestions."""

    consultation_id: str | None = Field(
        default=None,
        description="CMS consultation encounter ID if reading from CMS",
    )
    consultation_context: ConsultationContext | None = Field(
        default=None,
        description="Direct consultation context payload (standalone mode)",
    )
    max_suggestions: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum differential diagnosis candidates to return",
    )


class DiagnosisCandidateResult(BaseModel):
    """A single differential diagnosis candidate for doctor review."""

    candidate_id: str = Field(description="Unique candidate identifier (e.g., 'dx-01')")
    display: str = Field(description="Clinical diagnosis name")
    snomed_concept_id: str | None = Field(
        default=None,
        description="Verified SNOMED CT concept ID matched against local terminology DB",
    )
    snomed_display: str | None = Field(
        default=None,
        description="Official SNOMED CT preferred term",
    )
    mapping_status: MappingStatus = Field(
        default=MappingStatus.UNRESOLVED,
        description="verified | unresolved | ambiguous | pending",
    )
    supporting_factors: list[str] = Field(
        default_factory=list,
        description="Documented patient findings that support this diagnosis",
    )
    contradicting_factors: list[str] = Field(
        default_factory=list,
        description="Findings that make this diagnosis less likely",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Clinical checks or examinations needed to confirm/refute",
    )
    clinical_reasoning_summary: str = Field(
        default="",
        description="Brief clinical reasoning explanation for the doctor",
    )
    requires_doctor_review: bool = Field(
        default=True,
        description="Clinical governance flag: always true; AI cannot make autonomous diagnoses",
    )


class DiagnosisSuggestionResponse(BaseModel):
    """API response contract for differential diagnosis suggestions."""

    request_id: str
    status: ReviewStatus = ReviewStatus.REVIEW_REQUIRED
    model_used: str
    prompt_version: str
    suggestions: list[DiagnosisCandidateResult]
    unmapped_candidates_count: int = 0
    warnings: list[str] = Field(default_factory=list)

