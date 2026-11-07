"""Pydantic v2 schemas for SDD (Singapore Drug Dictionary) endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request / Query schemas
# ---------------------------------------------------------------------------

class SDDSearchParams(BaseModel):
    """Query parameters for SDD medication search."""

    q: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Search query text (medication name, generic name, brand, or ingredient)",
    )
    active_only: bool = Field(default=True, description="Return only active medications")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class SDDIngredientResult(BaseModel):
    """An active ingredient within a medication result."""

    ingredient_name: str
    strength_value: str | None = None
    strength_unit: str | None = None


class SDDMedicationResult(BaseModel):
    """A single SDD medication in search results."""

    medication_id: str
    name: str
    generic_name: str | None = None
    brand_name: str | None = None
    active_ingredients: list[SDDIngredientResult] = Field(default_factory=list)
    strength: str | None = None
    dosage_form: str | None = None
    route: str | None = None
    manufacturer: str | None = None
    atc_code: str | None = None
    active: bool
    match_type: str = Field(description="exact | partial | fuzzy | ingredient")
    relevance_score: float = Field(ge=0.0, le=1.0)


class SDDSearchResponse(BaseModel):
    """Paginated SDD medication search response."""

    request_id: str
    query: str
    catalogue: str = "SDD"
    catalogue_version: str
    results: list[SDDMedicationResult]
    total: int
    page: int
    page_size: int


class SDDMedicationValidation(BaseModel):
    """Result of validating a single SDD medication ID."""

    medication_id: str
    valid: bool
    active: bool | None = None
    name: str | None = None
