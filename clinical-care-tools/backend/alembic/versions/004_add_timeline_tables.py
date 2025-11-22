"""Add timeline_filters and timeline_exports tables

Revision ID: 004
Revises: 003
Create Date: 2025-11-22

Sprint: Sprint 2 - Timeline View Module
Task: 1.1 - Create Timeline Database Tables
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Create timeline_filters and timeline_exports tables"""

    # Create timeline_filters table
    op.create_table(
        'timeline_filters',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('filters', JSONB, nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),

        # Foreign key constraints
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),

        # Unique constraints
        sa.UniqueConstraint('user_id', 'name', name='timeline_filters_user_name_unique'),

        # Check constraints
        sa.CheckConstraint("LENGTH(name) >= 3", name='timeline_filters_name_min_length')
    )

    # Create indexes for timeline_filters
    op.create_index('idx_timeline_filters_user_id', 'timeline_filters', ['user_id'])
    op.create_index(
        'idx_timeline_filters_one_default_per_user',
        'timeline_filters',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text('is_default = TRUE')
    )

    # Create timeline_exports table
    op.create_table(
        'timeline_exports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True)),
        sa.Column('format', sa.String(10), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='processing'),
        sa.Column('filters', JSONB, nullable=False),
        sa.Column('options', JSONB),
        sa.Column('file_path', sa.String(500)),
        sa.Column('file_size', sa.Integer()),
        sa.Column('content_hash', sa.String(64)),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', TIMESTAMP(timezone=True)),
        sa.Column('error_message', sa.Text()),
        sa.Column('audit_log_id', UUID(as_uuid=True)),

        # Foreign key constraints
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['audit_log_id'], ['audit_logs.id']),

        # Check constraints
        sa.CheckConstraint("format IN ('pdf', 'fhir', 'json')", name='timeline_exports_format_check'),
        sa.CheckConstraint("status IN ('processing', 'completed', 'failed')", name='timeline_exports_status_check')
    )

    # Create indexes for timeline_exports
    op.create_index('idx_timeline_exports_patient_id', 'timeline_exports', ['patient_id'])
    op.create_index('idx_timeline_exports_user_id', 'timeline_exports', ['user_id'])
    op.create_index('idx_timeline_exports_status', 'timeline_exports', ['status'])
    op.create_index('idx_timeline_exports_created_at', 'timeline_exports', [sa.text('created_at DESC')])
    op.create_index('idx_timeline_exports_expires_at', 'timeline_exports', ['expires_at'])

    # Create trigger function for auto-expiry (7 days from creation)
    op.execute("""
        CREATE OR REPLACE FUNCTION set_timeline_export_expiry()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.expires_at IS NULL THEN
                NEW.expires_at := NEW.created_at + INTERVAL '7 days';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger
    op.execute("""
        CREATE TRIGGER timeline_exports_set_expiry
        BEFORE INSERT ON timeline_exports
        FOR EACH ROW
        EXECUTE FUNCTION set_timeline_export_expiry();
    """)


def downgrade():
    """Drop timeline_filters and timeline_exports tables"""

    # Drop trigger and function
    op.execute('DROP TRIGGER IF EXISTS timeline_exports_set_expiry ON timeline_exports')
    op.execute('DROP FUNCTION IF EXISTS set_timeline_export_expiry()')

    # Drop timeline_exports table (cascade will drop indexes)
    op.drop_table('timeline_exports')

    # Drop timeline_filters table (cascade will drop indexes)
    op.drop_table('timeline_filters')
