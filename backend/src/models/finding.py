"""
AgentFinding & ConsensusReport Models

AgentFinding — One finding from one AI agent.
ConsensusReport — The final synthesized report for an analysis run.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class AgentType(str, enum.Enum):
    """The type of agent that produced a finding."""
    EVIDENCE = "EVIDENCE"
    CONTRADICTION = "CONTRADICTION"
    LEGAL_RESEARCH = "LEGAL_RESEARCH"


class AgentFinding(Base):
    __tablename__ = "agent_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
    )
    agent_type: Mapped[AgentType] = mapped_column(
        Enum(AgentType), nullable=False
    )
    finding_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="0.0 to 1.0 — heuristic confidence, not statistically calibrated"
    )
    source_references: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Array of {document_id, page_number, excerpt} for traceability"
    )
    raw_llm_response: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Full LLM response stored for audit/debugging"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Relationships ──
    analysis = relationship("Analysis", back_populates="findings")

    def __repr__(self) -> str:
        return f"<AgentFinding(agent={self.agent_type}, confidence={self.confidence_score})>"


class ConsensusReport(Base):
    __tablename__ = "consensus_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    report_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="Structured report: {evidence_summary, contradictions, legal_refs, timeline, assessment}"
    )
    overall_confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Relationships ──
    analysis = relationship("Analysis", back_populates="consensus_report")

    def __repr__(self) -> str:
        return f"<ConsensusReport(confidence={self.overall_confidence})>"
