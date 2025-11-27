"""create phi entities table

Revision ID: 013
Revises: 012
Create Date: 2025-11-22 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create phi_entities table for tracking PHI entities detected during de-identification.

    Supports:
    - Entity tracking (type, offsets, confidence)
    - Manual review flags
    - Action tracking (remove, replace, generalize)
    - Job association (job_id foreign key)
    - Audit trail (created_at)
    """
    op.create_table(
        'phi_entities',
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('note_id', sa.String(255), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('start_offset', sa.Integer(), nullable=False),
        sa.Column('end_offset', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('manually_reviewed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='valid_confidence'),
        sa.CheckConstraint("action IN ('remove', 'replace', 'generalize')", name='valid_action'),
        sa.ForeignKeyConstraint(['job_id'], ['deidentification_jobs.job_id'], name='fk_phi_entities_job_id', ondelete='CASCADE'),
    )

    # Index on job_id for querying entities by job
    op.create_index(
        'ix_phi_entities_job_id',
        'phi_entities',
        ['job_id']
    )

    # Index on entity_type for filtering by PHI type
    op.create_index(
        'ix_phi_entities_entity_type',
        'phi_entities',
        ['entity_type']
    )

    # Index on confidence for querying low-confidence entities
    op.create_index(
        'ix_phi_entities_confidence',
        'phi_entities',
        ['confidence']
    )

    # Composite index for manual review queries
    op.create_index(
        'ix_phi_entities_job_manually_reviewed',
        'phi_entities',
        ['job_id', 'manually_reviewed']
    )

    # Index on note_id for querying entities by note
    op.create_index(
        'ix_phi_entities_note_id',
        'phi_entities',
        ['note_id']
    )


def downgrade() -> None:
    """Drop phi_entities table and indexes."""
    op.drop_index('ix_phi_entities_note_id', table_name='phi_entities')
    op.drop_index('ix_phi_entities_job_manually_reviewed', table_name='phi_entities')
    op.drop_index('ix_phi_entities_confidence', table_name='phi_entities')
    op.drop_index('ix_phi_entities_entity_type', table_name='phi_entities')
    op.drop_index('ix_phi_entities_job_id', table_name='phi_entities')
    op.drop_table('phi_entities')
