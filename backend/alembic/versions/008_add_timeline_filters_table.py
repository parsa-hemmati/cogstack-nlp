"""
Add timeline_filters table

Revision ID: 008
Revises: 007
Create Date: 2025-11-19 07:05:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create timeline_filters table for saving user filter presets."""
    op.create_table(
        'timeline_filters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('filters', postgresql.JSONB(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'name', name='uq_timeline_filters_user_name')
    )

    # Create index on user_id for faster lookups
    op.create_index('idx_timeline_filters_user', 'timeline_filters', ['user_id'])


def downgrade() -> None:
    """Drop timeline_filters table."""
    # Drop index first
    op.drop_index('idx_timeline_filters_user', table_name='timeline_filters')

    # Drop table
    op.drop_table('timeline_filters')
