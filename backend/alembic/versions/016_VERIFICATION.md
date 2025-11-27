# Migration 016 Verification

## Overview
This migration creates the `cds_rules` table for storing clinical decision support business rules in IF-THEN format using JSONB for flexible condition/action definitions.

## Table Schema

```sql
CREATE TABLE cds_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,  -- Higher = more urgent
    conditions JSONB NOT NULL,             -- IF conditions (JSON array)
    actions JSONB NOT NULL,                -- THEN actions (JSON array)
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT uq_cds_rules_name UNIQUE (rule_name)
);
```

## Indexes

```sql
-- Query pattern: filter by active rules
CREATE INDEX ix_cds_rules_active ON cds_rules (active);

-- Query pattern: order by priority DESC
CREATE INDEX ix_cds_rules_priority_desc ON cds_rules (priority DESC);
```

## Triggers

```sql
-- Automatically update updated_at timestamp on row modification
CREATE OR REPLACE FUNCTION update_cds_rules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_cds_rules_updated_at
BEFORE UPDATE ON cds_rules
FOR EACH ROW
EXECUTE FUNCTION update_cds_rules_updated_at();
```

## JSONB Structure Examples

### Conditions (IF part)

```json
{
  "conditions": [
    {
      "field": "condition_code",
      "operator": "equals",
      "value": "E11.9"
    },
    {
      "field": "hba1c_value",
      "operator": "greater_than",
      "value": 7.0
    }
  ]
}
```

### Actions (THEN part)

```json
{
  "actions": [
    {
      "type": "recommend_guideline",
      "guideline_id": "ada-diabetes-first-line",
      "message": "Consider metformin as first-line therapy for Type 2 Diabetes"
    },
    {
      "type": "order_lab",
      "test": "HbA1c",
      "frequency": "3 months"
    }
  ]
}
```

## Sample Rule Data

```sql
-- Example: High HbA1c Alert Rule
INSERT INTO cds_rules (
    rule_name,
    description,
    priority,
    conditions,
    actions,
    active
) VALUES (
    'high-hba1c-alert',
    'Alert clinician when HbA1c > 7.0% for diabetic patient',
    10,  -- High priority
    '[
        {"field": "condition_code", "operator": "equals", "value": "E11.9"},
        {"field": "hba1c_value", "operator": "greater_than", "value": 7.0}
    ]'::jsonb,
    '[
        {
            "type": "alert",
            "severity": "warning",
            "message": "HbA1c elevated (>7.0%). Consider medication adjustment."
        },
        {
            "type": "recommend_guideline",
            "guideline_id": "ada-diabetes-glycemic-control"
        }
    ]'::jsonb,
    true
);
```

## Verification Steps

When PostgreSQL is available, verify with:

```sql
-- Verify table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'cds_rules'
);

-- Verify columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'cds_rules'
ORDER BY ordinal_position;

-- Verify indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'cds_rules';

-- Verify trigger exists
SELECT trigger_name, event_manipulation, action_statement
FROM information_schema.triggers
WHERE event_object_table = 'cds_rules';

-- Test JSONB querying
SELECT * FROM cds_rules
WHERE conditions @> '[{"field": "condition_code"}]'::jsonb;

-- Test priority ordering
SELECT rule_name, priority, active
FROM cds_rules
WHERE active = true
ORDER BY priority DESC;
```

## Expected Query Performance

With the indexes in place:

- **Filter by active**: O(log n) - indexed
- **Order by priority DESC**: O(log n) - indexed with DESC operator
- **JSONB containment queries**: O(n) - sequential scan (consider GIN index if needed)
- **Unique rule_name check**: O(1) - hash-based

## JSONB Query Examples

```sql
-- Find rules for specific condition
SELECT * FROM cds_rules
WHERE conditions @> '[{"field": "condition_code", "value": "E11.9"}]'::jsonb
AND active = true
ORDER BY priority DESC;

-- Find rules with specific action type
SELECT * FROM cds_rules
WHERE actions @> '[{"type": "alert"}]'::jsonb
AND active = true;

-- Get highest priority active rules
SELECT rule_name, priority, description
FROM cds_rules
WHERE active = true
ORDER BY priority DESC
LIMIT 10;
```

## Usage Example

```python
from app.models.cds import CDSRule
from sqlalchemy import select

# Query active rules ordered by priority
async def get_active_rules(session):
    query = select(CDSRule).where(
        CDSRule.active == True
    ).order_by(
        CDSRule.priority.desc()
    )

    result = await session.execute(query)
    return result.scalars().all()

# Evaluate rule conditions (using business-rules library)
from business_rules import run_all

def evaluate_rule(rule, patient_data):
    """Evaluate rule conditions against patient data."""
    conditions = rule.conditions  # JSONB deserialized to dict
    actions = rule.actions

    # business-rules library evaluates conditions
    results = run_all(
        rule_list=conditions,
        defined_variables=patient_data,
        defined_actions=actions
    )

    return results
```

## Rollback

To rollback this migration:

```sql
DROP TRIGGER IF EXISTS trigger_update_cds_rules_updated_at ON cds_rules;
DROP FUNCTION IF EXISTS update_cds_rules_updated_at();
DROP TABLE IF EXISTS cds_rules CASCADE;
```

## Migration Status

- ✅ Migration file created: `016_create_cds_rules_table.py`
- ⏳ Migration pending: Run `alembic upgrade head` when PostgreSQL is available
- ⏳ Verification pending: Check table schema, indexes, and trigger in database
