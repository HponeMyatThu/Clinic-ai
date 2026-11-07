"""Common Pydantic schemas shared across all API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request ID
# ---------------------------------------------------------------------------

def generate_request_id() -> str:
    """Generate a unique request identifier."""
    return f"req-{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper."""
    results: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Error Responses
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Machine-readable error detail."""
    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response body. Never includes PHI."""
    request_id: str
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Enums used across modules
# ---------------------------------------------------------------------------

class MappingStatus(str, Enum):
    VERIFIED = "verified"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"
    PENDING = "pending"


class SafetyStatus(str, Enum):
    SAFE = "safe"
    REQUIRES_REVIEW = "requires_review"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"


class ReviewStatus(str, Enum):
    REVIEW_REQUIRED = "review_required"
    REVIEWED = "reviewed"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class HealthCheckResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    services: dict[str, str] = {}

