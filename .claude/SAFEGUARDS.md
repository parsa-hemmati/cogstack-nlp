# Code Integrity Safeguards

**Version**: 1.0.0
**Last Updated**: 2025-11-18
**Purpose**: Multi-layer validation framework to ensure code quality and prevent regressions

---

## Overview

This project implements **4 layers of code validation** to ensure integrity:

```
Layer 1: Pre-Commit Hook (Local)
   ↓
Layer 2: Validation Script (Manual/Automated)
   ↓
Layer 3: Validation Agent (AI-Powered)
   ↓
Layer 4: CI/CD Pipeline (GitHub Actions)
```

---

## Layer 1: Pre-Commit Hook (Automated)

**File**: `.git/hooks/pre-commit`
**Runs**: Automatically on every `git commit`

### Checks Performed

1. **CONTEXT.md Update** ✅
   - Ensures code changes include CONTEXT.md updates
   - Verifies meaningful changes (not just date)
   - Blocks commits without proper documentation

2. **Python Syntax Validation** ✅
   - Compiles all staged .py files
   - Blocks commits with syntax errors
   - Fast (<1 second for most commits)

3. **Test Execution** ✅ **NEW**
   - Runs pytest on modified test files
   - 30-second timeout per test file
   - Blocks commits with failing tests

