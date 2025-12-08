"""create patients table

Revision ID: 008_j6k7l8m9n0p1
Revises: 007_e1f2g3h4i5j6
Create Date: 2025-11-23

NOTE: This migration is now a NO-OP.
The patients table is already created in 001_initial_schema.py.
The FK from extracted_entities.patient_id is added here but was already handled.
This file is kept for migration chain integrity.
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
    """No-op: patients table already exists from 001_initial_schema."""
    # The FK from extracted_entities.patient_id may need to be added
    # if 007 created extracted_entities. We'll try to create it safely.
    try:
        op.create_foreign_key(
            'fk_extracted_entities_patient_id',
            'extracted_entities',
            'patients',
            ['patient_id'],
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        pass  # FK may already exist


def downgrade() -> None:
    """No-op: patients table is managed by 001_initial_schema."""
    pass
