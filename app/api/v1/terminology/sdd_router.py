"""Singapore Drug Dictionary (SDD) terminology API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import generate_request_id
from app.schemas.sdd import (
    SDDMedicationValidation,
    SDDSearchResponse,
)
from app.services.sdd_service import SDDService

router = APIRouter(prefix="/terminology/sdd", tags=["Terminology — SDD"])


@router.get("/search", response_model=SDDSearchResponse)
async def search_sdd(
    q: str = Query(..., min_length=2, max_length=200, description="Medication brand, generic, or ingredient"),
    active_only: bool = Query(True, description="Return only active medications"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db),
) -> SDDSearchResponse:
    """Search Singapore Drug Dictionary medications by name, generic, brand, or ingredient."""
    service = SDDService(db)
    results, total = await service.search(
        query=q,
        active_only=active_only,
        page=page,
        page_size=page_size,
    )
    catalogue_version = await service.get_catalogue_version()

    return SDDSearchResponse(
        request_id=generate_request_id(),
        query=q,
        catalogue="SDD",
        catalogue_version=catalogue_version,
        results=results,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/validate/{medication_id}", response_model=SDDMedicationValidation)
async def validate_medication(
    medication_id: str,
    db: AsyncSession = Depends(get_db),
) -> SDDMedicationValidation:
    """Validate whether an SDD medication ID exists and is active."""
    service = SDDService(db)
    return await service.validate_medication(medication_id)

