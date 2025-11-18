"""
Create audit_logs table

Revision ID: 002
Revises: 001
Create Date: 2025-11-18 08:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audit_logs table for HIPAA compliance."""
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('details', postgresql.JSONB, nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.String(length=10), nullable=False, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
    )

    # Create indexes for performance
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])

    # Composite indexes for common queries
    op.create_index('ix_audit_user_timestamp', 'audit_logs', ['user_id', 'timestamp'])
    op.create_index('ix_audit_action_timestamp', 'audit_logs', ['action', 'timestamp'])
    op.create_index('ix_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])


def downgrade() -> None:
    """Drop audit_logs table."""
    op.drop_table('audit_logs')
