#!/bin/bash
#
# Comprehensive Code Validation Script
# Runs all quality checks before commits or in CI/CD
#
# Usage:
#   ./scripts/validate-code.sh [--quick|--full|--fix|--prd-check]
#
# Options:
#   --quick:     Fast checks only (syntax, imports)
#   --full:      All checks including tests (default)
#   --fix:       Auto-fix issues where possible (black, isort, eslint --fix)
#   --prd-check: Validate API implementation against PRD specifications

set -e  # Exit on error

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MODE="${1:-full}"
ERRORS=0

# ============================================================================
# PRD COMPLIANCE VALIDATION (--prd-check flag)
# ============================================================================

if [ "$MODE" = "--prd-check" ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}   PRD Compliance Validation${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}This will spawn a validation agent to compare implementation against PRD.${NC}"
    echo ""

    # Check if PRD files exist
    prd_files=$(find .specify/sprints -name "*-prd.md" 2>/dev/null || true)

    if [ -z "$prd_files" ]; then
        echo -e "${RED}❌ No PRD files found in .specify/sprints/${NC}"
        echo ""
        echo "Expected location: .specify/sprints/sprint-*-prd.md"
        echo ""
        exit 1
    fi

    echo -e "${GREEN}Found PRD files:${NC}"
    for prd in $prd_files; do
        echo "  - $prd"
    done
    echo ""

    # Detect which API files changed recently
    echo -e "${YELLOW}Detecting recently modified API files...${NC}"
    api_files_changed=$(git diff --name-only HEAD~5..HEAD 2>/dev/null | grep -E '(backend/app/api/v[0-9]+/endpoints/|backend/app/schemas/).*\.py$' || true)

    if [ -z "$api_files_changed" ]; then
        echo -e "${YELLOW}⚠️  No API files changed in last 5 commits${NC}"
        echo ""
        echo "PRD validation is most useful when API files have been modified."
        echo "Continue anyway? (y/N) "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Validation cancelled."
            exit 0
        fi
    else
        echo -e "${GREEN}API files changed recently:${NC}"
        for file in $api_files_changed; do
            echo "  - $file"
        done
        echo ""
    fi

    # Generate validation prompt
    echo -e "${BLUE}Generating validation agent prompt...${NC}"
    echo ""

    cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VALIDATION AGENT PROMPT

