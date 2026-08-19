"""Initial schema migration for NyayaAI Phase 1.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-16 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Safely create enum types if they do not exist
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'casestatus') THEN
                CREATE TYPE casestatus AS ENUM ('CREATED', 'DOCUMENTS_UPLOADED', 'EXTRACTING', 'ANALYZING', 'COMPLETED', 'FAILED');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'documenttype') THEN
                CREATE TYPE documenttype AS ENUM ('FIR', 'WITNESS_STATEMENT', 'EVIDENCE', 'ARGUMENT', 'JUDGMENT', 'OTHER');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'analysisstatus') THEN
                CREATE TYPE analysisstatus AS ENUM ('PENDING', 'EXTRACTING_ENTITIES', 'RUNNING_AGENTS', 'BUILDING_CONSENSUS', 'COMPLETED', 'FAILED');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agenttype') THEN
                CREATE TYPE agenttype AS ENUM ('EVIDENCE', 'CONTRADICTION', 'LEGAL_RESEARCH');
            END IF;
        END $$;
    """)

    # Enum Column Definitions with create_type=False to prevent duplicate CREATE TYPE in create_table
    casestatus_type = postgresql.ENUM(
        'CREATED', 'DOCUMENTS_UPLOADED', 'EXTRACTING', 'ANALYZING', 'COMPLETED', 'FAILED',
        name='casestatus', create_type=False
    )
    documenttype_type = postgresql.ENUM(
        'FIR', 'WITNESS_STATEMENT', 'EVIDENCE', 'ARGUMENT', 'JUDGMENT', 'OTHER',
        name='documenttype', create_type=False
    )
    analysisstatus_type = postgresql.ENUM(
        'PENDING', 'EXTRACTING_ENTITIES', 'RUNNING_AGENTS', 'BUILDING_CONSENSUS', 'COMPLETED', 'FAILED',
        name='analysisstatus', create_type=False
    )
    agenttype_type = postgresql.ENUM(
        'EVIDENCE', 'CONTRADICTION', 'LEGAL_RESEARCH',
        name='agenttype', create_type=False
    )

    # 2. Table: cases
    op.create_table(
        'cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', casestatus_type, nullable=False, server_default='CREATED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Table: documents
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('document_type', documenttype_type, nullable=False, server_default='OTHER'),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Table: extracted_entities
    op.create_table(
        'extracted_entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False, comment='E.g. PETITIONER, RESPONDENT, PROVISION, STATUTE, DATE'),
        sa.Column('entity_text', sa.Text(), nullable=False),
        sa.Column('start_char', sa.Integer(), nullable=True),
        sa.Column('end_char', sa.Integer(), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('source_sentence', sa.Text(), nullable=True, comment='The sentence containing this entity, for context'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Table: analyses
    op.create_table(
        'analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', analysisstatus_type, nullable=False, server_default='PENDING'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Table: agent_findings
    op.create_table(
        'agent_findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', agenttype_type, nullable=False),
        sa.Column('finding_text', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, comment='0.0 to 1.0 — heuristic confidence, not statistically calibrated'),
        sa.Column('source_references', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Array of {document_id, page_number, excerpt} for traceability'),
        sa.Column('raw_llm_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Full LLM response stored for audit/debugging'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Table: consensus_reports
    op.create_table(
        'consensus_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Structured report: {evidence_summary, contradictions, legal_refs, timeline, assessment}'),
        sa.Column('overall_confidence', sa.Float(), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('analysis_id')
    )


def downgrade() -> None:
    op.drop_table('consensus_reports')
    op.drop_table('agent_findings')
    op.drop_table('analyses')
    op.drop_table('extracted_entities')
    op.drop_table('documents')
    op.drop_table('cases')

    op.execute('DROP TYPE IF EXISTS agenttype')
    op.execute('DROP TYPE IF EXISTS analysisstatus')
    op.execute('DROP TYPE IF EXISTS documenttype')
    op.execute('DROP TYPE IF EXISTS casestatus')
