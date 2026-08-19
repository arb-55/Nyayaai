"""
Case Schemas — Pydantic models for case request/response validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.case import CaseStatus


# ── Request Schemas ──

class CaseCreate(BaseModel):
    """Schema for creating a new case."""
    title: str = Field(..., min_length=1, max_length=500, examples=["State vs. Sharma"])
    description: str | None = Field(None, examples=["Criminal case involving theft charges"])


class CaseUpdate(BaseModel):
    """Schema for updating a case (partial update)."""
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None


# ── Response Schemas ──

class CaseResponse(BaseModel):
    """Schema for case data in API responses."""
    id: UUID
    title: str
    description: str | None
    status: CaseStatus
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    """Schema for list of cases."""
    status: str = "success"
    data: list[CaseResponse]
    count: int


class CaseSingleResponse(BaseModel):
    """Schema for a single case response."""
    status: str = "success"
    data: CaseResponse
