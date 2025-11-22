"""create manual annotations table

Revision ID: 014
Revises: 013
Create Date: 2025-11-22

Stores manual PHI annotations from human reviewers for continuous model improvement.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create manual_annotations table for human-in-the-loop PHI review."""
    op.create_table(
        'manual_annotations',
        sa.Column('annotation_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('note_id', sa.String(255), nullable=False, comment='Note identifier from source system'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='User who created annotation'),
        sa.Column('text', sa.String(500), nullable=False, comment='Annotated PHI text (max 500 chars)'),
        sa.Column('start_offset', sa.Integer, nullable=False, comment='Character start position in note'),
        sa.Column('end_offset', sa.Integer, nullable=False, comment='Character end position in note'),
        sa.Column('entity_type', sa.String(50), nullable=False, comment='PHI category (e.g., NAME, DOB, MRN)'),
        sa.Column('confidence', sa.Float, nullable=False, default=1.0, comment='Annotator confidence (0.0-1.0)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True, comment='Soft delete flag'),

        # Foreign keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_manual_annotations_user_id'),

        # Indexes for performance
        sa.Index('ix_manual_annotations_note_id', 'note_id'),
        sa.Index('ix_manual_annotations_user_id', 'user_id'),
        sa.Index('ix_manual_annotations_entity_type', 'entity_type'),
        sa.Index('ix_manual_annotations_created_at', 'created_at'),
        sa.Index('ix_manual_annotations_is_active', 'is_active'),
    )

    # Add check constraints
    op.create_check_constraint(
        'ck_manual_annotations_confidence',
        'manual_annotations',
        'confidence >= 0.0 AND confidence <= 1.0'
    )

    op.create_check_constraint(
        'ck_manual_annotations_offsets',
        'manual_annotations',
        'start_offset >= 0 AND end_offset > start_offset'
    )


def downgrade() -> None:
    """Drop manual_annotations table."""
    op.drop_table('manual_annotations')
