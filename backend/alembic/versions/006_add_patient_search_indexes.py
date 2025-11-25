"""
Add patient search indexes

Revision ID: 006
Revises: 005
Create Date: 2025-11-18 11:50:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes for patient search optimization.

    These indexes optimize the following query patterns:
    1. Search by CUI + meta-annotation filters (Negation, Temporality, Experiencer)
    2. Flexible JSON filtering on meta_anns (for additional filters)
    """

    # Composite index for CUI + meta-annotations (most common search pattern)
    # This supports queries like:
    # SELECT * FROM extracted_entities
    # WHERE cui = 'C0004238'
    #   AND meta_anns->>'Negation' = 'Affirmed'
    #   AND meta_anns->>'Temporality' = 'Current'
    #   AND meta_anns->>'Experiencer' = 'Patient'
    op.execute("""
        CREATE INDEX idx_entities_cui_meta
        ON extracted_entities (
            cui,
            (meta_anns->>'Negation'),
            (meta_anns->>'Temporality'),
            (meta_anns->>'Experiencer')
        )
        WHERE cui IS NOT NULL
    """)

    # GIN index for flexible JSON filtering
    # Supports containment queries (@> operator) and existence checks
    # Example: meta_anns @> '{"Negation": "Affirmed"}'::jsonb
    op.create_index(
        'idx_entities_meta_anns_gin',
        'extracted_entities',
        ['meta_anns'],
        postgresql_using='gin'
    )

    # Note: Patient and document lookup indexes already exist from migration 004:
    # - ix_extracted_entities_patient_id
    # - ix_extracted_entities_document_id
    # No need to recreate them


def downgrade() -> None:
    """Remove patient search indexes."""
    op.drop_index('idx_entities_meta_anns_gin', table_name='extracted_entities')
    op.drop_index('idx_entities_cui_meta', table_name='extracted_entities')
