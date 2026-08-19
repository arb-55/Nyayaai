"""
Entity Repository — Database access layer for ExtractedEntity model.
"""

from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import Document
from src.models.entity import ExtractedEntity


class EntityRepository:
    """Provides database operations for ExtractedEntity objects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(self, entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
        """Bulk add extracted entity records."""
        self.db.add_all(entities)
        await self.db.flush()
        return entities

    async def list_by_document(self, document_id: UUID) -> list[ExtractedEntity]:
        """List all entities extracted from a specific document."""
        stmt = (
            select(ExtractedEntity)
            .where(ExtractedEntity.document_id == document_id)
            .order_by(ExtractedEntity.entity_type, ExtractedEntity.entity_text)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_case(self, case_id: UUID) -> list[ExtractedEntity]:
        """List all entities extracted across all documents belonging to a case."""
        stmt = (
            select(ExtractedEntity)
            .join(Document, ExtractedEntity.document_id == Document.id)
            .where(Document.case_id == case_id)
            .order_by(ExtractedEntity.entity_type, ExtractedEntity.entity_text)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_case(self, case_id: UUID) -> int:
        """Delete all extracted entities for documents belonging to a case."""
        doc_stmt = select(Document.id).where(Document.case_id == case_id)
        stmt = delete(ExtractedEntity).where(ExtractedEntity.document_id.in_(doc_stmt))
        result = await self.db.execute(stmt)
        return result.rowcount
