"""
Create documents table

Revision ID: 003
Revises: 002
Create Date: 2025-11-18 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create documents table for encrypted clinical document storage."""
    # Note: SQLAlchemy automatically creates the ENUM type when creating the table
    # with sa.Enum(..., name='processingstatus'). No need to manually create it.

    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False, server_default='application/rtf'),
        sa.Column('content_hash', sa.String(length=64), nullable=False),  # SHA-256 hash (64 hex chars)
        sa.Column('encrypted_content', sa.LargeBinary(), nullable=False),  # BYTEA for encrypted content
        sa.Column('encryption_algorithm', sa.String(length=50), nullable=False, server_default='aes-256-gcm'),
        sa.Column('file_size', sa.BigInteger(), nullable=False),  # Original file size in bytes
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),  # Future: projects table
        # SQLAlchemy will create the 'processingstatus' ENUM type automatically
        sa.Column('processing_status', sa.Enum('pending', 'processing', 'completed', 'failed', name='processingstatus'), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create indexes for performance
    op.create_index('ix_documents_id', 'documents', ['id'])
    op.create_index('ix_documents_filename', 'documents', ['filename'])
    op.create_index('ix_documents_content_hash', 'documents', ['content_hash'], unique=True)  # Deduplication
    op.create_index('ix_documents_uploaded_by', 'documents', ['uploaded_by'])
    op.create_index('ix_documents_processing_status', 'documents', ['processing_status'])
    op.create_index('ix_documents_created_at', 'documents', ['created_at'])

    # Add unique constraint on content_hash for deduplication
    op.create_unique_constraint('uq_documents_content_hash', 'documents', ['content_hash'])


def downgrade() -> None:
    """Drop documents table."""
    # SQLAlchemy automatically drops the ENUM type when dropping the table
    op.drop_table('documents')
