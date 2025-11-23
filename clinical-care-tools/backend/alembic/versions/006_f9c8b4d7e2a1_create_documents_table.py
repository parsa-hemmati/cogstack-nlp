"""create documents table

Revision ID: 006_f9c8b4d7e2a1
Revises: a3b7c9d4e5f6
Create Date: 2025-11-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_f9c8b4d7e2a1'
down_revision = 'a3b7c9d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create documents table for encrypted clinical document storage.

    Table Structure:
    - id: UUID primary key
    - filename: Original filename (max 255 chars, indexed)
    - content_type: MIME type (max 100 chars)
    - content_hash: SHA-256 hash of original content (64 chars, unique, indexed)
    - encrypted_content: AES-256-GCM encrypted content (BYTEA)
    - encryption_algorithm: Algorithm used (max 50 chars)
    - file_size: Original file size in bytes (INTEGER)
    - uploaded_by: User ID (UUID, foreign key to users)
    - project_id: Project ID (UUID, foreign key to projects with CASCADE DELETE)
    - processing_status: NLP processing status (max 20 chars, indexed)
    - created_at: Upload timestamp (TIMESTAMP, indexed)

    Constraints:
    - content_hash must be unique (prevents duplicate uploads)
    - Foreign key to users.id for uploaded_by
    - Foreign key to projects.id for project_id with CASCADE DELETE

    Indexes:
    - content_hash (unique) for fast duplicate detection
    - filename for file searches
    - uploaded_by for user's documents
    - project_id for project's documents
    - processing_status for filtering by status
    - created_at for chronological queries
    """
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('encrypted_content', sa.LargeBinary(), nullable=False),
        sa.Column('encryption_algorithm', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('processing_status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_hash')
    )

    # Create indexes
    op.create_index(op.f('ix_documents_content_hash'), 'documents', ['content_hash'], unique=True)
    op.create_index(op.f('ix_documents_filename'), 'documents', ['filename'], unique=False)
    op.create_index(op.f('ix_documents_uploaded_by'), 'documents', ['uploaded_by'], unique=False)
    op.create_index(op.f('ix_documents_project_id'), 'documents', ['project_id'], unique=False)
    op.create_index(op.f('ix_documents_processing_status'), 'documents', ['processing_status'], unique=False)
    op.create_index(op.f('ix_documents_created_at'), 'documents', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop documents table and all indexes."""
    op.drop_index(op.f('ix_documents_created_at'), table_name='documents')
    op.drop_index(op.f('ix_documents_processing_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_project_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_uploaded_by'), table_name='documents')
    op.drop_index(op.f('ix_documents_filename'), table_name='documents')
    op.drop_index(op.f('ix_documents_content_hash'), table_name='documents')
    op.drop_table('documents')
