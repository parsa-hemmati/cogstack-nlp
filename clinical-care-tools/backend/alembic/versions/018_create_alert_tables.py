"""Create alert tables for Sprint 7 - Automated Alerting.

Revision ID: 018_create_alert_tables
Revises: 017_create_nhs_dmd_medications_table
Create Date: 2025-11-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '018_create_alert_tables'
down_revision = '017_create_nhs_dmd_medications_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alert Rules table - configurable alert conditions
    op.create_table(
        'alert_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('conditions', postgresql.JSONB, nullable=False),  # Rule conditions in JSON
        sa.Column('severity', sa.String(20), nullable=False),  # critical, high, medium, low
        sa.Column('notification_channels', postgresql.ARRAY(sa.String), nullable=False, server_default='{}'),
        sa.Column('escalation_minutes', sa.Integer, nullable=True),  # Minutes before escalation
        sa.Column('enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_alert_rules_enabled', 'alert_rules', ['enabled'])
    op.create_index('ix_alert_rules_severity', 'alert_rules', ['severity'])

    # Alert Rule Versions table - track rule changes
    op.create_table(
        'alert_rule_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('alert_rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('conditions', postgresql.JSONB, nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('change_reason', sa.Text, nullable=True),
    )
    op.create_index('ix_alert_rule_versions_rule_id', 'alert_rule_versions', ['rule_id'])

    # Triggered Alerts table - alerts that have been triggered
    op.create_table(
        'triggered_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('alert_rules.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='new'),  # new, acknowledged, dismissed, snoozed
        sa.Column('trigger_data', postgresql.JSONB, nullable=True),  # Data that triggered the alert
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('snooze_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
    )
    op.create_index('ix_triggered_alerts_status', 'triggered_alerts', ['status'])
    op.create_index('ix_triggered_alerts_severity', 'triggered_alerts', ['severity'])
    op.create_index('ix_triggered_alerts_triggered_at', 'triggered_alerts', ['triggered_at'])
    op.create_index('ix_triggered_alerts_patient_id', 'triggered_alerts', ['patient_id'])

    # Alert Notifications table - track notification delivery
    op.create_table(
        'alert_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('alert_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('triggered_alerts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(20), nullable=False),  # email, sms, in_app
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # pending, sent, delivered, failed
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
    )
    op.create_index('ix_alert_notifications_alert_id', 'alert_notifications', ['alert_id'])
    op.create_index('ix_alert_notifications_status', 'alert_notifications', ['status'])

    # Notification Preferences table - user notification settings
    op.create_table(
        'notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('email_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('sms_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('in_app_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('quiet_hours_start', sa.Time, nullable=True),  # e.g., 22:00
        sa.Column('quiet_hours_end', sa.Time, nullable=True),    # e.g., 07:00
        sa.Column('min_severity', sa.String(20), nullable=False, server_default='medium'),  # Only alert for this severity or higher
        sa.Column('phone_number', sa.String(20), nullable=True),  # For SMS
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('notification_preferences')
    op.drop_table('alert_notifications')
    op.drop_table('triggered_alerts')
    op.drop_table('alert_rule_versions')
    op.drop_table('alert_rules')
