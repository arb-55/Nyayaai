"""
Case Repository — Database access layer for Case model.

Abstracts raw SQL/ORM queries from the service layer.
"""

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.case import Case, CaseStatus
from src.models.document import Document


class CaseRepository:
    """Provides database operations for Case entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, title: str, description: str | None = None) -> Case:
        case = Case(title=title, description=description)
        self.db.add(case)
        await self.db.flush()
        await self.db.refresh(case)
        return case

    async def get_by_id(self, case_id: UUID) -> Case | None:
        return await self.db.get(Case, case_id)

    async def list_all(self) -> list[tuple[Case, int]]:
        """List all cases with document counts."""
        stmt = (
            select(Case, func.count(Document.id).label("doc_count"))
            .outerjoin(Document, Case.id == Document.case_id)
            .group_by(Case.id)
            .order_by(Case.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.all()

    async def update_status(self, case_id: UUID, status: CaseStatus) -> None:
        case = await self.get_by_id(case_id)
        if case:
            case.status = status

    async def delete(self, case_id: UUID) -> bool:
        case = await self.get_by_id(case_id)
        if case:
            await self.db.delete(case)
            return True
        return False
