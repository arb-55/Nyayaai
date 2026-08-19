"""
Analysis Router — Endpoints for triggering AI analysis, entity extraction, evidence extraction, and contradiction detection.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import AnalysisNotFoundError, CaseNotFoundError
from src.models.analysis import Analysis
from src.models.case import Case
from src.models.finding import AgentFinding, AgentType
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.entity_repo import EntityRepository
from src.schemas.analysis import (
    AnalysisDetailResponse,
    AnalysisResponse,
    AnalysisTriggerResponse,
    EntityGroupedResponse,
    EntityItemResponse,
    FindingResponse,
)
from src.services.analysis_service import analysis_service

router = APIRouter()


@router.post("/cases/{case_id}/analyze", response_model=AnalysisTriggerResponse, status_code=status.HTTP_200_OK)
async def trigger_analysis(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Trigger Phase 3A (Entities), Phase 3B (Evidence), and Phase 3C (Contradictions) analysis for a case.
    """
    case = await db.get(Case, case_id)
    if not case:
        raise CaseNotFoundError(str(case_id))

    try:
        result = await analysis_service.run_analysis(case_id, db)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "ANALYSIS_FAILED", "message": f"Analysis execution failed: {str(err)}"},
        )

    analysis_obj = result["analysis"]
    entities_list = result["entities"]
    evidence_list = result["evidence_findings"]
    contradiction_list = result["contradiction_findings"]
    all_findings = evidence_list + contradiction_list

    return AnalysisTriggerResponse(
        status="success",
        message=result.get("message", "Analysis completed successfully."),
        data=AnalysisResponse(
            id=analysis_obj.id,
            case_id=analysis_obj.case_id,
            status=analysis_obj.status,
            started_at=analysis_obj.started_at,
            completed_at=analysis_obj.completed_at,
            error_message=analysis_obj.error_message,
            findings_count=len(all_findings),
        ),
        entities_count=len(entities_list),
        entities=[
            EntityItemResponse(
                id=e.id,
                document_id=e.document_id,
                entity_type=e.entity_type,
                entity_text=e.entity_text,
                normalized_value=e.normalized_value,
                confidence=e.confidence,
                page_number=e.page_number,
                source_sentence=e.source_sentence,
            )
            for e in entities_list
        ],
    )


@router.get("/cases/{case_id}/contradictions")
async def get_case_contradictions(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get all potential contradiction findings for a case.
    """
    case = await db.get(Case, case_id)
    if not case:
        raise CaseNotFoundError(str(case_id))

    analysis_repo = AnalysisRepository(db)
    latest_analysis = await analysis_repo.get_latest_for_case(case_id)
    if not latest_analysis:
        return {"status": "success", "case_id": str(case_id), "total_count": 0, "data": []}

    findings = await analysis_repo.get_findings(latest_analysis.id, agent_type=AgentType.CONTRADICTION)

    return {
        "status": "success",
        "case_id": str(case_id),
        "total_count": len(findings),
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
    }


@router.get("/cases/{case_id}/evidence")
async def get_case_evidence(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get all evidence findings for a case grouped by evidence category.
    """
    case = await db.get(Case, case_id)
    if not case:
        raise CaseNotFoundError(str(case_id))

    analysis_repo = AnalysisRepository(db)
    latest_analysis = await analysis_repo.get_latest_for_case(case_id)
    if not latest_analysis:
        return {"status": "success", "case_id": str(case_id), "total_count": 0, "data": {}}

    findings = await analysis_repo.get_findings(latest_analysis.id, agent_type=AgentType.EVIDENCE)

    grouped = {}
    for f in findings:
        cat = (f.source_references or {}).get("category", "FACT")
        grp = grouped.setdefault(cat, [])
        grp.append(
            FindingResponse(
                id=f.id,
                agent_type=f.agent_type,
                finding_text=f.finding_text,
                confidence_score=f.confidence_score,
                source_references=f.source_references,
                created_at=f.created_at,
            ).model_dump()
        )

    return {
        "status": "success",
        "case_id": str(case_id),
        "total_count": len(findings),
        "data": grouped,
    }


@router.get("/cases/{case_id}/entities")
async def get_case_entities(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get all extracted entities for a case, grouped by controlled entity type.
    """
    case = await db.get(Case, case_id)
    if not case:
        raise CaseNotFoundError(str(case_id))

    entity_repo = EntityRepository(db)
    entities = await entity_repo.list_by_case(case_id)

    grouped_map = {}
    for e in entities:
        grp = grouped_map.setdefault(e.entity_type, [])
        grp.append(
            EntityItemResponse(
                id=e.id,
                document_id=e.document_id,
                entity_type=e.entity_type,
                entity_text=e.entity_text,
                normalized_value=e.normalized_value,
                confidence=e.confidence,
                page_number=e.page_number,
                source_sentence=e.source_sentence,
            )
        )

    grouped_list = [
        EntityGroupedResponse(entity_type=etype, count=len(items), entities=items)
        for etype, items in grouped_map.items()
    ]

    return {
        "status": "success",
        "case_id": str(case_id),
        "total_count": len(entities),
        "data": grouped_list,
    }


@router.get("/cases/{case_id}/analysis")
async def get_analysis(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get the latest analysis for a case, including status, findings, and extracted entities."""
    case = await db.get(Case, case_id)
    if not case:
        raise CaseNotFoundError(str(case_id))

    analysis_repo = AnalysisRepository(db)
    analysis = await analysis_repo.get_latest_for_case(case_id)

    if not analysis:
        return {"status": "success", "data": None, "message": "No analysis has been run for this case yet."}

    findings = await analysis_repo.get_findings(analysis.id)

    entity_repo = EntityRepository(db)
    entities = await entity_repo.list_by_case(case_id)

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
        entities=[
            EntityItemResponse(
                id=e.id,
                document_id=e.document_id,
                entity_type=e.entity_type,
                entity_text=e.entity_text,
                normalized_value=e.normalized_value,
                confidence=e.confidence,
                page_number=e.page_number,
                source_sentence=e.source_sentence,
            )
            for e in entities
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

    analysis_repo = AnalysisRepository(db)
    findings = await analysis_repo.get_findings(analysis_id, agent_type=agent)

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
