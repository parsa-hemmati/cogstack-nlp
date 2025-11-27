# Code Validation Checklist

**Purpose**: Ensure code integrity before committing changes

**When to use**: Before every commit (automated in pre-commit hook)

---

## Automated Validation (Pre-Commit Hook)

✅ Runs automatically on `git commit`

The pre-commit hook at `.git/hooks/pre-commit` automatically checks:

1. **CONTEXT.md Update** - Code changes must update CONTEXT.md
2. **Python Syntax** - All .py files must compile without errors
3. **Import Validation** - Test files must have resolvable imports
4. **Console Statements** - Warns about console.log/debugger
5. **TODO Comments** - Prompts to document TODOs properly

**To bypass** (NOT recommended): `git commit --no-verify`

---

## Manual Validation (Before Major Commits)

Run this script before committing significant changes:

```bash
# Full validation (includes tests)
./scripts/validate-code.sh --full

# Quick validation (syntax only, faster)
./scripts/validate-code.sh --quick

# Auto-fix formatting issues
./scripts/validate-code.sh --fix
```

---

## Validation Agent (For Complex Features)

For complex features or before phase completion, spawn a validation agent:

```markdown
Use the Task tool with subagent_type="general-purpose" and prompt:

"You are a code quality validation agent. Validate the following:

**Files to check**: [list specific files or directories]

**Validation tasks**:
1. Python syntax and imports
2. TypeScript type errors
3. Test coverage (>80%)
4. Security issues (hardcoded secrets, SQL injection)
5. HIPAA compliance (PHI in logs, audit logging)

Report:
- Critical issues (blocking)
- Warnings (non-blocking)
- Suggested fixes

Format as: ## Validation Results with sections for Critical/Warnings/Summary"
```

---

## CI/CD Pipeline (Automated on Push)

GitHub Actions runs automatically on push to main/develop/autonomous/* branches:

**Pipeline**: `.github/workflows/code-quality.yml`

**Checks**:
1. **Backend**: Python syntax, black formatting, flake8 linting, mypy types, pytest with coverage
2. **Frontend**: TypeScript types, ESLint, build verification
3. **Security**: Trivy vulnerability scan, TruffleHog secret detection

**View results**: GitHub Actions tab in repository

---

## Manual Testing Checklist

Before marking a task complete:

### Backend Tests
```bash
cd backend

# Run all tests
PYTHONPATH=. pytest tests/ -v

# Run specific test file
PYTHONPATH=. pytest tests/integration/test_user_management_api.py -v

# Run with coverage
PYTHONPATH=. pytest tests/ -v --cov=app --cov-report=term
```

### Frontend Tests (when implemented)
```bash
cd frontend

# Type checking
npm run type-check

# Linting
npm run lint

# Build
npm run build
```

---

## Healthcare Compliance Checklist

For features touching patient data:

### Use healthcare-compliance-checker Skill

Automatically reviews for:
- ✅ No PHI in application logs
- ✅ Audit logging for all PHI access
- ✅ Encryption in transit (TLS 1.3)
- ✅ Encryption at rest (AES-256)
- ✅ RBAC enforcement
- ✅ Minimum necessary access

**When to use**:
- Any code accessing patient data
- Authentication/authorization changes
- API endpoints handling PHI
- Database schema changes
- Logging additions

---

## Code Review Checklist (Self-Review)

Before requesting human review:

### Functionality
- [ ] All acceptance criteria met (reference spec)
- [ ] Edge cases handled
- [ ] No hardcoded values
- [ ] Logging appropriate (not excessive)

### Security
- [ ] Input validation
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized outputs)
- [ ] Authentication/authorization checks
- [ ] No secrets in code
- [ ] Audit logging for PHI access

### Performance
- [ ] Database queries optimized
- [ ] API calls cached (where appropriate)
- [ ] Large lists paginated
- [ ] No blocking in async code

### Testing
- [ ] Test coverage ≥80% (critical paths 100%)
- [ ] All tests passing
- [ ] Unit tests for business logic
- [ ] Integration tests for API contracts

### Documentation
- [ ] Code comments for complex logic
- [ ] API documentation updated
- [ ] README updated (if needed)
- [ ] CONTEXT.md updated (MANDATORY)

### Accessibility
- [ ] Semantic HTML
- [ ] ARIA labels
- [ ] Keyboard navigation
- [ ] Color contrast (WCAG AA)

---

## Validation Failure Response

If validation fails:

1. **Fix Critical Issues Immediately**
   - Syntax errors (blocking)
   - Test failures (blocking)
   - Security vulnerabilities (blocking)

2. **Address Warnings**
   - Code formatting
   - Type errors
   - Linting issues

3. **Re-Run Validation**
   ```bash
   ./scripts/validate-code.sh --full
   ```

4. **Update CONTEXT.md**
   - Document fixes made
   - Note any technical debt

5. **Commit Fixed Code**
   ```bash
   git add .
   git commit -m "fix: address validation issues"
   ```

---

## Integration with Autonomous Workflow

### Before Every Commit
1. ✅ Pre-commit hook runs automatically
2. ✅ Python syntax validated
3. ✅ CONTEXT.md update verified

### Before Phase Completion
1. ✅ Run full validation script
2. ✅ Spawn validation agent
3. ✅ Fix all critical issues
4. ✅ Document in CONTEXT.md

### On Push to GitHub
1. ✅ CI/CD pipeline runs
2. ✅ All tests execute
3. ✅ Security scan runs
4. ✅ Coverage reported

---

## Quick Reference

```bash
# Pre-commit validation (automatic)
git commit -m "message"

# Manual full validation
./scripts/validate-code.sh --full

# Quick syntax check
./scripts/validate-code.sh --quick

# Auto-fix formatting
./scripts/validate-code.sh --fix

# Run backend tests
cd backend && PYTHONPATH=. pytest tests/ -v

# Run frontend validation
cd frontend && npm run type-check && npm run lint

# Spawn validation agent (in Claude Code)
Use Task tool with subagent_type="general-purpose"
```

---

**Last Updated**: 2025-11-18
**Version**: 1.0.0
