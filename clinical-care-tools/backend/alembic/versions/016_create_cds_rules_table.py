"""create cds rules table

Revision ID: 016
Revises: 015
Create Date: 2025-11-23

Stores CDS business rules in IF-THEN format using JSONB for flexible condition/action definitions.
Rules are evaluated against patient data to generate clinical recommendations.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create cds_rules table for clinical decision support business rules."""
    op.create_table(
        'cds_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('rule_name', sa.String(255), nullable=False, unique=True, comment='Unique rule name/identifier'),
        sa.Column('description', sa.Text, nullable=False, comment='Human-readable rule description'),
        sa.Column('priority', sa.Integer, nullable=False, default=0, comment='Rule priority (higher = more urgent)'),
        sa.Column('conditions', postgresql.JSONB, nullable=False, comment='IF conditions (JSONB array of condition objects)'),
        sa.Column('actions', postgresql.JSONB, nullable=False, comment='THEN actions (JSONB array of action objects)'),
        sa.Column('active', sa.Boolean, nullable=False, default=True, comment='Whether rule is currently active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Date rule was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Date rule was last updated'),

        # Unique constraint on rule_name
        sa.UniqueConstraint('rule_name', name='uq_cds_rules_name'),

        # Indexes for performance
        sa.Index('ix_cds_rules_active', 'active'),
        sa.Index('ix_cds_rules_priority_desc', 'priority', postgresql_ops={'priority': 'DESC'}),  # DESC for ORDER BY priority DESC
    )

    # Create trigger to automatically update updated_at timestamp
    # This trigger updates the updated_at column whenever a row is modified
    op.execute("""
        CREATE OR REPLACE FUNCTION update_cds_rules_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trigger_update_cds_rules_updated_at
        BEFORE UPDATE ON cds_rules
        FOR EACH ROW
        EXECUTE FUNCTION update_cds_rules_updated_at();
    """)


def downgrade() -> None:
    """Drop cds_rules table and associated trigger/function."""
    # Drop trigger first, then function, then table
    op.execute("DROP TRIGGER IF EXISTS trigger_update_cds_rules_updated_at ON cds_rules;")
    op.execute("DROP FUNCTION IF EXISTS update_cds_rules_updated_at();")
    op.drop_table('cds_rules')
