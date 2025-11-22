"""
Phase 5-6 Models: Session Security, Break-Glass Access, Retention, and Safety.

Creates tables for:
- Enhanced session security (Phase 5)
- Break-glass emergency access (Phase 5)
- Data retention policies (Phase 6)
- Clinical safety warnings (Phase 6)

Revision ID: 003
Revises: 002
Create Date: 2025-01-22 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 5-6 tables."""

    # Update sessions table with new security fields
    op.add_column(
        "sessions",
        sa.Column("token", sa.String(64), nullable=True)
    )
    op.add_column(
        "sessions",
        sa.Column("ip_hash", sa.String(255), nullable=True)
    )
    op.add_column(
        "sessions",
        sa.Column("user_agent_hash", sa.String(255), nullable=True)
    )
    op.add_column(
        "sessions",
        sa.Column("session_hash", sa.String(255), nullable=True)
    )
    op.add_column(
        "sessions",
        sa.Column("device_name", sa.String(255), nullable=True)
    )
    op.add_column(
        "sessions",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true")
    )
    op.add_column(
        "sessions",
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True)
    )

    # Create break_glass_access table (Phase 5)
    op.create_table(
        "break_glass_access",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "denied", "revoked", "expired", name="break_glass_status"),
            nullable=False,
            server_default="pending"
        ),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("access_granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("revoked_by", sa.String(36), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_break_glass_user", "break_glass_access", ["user_id"])
    op.create_index("idx_break_glass_patient", "break_glass_access", ["patient_id"])
    op.create_index("idx_break_glass_status", "break_glass_access", ["status"])
    op.create_index("idx_break_glass_created", "break_glass_access", ["created_at"])
    op.create_index("idx_break_glass_expires", "break_glass_access", ["access_expires_at"])

    # Create data_retention_policies table (Phase 6)
    op.create_table(
        "data_retention_policies",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column(
            "data_type",
            sa.Enum(
                "clinical_documents",
                "audit_logs",
                "session_data",
                "temp_files",
                "research_data",
                "user_data",
                name="data_retention_type"
            ),
            nullable=False,
            unique=True
        ),
        sa.Column("retention_years", sa.Integer(), nullable=True),
        sa.Column("retention_days", sa.Integer(), nullable=True),
        sa.Column("retention_description", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("archive_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("archive_location", sa.String(500), nullable=True),
        sa.Column("notification_days_before", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("last_executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_execution_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_archived_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_deleted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_retention_policy_type", "data_retention_policies", ["data_type"])
    op.create_index("idx_retention_policy_active", "data_retention_policies", ["is_active"])
    op.create_index("idx_retention_policy_executed", "data_retention_policies", ["last_executed_at"])

    # Create data_retention_records table (Phase 6)
    op.create_table(
        "data_retention_records",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("policy_id", sa.String(36), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "archived", "deleted", "failed", name="data_retention_status"),
            nullable=False,
            server_default="pending"
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archive_location", sa.String(500), nullable=True),
        sa.Column("deletion_reason", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_retention_record_policy", "data_retention_records", ["policy_id"])
    op.create_index("idx_retention_record_resource", "data_retention_records", ["resource_type", "resource_id"])
    op.create_index("idx_retention_record_status", "data_retention_records", ["status"])
    op.create_index("idx_retention_record_deleted", "data_retention_records", ["deleted_at"])

    # Create clinical_safety_warnings table (Phase 6)
    op.create_table(
        "clinical_safety_warnings",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=True),
        sa.Column(
            "warning_type",
            sa.Enum(
                "low_confidence",
                "critical_concept",
                "duplicate_patient",
                "future_date",
                "missing_field",
                "conflicting_data",
                "high_risk_modification",
                name="safety_warning_type"
            ),
            nullable=False
        ),
        sa.Column(
            "warning_level",
            sa.Enum("info", "warning", "critical", "alert", name="safety_warning_level"),
            nullable=False,
            server_default="warning"
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context_data", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_by", sa.String(36), nullable=True),
        sa.Column("dismissed_reason", sa.Text(), nullable=True),
        sa.Column("override_justification", sa.Text(), nullable=True),
        sa.Column("override_approved_by", sa.String(36), nullable=True),
        sa.Column("override_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_safety_warning_user", "clinical_safety_warnings", ["user_id"])
    op.create_index("idx_safety_warning_patient", "clinical_safety_warnings", ["patient_id"])
    op.create_index("idx_safety_warning_type", "clinical_safety_warnings", ["warning_type"])
    op.create_index("idx_safety_warning_level", "clinical_safety_warnings", ["warning_level"])
    op.create_index("idx_safety_warning_active", "clinical_safety_warnings", ["is_active"])
    op.create_index("idx_safety_warning_created", "clinical_safety_warnings", ["created_at"])

    # Create clinical_safety_overrides table (Phase 6)
    op.create_table(
        "clinical_safety_overrides",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("warning_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False, server_default="low"),
        sa.Column("approved_by", sa.String(36), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_level_required", sa.String(50), nullable=False, server_default="clinician"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_safety_override_warning", "clinical_safety_overrides", ["warning_id"])
    op.create_index("idx_safety_override_user", "clinical_safety_overrides", ["user_id"])
    op.create_index("idx_safety_override_created", "clinical_safety_overrides", ["created_at"])


def downgrade() -> None:
    """Drop Phase 5-6 tables."""

    # Drop tables in reverse order
    op.drop_table("clinical_safety_overrides")
    op.drop_table("clinical_safety_warnings")
    op.drop_table("data_retention_records")
    op.drop_table("data_retention_policies")
    op.drop_table("break_glass_access")

    # Remove columns from sessions table
    op.drop_column("sessions", "invalidated_at")
    op.drop_column("sessions", "is_active")
    op.drop_column("sessions", "device_name")
    op.drop_column("sessions", "session_hash")
    op.drop_column("sessions", "user_agent_hash")
    op.drop_column("sessions", "ip_hash")
    op.drop_column("sessions", "token")
