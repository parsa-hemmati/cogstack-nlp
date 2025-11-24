# PRD Test Generator & Coverage Tracker

**Version**: 1.0.0
**Type**: Quality Assurance Agent
**Activation**: Manual (via Task tool) or Pre-Commit Hook

---

## 🎯 Purpose

Generate comprehensive tests from PRD specifications, execute them, and track test coverage over time. Ensures implementation matches requirements through automated test validation.

**Complements**: `auditor` skill (auditor checks compliance, this ensures testability)

---

## 📋 When to Use This Skill

### ✅ Use This Skill When:

1. **Starting New Feature** - Generate tests BEFORE implementation (TDD approach)
2. **PRD Updated** - Regenerate tests when requirements change
3. **Low Test Coverage** - Identify missing tests for existing features
4. **Pre-Commit** - Verify all requirements are tested (optional hook)
5. **Sprint Completion** - Generate comprehensive test coverage report

### ❌ Don't Use When:

- Writing simple bug fixes (<50 lines, no new requirements)
- Refactoring without behavior changes
- Documentation-only updates

---

## 🔧 How It Works

### Workflow Overview

```
PRD Specification → Extract Requirements → Generate Tests → Run Tests → Report
```

### Step-by-Step Process

1. **Read PRD** - Parse specification file (`.specify/sprints/*.md` or `.specify/specifications/*.md`)
2. **Extract Requirements** - Identify testable functional/non-functional requirements
3. **Generate Tests** - Create pytest (backend) or vitest (frontend) test cases
4. **Execute Tests** - Run generated + existing tests, collect results
5. **Report** - Update `TEST_REPORT.md` with coverage, pass/fail status, recommendations

---

## 📝 Test Generation Strategy

### Backend (Python + pytest)

**Generates**:
- **Unit Tests**: Functions, classes, business logic
- **Integration Tests**: API endpoints, database queries, service interactions
- **Contract Tests**: Request/response schema validation (Pydantic)
- **Security Tests**: Authentication, authorization, PHI handling

**Example Generated Test**:
```python
# Generated from PRD: Sprint 1 - Patient Search API
# Requirement: FR1 - Search by medical concept

import pytest
from app.schemas.patient_search import PatientSearchRequest, SearchFilters

class TestPatientSearchAPI:
    """
    PRD Requirement: FR1 - Search patients by medical concept
    Acceptance Criteria:
    - Accept concept name or CUI
    - Return matching patients with annotations
    - Response time < 500ms for 1000 patients
    """

    @pytest.mark.asyncio
    async def test_search_by_concept_name(self, client, test_db):
        """Test search with concept name (FR1.1)"""
        request = PatientSearchRequest(
            concept="atrial flutter",
            filters=SearchFilters(temporal="current"),
            pagination={"page": 1, "pageSize": 20}
        )

        response = await client.post("/api/v1/patients/search", json=request.dict())

        # FR1.1: Returns 200 OK
        assert response.status_code == 200

        # FR1.2: Response includes pagination
        data = response.json()
        assert "pagination" in data
        assert data["pagination"]["page"] == 1

        # FR1.3: Results include annotations
        assert "results" in data
        for result in data["results"]:
            assert "annotations" in result
            assert len(result["annotations"]) > 0

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_search_performance_requirement(self, client, test_db_1000_patients):
        """Test NFR1 - Response time < 500ms for 1000 patients"""
        import time

        request = PatientSearchRequest(concept="diabetes")

        start = time.time()
        response = await client.post("/api/v1/patients/search", json=request.dict())
        duration_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert duration_ms < 500, f"Response took {duration_ms}ms (requirement: <500ms)"
```

### Frontend (TypeScript + vitest)

**Generates**:
- **Component Tests**: Vue component behavior, props, events
- **Composable Tests**: Reactive state management, API calls
- **E2E Tests**: User workflows (with Playwright)
- **Accessibility Tests**: WCAG compliance, keyboard navigation

