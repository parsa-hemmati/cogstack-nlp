"""
Add search tables (saved_searches, search_analytics) and document indexing columns

Revision ID: 011
Revises: 010
Create Date: 2025-11-19 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create saved_searches and search_analytics tables for Sprint 3.
    Add indexing tracking columns to documents table.
    """

    # =========================================================================
    # Table 1: saved_searches - User-defined reusable search queries
    # =========================================================================
    op.create_table(
        'saved_searches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),  # Full-text search query string
        sa.Column('filters', postgresql.JSONB(), nullable=True),  # Meta-annotation filters, date ranges, etc.
        sa.Column('is_shared', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('execution_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Indexes for saved_searches
    op.create_index('ix_saved_searches_id', 'saved_searches', ['id'])
    op.create_index('ix_saved_searches_user_id', 'saved_searches', ['user_id'])
    op.create_index('ix_saved_searches_created_at', 'saved_searches', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('ix_saved_searches_is_shared', 'saved_searches', ['is_shared'])

    # Unique constraint: user cannot have duplicate search names
    op.create_unique_constraint('uq_saved_searches_user_name', 'saved_searches', ['user_id', 'name'])

    # =========================================================================
    # Table 2: search_analytics - Query performance and user behavior tracking
    # =========================================================================
    op.create_table(
        'search_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),  # Raw search query
        sa.Column('filters', postgresql.JSONB(), nullable=True),  # Applied filters
        sa.Column('results_count', sa.Integer(), nullable=False),  # Number of results returned
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),  # Query execution time in milliseconds
        sa.Column('clicked_documents', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),  # Document IDs user clicked
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Indexes for search_analytics
    op.create_index('ix_search_analytics_id', 'search_analytics', ['id'])
    op.create_index('ix_search_analytics_user_id', 'search_analytics', ['user_id'])
    op.create_index('ix_search_analytics_created_at', 'search_analytics', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('ix_search_analytics_results_count', 'search_analytics', ['results_count'])

    # GIN index for full-text search on query field (for query autocomplete/suggestions)
    op.execute("""
        CREATE INDEX ix_search_analytics_query_gin
        ON search_analytics
        USING gin(to_tsvector('english', query))
    """)

    # =========================================================================
    # Table 3: documents - Add Elasticsearch indexing tracking columns
    # =========================================================================
    op.add_column('documents', sa.Column('indexed', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('documents', sa.Column('last_indexed_at', sa.DateTime(), nullable=True))

    # Index for finding documents needing indexing
    op.create_index('ix_documents_indexed', 'documents', ['indexed'])
    op.create_index('ix_documents_last_indexed_at', 'documents', ['last_indexed_at'])


def downgrade() -> None:
    """
    Drop search tables and document indexing columns.
    """

    # Drop columns from documents table
    op.drop_index('ix_documents_last_indexed_at', table_name='documents')
    op.drop_index('ix_documents_indexed', table_name='documents')
    op.drop_column('documents', 'last_indexed_at')
    op.drop_column('documents', 'indexed')

    # Drop search_analytics table (indexes dropped automatically)
    op.drop_table('search_analytics')

    # Drop saved_searches table (indexes dropped automatically)
    op.drop_table('saved_searches')
