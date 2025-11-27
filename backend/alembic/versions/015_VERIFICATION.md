# Migration 015 Verification

## Overview
This migration creates the `cds_guidelines` table for storing clinical decision support guidelines from multiple authoritative sources.

## Table Schema

```sql
CREATE TABLE cds_guidelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guideline_source VARCHAR(50) NOT NULL,  -- 'ADA', 'AHA', 'USPSTF', 'NICE'
    guideline_name VARCHAR(255) NOT NULL,
    condition_code VARCHAR(50) NOT NULL,    -- ICD-10 or SNOMED CT code
    recommendation TEXT NOT NULL,
    evidence_level VARCHAR(10) NOT NULL,    -- 'A', 'B', 'C'
    rationale TEXT NOT NULL,
    last_updated TIMESTAMPTZ NOT NULL,      -- Date guideline updated by source
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT uq_cds_guidelines_source_name_condition
        UNIQUE (guideline_source, guideline_name, condition_code)
);
```

## Indexes

```sql
-- Primary query pattern: lookup by condition code
CREATE INDEX ix_cds_guidelines_condition_code ON cds_guidelines (condition_code);

-- Additional query patterns
CREATE INDEX ix_cds_guidelines_source ON cds_guidelines (guideline_source);
CREATE INDEX ix_cds_guidelines_evidence_level ON cds_guidelines (evidence_level);
```

## Check Constraints

```sql
-- Validate guideline source
ALTER TABLE cds_guidelines
    ADD CONSTRAINT ck_cds_guidelines_source
    CHECK (guideline_source IN ('ADA', 'AHA', 'USPSTF', 'NICE'));

-- Validate evidence level
ALTER TABLE cds_guidelines
    ADD CONSTRAINT ck_cds_guidelines_evidence_level
    CHECK (evidence_level IN ('A', 'B', 'C'));
```

## Sample Data

```sql
-- Example guideline for Type 2 Diabetes
INSERT INTO cds_guidelines (
    guideline_source,
    guideline_name,
    condition_code,
    recommendation,
    evidence_level,
    rationale,
    last_updated
) VALUES (
    'ADA',
    'Type 2 Diabetes First-Line Therapy',
    'E11.9',  -- ICD-10 for Type 2 diabetes without complications
    'Metformin is recommended as first-line pharmacologic therapy for type 2 diabetes, along with lifestyle modifications (nutrition therapy and physical activity).',
    'A',
    'Metformin has proven efficacy in reducing HbA1c, minimal risk of hypoglycemia, favorable effects on weight, low cost, and long-term safety data. Multiple RCTs and meta-analyses support its use as first-line therapy.',
    '2024-01-15'
);
```

## Verification Steps

When PostgreSQL is available, verify with:

```sql
-- Verify table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'cds_guidelines'
);

-- Verify columns
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_name = 'cds_guidelines'
ORDER BY ordinal_position;

-- Verify indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'cds_guidelines';

-- Verify constraints
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'cds_guidelines'::regclass;
```

## Expected Query Performance

With the indexes in place:

- **Lookup by condition_code** (primary use case): O(log n) - indexed
- **Filter by guideline_source**: O(log n) - indexed
- **Filter by evidence_level**: O(log n) - indexed
- **Unique constraint check**: O(1) - hash-based

## Usage Example

```python
from app.models.cds import CDSGuideline
from sqlalchemy import select

# Query guidelines for a patient with Type 2 Diabetes (ICD-10: E11.9)
async def get_guidelines_for_condition(condition_code: str, session):
    query = select(CDSGuideline).where(
        CDSGuideline.condition_code == condition_code
    ).order_by(
        CDSGuideline.evidence_level  # A first, then B, then C
    )

    result = await session.execute(query)
    return result.scalars().all()
```

## Rollback

To rollback this migration:

```sql
DROP TABLE IF EXISTS cds_guidelines CASCADE;
```

## Migration Status

- ✅ Migration file created: `015_create_cds_guidelines_table.py`
- ⏳ Migration pending: Run `alembic upgrade head` when PostgreSQL is available
- ⏳ Verification pending: Check table schema and constraints in database
