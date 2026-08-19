"""
Analysis Schemas — Pydantic models for analysis, entity extraction, and agent findings.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.models.analysis import AnalysisStatus
from src.models.finding import AgentType


# ── Entity Schemas ──

class EntityItemResponse(BaseModel):
    """Schema for an individual extracted entity."""
    id: UUID
    document_id: UUID
    entity_type: str
    entity_text: str
    normalized_value: str | None = None
    confidence: float | None = 1.0
    page_number: int | None = None
    source_sentence: str | None = None

    model_config = {"from_attributes": True}


class EntityGroupedResponse(BaseModel):
    """Schema for extracted entities grouped by entity_type."""
    entity_type: str
    count: int
    entities: list[EntityItemResponse]


# ── Response Schemas ──

class FindingResponse(BaseModel):
    """Schema for an individual agent finding."""
    id: UUID
    agent_type: AgentType
    finding_text: str
    confidence_score: float
    source_references: dict | list | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisResponse(BaseModel):
    """Schema for analysis status and results."""
    id: UUID
    case_id: UUID
    status: AnalysisStatus
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    findings_count: int = 0

    model_config = {"from_attributes": True}


class AnalysisDetailResponse(BaseModel):
    """Schema for analysis with findings and entities."""
    status: str = "success"
    data: AnalysisResponse
    findings: list[FindingResponse] = []
    entities: list[EntityItemResponse] = []


class AnalysisTriggerResponse(BaseModel):
    """Schema for analysis trigger response."""
    status: str = "success"
    message: str = "Analysis started"
    data: AnalysisResponse
    entities_count: int = 0
    entities: list[EntityItemResponse] = []