4. **Code Quality Warnings** ⚠️
   - Detects console.log/debugger statements
   - Warns about TODO comments
   - Prompts for confirmation (doesn't block)

### Bypass (Not Recommended)

```bash
git commit --no-verify
```

**Use only when**:
- Committing work-in-progress on feature branch
- Documentation-only changes
- Emergency hotfixes (fix tests after)

---

## Layer 2: Validation Script (Manual)

**File**: `scripts/validate-code.sh`
**Runs**: Manually before major commits or phase completion

### Usage

```bash
# Full validation (recommended before phase completion)
./scripts/validate-code.sh --full

# Quick validation (syntax and imports only)
./scripts/validate-code.sh --quick

# Auto-fix issues (formatting, linting)
./scripts/validate-code.sh --fix
```

### Checks Performed (--full mode)

#### Python Backend (5 checks)
1. **Syntax** - All .py files compile
2. **Imports** - All imports resolve
3. **Type Checking** - mypy validation (if installed)
4. **Formatting** - black code style (if installed)
5. **Tests** - Full pytest suite with coverage

#### Frontend (3 checks)
6. **TypeScript** - Type checking with vue-tsc
7. **ESLint** - Code linting and style
8. **Security** - Hardcoded secrets, SQL injection patterns

### Exit Codes

- `0` - All checks passed
- `1` - Critical errors found (syntax, failing tests)

---

## Layer 3: Validation Agent (AI-Powered)

**When to Use**:
- Complex features (>500 lines)
- Before phase completion
- After major refactoring
- When uncertain about code quality

### How to Invoke

Use Claude Code's Task tool:

```typescript
Task({
  subagent_type: "general-purpose",
  description: "Validate code quality",
  prompt: `You are a code quality validation agent.

**Files to check**: backend/app/api/v1/endpoints/*.py

**Validation tasks**:
1. Python syntax and imports
2. Security issues (PHI in logs, SQL injection)
3. HIPAA compliance (audit logging, encryption)
4. Test coverage
5. Code quality issues

**Report format**:
## Validation Results

### Critical Issues (blocking):
[List issues that prevent code from running]

### Warnings (non-blocking):
[List issues to address]

### Summary:
- Status: PASS/FAIL
- Files checked: X
- Critical issues: X
- Warnings: X
`
})
```

### Example Validation Session

```
User: "I just implemented Task 2.5-2.8. Validate the code."

Agent spawns validation subagent:
- Checks 13 files
- Finds 1 critical issue (missing db fixture)
- Finds 1 warning (print statements)
- Provides specific fixes

Agent fixes issues, re-validates, commits.
```

---

## Layer 4: CI/CD Pipeline (GitHub Actions)

**File**: `.github/workflows/code-quality.yml`
**Runs**: Automatically on push to main/develop/autonomous/* branches

### Jobs

#### 1. Backend Validation
- Python syntax check
- Code formatting (black)
- Linting (flake8)
- Type checking (mypy)
- Full test suite with coverage
- Coverage upload to Codecov

**Services**: PostgreSQL 15, Redis 7

#### 2. Frontend Validation
- TypeScript type checking
- ESLint
- Build verification

#### 3. Security Scanning
- Trivy vulnerability scanner
- TruffleHog secret detection
- Upload to GitHub Security tab

### Viewing Results

- GitHub repo → Actions tab
- Green checkmark = All passed
- Red X = Failures found (click for details)

### Branch Protection

**Recommended settings** (configure in GitHub):
- Require status checks to pass before merging
- Require branches to be up to date
- Require code review from 1 person

---

## Safeguard Comparison

| Safeguard | When | Speed | Coverage | Blocks Commit |
|-----------|------|-------|----------|---------------|
| Pre-Commit Hook | Every commit | Fast (2-5s) | Basic | Yes |
| Validation Script | Before major commits | Medium (30-60s) | Comprehensive | No (manual) |
| Validation Agent | Complex features | Slow (2-5 min) | Deep analysis | No (manual) |
| CI/CD Pipeline | On push | Slow (5-10 min) | Full suite | No (but fails PR) |

---

## Validation Workflow Recommendations

### For Every Commit (Small Changes)

```bash
# Pre-commit hook runs automatically
git add .
git commit -m "feat: small change"
# Hook validates: CONTEXT.md, Python syntax, tests
```

### Before Phase Completion (Major Milestone)

```bash
# 1. Run full validation
./scripts/validate-code.sh --full

# 2. Fix any issues found
# ... make fixes ...

# 3. Spawn validation agent (in Claude Code)
# Use Task tool as described above

# 4. Commit validated code
git add .
git commit -m "feat: Phase X complete"

# 5. Push to trigger CI/CD
git push origin autonomous/mvp-execution
```

### For Complex Features (>500 lines or critical code)

```bash
# 1. Implement feature

# 2. Run validation script
./scripts/validate-code.sh --full

# 3. Spawn validation agent
# (Use Task tool in Claude Code)

# 4. Use healthcare-compliance-checker skill
# (For PHI-related code)

# 5. Fix all critical issues

# 6. Commit and push
git add .
git commit -m "feat: complex feature"
git push
```

---

## Handling Validation Failures

### Pre-Commit Hook Failure

```bash
# Hook blocked commit due to test failure

# Option 1: Fix the test
# ... fix code ...
git add .
git commit -m "fix: address test failure"

# Option 2: Bypass (NOT recommended)
git commit --no-verify
# Then fix tests in next commit

# Option 3: Stash changes, fix on clean slate
git stash
# ... investigate and fix ...
git stash pop
git add .
git commit -m "fix: address test failure"
```

### Validation Script Failure

```bash
# Script reported critical errors

# View detailed output
./scripts/validate-code.sh --full 2>&1 | less

# Fix issues one by one
# - Syntax errors first
# - Then failing tests
# - Then warnings

# Re-run to verify
./scripts/validate-code.sh --full
```

### CI/CD Pipeline Failure

```bash
# Check GitHub Actions for details
# Fix issues locally

# Run same checks locally
./scripts/validate-code.sh --full

# Push fix
git add .
git commit -m "fix: address CI failures"
git push
```

---

## Monitoring and Metrics

### What to Track

1. **Pre-Commit Success Rate**
   - How often hooks pass on first try?
   - Target: >90%

2. **Test Coverage**
   - Tracked by pytest-cov and Codecov
   - Target: >80% overall, 100% for critical paths

3. **CI/CD Build Time**
   - How long does pipeline take?
   - Target: <10 minutes

4. **Security Scan Results**
   - Vulnerabilities found by Trivy
   - Secrets detected by TruffleHog
   - Target: 0 critical vulnerabilities

### Viewing Metrics

```bash
# Test coverage (local)
cd backend
PYTHONPATH=. pytest tests/ --cov=app --cov-report=term

# CI/CD metrics
# Check GitHub Actions tab

# Security metrics
# Check GitHub Security tab
```

---

## Maintenance

### Keeping Safeguards Effective

1. **Update validation script monthly**
   - Add new checks as needed
   - Update tool versions

2. **Review false positives**
   - If hooks block legitimate commits frequently
   - Adjust thresholds

3. **Monitor CI/CD costs**
   - GitHub Actions minutes
   - Consider caching strategies

4. **Train team on safeguards**
   - Document common failures
   - Share best practices

---

## Troubleshooting

### "pytest not found" in pre-commit hook

```bash
# Install pytest in your environment
pip install pytest pytest-asyncio

# Verify installation
which pytest
```

### "mypy not found" in validation script

```bash
# Install mypy
pip install mypy

# Validation script continues without mypy
# (non-blocking warning)
```

### Frontend validation skipped

```bash
# Install frontend dependencies
cd frontend
npm install

# Re-run validation
cd ..
./scripts/validate-code.sh --full
```

### Tests timing out in pre-commit

```bash
# 30-second timeout is intentional
# If legitimate tests are slow:

# Option 1: Optimize the test
# Option 2: Run full suite manually
pytest backend/tests/ -v

# Option 3: Bypass for this commit
git commit --no-verify
```

---

## Best Practices

1. ✅ **Never bypass safeguards on main/develop branches**
2. ✅ **Run full validation before phase completion**
3. ✅ **Use validation agent for complex features**
4. ✅ **Fix critical issues immediately**
5. ✅ **Address warnings during cleanup phases**
6. ✅ **Keep CONTEXT.md updated (mandatory)**
7. ✅ **Write tests before implementing features (TDD)**
8. ✅ **Use `--fix` mode to auto-format code**

---

## Future Enhancements

### Planned Improvements

- [ ] Add mutation testing (mutmut)
- [ ] Implement performance regression testing
- [ ] Add visual regression testing for frontend
- [ ] Integrate SAST tools (Bandit, Semgrep)
- [ ] Add API contract testing (Pact)
- [ ] Implement chaos engineering tests

---

**Questions?** See `.claude/VALIDATION_CHECKLIST.md` for quick reference.
