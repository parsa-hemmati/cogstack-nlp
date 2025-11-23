"""create extracted_entities table

Revision ID: 007_e1f2g3h4i5j6
Revises: 006_f9c8b4d7e2a1
Create Date: 2025-11-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_e1f2g3h4i5j6'
down_revision = '006_f9c8b4d7e2a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create extracted_entities table for storing PHI and clinical entities.

    Table Structure:
    - id: UUID primary key
    - document_id: Document ID (UUID, foreign key to documents with CASCADE DELETE)
    - patient_id: Patient ID (UUID, nullable, indexed) - FK added in later migration
    - entity_type: Type of entity (PHI or clinical, max 20 chars, indexed)
    - cui: Concept Unique Identifier (max 100 chars, indexed)
    - pretty_name: Human-readable entity text (max 500 chars)
    - start_char: Character position in document (start)
    - end_char: Character position in document (end)
    - accuracy: Model confidence score (FLOAT, 0.0-1.0)
    - meta_anns: Meta-annotations as JSONB (Negation, Temporality, etc.)
    - created_at: Extraction timestamp (TIMESTAMP)

    Constraints:
    - Foreign key to documents.id with CASCADE DELETE
    - patient_id foreign key will be added in later migration (after patients table created)

    Indexes:
    - document_id for retrieving all entities from a document
    - patient_id for retrieving all entities for a patient
    - entity_type for filtering PHI vs clinical entities
    - cui for searching by concept identifier
    """
    op.create_table(
        'extracted_entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('entity_type', sa.String(length=20), nullable=False),
        sa.Column('cui', sa.String(length=100), nullable=False),
        sa.Column('pretty_name', sa.String(length=500), nullable=False),
        sa.Column('start_char', sa.Integer(), nullable=False),
        sa.Column('end_char', sa.Integer(), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=False),
        sa.Column('meta_anns', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['document_id'],
            ['documents.id'],
            ondelete='CASCADE'
        ),
        # Note: patient_id FK will be added in later migration after patients table created
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(
        op.f('ix_extracted_entities_document_id'),
        'extracted_entities',
        ['document_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_extracted_entities_patient_id'),
        'extracted_entities',
        ['patient_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_extracted_entities_entity_type'),
        'extracted_entities',
        ['entity_type'],
        unique=False
    )
    op.create_index(
        op.f('ix_extracted_entities_cui'),
        'extracted_entities',
        ['cui'],
        unique=False
    )


def downgrade() -> None:
    """Drop extracted_entities table and all indexes."""
    op.drop_index(op.f('ix_extracted_entities_cui'), table_name='extracted_entities')
    op.drop_index(op.f('ix_extracted_entities_entity_type'), table_name='extracted_entities')
    op.drop_index(op.f('ix_extracted_entities_patient_id'), table_name='extracted_entities')
    op.drop_index(op.f('ix_extracted_entities_document_id'), table_name='extracted_entities')
    op.drop_table('extracted_entities')
