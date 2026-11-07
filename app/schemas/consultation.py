"""Consultation context schemas for clinical decision support."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class VitalSigns(BaseModel):
    """Patient vital signs at consultation."""

    temperature_celsius: float | None = Field(default=None, description="Body temperature in °C")
    blood_pressure_systolic: int | None = Field(default=None, description="Systolic BP (mmHg)")
    blood_pressure_diastolic: int | None = Field(default=None, description="Diastolic BP (mmHg)")
    heart_rate_bpm: int | None = Field(default=None, description="Heart rate (bpm)")
    respiratory_rate: int | None = Field(default=None, description="Respiratory rate (breaths/min)")
    oxygen_saturation_percent: float | None = Field(default=None, description="SpO2 (%)")


class ConsultationContext(BaseModel):
    """Clinical consultation context payload (de-identified, no direct PII)."""

    consultation_id: str | None = Field(
        default=None,
        description="Optional encounter reference if linked to CMS",
    )
    chief_complaint: str = Field(
        ...,
        min_length=2,
        description="Primary reason for visit / chief complaint",
    )
    history_of_present_illness: str | None = Field(
        default=None,
        description="Narrative or structured history of present illness",
    )
    symptoms: list[str] = Field(
        default_factory=list,
        description="List of reported symptoms",
    )
    symptom_duration: str | None = Field(
        default=None,
        description="Duration of current symptoms (e.g., '3 days', '2 weeks')",
    )
    medical_history: list[str] = Field(
        default_factory=list,
        description="Past medical conditions and chronic illnesses",
    )
    current_medications: list[str] = Field(
        default_factory=list,
        description="Current medications being taken by patient",
    )
    allergies: list[str] = Field(
        default_factory=list,
        description="Known drug and environmental allergies",
    )
    vital_signs: VitalSigns | dict[str, Any] | None = Field(
        default=None,
        description="Recorded vital signs",
    )
    examination_findings: list[str] = Field(
        default_factory=list,
        description="Physical examination observations by doctor",
    )
    investigation_results: list[str] = Field(
        default_factory=list,
        description="Available lab or imaging findings",
    )
    patient_age: int | None = Field(
        default=None,
        ge=0,
        le=150,
        description="Patient age in years (indirect age bracket preferred)",
    )
    patient_gender: str | None = Field(
        default=None,
        description="Biological sex or gender (e.g., 'M', 'F')",
    )
    pregnancy_status: str | None = Field(
        default=None,
        description="Pregnancy / lactation status (e.g., 'pregnant_trimester_1', 'not_pregnant')",
    )
    renal_function: str | None = Field(
        default=None,
        description="Renal function indicator (e.g., 'normal', 'eGFR 45', 'impaired')",
    )
    hepatic_function: str | None = Field(
        default=None,
        description="Hepatic function indicator (e.g., 'normal', 'mild_impairment')",
    )

