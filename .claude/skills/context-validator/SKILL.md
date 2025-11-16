---
name: context-validator
description: Validates CONTEXT.md accuracy against actual codebase before commits. Use when updating CONTEXT.md, before creating PRs, or periodically to prevent metric drift. Checks Vue component counts, file sizes, migration counts, and internal consistency. Prevents documentation discrepancies like the Nov 2025 incident (65 vs 31 components).
---

# CONTEXT.md Validator

## When to use this skill

Activate when:
- Before committing CONTEXT.md updates
- Creating Pull Requests with CONTEXT.md changes
- Periodic CONTEXT.md audits (monthly recommended)
- After major codebase changes (migrations, new components)
- Discovering discrepancies in documentation

## Critical Metrics to Validate

### 1. Vue Component Count
**What to check**: Total Vue files in MedCAT Trainer

**Command**:
```bash
find medcat-trainer/webapp/frontend/src -name "*.vue" | wc -l
```

**Expected**: 31 Vue files (24 components + 6 views + App.vue)

**Where in CONTEXT.md**:
- Line ~55: Team section "Existing Codebase"
- Line ~70: System Architecture diagram
- Line ~172: MedCAT Trainer Frontend section
- Line ~192: Key Files reference
- Line ~309: Technology Stack table

**Common errors**:
- Overcounting by including node_modules
- Confusing components (24) with total Vue files (31)
- Including deleted/moved files

### 2. Database Migration Count
**What to check**: Django migration files

**Command**:
```bash
find medcat-trainer -path "*/migrations/*.py" -name "[0-9]*.py" | wc -l
```

**Expected**: 94 migrations (as of Nov 2025)

**Where in CONTEXT.md**:
- Line ~72: System Architecture diagram
- Line ~121: Key Architecture Notes
- Line ~185: MedCAT Trainer Database section
- Line ~314: Technology Stack table

**Common errors**:
- Including `__init__.py` in count
- Missing `-name "[0-9]*.py"` filter
- Counting migrations from node_modules or venv

### 3. Large File Sizes
**What to check**: Vue view file line counts

**Commands**:
```bash
wc -l medcat-trainer/webapp/frontend/src/views/TrainAnnotations.vue
wc -l medcat-trainer/webapp/frontend/src/views/Metrics.vue
```

**Expected**:
- TrainAnnotations.vue: ~986 lines
- Metrics.vue: ~771 lines

**Where in CONTEXT.md**:
- Line ~167-168: MedCAT Trainer Frontend section

**Common errors**:
- Using `git show` with wrong commit (historical large versions)
- Confusing character count with line count
- Including generated/compiled code

### 4. Python File Counts
**What to check**: Python files in each component

**Commands**:
```bash
find medcat-v2 -name "*.py" -type f | wc -l                    # Expected: 228
find medcat-trainer/webapp/api -name "*.py" -type f | wc -l    # Expected: 118
```

**Where in CONTEXT.md**:
- Line ~55: Team section
- Line ~143: MedCAT v2 Key Metrics

### 5. Internal Consistency
**What to check**: Same metric appears multiple times with same value

**Examples**:
- "31 Vue files" should appear consistently (not "65" in one place, "31" in another)
- "94 migrations" should be consistent throughout
- File sizes should match across all references

**How to check**:
```bash
# Find all Vue component count references
grep -n "Vue\|components" CONTEXT.md | grep -E "[0-9]+"

# Find all migration count references
grep -n "migration" CONTEXT.md | grep -E "[0-9]+"
```

## Validation Checklist

Before committing CONTEXT.md:

### Automated Checks (run these commands)
```bash
# 1. Vue files count
ACTUAL_VUE=$(find medcat-trainer/webapp/frontend/src -name "*.vue" | wc -l)
echo "Vue files: $ACTUAL_VUE (expected: 31)"

# 2. Migrations count
ACTUAL_MIGRATIONS=$(find medcat-trainer -path "*/migrations/*.py" -name "[0-9]*.py" | wc -l)
echo "Migrations: $ACTUAL_MIGRATIONS (expected: 94)"

# 3. TrainAnnotations.vue size
ACTUAL_TRAIN=$(wc -l medcat-trainer/webapp/frontend/src/views/TrainAnnotations.vue | awk '{print $1}')
echo "TrainAnnotations.vue: $ACTUAL_TRAIN lines (expected: ~986)"

# 4. Metrics.vue size
ACTUAL_METRICS=$(wc -l medcat-trainer/webapp/frontend/src/views/Metrics.vue | awk '{print $1}')
echo "Metrics.vue: $ACTUAL_METRICS lines (expected: ~771)"

# 5. MedCAT v2 files
ACTUAL_V2=$(find medcat-v2 -name "*.py" -type f | wc -l)
echo "MedCAT v2 files: $ACTUAL_V2 (expected: 228)"

# 6. Trainer backend files
ACTUAL_TRAINER=$(find medcat-trainer/webapp/api -name "*.py" -type f | wc -l)
echo "Trainer backend files: $ACTUAL_TRAINER (expected: 118)"
```

