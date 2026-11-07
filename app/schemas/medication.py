"""Pydantic schemas for AI medication suggestion API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import MappingStatus, ReviewStatus, SafetyStatus
from app.schemas.consultation import ConsultationContext


class SelectedDiagnosis(BaseModel):
    """Doctor-selected diagnosis requiring medication recommendations."""

    display: str = Field(..., min_length=2, description="Doctor-confirmed diagnosis name")
    snomed_concept_id: str | None = Field(
        default=None,
        description="Verified SNOMED CT concept ID if available",
    )


class MedicationSuggestionRequest(BaseModel):
    """Request payload for AI medication suggestions."""

    consultation_id: str | None = Field(
        default=None,
        description="CMS consultation encounter ID if reading from CMS",
    )
    consultation_context: ConsultationContext | None = Field(
        default=None,
        description="Direct consultation context payload",
    )
    selected_diagnosis: SelectedDiagnosis = Field(
        ...,
        description="Mandatory doctor-selected diagnosis. AI cannot prescribe without confirmed diagnosis.",
    )


class MedicationSuggestionResult(BaseModel):
    """A single medication candidate matched to SDD with safety checks."""

    candidate_id: str = Field(description="Unique candidate identifier (e.g., 'med-01')")
    display: str = Field(description="Medication name suggested by clinical guidelines")
    generic_name: str | None = Field(default=None, description="Active generic substance")
    medication_id: str | None = Field(
        default=None,
        description="Matched SDD concept ID from authorized Singapore Drug Dictionary",
    )
    sdd_match_status: MappingStatus = Field(
        default=MappingStatus.UNRESOLVED,
        description="verified | unresolved | ambiguous",
    )
    matched_sdd_name: str | None = Field(
        default=None,
        description="Official name in SDD catalog",
    )
    dosage_form: str | None = Field(default=None, description="e.g., Tablet, Inhaler")
    strength: str | None = Field(default=None, description="e.g., 500mg, 10mg")
    route: str | None = Field(default=None, description="e.g., Oral, Inhalation")
    clinical_rationale: str = Field(
        default="",
        description="Indication rationale under standard clinical guidelines",
    )
    safety_status: SafetyStatus = Field(
        default=SafetyStatus.REQUIRES_REVIEW,
        description="safe | requires_review | blocked | unresolved",
    )
    allergy_warnings: list[str] = Field(
        default_factory=list,
        description="Specific allergy alerts detected against patient's allergy profile",
    )
    interaction_warnings: list[str] = Field(
        default_factory=list,
        description="Drug-drug interaction warnings against current medications",
    )
    contraindication_warnings: list[str] = Field(
        default_factory=list,
        description="Contraindication flags based on organ function, pregnancy, or medical history",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Safety data missing (e.g., renal function, allergy status)",
    )
    requires_doctor_review: bool = Field(
        default=True,
        description="Always true: doctor review and signature required before prescribing",
    )


class MedicationSuggestionResponse(BaseModel):
    """API response contract for medication suggestions."""

    request_id: str
    status: ReviewStatus = ReviewStatus.REVIEW_REQUIRED
    model_used: str
    prompt_version: str
    selected_diagnosis: SelectedDiagnosis
    suggestions: list[MedicationSuggestionResult]
    safety_summary: str = Field(
        default="",
        description="High-level safety alert summary",
    )
    warnings: list[str] = Field(default_factory=list)

