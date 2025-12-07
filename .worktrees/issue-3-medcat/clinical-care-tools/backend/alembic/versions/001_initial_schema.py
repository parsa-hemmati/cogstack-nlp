"""Initial schema with all MVP models.

Revision ID: 001
Revises:
Create Date: 2025-11-18 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'clinician', 'researcher', 'auditor', 'viewer', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('session_token', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)

    # Patients table
    op.create_table(
        'patients',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('mrn', sa.String(length=50), nullable=False),
        sa.Column('nhs_number', sa.String(length=10), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mrn')
    )
    op.create_index(op.f('ix_patients_mrn'), 'patients', ['mrn'], unique=True)
    op.create_index(op.f('ix_patients_nhs_number'), 'patients', ['nhs_number'], unique=False)

    # Documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('document_type', sa.Enum('clinical_note', 'discharge_summary', 'lab_report', 'radiology_report', 'pathology_report', 'consultation', 'prescription', 'other', name='documenttype'), nullable=False),
        sa.Column('document_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('elasticsearch_id', sa.String(length=100), nullable=True, comment='Reference to document in Elasticsearch'),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='documentstatus'), nullable=False),
        sa.Column('nlp_processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('nlp_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=False, server_default='false', comment='If true, document cannot be deleted per retention policy'),
        sa.Column('legal_hold_reason', sa.Text(), nullable=True, comment='Reason for legal hold (e.g., litigation, audit)'),
        sa.Column('legal_hold_by', sa.UUID(), nullable=True, comment='User who placed the legal hold'),
        sa.Column('legal_hold_at', sa.DateTime(timezone=True), nullable=True, comment='When legal hold was placed'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['legal_hold_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_patient_id'), 'documents', ['patient_id'], unique=False)
    op.create_index(op.f('ix_documents_document_date'), 'documents', ['document_date'], unique=False)
    op.create_index(op.f('ix_documents_elasticsearch_id'), 'documents', ['elasticsearch_id'], unique=False)
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)
    op.create_index(op.f('ix_documents_legal_hold'), 'documents', ['legal_hold'], unique=False)

    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)

    # Clinical overrides table
    op.create_table(
        'clinical_overrides',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False, comment='Clinician who made the override'),
        sa.Column('patient_id', sa.UUID(), nullable=False, comment='Patient affected by override'),
        sa.Column('recommendation_type', sa.String(length=100), nullable=False, comment='Type of recommendation (e.g., "critical_alert", "dosage_warning")'),
        sa.Column('recommendation_value', sa.Text(), nullable=False, comment='Original system recommendation'),
        sa.Column('override_value', sa.Text(), nullable=False, comment='Clinician\'s override decision'),
        sa.Column('justification', sa.Text(), nullable=False, comment='Required justification (min 20 characters)'),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium', comment='Severity of override: low, medium, high'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clinical_overrides_user_id'), 'clinical_overrides', ['user_id'], unique=False)
    op.create_index(op.f('ix_clinical_overrides_patient_id'), 'clinical_overrides', ['patient_id'], unique=False)

    # Critical finding alerts table
    op.create_table(
        'critical_finding_alerts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False, comment='Patient with critical finding'),
        sa.Column('concept_cui', sa.String(length=20), nullable=False, comment='UMLS/SNOMED concept identifier'),
        sa.Column('concept_name', sa.String(length=500), nullable=False, comment='Human-readable concept name'),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='findingseverity'), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=True, comment='Source document where finding was detected'),
        sa.Column('acknowledged_by', sa.UUID(), nullable=True, comment='Clinician who acknowledged the alert'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notified_users', sa.Text(), nullable=True, comment='JSON array of user IDs who were notified'),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_critical_finding_alerts_patient_id'), 'critical_finding_alerts', ['patient_id'], unique=False)
    op.create_index(op.f('ix_critical_finding_alerts_severity'), 'critical_finding_alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_critical_finding_alerts_acknowledged_at'), 'critical_finding_alerts', ['acknowledged_at'], unique=False)

    # Clinical incidents table
    op.create_table(
        'clinical_incidents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('incident_type', sa.Enum('data_accuracy', 'system_error', 'user_error', 'safety_concern', 'privacy_breach', 'other', name='incidenttype'), nullable=False),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='incidentseverity'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, comment='Detailed incident description'),
        sa.Column('patient_id', sa.UUID(), nullable=True, comment='Patient affected (if applicable)'),
        sa.Column('reported_by', sa.UUID(), nullable=False, comment='User who reported the incident'),
        sa.Column('investigated_by', sa.UUID(), nullable=True, comment='User assigned to investigate'),
        sa.Column('resolution', sa.Text(), nullable=True, comment='How the incident was resolved'),
        sa.Column('status', sa.Enum('reported', 'under_investigation', 'resolved', 'closed', name='incidentstatus'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reported_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['investigated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clinical_incidents_incident_type'), 'clinical_incidents', ['incident_type'], unique=False)
    op.create_index(op.f('ix_clinical_incidents_severity'), 'clinical_incidents', ['severity'], unique=False)
    op.create_index(op.f('ix_clinical_incidents_status'), 'clinical_incidents', ['status'], unique=False)
    op.create_index(op.f('ix_clinical_incidents_patient_id'), 'clinical_incidents', ['patient_id'], unique=False)
    op.create_index(op.f('ix_clinical_incidents_reported_by'), 'clinical_incidents', ['reported_by'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('clinical_incidents')
    op.drop_table('critical_finding_alerts')
    op.drop_table('clinical_overrides')
    op.drop_table('audit_logs')
    op.drop_table('documents')
    op.drop_table('patients')
    op.drop_table('users')

    # Drop enums
    sa.Enum(name='incidentstatus').drop(op.get_bind())
    sa.Enum(name='incidentseverity').drop(op.get_bind())
    sa.Enum(name='incidenttype').drop(op.get_bind())
    sa.Enum(name='findingseverity').drop(op.get_bind())
    sa.Enum(name='documentstatus').drop(op.get_bind())
    sa.Enum(name='documenttype').drop(op.get_bind())
    sa.Enum(name='userrole').drop(op.get_bind())
