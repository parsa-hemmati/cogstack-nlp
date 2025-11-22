"""
Module-specific tables.

Creates tables for optional modules:
- patient_search_results: Patient Search module
- timeline_views: Timeline module

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create module-specific tables."""

    # Create patient_search_results table
    op.create_table(
        "patient_search_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("query", sa.JSON(), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_patient_search_task", "patient_search_results", ["task_id"], unique=False)
    op.create_index("idx_patient_search_user", "patient_search_results", ["user_id"], unique=False)

    # Create timeline_views table
    op.create_table(
        "timeline_views",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.String(length=255), nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_timeline_views_task", "timeline_views", ["task_id"], unique=False)
    op.create_index("idx_timeline_views_user", "timeline_views", ["user_id"], unique=False)
    op.create_index("idx_timeline_views_patient", "timeline_views", ["patient_id"], unique=False)


def downgrade() -> None:
    """Drop module-specific tables."""

    op.drop_table("timeline_views")
    op.drop_table("patient_search_results")
