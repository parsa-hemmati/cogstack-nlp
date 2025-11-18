"""
Create users table

Revision ID: 001
Revises:
Create Date: 2025-11-18 02:00:00.000000
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
    """
    Create users table with UUID primary key and password hashing support.
    """
    # Create user_role enum type
    op.execute("CREATE TYPE user_role AS ENUM ('clinician', 'researcher', 'admin')")

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('clinician', 'researcher', 'admin', name='user_role'), nullable=False, server_default='clinician'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_break_glass', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create indexes for performance
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])

    # Create unique constraints
    op.create_unique_constraint('uq_users_username', 'users', ['username'])
    op.create_unique_constraint('uq_users_email', 'users', ['email'])


def downgrade() -> None:
    """
    Drop users table and enum type.
    """
    op.drop_table('users')
    op.execute("DROP TYPE user_role")
