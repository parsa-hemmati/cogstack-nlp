"""Add search_analytics table for search query tracking.

Revision ID: 003
Revises: 002
Create Date: 2025-11-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create search_analytics table."""
    op.create_table(
        'search_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('query', sa.Text, nullable=False),
        sa.Column('filters', postgresql.JSONB, nullable=True),
        sa.Column('total_results', sa.Integer, nullable=False),
        sa.Column('page', sa.Integer, nullable=False, server_default='1'),
        sa.Column('execution_time_ms', sa.Integer, nullable=True),
        sa.Column('clicked_result_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('clicked_result_rank', sa.Integer, nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )

    # Create indexes for efficient querying
    op.create_index('idx_search_analytics_user_id', 'search_analytics', ['user_id'])
    op.create_index('idx_search_analytics_created_at', 'search_analytics', ['created_at'])

    # GIN index for full-text search on query field
    op.execute("CREATE INDEX idx_search_analytics_query ON search_analytics USING gin(to_tsvector('english', query))")


def downgrade() -> None:
    """Drop search_analytics table."""
    op.drop_index('idx_search_analytics_query')
    op.drop_index('idx_search_analytics_created_at')
    op.drop_index('idx_search_analytics_user_id')
    op.drop_table('search_analytics')
