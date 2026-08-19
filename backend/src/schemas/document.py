"""
Document Schemas — Pydantic models for document upload and retrieval.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.document import DocumentType, ExtractionStatus


# ── Request Schemas ──

class DocumentUploadMeta(BaseModel):
    """Metadata sent alongside file upload."""
    document_type: DocumentType = Field(
        default=DocumentType.OTHER,
        examples=["FIR"],
    )


# ── Response Schemas ──

class DocumentResponse(BaseModel):
    """Schema for document data in API response lists."""
    id: UUID
    case_id: UUID
    filename: str
    document_type: DocumentType
    extraction_status: ExtractionStatus
    page_count: int | None
    uploaded_at: datetime
    has_extracted_text: bool = False
    has_cleaned_text: bool = False

    model_config = {"from_attributes": True}


class DocumentDetailResponse(BaseModel):
    """Schema for document detail including raw and cleaned text."""
    id: UUID
    case_id: UUID
    filename: str
    document_type: DocumentType
    extraction_status: ExtractionStatus
    extraction_error: str | None = None
    extracted_text: str | None = None
    cleaned_text: str | None = None
    page_count: int | None = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Schema for list of documents."""
    status: str = "success"
    data: list[DocumentResponse]
    count: int


class EntityResponse(BaseModel):
    """Schema for an extracted entity."""
    id: UUID
    entity_type: str
    entity_text: str
    page_number: int | None
    source_sentence: str | None

    model_config = {"from_attributes": True}