**Example Generated Test**:
```typescript
// Generated from PRD: Sprint 1 - Patient Search UI
// Requirement: FR4 - Search filters (temporal, negation, family)

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PatientSearchView from '@/views/PatientSearchView.vue'

describe('PatientSearchView - FR4: Search Filters', () => {
  /**
   * PRD Requirement: FR4.1 - Temporal filter
   * Acceptance Criteria:
   * - Display temporal filter (Current, Historical, Future, Any)
   * - Default to "Current"
   * - Filter applied to search request
   */
  it('FR4.1: applies temporal filter to search request', async () => {
    const wrapper = mount(PatientSearchView)

    // FR4.1.1: Default to "Current"
    expect(wrapper.vm.filters.temporal).toBe('current')

    // FR4.1.2: Change filter
    await wrapper.find('[data-testid="temporal-filter"]').setValue('historical')

    // FR4.1.3: Filter applied to search
    await wrapper.find('[data-testid="search-button"]').trigger('click')

    expect(wrapper.vm.searchRequest.filters.temporal).toBe('historical')
  })

  /**
   * PRD Requirement: FR4.2 - Include negated mentions
   * Acceptance Criteria:
   * - Checkbox for "Include negated"
   * - Default unchecked
   * - Applies to search request
   */
  it('FR4.2: includes negated filter when checked', async () => {
    const wrapper = mount(PatientSearchView)

    // FR4.2.1: Default unchecked
    expect(wrapper.vm.filters.includeNegated).toBe(false)

    // FR4.2.2: Check box
    await wrapper.find('[data-testid="include-negated"]').setChecked(true)

    // FR4.2.3: Applied to request
    await wrapper.find('[data-testid="search-button"]').trigger('click')

    expect(wrapper.vm.searchRequest.filters.includeNegated).toBe(true)
  })
})
```

---

## 📊 TEST_REPORT.md Format

The agent generates/updates `TEST_REPORT.md` with this structure:

```markdown
# Test Coverage Report

**Last Updated**: 2025-11-18
**Generated By**: prd-test-generator agent
**PRD Specification**: .specify/sprints/sprint-1-prd.md

---

## 📊 Overall Coverage

| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| **Functional Requirements** | 45/50 (90%) | 100% | ⚠️ 5 missing |
| **Non-Functional Requirements** | 8/10 (80%) | 100% | ⚠️ 2 missing |
| **Test Execution** | 53/53 (100%) | 100% | ✅ PASS |
| **Line Coverage** | 87% | 80% | ✅ PASS |
| **Branch Coverage** | 75% | 70% | ✅ PASS |

---

## 📋 Requirement Coverage

### ✅ Fully Tested (45/50)

#### FR1: Search by Medical Concept
- ✅ FR1.1: Accept concept name → `test_search_by_concept_name`
- ✅ FR1.2: Accept SNOMED-CT CUI → `test_search_by_cui`
- ✅ FR1.3: Return matching patients → `test_search_returns_patients`
- ✅ FR1.4: Include annotations → `test_search_includes_annotations`

#### FR2: Meta-Annotation Filtering
- ✅ FR2.1: Temporal filter → `test_temporal_filter`
- ✅ FR2.2: Negation filter → `test_negation_filter`
- ✅ FR2.3: Experiencer filter → `test_experiencer_filter`

### ⚠️ Missing Tests (5/50)

#### FR5: Pagination
- ❌ FR5.3: Navigate to specific page → **NO TEST FOUND**
  - **Recommendation**: Add `test_pagination_specific_page` in `test_patient_search_api.py`
  - **Acceptance Criteria**: User can jump to page N, results update correctly
  - **Priority**: HIGH (core functionality)

#### NFR1: Performance
- ❌ NFR1.2: Response time < 500ms for 10,000 patients → **NO TEST FOUND**
  - **Recommendation**: Add `test_search_performance_10k_patients` with `@pytest.mark.performance`
  - **Fixture**: Create `test_db_10k_patients` fixture
  - **Priority**: MEDIUM (performance validation)

---

## 🧪 Test Execution Results

### Backend Tests (pytest)

```
=============================== test session starts ================================
platform linux -- Python 3.11.8, pytest-8.1.1
collected 53 items

tests/unit/services/test_patient_search_service.py ........................... [ 47%]
tests/integration/test_patient_search_api.py ....................... [ 88%]
tests/security/test_phi_handling.py ...... [100%]

============================== 53 passed in 4.23s ==================================
```

**Coverage Report**:
```
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
app/services/patient_search_service.py       145      8    94%   234-236, 412-415
app/api/v1/endpoints/patient_search.py        87      5    94%   156-158, 298-301
------------------------------------------------------------------------
TOTAL                                        232     13    94%
```

### Frontend Tests (vitest)

```
✓ src/views/PatientSearchView.spec.ts (12)
✓ src/composables/usePatientSearch.spec.ts (8)
✓ src/api/patientSearch.spec.ts (6)

