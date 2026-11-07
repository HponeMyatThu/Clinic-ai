"""Aggregated v1 API Router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.ai.diagnosis_router import router as diagnosis_router
from app.api.v1.ai.medication_router import router as medication_router
from app.api.v1.consultations.consultation_router import router as consultation_router
from app.api.v1.health.health_router import router as health_router
from app.api.v1.terminology.sdd_router import router as sdd_router
from app.api.v1.terminology.snomed_router import router as snomed_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount Terminology Search APIs (API 1 & API 2)
api_v1_router.include_router(snomed_router)
api_v1_router.include_router(sdd_router)

# Mount AI Clinical Decision Support APIs (API 3 & API 4)
api_v1_router.include_router(diagnosis_router)
api_v1_router.include_router(medication_router)

# Mount Consultations & Health
api_v1_router.include_router(consultation_router)
api_v1_router.include_router(health_router)

