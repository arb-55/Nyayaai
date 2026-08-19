"""Add normalized_value and confidence to extracted_entities table.

Revision ID: 003_add_entity_fields
Revises: 002_doc_extraction_fields
Create Date: 2026-08-19 15:33:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_add_entity_fields'
down_revision: Union[str, None] = '002_doc_extraction_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('extracted_entities', sa.Column('normalized_value', sa.String(length=500), nullable=True))
    op.add_column('extracted_entities', sa.Column('confidence', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('extracted_entities', 'confidence')
    op.drop_column('extracted_entities', 'normalized_value')
