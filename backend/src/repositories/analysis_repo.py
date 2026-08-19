"""
Analysis Repository — Database access layer for Analysis, AgentFinding, ConsensusReport.
"""

from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.analysis import Analysis, AnalysisStatus
from src.models.finding import AgentFinding, AgentType, ConsensusReport


class AnalysisRepository:
    """Provides database operations for Analysis entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, case_id: UUID) -> Analysis:
        analysis = Analysis(case_id=case_id)
        self.db.add(analysis)
        await self.db.flush()
        await self.db.refresh(analysis)
        return analysis

    async def get_by_id(self, analysis_id: UUID) -> Analysis | None:
        return await self.db.get(Analysis, analysis_id)

    async def get_latest_for_case(self, case_id: UUID) -> Analysis | None:
        stmt = (
            select(Analysis)
            .where(Analysis.case_id == case_id)
            .order_by(Analysis.started_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self, analysis_id: UUID, status: AnalysisStatus, error_message: str | None = None
    ) -> None:
        analysis = await self.get_by_id(analysis_id)
        if analysis:
            analysis.status = status
            if error_message:
                analysis.error_message = error_message

    async def add_finding(self, analysis_id: UUID, **kwargs) -> AgentFinding:
        finding = AgentFinding(analysis_id=analysis_id, **kwargs)
        self.db.add(finding)
        await self.db.flush()
        await self.db.refresh(finding)
        return finding

    async def get_findings(
        self, analysis_id: UUID, agent_type: AgentType | None = None
    ) -> list[AgentFinding]:
        stmt = select(AgentFinding).where(AgentFinding.analysis_id == analysis_id)
        if agent_type:
            stmt = stmt.where(AgentFinding.agent_type == agent_type)
        stmt = stmt.order_by(AgentFinding.confidence_score.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_evidence_findings_by_case(self, case_id: UUID) -> int:
        """
        Delete previous evidence findings for a case to guarantee zero duplicates on re-runs.
        Preserves non-evidence findings or other analysis records.
        """
        subq = select(Analysis.id).where(Analysis.case_id == case_id)
        stmt = delete(AgentFinding).where(
            AgentFinding.analysis_id.in_(subq),
            AgentFinding.agent_type == AgentType.EVIDENCE
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def delete_contradiction_findings_by_case(self, case_id: UUID) -> int:
        """
        Delete previous contradiction findings for a case to guarantee zero duplicates on re-runs.
        Preserves evidence findings (EVIDENCE) and extracted entities.
        """
        subq = select(Analysis.id).where(Analysis.case_id == case_id)
        stmt = delete(AgentFinding).where(
            AgentFinding.analysis_id.in_(subq),
            AgentFinding.agent_type == AgentType.CONTRADICTION
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def save_consensus_report(self, analysis_id: UUID, **kwargs) -> ConsensusReport:
        report = ConsensusReport(analysis_id=analysis_id, **kwargs)
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        return report

    async def get_consensus_report(self, analysis_id: UUID) -> ConsensusReport | None:
        stmt = select(ConsensusReport).where(ConsensusReport.analysis_id == analysis_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
