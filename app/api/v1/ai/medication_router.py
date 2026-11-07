"""AI Medication Suggestion API endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama.client import OllamaClient
from app.ai.ollama.model_config import OllamaModelConfig
from app.ai.orchestrator.medication_orchestrator import MedicationOrchestrator
from app.api.middleware.auth import CurrentUser, require_clinician
from app.audit.logger import AuditLogger
from app.clinical_safety.safety_orchestrator import SafetyOrchestrator
from app.cms.adapter import CMSAdapter
from app.cms.client import CMSClient
from app.config import get_settings
from app.db.session import get_db
from app.schemas.common import generate_request_id
from app.schemas.medication import (
    MedicationSuggestionRequest,
    MedicationSuggestionResponse,
)
from app.services.sdd_service import SDDService

router = APIRouter(prefix="/ai", tags=["AI Clinical Decision Support"])
settings = get_settings()


@router.post("/medications/suggest", response_model=MedicationSuggestionResponse)
async def suggest_medications(
    request: MedicationSuggestionRequest,
    current_user: CurrentUser = Depends(require_clinician),
    db: AsyncSession = Depends(get_db),
) -> MedicationSuggestionResponse:
    """Generate guideline-aligned medication candidates for a doctor-selected diagnosis.

    Candidates are grounded in the local Singapore Drug Dictionary (SDD).
    Cross-checks patient allergies, drug interactions, contraindications, and duplications.
    """
    req_id = generate_request_id()

    # Step 1: Obtain consultation context
    context = request.consultation_context

    if not context:
        if request.consultation_id:
            try:
                cms_client = CMSClient(base_url=settings.cms_base_url)
                adapter = CMSAdapter(cms_client)
                context = await adapter.fetch_and_map_consultation(request.consultation_id)
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Unable to retrieve consultation context from upstream CMS: {str(exc)}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Either 'consultation_context' payload or 'consultation_id' is required",
            )

    # Step 2: Initialize dependencies
    ollama_config = OllamaModelConfig.from_settings(settings)
    ai_client = OllamaClient(ollama_config)
    sdd_service = SDDService(db)
    safety_orchestrator = SafetyOrchestrator()

    orchestrator = MedicationOrchestrator(
        ai_provider=ai_client,
        sdd_service=sdd_service,
        safety_orchestrator=safety_orchestrator,
    )

    try:
        response = await orchestrator.suggest_medications(
            selected_diagnosis=request.selected_diagnosis,
            context=context,
            request_id=req_id,
        )

        # Audit log (no PHI)
        await AuditLogger.log_event(
            db=db,
            request_id=req_id,
            event_type="ai_medication_suggestion",
            status="success",
            endpoint="/api/v1/ai/medications/suggest",
            model_used=response.model_used,
            prompt_version=response.prompt_version,
            clinician_id=current_user.user_id,
            tenant_id=current_user.tenant_id,
            metadata={
                "selected_diagnosis": request.selected_diagnosis.display,
                "suggestions_count": len(response.suggestions),
            },
        )

        return response
    finally:
        await ai_client.close()