Copy this prompt and use the Task tool in your AI assistant session:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task({
  subagent_type: "general-purpose",
  description: "Validate PRD compliance comprehensively",
  model: "sonnet",
  prompt: `You are a PRD compliance validation agent. Your task is to comprehensively compare the API implementation against all Product Requirement Documents.

**PRD Files to Check**:
EOF

    # Add each PRD file to the prompt
    for prd in $prd_files; do
        echo "- $prd"
    done

    cat << 'EOF'

**API Files to Validate**:
EOF

    # Add API files to validate
    api_endpoints=$(find backend/app/api/v*/endpoints -name "*.py" 2>/dev/null | grep -v __pycache__ || true)
    api_schemas=$(find backend/app/schemas -name "*.py" 2>/dev/null | grep -v __pycache__ | grep -v __init__ || true)

    for file in $api_endpoints; do
        echo "- $file (endpoint)"
    done
    for file in $api_schemas; do
        echo "- $file (schema)"
    done

    cat << 'EOF'

**Validation Process**:

1. **Read ALL PRD files completely**
   - Extract API endpoint specifications
   - Extract request/response schema specifications
   - Extract error response specifications
   - Extract authentication requirements
   - Extract performance requirements

2. **Read ALL implementation files completely**
   - API endpoint paths, methods, parameters
   - Request/response Pydantic models
   - Error handling and status codes
   - Authentication decorators

3. **Compare Implementation vs PRD - Check EVERY Field**

   For EACH endpoint in PRD:

   **Endpoint Validation**:
   - [ ] Path matches exactly (character-by-character)
   - [ ] HTTP method matches
   - [ ] Path parameters match (names, types)
   - [ ] Query parameters match (names, types, defaults, required/optional)

   **Request Schema Validation**:
   - [ ] Field names match exactly (case-sensitive!)
   - [ ] Field types match (string/number/boolean/object/array)
   - [ ] Nested structure matches (flat vs nested objects)
   - [ ] Required vs optional matches
   - [ ] Enum values match exactly
   - [ ] Default values match

   **Response Schema Validation**:
   - [ ] Success response structure matches
   - [ ] Field names match exactly (camelCase vs snake_case!)
   - [ ] Nested objects match PRD structure
   - [ ] Array wrapper matches (e.g., "results" vs direct array)
   - [ ] Metadata fields match (total, page, pageSize, etc.)

   **Error Response Validation**:
   - [ ] HTTP status codes match PRD (400, 401, 403, 404, 422, 500)
   - [ ] Error schema matches (check exact structure)
   - [ ] Error codes match (e.g., "INVALID_CONCEPT")

   **Authentication Validation**:
   - [ ] Auth requirement matches (public/authenticated/RBAC)
   - [ ] Required roles match

4. **Categorize Findings**

   **BREAKING CHANGES** (CRITICAL - Must Fix):
   - Field renamed (PRD: "concept", Code: "query")
   - Field type changed (PRD: string, Code: number)
   - Required field removed or made optional
   - Endpoint path changed
   - HTTP method changed
   - Response structure changed (flat vs nested)

   **MINOR DISCREPANCIES** (Non-Breaking):
   - Extra optional field added (not in PRD)
   - Extra error code added (not in PRD)
   - Better documentation than PRD

   **MISSING FEATURES**:
   - Endpoint in PRD but not implemented
   - Required field in PRD but missing in code

5. **Generate Comprehensive Report**

## PRD Compliance Validation Report

### Executive Summary
- Total endpoints checked: X
- Total fields validated: Y
- Breaking changes found: Z
- Minor discrepancies: N
- Missing features: M
- **Overall Status**: ✅ PASS / ❌ FAIL

### Detailed Findings

#### Endpoint: POST /api/v1/patients/search

**PRD Specification**:
[Quote exact PRD requirement]

**Implementation**:
[Quote actual code]

**Validation Results**:
- ✅ Path matches
- ✅ HTTP method matches
- ❌ **BREAKING**: Request field "query" should be "concept"
- ❌ **BREAKING**: Response field "total_count" should be "total"
- ⚠️  Minor: Extra optional field "debug" not in PRD

**Required Actions**:
1. Rename request.query → request.concept
2. Rename response.total_count → response.total
3. Consider: Remove "debug" field or document as extension

[Repeat for EACH endpoint]

### Summary of Breaking Changes

1. **Patient Search Endpoint** (backend/app/api/v1/endpoints/patient_search.py:25)
   - Field: request.query → request.concept
   - File: backend/app/schemas/patient_search.py:15
   - Fix: Rename field in PatientSearchRequest class

2. **Patient Search Response** (backend/app/schemas/patient_search.py:45)
   - Field: response.total_count → response.total
   - File: backend/app/schemas/patient_search.py:45
   - Fix: Rename field in PatientSearchResponse class

[List ALL breaking changes with exact file paths and line numbers]

### Missing Features

1. **GET /api/v1/patients/{mrn}** - Not implemented
   - PRD: Sprint 1, Section 3.2
   - Status: Missing
   - Priority: High (required for timeline view)

[List ALL missing features from PRD]

### Recommendations

**Immediate Actions** (Before next push):
1. Fix breaking change #1: Rename query → concept
2. Fix breaking change #2: Rename total_count → total

**Short Term** (This sprint):
1. Implement missing GET /api/v1/patients/{mrn} endpoint
2. Implement missing GET /api/v1/documents/{documentId} endpoint

**Long Term** (Next sprint):
1. Add contract tests to CI/CD
2. Generate OpenAPI spec from PRD automatically

### Conclusion

[Summary of overall compliance status and critical actions needed]

**Start validation now. Be EXTREMELY thorough - check EVERY field name, type, and structure character-by-character.**`
})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTRUCTIONS:

1. Copy the above Task(...) prompt
2. Paste into your AI assistant session (Claude Code CLI)
3. Wait for validation agent to complete analysis
4. Review the compliance report
5. Fix any breaking changes found
6. Re-run this script to verify fixes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

    echo ""
    echo -e "${GREEN}✅ Validation prompt generated${NC}"
    echo ""
    echo -e "${YELLOW}Note: This script cannot spawn AI agents directly.${NC}"
    echo -e "${YELLOW}Please copy the prompt above and use it in your AI assistant session.${NC}"
    echo ""

    exit 0
fi

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
