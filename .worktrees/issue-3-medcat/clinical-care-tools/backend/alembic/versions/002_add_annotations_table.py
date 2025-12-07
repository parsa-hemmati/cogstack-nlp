"""Add annotations table for NLP-extracted concepts.

Revision ID: 002
Revises: 001
Create Date: 2025-11-18 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema - add annotations table."""
    op.create_table(
        'annotations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False, comment='Foreign key to document'),
        sa.Column('start_char', sa.Integer(), nullable=False, comment='Start character position in document'),
        sa.Column('end_char', sa.Integer(), nullable=False, comment='End character position in document'),
        sa.Column('text', sa.Text(), nullable=False, comment='Actual text span that was annotated'),
        sa.Column('cui', sa.String(length=20), nullable=False, comment='SNOMED-CT/UMLS Concept Unique Identifier'),
        sa.Column('preferred_name', sa.String(length=500), nullable=False, comment='Preferred term for the concept'),
        sa.Column('concept_type', sa.String(length=50), nullable=False, comment='Type: condition, medication, procedure, etc.'),
        sa.Column('negation', sa.String(length=20), nullable=True, comment='Affirmed or Negated'),
        sa.Column('temporality', sa.String(length=20), nullable=True, comment='Current, Past, Future, or Hypothetical'),
        sa.Column('experiencer', sa.String(length=20), nullable=True, comment='Patient, Family, or Other'),
        sa.Column('certainty', sa.String(length=20), nullable=True, comment='Certain or Uncertain'),
        sa.Column('confidence', sa.Float(), nullable=True, comment='MedCAT confidence score (0.0-1.0)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient timeline queries
    op.create_index(op.f('ix_annotations_document_id'), 'annotations', ['document_id'], unique=False)
    op.create_index(op.f('ix_annotations_cui'), 'annotations', ['cui'], unique=False)
    op.create_index(op.f('ix_annotations_concept_type'), 'annotations', ['concept_type'], unique=False)
    op.create_index(op.f('ix_annotations_negation'), 'annotations', ['negation'], unique=False)
    op.create_index(op.f('ix_annotations_temporality'), 'annotations', ['temporality'], unique=False)
    op.create_index(op.f('ix_annotations_experiencer'), 'annotations', ['experiencer'], unique=False)

    # Composite index for timeline queries (CUI + meta-annotations)
    op.create_index(
        'ix_annotations_cui_negation_experiencer',
        'annotations',
        ['cui', 'negation', 'experiencer'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade database schema - remove annotations table."""
    op.drop_index('ix_annotations_cui_negation_experiencer', table_name='annotations')
    op.drop_index(op.f('ix_annotations_experiencer'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_temporality'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_negation'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_concept_type'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_cui'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_document_id'), table_name='annotations')
    op.drop_table('annotations')
