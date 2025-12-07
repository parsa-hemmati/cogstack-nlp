"""create patients table

Revision ID: 008_j6k7l8m9n0p1
Revises: 007_e1f2g3h4i5j6
Create Date: 2025-11-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_j6k7l8m9n0p1'
down_revision = '007_e1f2g3h4i5j6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create patients table for aggregated patient records.

    Table Structure:
    - id: UUID primary key
    - nhs_number: NHS number (unique, indexed, max 12 chars for "XXX XXX XXXX" format)
    - full_name: Patient full name (max 255 chars, nullable)
    - date_of_birth: Patient date of birth (DATE, nullable)
    - address: Patient address (max 500 chars, nullable)
    - first_seen_at: Timestamp of first document (TIMESTAMP)
    - last_seen_at: Timestamp of most recent document (TIMESTAMP)
    - document_count: Number of documents referencing this patient (INTEGER, default 0)
    - created_at: Record creation timestamp (TIMESTAMP)
    - updated_at: Record last updated timestamp (TIMESTAMP)

    Constraints:
    - nhs_number must be unique

    Indexes:
    - nhs_number (unique) for fast patient lookup

    Also adds foreign key constraint from extracted_entities.patient_id to patients.id
    (deferred from migration 007 until patients table existed).
    """
    # Create patients table
    op.create_table(
        'patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nhs_number', sa.String(length=12), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('document_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nhs_number')
    )

    # Create indexes
    op.create_index(
        op.f('ix_patients_nhs_number'),
        'patients',
        ['nhs_number'],
        unique=True
    )

    # Add foreign key constraint from extracted_entities.patient_id to patients.id
    # This was deferred in migration 007 until patients table existed
    op.create_foreign_key(
        'fk_extracted_entities_patient_id',
        'extracted_entities',
        'patients',
        ['patient_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """
    Drop patients table and remove foreign key from extracted_entities.

    Also removes the foreign key constraint from extracted_entities.patient_id
    before dropping patients table.
    """
    # Remove foreign key from extracted_entities first
    op.drop_constraint(
        'fk_extracted_entities_patient_id',
        'extracted_entities',
        type_='foreignkey'
    )

    # Drop patients table indexes and table
    op.drop_index(op.f('ix_patients_nhs_number'), table_name='patients')
    op.drop_table('patients')
