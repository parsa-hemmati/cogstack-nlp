"""create cds guidelines table

Revision ID: 015
Revises: 014
Create Date: 2025-11-23

Stores clinical decision support guidelines from ADA, AHA, USPSTF, and NICE.
Guidelines are matched to patient conditions (ICD-10/SNOMED CT) to provide
evidence-based recommendations for clinical care.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = '015'
down_revision = 'a3b7c9d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create cds_guidelines table for clinical decision support recommendations."""
    op.create_table(
        'cds_guidelines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('guideline_source', sa.String(50), nullable=False, comment='Guideline source: ADA, AHA, USPSTF, NICE'),
        sa.Column('guideline_name', sa.String(255), nullable=False, comment='Guideline name/title'),
        sa.Column('condition_code', sa.String(50), nullable=False, comment='ICD-10 or SNOMED CT condition code'),
        sa.Column('recommendation', sa.Text, nullable=False, comment='Clinical recommendation text'),
        sa.Column('evidence_level', sa.String(10), nullable=False, comment='Evidence level: A (strong), B (moderate), C (weak)'),
        sa.Column('rationale', sa.Text, nullable=False, comment='Rationale and supporting evidence'),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, comment='Date guideline was last updated by source'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Date record was created in database'),

        # Unique constraint: prevent duplicate guidelines for same source/name/condition
        sa.UniqueConstraint('guideline_source', 'guideline_name', 'condition_code', name='uq_cds_guidelines_source_name_condition'),

        # Index for fast lookups by condition code (primary query pattern)
        sa.Index('ix_cds_guidelines_condition_code', 'condition_code'),

        # Indexes for additional query patterns
        sa.Index('ix_cds_guidelines_source', 'guideline_source'),
        sa.Index('ix_cds_guidelines_evidence_level', 'evidence_level'),
    )

    # Add check constraint for valid guideline sources
    op.create_check_constraint(
        'ck_cds_guidelines_source',
        'cds_guidelines',
        "guideline_source IN ('ADA', 'AHA', 'USPSTF', 'NICE')"
    )

    # Add check constraint for valid evidence levels
    op.create_check_constraint(
        'ck_cds_guidelines_evidence_level',
        'cds_guidelines',
        "evidence_level IN ('A', 'B', 'C')"
    )


def downgrade() -> None:
    """Drop cds_guidelines table."""
    op.drop_table('cds_guidelines')