Test Files  3 passed (3)
     Tests  26 passed (26)
  Start at  22:45:32
  Duration  2.18s
```

---

## 🎯 Recommendations

### High Priority (Blocking)

1. **Add FR5.3 Test** (Pagination - Navigate to specific page)
   - File: `tests/integration/test_patient_search_api.py`
   - Test: `test_pagination_navigate_to_page`
   - Acceptance: Page number changes, results update, URL updated

2. **Add FR7.2 Test** (Error Handling - Invalid CUI)
   - File: `tests/integration/test_patient_search_api.py`
   - Test: `test_search_invalid_cui_returns_400`
   - Acceptance: Returns 400 with error message

### Medium Priority (Performance)

3. **Add NFR1.2 Test** (Performance - 10,000 patients)
   - File: `tests/performance/test_search_performance.py`
   - Test: `test_search_10k_patients_under_500ms`
   - Fixture: Generate 10,000 test patients with annotations

### Low Priority (Nice to Have)

4. **Add E2E Test** (Full User Workflow)
   - File: `tests/e2e/test_patient_search_workflow.spec.ts`
   - Test: `test_search_filter_view_patient_workflow`
   - Tool: Playwright

---

## 📈 Trends

| Date | FR Coverage | NFR Coverage | Test Count | Pass Rate |
|------|-------------|--------------|------------|-----------|
| 2025-11-18 | 90% | 80% | 53 | 100% |
| 2025-11-17 | 88% | 70% | 48 | 100% |
| 2025-11-16 | 82% | 60% | 42 | 98% |

**Analysis**: Coverage increasing steadily. Focus on NFR tests (performance, security).

---

## 🔄 Next Steps

1. ✅ Generate missing tests (run `prd-test-generator` agent)
2. ⚠️ Add performance fixtures (`test_db_10k_patients`)
3. ⏳ Schedule E2E tests in CI/CD pipeline
4. ⏳ Add mutation testing (optional)
```

---

## 🚀 Usage

### Method 1: Spawn Agent Manually

```typescript
Task({
  subagent_type: "general-purpose",
  description: "Generate tests from PRD",
  model: "sonnet",
  prompt: `You are a PRD test generator. Your task is to generate comprehensive tests from PRD specifications and create a test coverage report.

**PRD Specification**: .specify/sprints/sprint-1-prd.md

**Tasks**:

1. **Read PRD** - Parse specification file
2. **Extract Requirements** - List all functional (FR) and non-functional (NFR) requirements
3. **Generate Tests** - Create pytest (backend) and vitest (frontend) test cases
4. **Run Tests** - Execute tests and collect results
5. **Report** - Create/update TEST_REPORT.md

**Output Format**:

## Requirements Extracted

| ID | Requirement | Testable | Priority |
|----|-------------|----------|----------|
| FR1 | Search by concept | ✅ Yes | HIGH |
| ... | ... | ... | ... |

## Generated Tests

### Backend (pytest)

\`\`\`python
# File: tests/integration/test_patient_search_api.py
# Generated test code...
\`\`\`

### Frontend (vitest)

\`\`\`typescript
// File: tests/unit/PatientSearchView.spec.ts
// Generated test code...
\`\`\`

## Test Execution Results

[Test output...]

## TEST_REPORT.md Updated

[Report content...]

Start now.`
})
```

### Method 2: Pre-Commit Hook (Optional)

Add to `.git-hooks/pre-commit`:

```bash
# PRD Test Coverage Check (optional)
if [ "$ENFORCE_TEST_COVERAGE" = "true" ]; then
    echo "🧪 Checking test coverage..."

    # Check if TEST_REPORT.md shows missing tests
    if grep -q "⚠️ Missing Tests" TEST_REPORT.md; then
        echo "❌ Missing tests detected. Run prd-test-generator agent."
        exit 1
    fi
fi
```

### Method 3: CI/CD Integration

```yaml
# .github/workflows/test-coverage.yml
name: PRD Test Coverage

on: [push, pull_request]

jobs:
  test-coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Generate Test Coverage Report
        run: |
          # Spawn prd-test-generator agent
          # Parse TEST_REPORT.md
          # Fail if coverage < 90%
