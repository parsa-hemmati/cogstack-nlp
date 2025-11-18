"""
Create users table

Revision ID: 001
Revises:
Create Date: 2025-11-18 07:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users table for authentication and authorization."""

    # Create role enum
    op.execute("""
        CREATE TYPE userrole AS ENUM (
            'admin',
            'clinician',
            'researcher',
            'auditor'
        )
    """)

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('username', sa.String(length=50), unique=True, nullable=False),
        sa.Column('email', sa.String(length=255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'clinician', 'researcher', 'auditor', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
    )

    # Create indexes for performance
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_role', 'users', ['role'])


def downgrade() -> None:
    """Drop users table."""
    op.drop_table('users')
    op.execute("DROP TYPE userrole")
