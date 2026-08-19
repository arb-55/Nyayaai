"""
Analysis Schemas — Pydantic models for analysis and agent findings.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.models.analysis import AnalysisStatus
from src.models.finding import AgentType


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
    completed_at: datetime | None
    error_message: str | None
    findings_count: int = 0

    model_config = {"from_attributes": True}


class AnalysisDetailResponse(BaseModel):
    """Schema for analysis with findings."""
    status: str = "success"
    data: AnalysisResponse
    findings: list[FindingResponse] = []


class AnalysisTriggerResponse(BaseModel):
    """Schema for analysis trigger response."""
    status: str = "success"
    message: str = "Analysis started"
    data: AnalysisResponse