### Manual Checks
- [ ] "Last Updated" date is today
- [ ] "Recent Changes" section has new entry
- [ ] All metric references consistent (grep for numbers)
- [ ] No copy-paste errors (same line duplicated)
- [ ] ADRs correctly numbered and linked
- [ ] Internal links work (relative paths)

## Common Discrepancy Patterns

### Pattern 1: Overcounting Components
**Symptom**: "65 Vue components" when actual is 31

**Root cause**:
- Including node_modules in find
- Counting lines instead of files
- Using outdated Explore agent results

**Fix**: Always use explicit paths and verify manually

### Pattern 2: Historical File Sizes
**Symptom**: "34,490 lines" when actual is 986

**Root cause**:
- Looking at wrong git commit
- Confusing character count with line count
- Including multiple files in count

**Fix**: Check current HEAD, use `wc -l` on specific files

### Pattern 3: Off-by-One Migrations
**Symptom**: "95 migrations" when actual is 94

**Root cause**:
- Including `__init__.py` in count
- Counting migration folders instead of files
- Using wrong glob pattern

**Fix**: Use `find` with `-name "[0-9]*.py"` filter

## Automation Script

Create `.git-hooks/validate-context.sh`:

```bash
#!/bin/bash
# Validates CONTEXT.md metrics against actual codebase

set -e

echo "🔍 Validating CONTEXT.md metrics..."

# Vue files
EXPECTED_VUE=31
ACTUAL_VUE=$(find medcat-trainer/webapp/frontend/src -name "*.vue" 2>/dev/null | wc -l || echo "0")
if [ "$ACTUAL_VUE" -ne "$EXPECTED_VUE" ]; then
    echo "❌ Vue files mismatch: expected $EXPECTED_VUE, found $ACTUAL_VUE"
    echo "   Update CONTEXT.md or investigate codebase changes"
    exit 1
fi

# Migrations
EXPECTED_MIGRATIONS=94
ACTUAL_MIGRATIONS=$(find medcat-trainer -path "*/migrations/*.py" -name "[0-9]*.py" 2>/dev/null | wc -l || echo "0")
if [ "$ACTUAL_MIGRATIONS" -ne "$EXPECTED_MIGRATIONS" ]; then
    echo "⚠️  Migrations count changed: expected $EXPECTED_MIGRATIONS, found $ACTUAL_MIGRATIONS"
    echo "   This may be OK if migrations were added. Update CONTEXT.md if intentional."
    # Don't exit - migrations can legitimately change
fi

# Check CONTEXT.md internal consistency
INCONSISTENT=$(grep -o "[0-9]* Vue" CONTEXT.md | sort -u | wc -l)
if [ "$INCONSISTENT" -gt 1 ]; then
    echo "❌ Internal inconsistency detected in CONTEXT.md"
    grep -n "[0-9]* Vue" CONTEXT.md
    exit 1
fi

echo "✅ CONTEXT.md validation passed"
```

## Integration with Pre-Commit Hook

Add to `.git-hooks/pre-commit`:

```bash
# Check if CONTEXT.md is being committed
if git diff --cached --name-only | grep -q "CONTEXT.md"; then
    # Run validation
    if [ -f .git-hooks/validate-context.sh ]; then
        bash .git-hooks/validate-context.sh || {
            echo ""
            echo "CONTEXT.md validation failed. Fix issues or skip with --no-verify"
            exit 1
        }
    fi
fi
```

## When Metrics Should Change

**Legitimate changes**:
- ✅ New migrations added → update migration count
- ✅ New Vue components created → update component count
- ✅ Files refactored/split → update file counts
- ✅ Documentation improvements → update "Last Updated"

**Red flags**:
- ❌ Metrics change without corresponding code changes
- ❌ Large jumps in metrics (65 to 31 suggests error)
- ❌ Historical metrics don't match git history
- ❌ Internal inconsistencies (different values for same metric)

## Historical Incident: Nov 2025 Discrepancy

**What happened**:
- CONTEXT.md claimed "65 Vue components", "34,490 line files", "25,991 line files", "95 migrations"
- Actual counts: 31 Vue files, 986 lines, 771 lines, 94 migrations
- Root cause: November 7th Explore agent incorrectly counted metrics
- Discovery: Manual verification during session review

**Prevention**:
- ✅ Use this skill before committing CONTEXT.md
- ✅ Run validation script in pre-commit hook
- ✅ Periodic audits (monthly)
- ✅ Verify Explore agent outputs with manual commands

## References

- CONTEXT.md: Living project documentation
- Git hooks: `.git-hooks/pre-commit`, `.git-hooks/commit-msg`
- Validation script: `.git-hooks/validate-context.sh` (to be created)
