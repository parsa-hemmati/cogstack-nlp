"""fix_audit_logs

Revision ID: 022
Revises: b3f52d0c840f
Create Date: 2025-12-07 14:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '022'
down_revision: Union[str, None] = 'b3f52d0c840f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix Audit Logs Schema to match Model
    
    # 1. Add username column
    op.add_column('audit_logs', sa.Column('username', sa.String(length=50), nullable=True))
    op.execute("UPDATE audit_logs SET username = 'unknown' WHERE username IS NULL")
    op.alter_column('audit_logs', 'username', nullable=False)
    
    # 2. Rename created_at -> timestamp
    op.alter_column('audit_logs', 'created_at', new_column_name='timestamp')
    
    # 3. Alter user_id to String(255)
    # Note: user_id foreign key constraint might block type change if it refers to users.id (UUID).
    # Model says user_id is String. But logic uses User.id (UUID).
    # If we change it to String, we break specific FK type if strictly typed?
    # But usually FK needs same type.
    # users.id IS UUID.
    # audit_logs.user_id FK -> users.id.
    # If I change audit_logs.user_id to String, I must DROP FK.
    # AuditLog model does NOT define ForeignKey explicitly in snippet above?
    # Snippet: `user_id = Column(String(255)...)`
    # It does NOT have ForeignKey(...).
    # Schema 001 did: `sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')`.
    # Autogen recommended: `op.drop_constraint('audit_logs_user_id_fkey', 'audit_logs', type_='foreignkey')`.
    # So Code does NOT want FK. Code treats it as plain string.
    
    op.drop_constraint('audit_logs_user_id_fkey', 'audit_logs', type_='foreignkey')
    
    op.alter_column('audit_logs', 'user_id', 
               existing_type=sa.UUID(),
               type_=sa.String(255),
               postgresql_using='user_id::text') # Cast UUID to text
               
    # 4. Alter resource_type/id
    op.alter_column('audit_logs', 'resource_type', 
               existing_type=sa.String(100), 
               type_=sa.String(50))
               
    op.alter_column('audit_logs', 'resource_id', 
               existing_type=sa.String(100), 
               type_=sa.String(255))
               
    # 5. Details to JSONB
    op.alter_column('audit_logs', 'details',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               postgresql_using='details::jsonb')

    # Indices
    # op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    # index rename ix_audit_logs_created_at -> ix_audit_logs_timestamp?
    # If I rename column, index follows? No, typically index name remains unless renamed.
    # I'll drop old index and create new one.
    
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    
    op.create_index(op.f('ix_audit_logs_username'), 'audit_logs', ['username'], unique=False)


def downgrade() -> None:
    pass # Irreversible changes (type casts) not easily reverted without data loss or complexity.
