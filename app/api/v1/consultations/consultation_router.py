"""CMS Consultation proxy endpoints as specified in Section 4."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.middleware.auth import CurrentUser, require_clinician
from app.cms.adapter import CMSAdapter
from app.cms.client import CMSClient
from app.config import get_settings
from app.schemas.consultation import ConsultationContext

router = APIRouter(prefix="/consultations", tags=["CMS Consultations"])
settings = get_settings()


@router.get("/{encounter_id}", response_model=ConsultationContext)
async def get_consultation(
    encounter_id: str,
    current_user: CurrentUser = Depends(require_clinician),
) -> ConsultationContext:
    """Read consultation context from system-of-record CMS."""
    try:
        cms_client = CMSClient(base_url=settings.cms_base_url)
        adapter = CMSAdapter(cms_client)
        return await adapter.fetch_and_map_consultation(encounter_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch consultation '{encounter_id}' from CMS: {str(exc)}",
        )

