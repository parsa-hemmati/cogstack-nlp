"""Create population health tables for Sprint 8 - Population Health Dashboards.

Revision ID: 019_create_population_health_tables
Revises: 018_create_alert_tables
Create Date: 2025-11-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '019_create_population_health_tables'
down_revision = '018_create_alert_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cohort Definitions table - saved patient cohort queries
    op.create_table(
        'cohort_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('query_definition', postgresql.JSONB, nullable=False, comment='Saved search query with filters'),
        sa.Column('inclusion_criteria', postgresql.JSONB, nullable=True, comment='Additional inclusion rules'),
        sa.Column('exclusion_criteria', postgresql.JSONB, nullable=True, comment='Exclusion rules'),
        sa.Column('is_dynamic', sa.Boolean, nullable=False, server_default='true', comment='Auto-update membership'),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='false', comment='Visible to all users'),
        sa.Column('patient_count', sa.Integer, nullable=True, comment='Cached member count'),
        sa.Column('last_refreshed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_cohort_definitions_name', 'cohort_definitions', ['name'])
    op.create_index('ix_cohort_definitions_created_by', 'cohort_definitions', ['created_by'])

    # Cohort Memberships table - patients in each cohort
    op.create_table(
        'cohort_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cohort_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cohort_definitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('added_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True, comment='NULL if auto-added'),
        sa.Column('match_score', sa.Float, nullable=True, comment='Relevance score if applicable'),
        sa.Column('metadata', postgresql.JSONB, nullable=True, comment='Why this patient matched'),
    )
    op.create_index('ix_cohort_memberships_cohort', 'cohort_memberships', ['cohort_id'])
    op.create_index('ix_cohort_memberships_patient', 'cohort_memberships', ['patient_id'])
    op.create_unique_constraint('uq_cohort_patient', 'cohort_memberships', ['cohort_id', 'patient_id'])

    # Population Metrics table - aggregated statistics
    op.create_table(
        'population_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cohort_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cohort_definitions.id', ondelete='CASCADE'), nullable=True, comment='NULL for global metrics'),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False, comment='count, percentage, average, distribution'),
        sa.Column('value', sa.Float, nullable=True),
        sa.Column('value_json', postgresql.JSONB, nullable=True, comment='Complex values like distributions'),
        sa.Column('dimension', sa.String(100), nullable=True, comment='Age group, gender, etc.'),
        sa.Column('dimension_value', sa.String(255), nullable=True),
        sa.Column('period_start', sa.Date, nullable=True),
        sa.Column('period_end', sa.Date, nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_population_metrics_cohort', 'population_metrics', ['cohort_id'])
    op.create_index('ix_population_metrics_name', 'population_metrics', ['metric_name'])
    op.create_index('ix_population_metrics_period', 'population_metrics', ['period_start', 'period_end'])

    # Dashboard Configurations table - saved dashboard layouts
    op.create_table(
        'dashboard_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('layout', postgresql.JSONB, nullable=False, comment='Widget positions and sizes'),
        sa.Column('widgets', postgresql.JSONB, nullable=False, comment='Widget configurations'),
        sa.Column('filters', postgresql.JSONB, nullable=True, comment='Default dashboard filters'),
        sa.Column('refresh_interval_seconds', sa.Integer, nullable=True, comment='Auto-refresh interval'),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_dashboard_configurations_created_by', 'dashboard_configurations', ['created_by'])

    # Saved Reports table - generated PDF/Excel reports
    op.create_table(
        'saved_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False, comment='cohort_summary, trend_analysis, etc.'),
        sa.Column('cohort_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cohort_definitions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('parameters', postgresql.JSONB, nullable=True, comment='Report generation parameters'),
        sa.Column('file_path', sa.String(500), nullable=True, comment='Path to generated file'),
        sa.Column('file_format', sa.String(20), nullable=False, comment='pdf, xlsx, csv'),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', comment='pending, generating, completed, failed'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='Auto-delete after this time'),
    )
    op.create_index('ix_saved_reports_cohort', 'saved_reports', ['cohort_id'])
    op.create_index('ix_saved_reports_status', 'saved_reports', ['status'])


def downgrade() -> None:
    op.drop_table('saved_reports')
    op.drop_table('dashboard_configurations')
    op.drop_table('population_metrics')
    op.drop_table('cohort_memberships')
    op.drop_table('cohort_definitions')
