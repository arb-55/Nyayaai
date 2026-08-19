"""
ExtractedEntity Model — NLP-extracted named entities from documents.

Stores character offsets, normalized value, confidence, and source sentence back to the source document for traceability.
"""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="E.g. PERSON, LOCATION, DATE, LEGAL_SECTION, COURT"
    )
    entity_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True, default=1.0)
    start_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_sentence: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="The sentence containing this entity, for context"
    )

    # ── Relationships ──
    document = relationship("Document", back_populates="entities")

    def __repr__(self) -> str:
        return f"<ExtractedEntity(type={self.entity_type}, text='{self.entity_text[:30]}', norm='{self.normalized_value}')>"
