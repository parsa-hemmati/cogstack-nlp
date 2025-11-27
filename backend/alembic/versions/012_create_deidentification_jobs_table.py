"""create deidentification jobs table

Revision ID: 012
Revises: 011
Create Date: 2025-11-22 00:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create deidentification_jobs table for tracking batch de-identification jobs.

    Supports:
    - Job status tracking (pending, processing, completed, failed, cancelled)
    - Progress monitoring (processed_notes, total_notes)
    - Error tracking (error_count)
    - Email notifications (notify_email)
    - Audit trail (user_id, created_at, updated_at, completed_at)
    """
    op.create_table(
        'deidentification_jobs',
        sa.Column('job_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('method', sa.String(20), nullable=False, server_default='removal'),
        sa.Column('total_notes', sa.Integer(), nullable=False),
        sa.Column('processed_notes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notify_email', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    # Index on user_id for querying user's jobs
    op.create_index(
        'ix_deidentification_jobs_user_id',
        'deidentification_jobs',
        ['user_id']
    )

    # Index on status for filtering active jobs
    op.create_index(
        'ix_deidentification_jobs_status',
        'deidentification_jobs',
        ['status']
    )

    # Composite index for user + status queries
    op.create_index(
        'ix_deidentification_jobs_user_status',
        'deidentification_jobs',
        ['user_id', 'status']
    )

    # Index on created_at for ordering
    op.create_index(
        'ix_deidentification_jobs_created_at',
        'deidentification_jobs',
        ['created_at']
    )


def downgrade() -> None:
    """Drop deidentification_jobs table and indexes."""
    op.drop_index('ix_deidentification_jobs_created_at', table_name='deidentification_jobs')
    op.drop_index('ix_deidentification_jobs_user_status', table_name='deidentification_jobs')
    op.drop_index('ix_deidentification_jobs_status', table_name='deidentification_jobs')
    op.drop_index('ix_deidentification_jobs_user_id', table_name='deidentification_jobs')
    op.drop_table('deidentification_jobs')
