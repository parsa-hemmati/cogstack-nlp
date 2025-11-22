"""
Initial database schema for Clinical Care Tools.

Creates all core tables:
- users: User accounts with authentication
- sessions: Active user sessions
- audit_logs: Immutable audit trail (HIPAA/GDPR compliance)
- projects: Shared workspaces
- project_members: Project membership and roles
- tasks: User assignments
- documents: Encrypted clinical documents
- extracted_entities: NLP extraction results from MedCAT
- patients: Aggregated patient records
- modules: Installed system modules

Revision ID: 001
Revises: None
Create Date: 2025-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all core tables and indexes."""

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="users_username_key"),
        sa.UniqueConstraint("email", name="users_email_key"),
        sa.CheckConstraint("role IN ('admin', 'clinician', 'researcher')", name="users_role_check"),
        sa.CheckConstraint("failed_login_attempts >= 0", name="users_failed_attempts_check"),
    )

    op.create_index("idx_users_username", "users", ["username"], unique=False)
    op.create_index("idx_users_email", "users", ["email"], unique=False)
    op.create_index("idx_users_role", "users", ["role"], unique=False)
    op.create_index("idx_users_is_active", "users", ["is_active"], unique=False)

    # Create sessions table
    op.create_table(
        "sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("expires_at > created_at", name="sessions_expires_after_created"),
    )

    op.create_index("idx_sessions_user", "sessions", ["user_id"], unique=False)
    op.create_index("idx_sessions_token", "sessions", ["token_hash"], unique=False)
    op.create_index("idx_sessions_expires", "sessions", ["expires_at"], unique=False)
    op.create_index(
        "idx_sessions_cleanup",
        "sessions",
        ["expires_at"],
        unique=False,
        postgresql_where="expires_at < now()",
    )

    # Create audit_logs table (immutable audit trail)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("resource_name", sa.String(length=255), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("timestamp IS NOT NULL", name="audit_logs_no_null_timestamp"),
    )

    op.create_index("idx_audit_logs_user", "audit_logs", ["user_id"], unique=False)
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("idx_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"], unique=False)
    op.create_index("idx_audit_logs_timestamp", "audit_logs", ["timestamp"], unique=False, postgresql_using="desc")
    op.create_index("idx_audit_logs_session", "audit_logs", ["session_id"], unique=False)
    op.create_index("idx_audit_logs_user_timestamp", "audit_logs", ["user_id", "timestamp"], unique=False)

    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False, server_default=""),
        sa.Column("project_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("dataset_id", sa.UUID(), nullable=True),
        sa.Column("medcat_model_id", sa.UUID(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="projects_name_key"),
        sa.CheckConstraint("status IN ('active', 'complete', 'archived')", name="projects_status_check"),
    )

    op.create_index("idx_projects_name", "projects", ["name"], unique=False)
    op.create_index("idx_projects_type", "projects", ["project_type"], unique=False)
    op.create_index("idx_projects_status", "projects", ["status"], unique=False)
    op.create_index("idx_projects_created_by", "projects", ["created_by"], unique=False)

    # Create project_members table
    op.create_table(
        "project_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("added_by", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["added_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "user_id", name="unique_project_member"),
        sa.CheckConstraint("role IN ('owner', 'member', 'viewer')", name="project_members_role_check"),
    )

    op.create_index("idx_project_members_project", "project_members", ["project_id"], unique=False)
    op.create_index("idx_project_members_user", "project_members", ["user_id"], unique=False)
    op.create_index("idx_project_members_role", "project_members", ["role"], unique=False)

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("assigned_to", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("updated_by", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False, server_default=""),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(length=50), nullable=False, server_default="medium"),
        sa.Column("configuration", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('pending', 'in_progress', 'complete', 'cancelled')", name="tasks_status_check"),
        sa.CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="tasks_priority_check",
        ),
    )

    op.create_index("idx_tasks_project", "tasks", ["project_id"], unique=False)
    op.create_index("idx_tasks_assigned_to", "tasks", ["assigned_to"], unique=False)
    op.create_index("idx_tasks_status", "tasks", ["status"], unique=False)
    op.create_index("idx_tasks_priority", "tasks", ["priority"], unique=False)
    op.create_index("idx_tasks_due_date", "tasks", ["due_date"], unique=False)
    op.create_index("idx_tasks_created_by", "tasks", ["created_by"], unique=False)

    # Create documents table
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("uploaded_by", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False, server_default="rtf"),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("encryption_key_id", sa.String(length=100), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=True),
        sa.Column("document_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("medcat_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("medcat_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("medcat_error", sa.String(length=2000), nullable=True),
        sa.Column("contains_phi", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("phi_types", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "file_size > 0 AND file_size < 10485760",
            name="documents_file_size_check",
        ),
        sa.CheckConstraint(
            "medcat_status IN ('pending', 'processing', 'complete', 'failed')",
            name="documents_medcat_status_check",
        ),
    )

    op.create_index("idx_documents_project", "documents", ["project_id"], unique=False)
    op.create_index("idx_documents_content_hash", "documents", ["content_hash"], unique=False)
    op.create_index("idx_documents_medcat_status", "documents", ["medcat_status"], unique=False)
    op.create_index("idx_documents_uploaded_by", "documents", ["uploaded_by"], unique=False)
    op.create_index("idx_documents_uploaded_at", "documents", ["uploaded_at"], unique=False, postgresql_using="desc")
    op.create_index("idx_documents_document_type", "documents", ["document_type"], unique=False)

    # Create extracted_entities table
    op.create_table(
        "extracted_entities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("cui", sa.String(length=20), nullable=False),
        sa.Column("concept_name", sa.String(length=500), nullable=False),
        sa.Column("source_value", sa.String(length=2000), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("meta_annotations", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("is_phi", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("phi_category", sa.String(length=100), nullable=True),
        sa.Column("structured_data", sa.JSON(), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("medcat_version", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="extracted_entities_confidence_check",
        ),
        sa.CheckConstraint("end_char > start_char", name="extracted_entities_position_check"),
    )

    op.create_index("idx_extracted_entities_document", "extracted_entities", ["document_id"], unique=False)
    op.create_index("idx_extracted_entities_project", "extracted_entities", ["project_id"], unique=False)
    op.create_index("idx_extracted_entities_cui", "extracted_entities", ["cui"], unique=False)
    op.create_index("idx_extracted_entities_entity_type", "extracted_entities", ["entity_type"], unique=False)
    op.create_index("idx_extracted_entities_is_phi", "extracted_entities", ["is_phi"], unique=False)
    op.create_index(
        "idx_extracted_entities_structured_data_gin",
        "extracted_entities",
        ["structured_data"],
        unique=False,
        postgresql_using="gin",
    )

    # Create patients table
    op.create_table(
        "patients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nhs_number", sa.String(length=10), nullable=True),
        sa.Column("mrn", sa.String(length=50), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("address_line1", sa.String(length=255), nullable=True),
        sa.Column("address_line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("postcode", sa.String(length=10), nullable=True),
        sa.Column("source_document_ids", sa.ARRAY(sa.UUID()), nullable=False),
        sa.Column("last_updated_from", sa.UUID(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nhs_number", name="patients_nhs_number_key"),
        sa.UniqueConstraint("mrn", name="patients_mrn_key"),
        sa.CheckConstraint(
            "nhs_number IS NOT NULL OR mrn IS NOT NULL",
            name="patients_identifier_check",
        ),
        sa.CheckConstraint(
            "nhs_number IS NULL OR nhs_number ~ '^\\d{10}$'",
            name="patients_nhs_format_check",
        ),
    )

    op.create_index(
        "idx_patients_nhs_number",
        "patients",
        ["nhs_number"],
        unique=True,
        postgresql_where="nhs_number IS NOT NULL",
    )
    op.create_index(
        "idx_patients_mrn",
        "patients",
        ["mrn"],
        unique=True,
        postgresql_where="mrn IS NOT NULL",
    )
    op.create_index("idx_patients_last_name", "patients", ["last_name"], unique=False)
    op.create_index("idx_patients_postcode", "patients", ["postcode"], unique=False)
    op.create_index("idx_patients_updated_at", "patients", ["updated_at"], unique=False, postgresql_using="desc")

    # Create modules table
    op.create_table(
        "modules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False, server_default=""),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("configuration", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("permissions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("routes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("installed_by", sa.UUID(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["installed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="modules_name_key"),
    )

    op.create_index("idx_modules_name", "modules", ["name"], unique=False)
    op.create_index("idx_modules_enabled", "modules", ["is_enabled"], unique=False)


def downgrade() -> None:
    """Drop all tables."""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("modules")
    op.drop_table("patients")
    op.drop_table("extracted_entities")
    op.drop_table("documents")
    op.drop_table("tasks")
    op.drop_table("project_members")
    op.drop_table("projects")
    op.drop_table("audit_logs")
    op.drop_table("sessions")
    op.drop_table("users")
