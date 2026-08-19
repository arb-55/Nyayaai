"""
Reports Router — Retrieve and download consensus reports.

NOTE: PDF generation (WeasyPrint) will be wired in Phase 5.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import AnalysisNotFoundError
from src.models.analysis import Analysis
from src.models.finding import ConsensusReport
from src.schemas.report import ReportDetailResponse, ReportResponse

router = APIRouter()


@router.get("/analyses/{analysis_id}/report")
async def get_report(analysis_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get the consensus report for a completed analysis.

    Returns the structured report data with AI disclaimer.
    """
    analysis = await db.get(Analysis, analysis_id)
    if not analysis:
        raise AnalysisNotFoundError(str(analysis_id))

    stmt = select(ConsensusReport).where(ConsensusReport.analysis_id == analysis_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": {
                    "code": "REPORT_NOT_FOUND",
                    "message": "No consensus report has been generated for this analysis yet.",
                },
            },
        )

    return ReportDetailResponse(
        data=ReportResponse(
            id=report.id,
            analysis_id=report.analysis_id,
            overall_confidence=report.overall_confidence,
            summary_text=report.summary_text,
            report_data=report.report_data,
            generated_at=report.generated_at,
        )
    )


@router.get("/analyses/{analysis_id}/report/pdf")
async def download_report_pdf(analysis_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Download the consensus report as a PDF.

    NOTE: PDF generation will be implemented in Phase 5 using WeasyPrint.
    """
    analysis = await db.get(Analysis, analysis_id)
    if not analysis:
        raise AnalysisNotFoundError(str(analysis_id))

    # TODO (Phase 5): Generate PDF using WeasyPrint + Jinja2 template
    return JSONResponse(
        status_code=501,
        content={
            "status": "error",
            "error": {
                "code": "NOT_IMPLEMENTED",
                "message": "PDF report generation will be available in a future update.",
            },
        },
    )
