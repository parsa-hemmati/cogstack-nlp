"""
Create extracted_entities table

Revision ID: 004
Revises: 003
Create Date: 2025-11-18 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create extracted_entities table for PHI and clinical entities."""
    # Create entitytype enum
    op.execute("""
        CREATE TYPE entitytype AS ENUM (
            'clinical',
            'phi_name',
            'phi_nhs_number',
            'phi_dob',
            'phi_address'
        )
    """)

    op.create_table(
        'extracted_entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),  # Future FK to patients
        sa.Column('entity_type', sa.Enum('clinical', 'phi_name', 'phi_nhs_number', 'phi_dob', 'phi_address', name='entitytype'), nullable=False),
        sa.Column('cui', sa.String(length=20), nullable=True),  # SNOMED-CT or UMLS CUI
        sa.Column('pretty_name', sa.String(length=500), nullable=False),
        sa.Column('start_char', sa.Integer(), nullable=False),
        sa.Column('end_char', sa.Integer(), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=True),  # MedCAT confidence
        sa.Column('meta_anns', postgresql.JSONB, nullable=True),  # Meta-annotations
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create indexes for performance
    op.create_index('ix_extracted_entities_id', 'extracted_entities', ['id'])
    op.create_index('ix_extracted_entities_document_id', 'extracted_entities', ['document_id'])
    op.create_index('ix_extracted_entities_patient_id', 'extracted_entities', ['patient_id'])
    op.create_index('ix_extracted_entities_entity_type', 'extracted_entities', ['entity_type'])
    op.create_index('ix_extracted_entities_cui', 'extracted_entities', ['cui'])

    # Composite index for common query: get entities for document by type
    op.create_index('ix_extracted_entities_doc_type', 'extracted_entities', ['document_id', 'entity_type'])


def downgrade() -> None:
    """Drop extracted_entities table."""
    op.drop_table('extracted_entities')
    op.execute("DROP TYPE entitytype")
