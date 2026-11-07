"""Pydantic v2 schemas for SNOMED CT terminology endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request / Query schemas
# ---------------------------------------------------------------------------

class SnomedSearchParams(BaseModel):
    """Query parameters for SNOMED CT search."""

    q: str = Field(..., min_length=2, max_length=200, description="Search query text")
    active_only: bool = Field(default=True, description="Return only active concepts")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class SnomedConceptResult(BaseModel):
    """A single SNOMED CT concept in search results."""

    concept_id: str
    display: str = Field(description="The preferred term for display")
    preferred_term: str
    synonyms: list[str] = Field(default_factory=list)
    active: bool
    semantic_tag: str | None = Field(
        default=None,
        description="Semantic tag extracted from the Fully Specified Name",
    )
    match_type: str = Field(description="exact | partial | fuzzy | synonym")
    relevance_score: float = Field(ge=0.0, le=1.0)


class SnomedSearchResponse(BaseModel):
    """Paginated SNOMED CT search response."""

    request_id: str
    query: str
    terminology: str = "SNOMED CT"
    release_version: str
    results: list[SnomedConceptResult]
    total: int
    page: int
    page_size: int


class SnomedConceptValidation(BaseModel):
    """Result of validating a single SNOMED CT concept ID."""

    concept_id: str
    valid: bool
    active: bool | None = None
    display: str | None = None
