"""
Create patients table

Revision ID: 005
Revises: 004
Create Date: 2025-11-18 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create patients table for aggregated patient records."""
    op.create_table(
        'patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('nhs_number', sa.String(length=10), nullable=False, unique=True),  # UK NHS number
        sa.Column('full_name', sa.String(length=200), nullable=True),  # For fuzzy matching
        sa.Column('date_of_birth', sa.Date(), nullable=True),  # For fuzzy matching
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),  # Earliest document
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),  # Most recent document
        sa.Column('document_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create indexes for performance
    op.create_index('ix_patients_id', 'patients', ['id'])
    op.create_index('ix_patients_nhs_number', 'patients', ['nhs_number'], unique=True)
    op.create_index('ix_patients_full_name', 'patients', ['full_name'])
    op.create_index('ix_patients_date_of_birth', 'patients', ['date_of_birth'])

    # Composite index for fuzzy matching (name + DOB)
    op.create_index('ix_patients_name_dob', 'patients', ['full_name', 'date_of_birth'])

    # Add unique constraint on NHS number
    op.create_unique_constraint('uq_patients_nhs_number', 'patients', ['nhs_number'])

    # Add foreign key to extracted_entities (patient_id)
    op.create_foreign_key(
        'fk_extracted_entities_patient_id',
        'extracted_entities',
        'patients',
        ['patient_id'],
        ['id'],
        ondelete='SET NULL'  # If patient deleted, set entity.patient_id to NULL
    )


def downgrade() -> None:
    """Drop patients table."""
    # Drop foreign key first
    op.drop_constraint('fk_extracted_entities_patient_id', 'extracted_entities', type_='foreignkey')

    # Drop table
    op.drop_table('patients')
