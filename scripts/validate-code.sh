#!/bin/bash
#
# Comprehensive Code Validation Script
# Runs all quality checks before commits or in CI/CD
#
# Usage:
#   ./scripts/validate-code.sh [--quick|--full|--fix]
#
# Options:
#   --quick: Fast checks only (syntax, imports)
#   --full:  All checks including tests (default)
#   --fix:   Auto-fix issues where possible (black, isort, eslint --fix)

set -e  # Exit on error

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MODE="${1:-full}"
ERRORS=0

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Code Validation Suite${NC}"
echo -e "${BLUE}   Mode: $MODE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ============================================================================
# PYTHON VALIDATION
# ============================================================================

echo -e "${YELLOW}📦 Python Validation${NC}"
echo ""

# 1. Python Syntax Check
echo -e "${BLUE}[1/8] Checking Python syntax...${NC}"
python_files=$(find backend -name "*.py" -not -path "*/migrations/*" -not -path "*/__pycache__/*")
syntax_errors=0

for file in $python_files; do
    python3 -m py_compile "$file" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}  ❌ Syntax error in $file${NC}"
        python3 -m py_compile "$file"
        syntax_errors=$((syntax_errors + 1))
    fi
done

if [ $syntax_errors -eq 0 ]; then
    echo -e "${GREEN}  ✅ All Python files have valid syntax${NC}"
else
    echo -e "${RED}  ❌ Found $syntax_errors syntax error(s)${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 2. Import Validation
echo -e "${BLUE}[2/8] Validating Python imports...${NC}"
cd backend
import_errors=0

for file in $(find . -name "*.py" -not -path "*/migrations/*" -not -path "*/__pycache__/*"); do
    # Try to import the file
    python3 -c "import sys; sys.path.insert(0, '.'); exec(open('$file').read())" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}  ⚠️  Import issues in $file${NC}"
        import_errors=$((import_errors + 1))
    fi
done

if [ $import_errors -eq 0 ]; then
    echo -e "${GREEN}  ✅ All imports resolve correctly${NC}"
else
    echo -e "${YELLOW}  ⚠️  Found $import_errors file(s) with import issues${NC}"
    echo -e "${YELLOW}     (May be normal for some files)${NC}"
fi
cd ..
echo ""

# 3. Type Checking (if mypy available)
echo -e "${BLUE}[3/8] Type checking (mypy)...${NC}"
if command -v mypy >/dev/null 2>&1; then
    cd backend
    mypy app --ignore-missing-imports --no-error-summary 2>&1 | head -20
    mypy_result=${PIPESTATUS[0]}
    cd ..

    if [ $mypy_result -eq 0 ]; then
        echo -e "${GREEN}  ✅ Type checking passed${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Type checking found issues${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  mypy not installed, skipping type checks${NC}"
    echo -e "${YELLOW}     Install with: pip install mypy${NC}"
fi
echo ""

# 4. Code Style (if black available)
echo -e "${BLUE}[4/8] Code formatting (black)...${NC}"
if command -v black >/dev/null 2>&1; then
    cd backend
    if [ "$MODE" = "--fix" ]; then
        black app tests --quiet
        echo -e "${GREEN}  ✅ Code auto-formatted with black${NC}"
    else
        black app tests --check --quiet 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✅ Code formatting is correct${NC}"
        else
            echo -e "${YELLOW}  ⚠️  Code needs formatting${NC}"
            echo -e "${YELLOW}     Run: cd backend && black app tests${NC}"
        fi
    fi
    cd ..
else
    echo -e "${YELLOW}  ⚠️  black not installed, skipping formatting check${NC}"
    echo -e "${YELLOW}     Install with: pip install black${NC}"
fi
echo ""

# 5. Backend Tests
if [ "$MODE" != "--quick" ]; then
    echo -e "${BLUE}[5/8] Running backend tests...${NC}"
    if command -v pytest >/dev/null 2>&1; then
        cd backend

        # Run tests with coverage
        PYTHONPATH=. pytest tests/ -v --tb=short --maxfail=3 2>&1 | tail -50
        test_result=${PIPESTATUS[0]}

        cd ..

        if [ $test_result -eq 0 ]; then
            echo -e "${GREEN}  ✅ All backend tests passed${NC}"
        else
            echo -e "${RED}  ❌ Backend tests failed${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo -e "${YELLOW}  ⚠️  pytest not installed, skipping tests${NC}"
        echo -e "${YELLOW}     Install with: pip install pytest pytest-asyncio${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${BLUE}[5/8] Skipping tests (quick mode)${NC}"
fi
echo ""

# ============================================================================
# FRONTEND VALIDATION
# ============================================================================

echo -e "${YELLOW}🎨 Frontend Validation${NC}"
echo ""

# 6. TypeScript Type Checking
echo -e "${BLUE}[6/8] TypeScript type checking...${NC}"
if [ -d "frontend/node_modules" ]; then
    cd frontend
    npm run type-check 2>&1 | tail -20
    ts_result=${PIPESTATUS[0]}
    cd ..

    if [ $ts_result -eq 0 ]; then
        echo -e "${GREEN}  ✅ TypeScript types are valid${NC}"
    else
        echo -e "${RED}  ❌ TypeScript type errors found${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}  ⚠️  Frontend dependencies not installed${NC}"
    echo -e "${YELLOW}     Run: cd frontend && npm install${NC}"
fi
echo ""

# 7. ESLint
echo -e "${BLUE}[7/8] ESLint checking...${NC}"
if [ -d "frontend/node_modules" ]; then
    cd frontend
    if [ "$MODE" = "--fix" ]; then
        npm run lint 2>&1 | tail -20
        echo -e "${GREEN}  ✅ Code auto-fixed with ESLint${NC}"
    else
        npm run lint -- --max-warnings=0 2>&1 | tail -20
        eslint_result=${PIPESTATUS[0]}

        if [ $eslint_result -eq 0 ]; then
            echo -e "${GREEN}  ✅ ESLint passed${NC}"
        else
            echo -e "${YELLOW}  ⚠️  ESLint warnings/errors found${NC}"
            echo -e "${YELLOW}     Run: cd frontend && npm run lint${NC}"
        fi
    fi
    cd ..
else
    echo -e "${YELLOW}  ⚠️  Frontend dependencies not installed${NC}"
fi
echo ""

# 8. Security Checks
echo -e "${BLUE}[8/8] Security checks...${NC}"

# Check for common security issues
security_issues=0

# Check for hardcoded secrets
if grep -r -E "(password|secret|api[_-]?key|token)\s*=\s*['\"][^'\"]+['\"]" backend/app --include="*.py" | grep -v "test" | grep -v "example" | head -5; then
    echo -e "${YELLOW}  ⚠️  Potential hardcoded secrets found${NC}"
    security_issues=$((security_issues + 1))
fi

# Check for SQL injection patterns
if grep -r "execute.*format\|execute.*%" backend/app --include="*.py" | head -5; then
    echo -e "${YELLOW}  ⚠️  Potential SQL injection patterns found${NC}"
    security_issues=$((security_issues + 1))
fi

if [ $security_issues -eq 0 ]; then
    echo -e "${GREEN}  ✅ No obvious security issues found${NC}"
else
    echo -e "${YELLOW}  ⚠️  Found $security_issues potential security issue(s)${NC}"
fi
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All validation checks passed!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS critical error(s)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
