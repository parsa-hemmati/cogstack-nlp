"""Create NHS dm+d medications table

Revision ID: 017
Revises: 016
Create Date: 2025-11-23 19:30:00.000000

NHS Dictionary of Medicines and Devices (dm+d) table for medication identification
and drug interaction checking. Source: NHS Digital TRUD.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create NHS dm+d medications table and drug interactions table."""

    # NHS dm+d Medications Table
    op.create_table(
        'nhs_dmd_medications',
        sa.Column('dm_d_code', sa.String(18), primary_key=True, nullable=False, comment='SNOMED CT dm+d code'),
        sa.Column('name', sa.String(500), nullable=False, comment='Medication name'),
        sa.Column('form', sa.String(200), nullable=True, comment='Tablet, Capsule, Injection, etc.'),
        sa.Column('strength', sa.String(100), nullable=True, comment='e.g., 500mg, 10mg/ml'),
        sa.Column('unit', sa.String(50), nullable=True, comment='mg, ml, etc.'),
        sa.Column('vtm_id', sa.String(18), nullable=True, comment='Virtual Therapeutic Moiety ID'),
        sa.Column('vmp_id', sa.String(18), nullable=True, comment='Virtual Medicinal Product ID'),
        sa.Column('amp_id', sa.String(18), nullable=True, comment='Actual Medicinal Product ID'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'), comment='Is medication currently active'),
        sa.Column('last_updated', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'), comment='Last update timestamp'),
        comment='NHS Dictionary of Medicines and Devices (dm+d) medication database'
    )

    # Create indexes for common query patterns
    op.create_index('idx_dmd_name', 'nhs_dmd_medications', ['name'], postgresql_ops={'name': 'varchar_pattern_ops'})
    op.create_index('idx_dmd_vtm', 'nhs_dmd_medications', ['vtm_id'])
    op.create_index('idx_dmd_vmp', 'nhs_dmd_medications', ['vmp_id'])
    op.create_index('idx_dmd_amp', 'nhs_dmd_medications', ['amp_id'])
    op.create_index('idx_dmd_active', 'nhs_dmd_medications', ['is_active'])

    # Drug Interactions Table
    op.create_table(
        'drug_interactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='Interaction ID'),
        sa.Column('drug_a_code', sa.String(18), nullable=False, comment='dm+d code for first drug'),
        sa.Column('drug_b_code', sa.String(18), nullable=False, comment='dm+d code for second drug'),
        sa.Column('interaction_type', sa.String(100), nullable=True, comment='contraindicated, major, moderate, minor'),
        sa.Column('severity', sa.Integer(), nullable=True, comment='1 (contraindicated) to 4 (minor)'),
        sa.Column('description', sa.Text(), nullable=True, comment='Clinical guidance for the interaction'),
        sa.Column('evidence_level', sa.String(1), nullable=True, comment='A, B, C'),
        sa.Column('source', sa.String(200), nullable=True, comment='OpenFDA, Micromedex, etc.'),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'), comment='Creation timestamp'),
        sa.Column('last_updated', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'), comment='Last update timestamp'),
        comment='Drug-drug interaction database'
    )

    # Create indexes for interaction lookups
    op.create_index('idx_interaction_drugs', 'drug_interactions', ['drug_a_code', 'drug_b_code'])
    op.create_index('idx_interaction_severity', 'drug_interactions', ['severity'])
    op.create_index('idx_interaction_type', 'drug_interactions', ['interaction_type'])

    # Create unique constraint to prevent duplicate interactions
    op.create_unique_constraint('uq_drug_interaction', 'drug_interactions', ['drug_a_code', 'drug_b_code', 'source'])


def downgrade() -> None:
    """Drop NHS dm+d medications and drug interactions tables."""
    op.drop_table('drug_interactions')
    op.drop_table('nhs_dmd_medications')
