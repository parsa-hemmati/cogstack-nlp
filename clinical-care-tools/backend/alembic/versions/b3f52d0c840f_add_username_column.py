"""add_username_column

Revision ID: b3f52d0c840f
Revises: 020
Create Date: 2025-12-07 14:16:40.836868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b3f52d0c840f'
down_revision: Union[str, None] = '020'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table alignment
    # Clean table to allow column changes
    op.execute("TRUNCATE TABLE users CASCADE")

    op.add_column('users', sa.Column('username', sa.String(length=50), nullable=False))
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=False))
    op.add_column('users', sa.Column('can_break_glass', sa.Boolean(), server_default='false', nullable=False))
    
    # Handle Role conversion from Enum to String
    op.alter_column('users', 'role',
               existing_type=postgresql.ENUM('admin', 'clinician', 'researcher', 'auditor', 'viewer', name='userrole'),
               type_=sa.String(length=20),
               existing_nullable=False,
               postgresql_using='role::text')

    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Drop old columns
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'full_name')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'session_token')
    op.drop_column('users', 'is_locked')
    op.drop_column('users', 'last_login')


def downgrade() -> None:
    op.add_column('users', sa.Column('last_login', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('is_locked', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('session_token', sa.VARCHAR(length=500), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('failed_login_attempts', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('full_name', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('hashed_password', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'can_break_glass')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'username')
