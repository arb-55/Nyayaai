"""
Report Schemas — Pydantic models for the consensus report.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReportResponse(BaseModel):
    """Schema for the consensus report."""
    id: UUID
    analysis_id: UUID
    overall_confidence: float
    summary_text: str
    report_data: dict
    generated_at: datetime

    model_config = {"from_attributes": True}


class ReportDetailResponse(BaseModel):
    """Wrapper for report API response."""
    status: str = "success"
    data: ReportResponse
    ai_disclaimer: str = (
        "This report is AI-generated assistive analysis. "
        "It should not be treated as a legal opinion or judgment. "
        "All findings are machine-generated and must be independently verified."
    )
