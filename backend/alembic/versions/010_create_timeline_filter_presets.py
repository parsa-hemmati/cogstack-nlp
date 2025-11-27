"""create timeline filter presets table

Revision ID: 010
Revises: 009
Create Date: 2025-11-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    """Create timeline_filter_presets table for saved filter configurations."""
    op.create_table(
        'timeline_filter_presets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, comment='Preset name (e.g., "Diabetes Management")'),
        sa.Column('filters', JSONB, nullable=False, comment='Serialized TimelineFilterRequest'),
        sa.Column('is_default', sa.Boolean, default=False, nullable=False, comment='Default preset for user'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Indexes
    op.create_index(
        'idx_timeline_filter_presets_user_id',
        'timeline_filter_presets',
        ['user_id']
    )

    # Unique constraint: user_id + name (user can't have duplicate preset names)
    op.create_index(
        'idx_timeline_filter_presets_user_name',
        'timeline_filter_presets',
        ['user_id', 'name'],
        unique=True
    )

    # Index on is_default for quick lookup of default preset
    op.create_index(
        'idx_timeline_filter_presets_user_default',
        'timeline_filter_presets',
        ['user_id', 'is_default']
    )


def downgrade():
    """Drop timeline_filter_presets table."""
    op.drop_index('idx_timeline_filter_presets_user_default', table_name='timeline_filter_presets')
    op.drop_index('idx_timeline_filter_presets_user_name', table_name='timeline_filter_presets')
    op.drop_index('idx_timeline_filter_presets_user_id', table_name='timeline_filter_presets')
    op.drop_table('timeline_filter_presets')
