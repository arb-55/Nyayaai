"""Add cleaned_text, extraction_status, and extraction_error to documents table.

Revision ID: 002_doc_extraction_fields
Revises: 001_initial_schema
Create Date: 2026-08-17 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_doc_extraction_fields'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Safely create extractionstatus enum type
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'extractionstatus') THEN
                CREATE TYPE extractionstatus AS ENUM ('PENDING', 'EXTRACTING', 'COMPLETED', 'FAILED');
            END IF;
        END $$;
    """)

    extractionstatus_type = postgresql.ENUM(
        'PENDING', 'EXTRACTING', 'COMPLETED', 'FAILED',
        name='extractionstatus', create_type=False
    )

    # 2. Add columns to documents table
    op.add_column('documents', sa.Column('cleaned_text', sa.Text(), nullable=True))
    op.add_column('documents', sa.Column('extraction_status', extractionstatus_type, nullable=False, server_default='PENDING'))
    op.add_column('documents', sa.Column('extraction_error', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('documents', 'extraction_error')
    op.drop_column('documents', 'extraction_status')
    op.drop_column('documents', 'cleaned_text')

    op.execute('DROP TYPE IF EXISTS extractionstatus')
