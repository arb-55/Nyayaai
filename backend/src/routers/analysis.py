"""
Analysis Router — Trigger analysis and retrieve results.

NOTE: The actual agent pipeline (LangGraph) will be wired in Phase 4.
      For now, these endpoints provide the API contract.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import AnalysisNotFoundError, CaseNotFoundError
from src.models.analysis import Analysis, AnalysisStatus
from src.models.case import Case, CaseStatus
from src.models.finding import AgentFinding, AgentType
from src.schemas.analysis import (
    AnalysisDetailResponse,
    AnalysisResponse,
    AnalysisTriggerResponse,
    FindingResponse,
)

router = APIRouter()


@router.post("/cases/{case_id}/analyze", response_model=AnalysisTriggerResponse, status_code=202)
async def trigger_analysis(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Trigger the multi-agent analysis pipeline for a case.

    The analysis runs asynchronously. Poll GET /cases/{case_id}/analysis
    to check the status.
    """
    case = await db.get(Case, case_id)
    if not case:
        raise CaseNotFoundError(str(case_id))

    # Create analysis record
    analysis = Analysis(case_id=case_id, status=AnalysisStatus.PENDING)
    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)

    # Update case status
    case.status = CaseStatus.ANALYZING

    # TODO (Phase 4): Dispatch background task to run LangGraph agent pipeline
    # background_tasks.add_task(run_analysis_pipeline, analysis.id)

    return AnalysisTriggerResponse(
        message="Analysis has been queued. Poll GET /cases/{case_id}/analysis for status.",
        data=AnalysisResponse(
            id=analysis.id,
            case_id=analysis.case_id,
            status=analysis.status,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
            error_message=analysis.error_message,
        ),
    )


@router.get("/cases/{case_id}/analysis")
async def get_analysis(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get the latest analysis for a case, including status and findings."""
    case = await db.get(Case, case_id)
    if not case:
        raise CaseNotFoundError(str(case_id))

    # Get the most recent analysis
    stmt = (
        select(Analysis)
        .where(Analysis.case_id == case_id)
        .order_by(Analysis.started_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        return {"status": "success", "data": None, "message": "No analysis has been run for this case"}

    # Get findings
    findings_stmt = (
        select(AgentFinding)
        .where(AgentFinding.analysis_id == analysis.id)
        .order_by(AgentFinding.agent_type, AgentFinding.created_at)
    )
    findings_result = await db.execute(findings_stmt)
    findings = findings_result.scalars().all()

    return AnalysisDetailResponse(
        data=AnalysisResponse(
            id=analysis.id,
            case_id=analysis.case_id,
            status=analysis.status,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
            error_message=analysis.error_message,
            findings_count=len(findings),
        ),
        findings=[
            FindingResponse(
                id=f.id,
                agent_type=f.agent_type,
                finding_text=f.finding_text,
                confidence_score=f.confidence_score,
                source_references=f.source_references,
                created_at=f.created_at,
            )
            for f in findings
        ],
    )


@router.get("/analyses/{analysis_id}/findings")
async def get_findings(
    analysis_id: UUID,
    agent: AgentType | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get findings for an analysis, optionally filtered by agent type."""
    analysis = await db.get(Analysis, analysis_id)
    if not analysis:
        raise AnalysisNotFoundError(str(analysis_id))

    stmt = select(AgentFinding).where(AgentFinding.analysis_id == analysis_id)
    if agent:
        stmt = stmt.where(AgentFinding.agent_type == agent)
    stmt = stmt.order_by(AgentFinding.confidence_score.desc())

    result = await db.execute(stmt)
    findings = result.scalars().all()

    return {
        "status": "success",
        "data": [
            FindingResponse(
                id=f.id,
                agent_type=f.agent_type,
                finding_text=f.finding_text,
                confidence_score=f.confidence_score,
                source_references=f.source_references,
                created_at=f.created_at,
            ).model_dump()
            for f in findings
        ],
        "count": len(findings),
    }
