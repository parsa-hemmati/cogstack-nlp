"""add certainty to search index

Revision ID: 007
Revises: 006
Create Date: 2025-11-18 14:30:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add Certainty to composite index for patient search optimization.

    Replaces the 3-field composite index with a 4-field index including Certainty.
    This improves query performance when filtering by all 4 meta-annotations.
    """
    # Drop the old 3-field composite index
    op.execute(
        """
        DROP INDEX IF EXISTS ix_extracted_entities_cui_meta_anns;
        """
    )

    # Create new 4-field composite index with Certainty
    op.execute(
        """
        CREATE INDEX ix_extracted_entities_cui_meta_anns_with_certainty
        ON extracted_entities (
            cui,
            (meta_anns->>'Negation'),
            (meta_anns->>'Temporality'),
            (meta_anns->>'Experiencer'),
            (meta_anns->>'Certainty')
        );
        """
    )


def downgrade() -> None:
    """
    Revert to 3-field composite index without Certainty.
    """
    # Drop the 4-field composite index
    op.execute(
        """
        DROP INDEX IF EXISTS ix_extracted_entities_cui_meta_anns_with_certainty;
        """
    )

    # Restore old 3-field composite index
    op.execute(
        """
        CREATE INDEX ix_extracted_entities_cui_meta_anns
        ON extracted_entities (
            cui,
            (meta_anns->>'Negation'),
            (meta_anns->>'Temporality'),
            (meta_anns->>'Experiencer')
        );
        """
    )
