"""create audit_logs table

Revision ID: eb6526cf211a
Revises: 58fbf7d3fdf2
Create Date: 2025-11-22 23:57:44.868610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = 'eb6526cf211a'
down_revision: Union[str, None] = '58fbf7d3fdf2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create audit_logs table with immutability rules.

    Implements HIPAA-compliant audit logging:
    - Captures WHO/WHAT/WHEN/WHERE for all actions
    - JSONB details for flexible context
    - PostgreSQL rules prevent UPDATE/DELETE (immutability)
    """
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=False),
        sa.Column('details', JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_username'), 'audit_logs', ['username'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_id'), 'audit_logs', ['resource_id'], unique=False)

    # Compound index for resource lookups (type + id)
    op.create_index(
        'ix_audit_logs_resource',
        'audit_logs',
        ['resource_type', 'resource_id'],
        unique=False
    )

    # Create PostgreSQL rules to enforce immutability
    # Block UPDATE operations
    op.execute("""
        CREATE RULE audit_logs_no_update AS
        ON UPDATE TO audit_logs
        DO INSTEAD NOTHING;
    """)

    # Block DELETE operations
    op.execute("""
        CREATE RULE audit_logs_no_delete AS
        ON DELETE TO audit_logs
        DO INSTEAD NOTHING;
    """)


def downgrade() -> None:
    """Drop audit_logs table and immutability rules."""
    # Drop PostgreSQL rules first
    op.execute("DROP RULE IF EXISTS audit_logs_no_delete ON audit_logs;")
    op.execute("DROP RULE IF EXISTS audit_logs_no_update ON audit_logs;")

    # Drop indexes
    op.drop_index('ix_audit_logs_resource', table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_username'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')

    # Drop table
    op.drop_table('audit_logs')
