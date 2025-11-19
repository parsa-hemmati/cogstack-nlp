"""
Add timeline_exports table

Revision ID: 009
Revises: 008
Create Date: 2025-11-19 07:10:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create timeline_exports table for tracking timeline exports."""
    op.create_table(
        'timeline_exports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('format', sa.String(length=10), nullable=False),  # "pdf", "fhir", "json"
        sa.Column('filters', postgresql.JSONB(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('audit_log_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['audit_log_id'], ['audit_logs.id'], ondelete='SET NULL')
    )

    # Create indexes for performance
    op.create_index('idx_timeline_exports_patient', 'timeline_exports', ['patient_id'])
    op.create_index('idx_timeline_exports_user', 'timeline_exports', ['user_id'])
    op.create_index('idx_timeline_exports_created', 'timeline_exports', ['created_at'])
    op.create_index('idx_timeline_exports_expires', 'timeline_exports', ['expires_at'])


def downgrade() -> None:
    """Drop timeline_exports table."""
    # Drop indexes first
    op.drop_index('idx_timeline_exports_expires', table_name='timeline_exports')
    op.drop_index('idx_timeline_exports_created', table_name='timeline_exports')
    op.drop_index('idx_timeline_exports_user', table_name='timeline_exports')
    op.drop_index('idx_timeline_exports_patient', table_name='timeline_exports')

    # Drop table
    op.drop_table('timeline_exports')
