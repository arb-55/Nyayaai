"""
Cases Router — CRUD endpoints for legal cases.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import CaseNotFoundError
from src.models.case import Case
from src.models.document import Document
from src.schemas.case import (
    CaseCreate,
    CaseListResponse,
    CaseResponse,
    CaseSingleResponse,
    CaseUpdate,
)

router = APIRouter()


@router.post("/cases", response_model=CaseSingleResponse, status_code=201)
async def create_case(payload: CaseCreate, db: AsyncSession = Depends(get_db)):
    """Create a new case for analysis."""
    case = Case(title=payload.title, description=payload.description)
    db.add(case)
    await db.flush()
    await db.refresh(case)

    return CaseSingleResponse(
        data=CaseResponse(
            id=case.id,
            title=case.title,
            description=case.description,
            status=case.status,
            created_at=case.created_at,
            updated_at=case.updated_at,
            document_count=0,
        )
    )


@router.get("/cases", response_model=CaseListResponse)
async def list_cases(db: AsyncSession = Depends(get_db)):
    """List all cases with document counts."""
    # Query cases with document count
    stmt = (
        select(
            Case,
            func.count(Document.id).label("doc_count"),
        )
        .outerjoin(Document, Case.id == Document.case_id)
        .group_by(Case.id)
        .order_by(Case.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    cases = [
        CaseResponse(
            id=case.id,
            title=case.title,
            description=case.description,
            status=case.status,
            created_at=case.created_at,
            updated_at=case.updated_at,
            document_count=doc_count,
        )
        for case, doc_count in rows
    ]

    return CaseListResponse(data=cases, count=len(cases))


@router.get("/cases/{case_id}", response_model=CaseSingleResponse)
async def get_case(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single case by ID."""
    case = await db.get(Case, case_id)
    if not case:
        raise CaseNotFoundError(str(case_id))

    # Count documents
    doc_count_result = await db.execute(
        select(func.count(Document.id)).where(Document.case_id == case_id)
    )
    doc_count = doc_count_result.scalar() or 0

    return CaseSingleResponse(
        data=CaseResponse(
            id=case.id,
            title=case.title,
            description=case.description,
            status=case.status,
            created_at=case.created_at,
            updated_at=case.updated_at,
            document_count=doc_count,
        )
    )


@router.delete("/cases/{case_id}", status_code=204)
async def delete_case(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a case and all associated data."""
    case = await db.get(Case, case_id)
    if not case:
        raise CaseNotFoundError(str(case_id))

    await db.delete(case)
