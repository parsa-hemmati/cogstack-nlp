"""create modules table

Revision ID: 009_q1r2s3t4u5v6
Revises: 008_j6k7l8m9n0p1
Create Date: 2025-11-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_q1r2s3t4u5v6'
down_revision = '008_j6k7l8m9n0p1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create modules table for dynamic module registry.

    Table Structure:
    - id: UUID primary key
    - name: Module name (unique, indexed, max 100 chars)
    - display_name: Human-readable module name (max 200 chars)
    - description: Module description (max 1000 chars, nullable)
    - version: Module version (max 20 chars, default "1.0.0")
    - enabled: Is module currently active (BOOLEAN, default True)
    - config: Module-specific configuration (JSONB, default {})
    - icon: Vuetify icon name (max 50 chars, nullable)
    - permissions: Required permissions to access module (ARRAY[TEXT], default [])
    - created_at: Module registration timestamp (TIMESTAMP)
    - updated_at: Last configuration update timestamp (TIMESTAMP)

    Constraints:
    - name must be unique

    Indexes:
    - name (unique) for fast module lookup

    Seed Modules:
    - patient-search: Search patients by clinical concepts
    - timeline-view: Visualize patient timeline
    - clinical-decision-support: CDS Hooks integration (disabled by default)
    """
    # Create modules table
    op.create_table(
        'modules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=False, server_default='1.0.0'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('permissions', postgresql.ARRAY(sa.String(length=100)), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create indexes
    op.create_index(
        op.f('ix_modules_name'),
        'modules',
        ['name'],
        unique=True
    )

    # Insert seed modules
    op.execute("""
        INSERT INTO modules (id, name, display_name, description, version, enabled, config, icon, permissions, created_at, updated_at)
        VALUES
        -- 1. Patient Search Module (enabled, Phase 4)
        (
            gen_random_uuid(),
            'patient-search',
            'Patient Search',
            'Search for patients by clinical concepts with meta-annotation filtering',
            '1.0.0',
            true,
            '{"max_results": 100, "default_filters": {"Negation": "Affirmed", "Experiencer": "Patient", "Temporality": "Current"}}'::jsonb,
            'mdi-account-search',
            ARRAY['search_patients', 'view_search_results'],
            NOW(),
            NOW()
        ),
        -- 2. Patient Timeline Module (enabled, Phase 5)
        (
            gen_random_uuid(),
            'timeline-view',
            'Patient Timeline',
            'Visualize patient''s clinical history on an interactive timeline',
            '1.0.0',
            true,
            '{"default_view": "chronological", "show_meta_annotations": true}'::jsonb,
            'mdi-timeline',
            ARRAY['view_patient_timeline', 'view_patient_documents'],
            NOW(),
            NOW()
        ),
        -- 3. Clinical Decision Support Module (disabled, Phase 7)
        (
            gen_random_uuid(),
            'clinical-decision-support',
            'Clinical Decision Support',
            'Integrate with CDS Hooks for clinical alerts and recommendations',
            '1.0.0',
            false,
            '{"cds_hooks_url": null, "enabled_hooks": []}'::jsonb,
            'mdi-lightbulb',
            ARRAY['view_cds_alerts', 'manage_cds_config'],
            NOW(),
            NOW()
        )
    """)


def downgrade() -> None:
    """
    Drop modules table and seed data.
    """
    # Drop indexes first
    op.drop_index(op.f('ix_modules_name'), table_name='modules')

    # Drop modules table (seed data deleted automatically)
    op.drop_table('modules')