```

---

## 📚 Examples

### Example 1: Generate Tests for New Feature

```bash
# User request: "Generate tests for Patient Search feature"

# Agent workflow:
# 1. Read .specify/sprints/sprint-1-prd.md
# 2. Extract 50 functional requirements
# 3. Generate 45 test cases (pytest + vitest)
# 4. Run tests → 43 pass, 2 fail (missing implementations)
# 5. Update TEST_REPORT.md
# 6. Report: "90% coverage, 2 tests failing (expected - not implemented yet)"
```

### Example 2: Verify PRD Compliance

```bash
# User request: "Check if all PRD requirements are tested"

# Agent workflow:
# 1. Read TEST_REPORT.md
# 2. Compare against .specify/sprints/sprint-1-prd.md
# 3. Identify 5 missing tests (FR5.3, NFR1.2, etc.)
# 4. Generate test skeletons for missing tests
# 5. Update TEST_REPORT.md with recommendations
# 6. Report: "5 requirements untested - high priority: FR5.3"
```

### Example 3: Continuous Coverage Tracking

```bash
# Run daily via cron job or CI/CD

# Agent workflow:
# 1. Run all tests (pytest + vitest)
# 2. Collect coverage metrics
# 3. Update TEST_REPORT.md trends section
# 4. Alert if coverage drops below 80%
```

---

## 🔗 Integration with Existing Skills

### Works With:

1. **`auditor`** - Auditor checks PRD compliance, this ensures testability
2. **`spec-kit-enforcer`** - Enforcer ensures specs exist, this ensures tests exist
3. **`healthcare-compliance-checker`** - Compliance checker validates PHI handling, this generates security tests

### Workflow:

```
Spec → Plan → Tasks → Implementation → Tests (THIS SKILL) → Audit → Deploy
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Enable PRD test generation in pre-commit hook
export ENFORCE_TEST_COVERAGE=true

# Minimum coverage thresholds
export MIN_FR_COVERAGE=90  # Functional requirements
export MIN_NFR_COVERAGE=80 # Non-functional requirements
export MIN_LINE_COVERAGE=80 # Line coverage
export MIN_BRANCH_COVERAGE=70 # Branch coverage
```

### Skill Settings

Create `.claude/skills/prd-test-generator/config.json`:

```json
{
  "default_model": "sonnet",
  "test_frameworks": {
    "backend": "pytest",
    "frontend": "vitest",
    "e2e": "playwright"
  },
  "coverage_targets": {
    "functional_requirements": 90,
    "non_functional_requirements": 80,
    "line_coverage": 80,
    "branch_coverage": 70
  },
  "report_path": "TEST_REPORT.md",
  "auto_generate": false,
  "run_tests": true
}
```

---

## 🎓 Best Practices

### DO:
- ✅ Generate tests BEFORE implementation (TDD)
- ✅ Map each test to specific PRD requirement
- ✅ Include acceptance criteria in test docstrings
- ✅ Run tests after generation to verify they work
- ✅ Update TEST_REPORT.md with every commit

### DON'T:
- ❌ Generate tests without reading PRD first
- ❌ Skip performance/security tests (NFRs)
- ❌ Ignore failing generated tests
- ❌ Commit code without running test generator

---

## 📈 Success Metrics

**Good**:
- 90%+ FR coverage
- 80%+ NFR coverage
- 100% test pass rate
- All high-priority requirements tested

**Needs Improvement**:
- <80% FR coverage → Run agent to generate missing tests
- <70% NFR coverage → Focus on performance/security tests
- Failing tests → Fix implementation or update tests
- Missing TEST_REPORT.md → Run agent to generate

---

## 🆘 Troubleshooting

### Issue: "Agent generates tests that don't run"

**Solution**:
- Check pytest/vitest configuration
- Verify test fixtures exist
- Update generated test imports

### Issue: "TEST_REPORT.md shows 50% coverage but tests are passing"

**Solution**:
- PRD may have more requirements than implemented
- This is expected for incomplete features
- Focus on high-priority missing tests first

### Issue: "Generated tests are too generic"

**Solution**:
- Provide more specific PRD acceptance criteria
- Run agent with `model: "opus"` for better quality
- Manually refine generated tests

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-18 | Initial release |

---

**Maintained By**: AI Development Team
**Questions?**: See `.claude/skills/README.md` or ask user
