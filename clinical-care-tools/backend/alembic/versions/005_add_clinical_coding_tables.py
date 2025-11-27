"""Add clinical coding tables (Sprint 5)

Revision ID: 005
Revises: 004
Create Date: 2025-11-18

Tables:
- icd10_library: ICD-10-CM code reference
- coding_assignments: Document code assignments
- coding_metrics: Coding quality metrics
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Create clinical coding tables"""

    # Enable pg_trgm extension for trigram text search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    # Table: icd10_library
    op.create_table(
        'icd10_library',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(10), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(200), nullable=True),
        sa.Column('billable', sa.Boolean, default=True),
        sa.Column('valid_for_coding', sa.Boolean, default=True),
        sa.Column('version', sa.String(10), default='2024'),
        sa.Column('effective_date', sa.DateTime, nullable=True),
    )

    # GIN index for full-text search on description
    op.execute("""
        CREATE INDEX idx_icd10_description_gin ON icd10_library
        USING gin (description gin_trgm_ops)
    """)

    # Table: coding_assignments
    op.create_table(
        'coding_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('icd10_code', sa.String(10), nullable=False, index=True),
        sa.Column('is_primary', sa.Boolean, default=False),
        sa.Column('source', sa.String(20), nullable=False, comment='Source: ai, manual, approved'),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('evidence', sa.Text, nullable=True),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.DateTime, nullable=False, index=True),

        # TODO: Add foreign keys when documents and users tables exist
        # sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        # sa.ForeignKeyConstraint(['assigned_by'], ['users.id'])
    )

    # Indexes
    op.create_index('idx_coding_document', 'coding_assignments', ['document_id'])
    op.create_index('idx_coding_code', 'coding_assignments', ['icd10_code'])
    op.create_index('idx_coding_assigned_at', 'coding_assignments', ['assigned_at'])

    # Table: coding_metrics
    op.create_table(
        'coding_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('date', sa.DateTime, nullable=False, index=True),
        sa.Column('period', sa.String(20), default='daily'),
        sa.Column('coder_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('documents_coded', sa.Integer, default=0),
        sa.Column('codes_assigned', sa.Integer, default=0),
        sa.Column('avg_codes_per_document', sa.Float, default=0.0),
        sa.Column('ai_suggestions_accepted', sa.Integer, default=0),
        sa.Column('ai_suggestions_rejected', sa.Integer, default=0),
        sa.Column('ai_precision', sa.Float, nullable=True),
        sa.Column('ai_recall', sa.Float, nullable=True),
        sa.Column('avg_time_per_document', sa.Float, nullable=True),
        sa.Column('total_coding_time', sa.Float, nullable=True),
        sa.Column('code_validation_errors', sa.Integer, default=0),
        sa.Column('duplicate_codes', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),

        # TODO: Add foreign key when users table exists
        # sa.ForeignKeyConstraint(['coder_id'], ['users.id'])
    )

    # Indexes
    op.create_index('idx_metrics_date', 'coding_metrics', ['date'])
    op.create_index('idx_metrics_coder', 'coding_metrics', ['coder_id'])


def downgrade():
    """Drop clinical coding tables"""
    op.drop_table('coding_metrics')
    op.drop_table('coding_assignments')
    op.drop_table('icd10_library')

    # Drop pg_trgm extension (optional)
    # op.execute('DROP EXTENSION IF EXISTS pg_trgm')
