"""Structured output parsing and normalization for LLM outputs."""

from __future__ import annotations

import json
from typing import Any
from pydantic import BaseModel, Field


class RawDiagnosisCandidate(BaseModel):
    candidate_id: str = "dx-00"
    display: str
    supporting_factors: list[str] = Field(default_factory=list)
    contradicting_factors: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    clinical_reasoning_summary: str = ""


class RawMedicationCandidate(BaseModel):
    candidate_id: str = "med-00"
    display: str
    generic_name: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    route: str | None = None
    clinical_rationale: str = ""
    precaution_notes: str = ""


class StructuredOutputParser:
    """Robust parser that extracts and validates typed JSON from model output."""

    @staticmethod
    def parse_diagnoses(parsed_json: Any) -> list[RawDiagnosisCandidate]:
        candidates: list[RawDiagnosisCandidate] = []
        if not parsed_json:
            return candidates

        raw_list = []
        if isinstance(parsed_json, dict):
            raw_list = parsed_json.get("suggestions") or parsed_json.get("diagnoses") or []
        elif isinstance(parsed_json, list):
            raw_list = parsed_json

        for i, item in enumerate(raw_list):
            if isinstance(item, dict) and "display" in item:
                cand_id = item.get("candidate_id") or f"dx-0{i+1}"
                candidates.append(
                    RawDiagnosisCandidate(
                        candidate_id=cand_id,
                        display=str(item["display"]).strip(),
                        supporting_factors=list(item.get("supporting_factors", [])),
                        contradicting_factors=list(item.get("contradicting_factors", [])),
                        missing_information=list(item.get("missing_information", [])),
                        clinical_reasoning_summary=str(item.get("clinical_reasoning_summary", "")),
                    )
                )
        return candidates

    @staticmethod
    def parse_medications(parsed_json: Any) -> list[RawMedicationCandidate]:
        candidates: list[RawMedicationCandidate] = []
        if not parsed_json:
            return candidates

        raw_list = []
        if isinstance(parsed_json, dict):
            raw_list = parsed_json.get("suggestions") or parsed_json.get("medications") or []
        elif isinstance(parsed_json, list):
            raw_list = parsed_json

        for i, item in enumerate(raw_list):
            if isinstance(item, dict) and "display" in item:
                cand_id = item.get("candidate_id") or f"med-0{i+1}"
                candidates.append(
                    RawMedicationCandidate(
                        candidate_id=cand_id,
                        display=str(item["display"]).strip(),
                        generic_name=item.get("generic_name"),
                        strength=item.get("strength"),
                        dosage_form=item.get("dosage_form"),
                        route=item.get("route"),
                        clinical_rationale=str(item.get("clinical_rationale", "")),
                        precaution_notes=str(item.get("precaution_notes", "")),
                    )
                )
        return candidates

