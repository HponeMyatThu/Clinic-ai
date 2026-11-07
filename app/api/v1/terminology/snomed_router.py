"""SNOMED CT terminology API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import generate_request_id
from app.schemas.snomed import (
    SnomedConceptValidation,
    SnomedSearchResponse,
)
from app.services.snomed_service import SnomedService

router = APIRouter(prefix="/terminology/snomed", tags=["Terminology — SNOMED CT"])


@router.get("/search", response_model=SnomedSearchResponse)
async def search_snomed(
    q: str = Query(..., min_length=2, max_length=200, description="Search term"),
    active_only: bool = Query(True, description="Return only active concepts"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db),
) -> SnomedSearchResponse:
    """Search SNOMED CT concepts by term.

    Supports exact matching, full-text search, and trigram fuzzy matching.
    Results are ranked by relevance and deduplicated by concept ID.
    """
    service = SnomedService(db)
    results, total = await service.search(
        query=q,
        active_only=active_only,
        page=page,
        page_size=page_size,
    )
    release_version = await service.get_release_version()

    return SnomedSearchResponse(
        request_id=generate_request_id(),
        query=q,
        release_version=release_version,
        results=results,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/validate/{concept_id}", response_model=SnomedConceptValidation)
async def validate_concept(
    concept_id: str,
    db: AsyncSession = Depends(get_db),
) -> SnomedConceptValidation:
    """Validate whether a SNOMED CT concept ID exists and is active."""
    service = SnomedService(db)
    return await service.validate_concept(concept_id)
