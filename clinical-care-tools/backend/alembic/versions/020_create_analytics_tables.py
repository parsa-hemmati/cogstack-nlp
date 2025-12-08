"""Create analytics tables for Sprint 9 - Advanced Analytics.

Revision ID: 020_create_analytics_tables
Revises: 019_create_population_health_tables
Create Date: 2025-01-15

Tables:
- analytics_models: ML model registry and versioning
- model_predictions: Prediction results and performance tracking
- quality_metrics: Quality measurement definitions and tracking
- quality_scores: Individual quality scores over time
- analytics_dashboards: Custom analytics dashboard configurations
- analytics_reports: Generated analytics reports
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY


revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade():
    # ==================== ML Models Registry ====================
    op.create_table(
        'analytics_models',
        sa.Column('id', PG_UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('model_type', sa.String(50), nullable=False),  # classification, regression, clustering, nlp
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),  # draft, training, active, deprecated, archived
        sa.Column('algorithm', sa.String(100), nullable=True),  # random_forest, xgboost, neural_network, etc.
        sa.Column('framework', sa.String(50), nullable=True),  # sklearn, pytorch, tensorflow, medcat

        # Model configuration and hyperparameters
        sa.Column('hyperparameters', JSONB, nullable=True),
        sa.Column('feature_columns', ARRAY(sa.String), nullable=True),
        sa.Column('target_column', sa.String(100), nullable=True),
        sa.Column('preprocessing_config', JSONB, nullable=True),

        # Model storage
        sa.Column('model_path', sa.String(500), nullable=True),  # Path to serialized model
        sa.Column('model_size_bytes', sa.BigInteger, nullable=True),

        # Performance metrics
        sa.Column('training_metrics', JSONB, nullable=True),  # accuracy, precision, recall, f1, auc, etc.
        sa.Column('validation_metrics', JSONB, nullable=True),
        sa.Column('test_metrics', JSONB, nullable=True),

        # Training information
        sa.Column('training_dataset_id', PG_UUID(as_uuid=True), nullable=True),
        sa.Column('training_samples', sa.Integer, nullable=True),
        sa.Column('training_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_duration_seconds', sa.Integer, nullable=True),

        # Deployment info
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deployed_by', PG_UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('endpoint_url', sa.String(500), nullable=True),

        # Audit
        sa.Column('created_by', PG_UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('updated_by', PG_UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),

        # Metadata
        sa.Column('tags', ARRAY(sa.String), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
    )

    op.create_index('ix_analytics_models_name', 'analytics_models', ['name'])
    op.create_index('ix_analytics_models_model_type', 'analytics_models', ['model_type'])
    op.create_index('ix_analytics_models_status', 'analytics_models', ['status'])
    op.create_index('ix_analytics_models_created_by', 'analytics_models', ['created_by'])

    # ==================== Model Predictions ====================
    op.create_table(
        'model_predictions',
        sa.Column('id', PG_UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('model_id', PG_UUID(as_uuid=True), sa.ForeignKey('analytics_models.id', ondelete='CASCADE'), nullable=False),
        sa.Column('patient_id', PG_UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True),
        sa.Column('document_id', PG_UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),

        # Prediction details
        sa.Column('prediction_type', sa.String(50), nullable=False),  # risk_score, classification, entity_extraction
        sa.Column('input_data', JSONB, nullable=True),  # Input features (sanitized)
        sa.Column('prediction_result', JSONB, nullable=False),  # The actual prediction
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('probabilities', JSONB, nullable=True),  # Class probabilities for classification

        # Risk predictions specific
        sa.Column('risk_level', sa.String(20), nullable=True),  # low, medium, high, critical
        sa.Column('risk_factors', JSONB, nullable=True),  # Contributing factors

        # Feedback and validation
        sa.Column('actual_outcome', JSONB, nullable=True),  # Ground truth if available
        sa.Column('feedback_status', sa.String(20), nullable=True),  # pending, correct, incorrect, partial
        sa.Column('feedback_by', PG_UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('feedback_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('feedback_notes', sa.Text, nullable=True),

        # Performance
        sa.Column('inference_time_ms', sa.Integer, nullable=True),

        # Timestamps
        sa.Column('predicted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index('ix_model_predictions_model_id', 'model_predictions', ['model_id'])
    op.create_index('ix_model_predictions_patient_id', 'model_predictions', ['patient_id'])
    op.create_index('ix_model_predictions_document_id', 'model_predictions', ['document_id'])
    op.create_index('ix_model_predictions_prediction_type', 'model_predictions', ['prediction_type'])
    op.create_index('ix_model_predictions_risk_level', 'model_predictions', ['risk_level'])
    op.create_index('ix_model_predictions_predicted_at', 'model_predictions', ['predicted_at'])

    # ==================== Quality Metrics Definitions ====================
    op.create_table(
        'quality_metrics',
        sa.Column('id', PG_UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=False),  # nlp_accuracy, data_quality, clinical_outcomes, operational
        sa.Column('metric_type', sa.String(50), nullable=False),  # percentage, count, ratio, score, time

        # Calculation configuration
        sa.Column('calculation_method', sa.String(50), nullable=False),  # automated, manual, hybrid
        sa.Column('calculation_query', sa.Text, nullable=True),  # SQL or ES query for automated calculation
        sa.Column('calculation_params', JSONB, nullable=True),

        # Thresholds and targets
        sa.Column('target_value', sa.Float, nullable=True),
        sa.Column('warning_threshold', sa.Float, nullable=True),
        sa.Column('critical_threshold', sa.Float, nullable=True),
        sa.Column('comparison_operator', sa.String(10), nullable=False, server_default='>='),  # >=, <=, ==, >, <

        # Display settings
        sa.Column('unit', sa.String(50), nullable=True),  # %, count, seconds, etc.
        sa.Column('decimal_places', sa.Integer, nullable=True, server_default='2'),
        sa.Column('display_format', sa.String(100), nullable=True),  # {value}%, {value} patients, etc.
        sa.Column('chart_type', sa.String(50), nullable=True),  # line, bar, gauge, sparkline

        # Scheduling
        sa.Column('calculation_frequency', sa.String(50), nullable=True),  # hourly, daily, weekly, monthly, on_demand
        sa.Column('last_calculated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_calculation_at', sa.DateTime(timezone=True), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='false'),

        # Audit
        sa.Column('created_by', PG_UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),

        # Metadata
        sa.Column('tags', ARRAY(sa.String), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
    )

    op.create_index('ix_quality_metrics_name', 'quality_metrics', ['name'])
    op.create_index('ix_quality_metrics_category', 'quality_metrics', ['category'])
    op.create_index('ix_quality_metrics_is_active', 'quality_metrics', ['is_active'])

    # ==================== Quality Scores (Time Series) ====================
    op.create_table(
        'quality_scores',
        sa.Column('id', PG_UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('metric_id', PG_UUID(as_uuid=True), sa.ForeignKey('quality_metrics.id', ondelete='CASCADE'), nullable=False),

        # Score value
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('previous_value', sa.Float, nullable=True),
        sa.Column('change_percentage', sa.Float, nullable=True),

        # Status based on thresholds
        sa.Column('status', sa.String(20), nullable=False),  # on_target, warning, critical, unknown

        # Context
        sa.Column('cohort_id', PG_UUID(as_uuid=True), sa.ForeignKey('cohort_definitions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('time_period', sa.String(50), nullable=True),  # 2024-01, Q1-2024, etc.
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),

        # Breakdown
        sa.Column('breakdown', JSONB, nullable=True),  # Sub-scores by category, department, etc.
        sa.Column('sample_size', sa.Integer, nullable=True),

        # Calculation details
        sa.Column('calculation_details', JSONB, nullable=True),  # Query results, intermediate values
        sa.Column('calculated_by', sa.String(50), nullable=False, server_default='system'),  # system, user_id

        # Timestamps
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index('ix_quality_scores_metric_id', 'quality_scores', ['metric_id'])
    op.create_index('ix_quality_scores_cohort_id', 'quality_scores', ['cohort_id'])
    op.create_index('ix_quality_scores_status', 'quality_scores', ['status'])
    op.create_index('ix_quality_scores_calculated_at', 'quality_scores', ['calculated_at'])
    op.create_index('ix_quality_scores_time_period', 'quality_scores', ['time_period'])

    # Composite index for efficient time-series queries
    op.create_index(
        'ix_quality_scores_metric_time',
        'quality_scores',
        ['metric_id', 'calculated_at']
    )

    # ==================== Analytics Dashboards ====================
    op.create_table(
        'analytics_dashboards',
        sa.Column('id', PG_UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('dashboard_type', sa.String(50), nullable=False),  # quality, predictive, operational, custom

        # Layout configuration
        sa.Column('layout', JSONB, nullable=True),  # Grid layout specification
        sa.Column('widgets', JSONB, nullable=True),  # Widget configurations
        sa.Column('theme', sa.String(50), nullable=True, server_default='default'),

        # Filters and defaults
        sa.Column('default_filters', JSONB, nullable=True),
        sa.Column('default_date_range', sa.String(50), nullable=True),  # last_7_days, last_30_days, this_month, etc.
        sa.Column('default_cohort_id', PG_UUID(as_uuid=True), sa.ForeignKey('cohort_definitions.id', ondelete='SET NULL'), nullable=True),

        # Refresh settings
        sa.Column('auto_refresh', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('refresh_interval_seconds', sa.Integer, nullable=True),

        # Access control
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('allowed_roles', ARRAY(sa.String), nullable=True),

        # Audit
        sa.Column('created_by', PG_UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('updated_by', PG_UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),

        # Metadata
        sa.Column('tags', ARRAY(sa.String), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
    )

    op.create_index('ix_analytics_dashboards_name', 'analytics_dashboards', ['name'])
    op.create_index('ix_analytics_dashboards_dashboard_type', 'analytics_dashboards', ['dashboard_type'])
    op.create_index('ix_analytics_dashboards_created_by', 'analytics_dashboards', ['created_by'])
    op.create_index('ix_analytics_dashboards_is_public', 'analytics_dashboards', ['is_public'])

    # ==================== Analytics Reports ====================
    op.create_table(
        'analytics_reports',
        sa.Column('id', PG_UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('report_type', sa.String(50), nullable=False),  # quality_summary, trend_analysis, model_performance, custom

        # Report configuration
        sa.Column('dashboard_id', PG_UUID(as_uuid=True), sa.ForeignKey('analytics_dashboards.id', ondelete='SET NULL'), nullable=True),
        sa.Column('metrics', ARRAY(PG_UUID(as_uuid=True)), nullable=True),  # Selected metric IDs
        sa.Column('parameters', JSONB, nullable=True),

        # Date range
        sa.Column('date_range_type', sa.String(50), nullable=True),  # fixed, relative
        sa.Column('start_date', sa.Date, nullable=True),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('relative_period', sa.String(50), nullable=True),  # last_7_days, last_30_days, etc.

        # Cohort filter
        sa.Column('cohort_id', PG_UUID(as_uuid=True), sa.ForeignKey('cohort_definitions.id', ondelete='SET NULL'), nullable=True),

        # Output configuration
        sa.Column('file_format', sa.String(20), nullable=False),  # pdf, xlsx, csv, html
        sa.Column('include_charts', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('include_raw_data', sa.Boolean, nullable=False, server_default='false'),

        # Generation status
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # pending, generating, completed, failed
        sa.Column('progress_percentage', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),

        # Generated file
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),

        # Scheduling
        sa.Column('is_scheduled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('schedule_cron', sa.String(100), nullable=True),  # Cron expression
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),

        # Distribution
        sa.Column('email_recipients', ARRAY(sa.String), nullable=True),
        sa.Column('auto_send', sa.Boolean, nullable=False, server_default='false'),

        # Audit
        sa.Column('created_by', PG_UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),

        # Metadata
        sa.Column('tags', ARRAY(sa.String), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
    )

    op.create_index('ix_analytics_reports_name', 'analytics_reports', ['name'])
    op.create_index('ix_analytics_reports_report_type', 'analytics_reports', ['report_type'])
    op.create_index('ix_analytics_reports_status', 'analytics_reports', ['status'])
    op.create_index('ix_analytics_reports_created_by', 'analytics_reports', ['created_by'])
    op.create_index('ix_analytics_reports_is_scheduled', 'analytics_reports', ['is_scheduled'])

    # Create unique constraint for default dashboard per user
    op.create_index(
        'ix_analytics_dashboards_user_default',
        'analytics_dashboards',
        ['created_by'],
        unique=True,
        postgresql_where=sa.text('is_default = true')
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('analytics_reports')
    op.drop_table('analytics_dashboards')
    op.drop_table('quality_scores')
    op.drop_table('quality_metrics')
    op.drop_table('model_predictions')
    op.drop_table('analytics_models')
