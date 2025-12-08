"""create documents table

Revision ID: 006_f9c8b4d7e2a1
Revises: 005
Create Date: 2025-11-23

NOTE: This migration is now a NO-OP.
The documents table is already created in 001_initial_schema.py.
This file is kept for migration chain integrity.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_f9c8b4d7e2a1'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op: documents table already exists from 001_initial_schema."""
    pass


def downgrade() -> None:
    """No-op: documents table is managed by 001_initial_schema."""
    pass

