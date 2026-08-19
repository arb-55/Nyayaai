"""
Document Repository — Database access layer for Document model.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import Document, ExtractionStatus


class DocumentRepository:
    """Provides database operations for Document entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Document:
        doc = Document(**kwargs)
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        return doc

    async def get_by_id(self, doc_id: UUID) -> Document | None:
        return await self.db.get(Document, doc_id)

    async def list_by_case(self, case_id: UUID) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.case_id == case_id)
            .order_by(Document.uploaded_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self, doc_id: UUID, status: ExtractionStatus, error_message: str | None = None
    ) -> None:
        doc = await self.get_by_id(doc_id)
        if doc:
            doc.extraction_status = status
            doc.extraction_error = error_message

    async def update_extracted_text(
        self,
        doc_id: UUID,
        raw_text: str,
        cleaned_text: str,
        page_count: int,
        status: ExtractionStatus = ExtractionStatus.COMPLETED,
    ) -> None:
        doc = await self.get_by_id(doc_id)
        if doc:
            doc.extracted_text = raw_text
            doc.cleaned_text = cleaned_text
            doc.page_count = page_count
            doc.extraction_status = status
            doc.extraction_error = None

    async def delete(self, doc_id: UUID) -> bool:
        doc = await self.get_by_id(doc_id)
        if doc:
            await self.db.delete(doc)
            return True
        return False
