#!/bin/bash
# Validates CONTEXT.md metrics against actual codebase
# Used by pre-commit hook to prevent metric drift

set -e

echo "🔍 Validating CONTEXT.md metrics..."

# Colors for output
RED='\033[0:31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Vue files count
EXPECTED_VUE=31
ACTUAL_VUE=$(find medcat-trainer/webapp/frontend/src -name "*.vue" 2>/dev/null | wc -l || echo "0")
if [ "$ACTUAL_VUE" -ne "$EXPECTED_VUE" ]; then
    echo -e "${RED}❌ Vue files mismatch: expected $EXPECTED_VUE, found $ACTUAL_VUE${NC}"
    echo "   Run: find medcat-trainer/webapp/frontend/src -name '*.vue' | wc -l"
    echo "   Update CONTEXT.md with actual count"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ Vue files: $ACTUAL_VUE${NC}"
fi

# Migrations count (soft check - migrations can legitimately change)
EXPECTED_MIGRATIONS=94
ACTUAL_MIGRATIONS=$(find medcat-trainer -path "*/migrations/*.py" -name "[0-9]*.py" 2>/dev/null | wc -l || echo "0")
if [ "$ACTUAL_MIGRATIONS" -ne "$EXPECTED_MIGRATIONS" ]; then
    echo -e "${YELLOW}⚠️  Migrations count changed: expected $EXPECTED_MIGRATIONS, found $ACTUAL_MIGRATIONS${NC}"
    echo "   This may be OK if migrations were added/removed intentionally"
    echo "   Update CONTEXT.md if this change is expected"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ Migrations: $ACTUAL_MIGRATIONS${NC}"
fi

# MedCAT v2 Python files
EXPECTED_V2=228
ACTUAL_V2=$(find medcat-v2 -name "*.py" -type f 2>/dev/null | wc -l || echo "0")
if [ "$ACTUAL_V2" -ne "$EXPECTED_V2" ]; then
    echo -e "${YELLOW}⚠️  MedCAT v2 files changed: expected $EXPECTED_V2, found $ACTUAL_V2${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ MedCAT v2 files: $ACTUAL_V2${NC}"
fi

# Trainer backend Python files
EXPECTED_TRAINER=118
ACTUAL_TRAINER=$(find medcat-trainer/webapp/api -name "*.py" -type f 2>/dev/null | wc -l || echo "0")
if [ "$ACTUAL_TRAINER" -ne "$EXPECTED_TRAINER" ]; then
    echo -e "${YELLOW}⚠️  Trainer backend files changed: expected $EXPECTED_TRAINER, found $ACTUAL_TRAINER${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ Trainer backend files: $ACTUAL_TRAINER${NC}"
fi

# Check CONTEXT.md internal consistency for Vue components
if [ -f CONTEXT.md ]; then
    # Extract all "X Vue" patterns and check if consistent
    VUE_REFS=$(grep -o "[0-9]* Vue" CONTEXT.md 2>/dev/null | sort -u | wc -l || echo "1")
    if [ "$VUE_REFS" -gt 1 ]; then
        echo -e "${RED}❌ Internal inconsistency: multiple different Vue counts in CONTEXT.md${NC}"
        grep -n "[0-9]* Vue" CONTEXT.md || true
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✅ Internal consistency: Vue count${NC}"
    fi

    # Check for migration count consistency
    MIG_REFS=$(grep -o "[0-9]* migrations" CONTEXT.md 2>/dev/null | sort -u | wc -l || echo "1")
    if [ "$MIG_REFS" -gt 1 ]; then
        echo -e "${RED}❌ Internal inconsistency: multiple different migration counts in CONTEXT.md${NC}"
        grep -n "[0-9]* migrations" CONTEXT.md || true
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✅ Internal consistency: Migration count${NC}"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Summary
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ Validation FAILED with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Fix errors in CONTEXT.md or verify codebase changes are intentional."
    echo "To bypass this check (not recommended): git commit --no-verify"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Validation completed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Warnings indicate metrics changed - verify this is intentional."
    echo "Update CONTEXT.md to reflect actual codebase state."
    exit 0
else
    echo -e "${GREEN}✅ All validations passed!${NC}"
    exit 0
fi
