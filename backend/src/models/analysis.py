"""
Analysis Model — Represents a single analysis run for a case.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class AnalysisStatus(str, enum.Enum):
    """Lifecycle states of an analysis run."""
    PENDING = "PENDING"
    EXTRACTING_ENTITIES = "EXTRACTING_ENTITIES"
    RUNNING_AGENTS = "RUNNING_AGENTS"
    BUILDING_CONSENSUS = "BUILDING_CONSENSUS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(nullable=True)

    # ── Relationships ──
    case = relationship("Case", back_populates="analyses")
    findings = relationship(
        "AgentFinding", back_populates="analysis", cascade="all, delete-orphan"
    )
    consensus_report = relationship(
        "ConsensusReport", back_populates="analysis", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, status={self.status})>"
