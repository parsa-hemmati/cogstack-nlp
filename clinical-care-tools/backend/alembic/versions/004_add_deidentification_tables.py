"""Add de-identification tables (Sprint 4)

Revision ID: 004
Revises: 003
Create Date: 2025-11-18

Tables:
- deidentified_documents: Stores de-identified document copies
- reidentification_mappings: Encrypted PHI→surrogate mappings
- deidentification_jobs: Batch processing job tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Create de-identification tables"""

    # Enable pgcrypto extension for encryption
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')

    # Table: deidentified_documents
    op.create_table(
        'deidentified_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('original_document_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('redaction_mode', sa.String(20), nullable=False, comment='Redaction mode: mask, surrogate, remove'),
        sa.Column('redacted_text', sa.Text, nullable=False),
        sa.Column('entities_redacted', sa.Integer, nullable=False, default=0),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, index=True),

        # TODO: Add foreign keys when documents and users tables exist
        # sa.ForeignKeyConstraint(['original_document_id'], ['documents.id']),
        # sa.ForeignKeyConstraint(['created_by'], ['users.id'])
    )

    # Indexes for deidentified_documents
    op.create_index('idx_deid_original_doc', 'deidentified_documents', ['original_document_id'])
    op.create_index('idx_deid_created_at', 'deidentified_documents', ['created_at'])

    # Table: reidentification_mappings
    op.create_table(
        'reidentification_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('original_value_encrypted', sa.LargeBinary, nullable=False, comment='Encrypted with pgcrypto'),
        sa.Column('surrogate_value', sa.String(200), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),

        # TODO: Add foreign key when documents table exists
        # sa.ForeignKeyConstraint(['document_id'], ['documents.id'])
    )

    # Indexes for reidentification_mappings
    op.create_index('idx_reid_document', 'reidentification_mappings', ['document_id'])
    op.create_index('idx_reid_surrogate', 'reidentification_mappings', ['surrogate_value'])

    # Encryption/decryption helper functions (using pgcrypto)
    op.execute("""
        CREATE OR REPLACE FUNCTION encrypt_value(plaintext TEXT, key TEXT)
        RETURNS BYTEA AS $$
        BEGIN
            RETURN pgp_sym_encrypt(plaintext, key);
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION decrypt_value(ciphertext BYTEA, key TEXT)
        RETURNS TEXT AS $$
        BEGIN
            RETURN pgp_sym_decrypt(ciphertext, key);
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Table: deidentification_jobs (batch processing)
    op.create_table(
        'deidentification_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('redaction_mode', sa.String(20), nullable=False),
        sa.Column('store_mapping', sa.String(5), nullable=False, default='true'),
        sa.Column('status', sa.String(20), nullable=False, default='pending', index=True,
                  comment='Status: pending, processing, completed, failed'),
        sa.Column('total_documents', sa.Integer, nullable=False),
        sa.Column('processed_documents', sa.Integer, nullable=False, default=0),
        sa.Column('failed_documents', sa.Integer, nullable=False, default=0),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),

        # TODO: Add foreign key when users table exists
        # sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )

    # Indexes for deidentification_jobs
    op.create_index('idx_deid_jobs_user', 'deidentification_jobs', ['user_id'])
    op.create_index('idx_deid_jobs_status', 'deidentification_jobs', ['status'])


def downgrade():
    """Drop de-identification tables"""

    # Drop tables
    op.drop_table('deidentification_jobs')
    op.drop_table('reidentification_mappings')
    op.drop_table('deidentified_documents')

    # Drop encryption functions
    op.execute('DROP FUNCTION IF EXISTS encrypt_value(TEXT, TEXT)')
    op.execute('DROP FUNCTION IF EXISTS decrypt_value(BYTEA, TEXT)')

    # Drop pgcrypto extension (optional - may be used by other features)
    # op.execute('DROP EXTENSION IF EXISTS pgcrypto')
