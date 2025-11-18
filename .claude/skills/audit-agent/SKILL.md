# Audit Agent Skill

**Version**: 1.0.0
**Last Updated**: 2025-11-18
**Type**: Quality Assurance / Continuous Compliance
**Activation**: Model-invoked (automatic when reviewing code or before commits)

---

## Purpose

Provides guidance for **continuous PRD compliance auditing** through a dedicated audit agent role. This agent reviews ALL previous and existing work against PRD specifications and maintains AUDIT.md.

**Problem Solved**: Prevents gradual PRD drift by continuously auditing implementation against specifications.

**Use When**:
- Before committing code changes (mandatory)
- After completing a Sprint/Phase
- Weekly during active development
- When implementing new PRD requirements
- Before creating pull requests

---

## Audit Agent Role

The audit agent is a **separate role** from implementation agents:

| Role | Responsibility | Output |
|------|----------------|--------|
| **Implementation Agent** | Build features, write code | Code files, tests |
| **Validation Agent** | Validate new code against PRD | Validation report |
| **Audit Agent** | Review ALL work against PRD | AUDIT.md updates |

**Key Difference**: Audit agent reviews **existing** work, not just new changes.

---

## When to Spawn Audit Agent

### Mandatory (Git Hook Enforced)

**Before committing code changes**:
- Git pre-commit hook requires AUDIT.md to be updated
- Spawn audit agent to review recent changes
- Update AUDIT.md based on agent findings
- Commit with both CONTEXT.md and AUDIT.md

### Recommended

**After Sprint/Phase completion**:
- Full audit of all features in Sprint/Phase
- Comprehensive compliance scoring
- Trend analysis

**Weekly during active development**:
- Review drift trends
- Catch gradual divergence early
- Update compliance scores

---

## How to Spawn Audit Agent

Use the `Task` tool with this prompt template:

```typescript
Task({
  subagent_type: "general-purpose",
  description: "Audit implementation against PRD specs",
  model: "sonnet", // Use sonnet for thorough auditing
  prompt: `You are a dedicated PRD compliance audit agent. Your role is to review ALL previous and existing work against PRD specifications and update AUDIT.md.

**Context**: [Describe what to audit - e.g., "Sprint 1 patient search feature" or "All Phase 3 work"]

**Your Tasks**:

1. **Read All Relevant PRD Files**:
   - .specify/sprints/sprint-*-prd.md
   - .specify/phases/phase-*-spec.md
   - Extract API contracts, schemas, requirements

2. **Read All Implementation Files**:
   - backend/app/api/v1/endpoints/*.py
   - backend/app/schemas/*.py
   - backend/app/services/*.py
   - backend/app/models/*.py
   - frontend/src/components/*.vue (if applicable)

3. **Compare Implementation vs PRD** (Character-by-Character):

   For EACH feature, check:

   **Endpoints**:
   - [ ] Path matches PRD exactly
   - [ ] HTTP method matches
   - [ ] Path parameters match
   - [ ] Query parameters match

   **Request Schemas**:
   - [ ] Field names match (case-sensitive!)
   - [ ] Field types match
   - [ ] Nested structure matches
   - [ ] Required vs optional matches
   - [ ] Default values match

   **Response Schemas**:
   - [ ] Success response structure matches
   - [ ] Field names match (camelCase!)
   - [ ] Nested objects match
   - [ ] Array structures match
   - [ ] Metadata fields match

   **Error Responses**:
   - [ ] HTTP status codes match
   - [ ] Error schema matches
   - [ ] Error codes match
   - [ ] All scenarios documented

   **Security**:
   - [ ] Authentication requirements match
   - [ ] Authorization roles match
   - [ ] Audit logging present
   - [ ] Encryption requirements met

   **Performance**:
   - [ ] Response time targets noted
   - [ ] Pagination implemented
   - [ ] Indexes created

4. **Categorize Findings**:

   **✅ COMPLIANT**: Matches PRD exactly
   - No action needed
   - Document in audit as "PASS"

   **⚠️ MINOR DISCREPANCY**: Non-breaking differences
   - Extra optional field (not in PRD)
   - Better documentation than PRD
   - Performance optimization not specified
   - Document in audit with "⚠️ MINOR"

   **❌ BREAKING CHANGE**: API contract violation
   - Field renamed
   - Field type changed
   - Required field missing
   - Endpoint path different
   - Document in audit with "❌ FAIL"

   **🚨 DRIFT**: Implementation diverged over time
   - Was compliant, now different
   - Gradual changes accumulated
   - Document in "Drift Detection Log"

5. **Update AUDIT.md**:

   **Current Compliance Status**:
   - Update overall compliance score
   - Update feature-specific scores
   - Update "Last Updated" timestamp
   - Update "Audited By" field

   **Feature-by-Feature Audit**:
   - Update relevant feature section
   - Add compliance check table results
   - List breaking changes (if any)
   - List minor discrepancies
   - Add audit notes

   **Drift Detection Log**:
   - Add new drift items (if detected)
   - Update historical drift status
   - Document severity and resolution

   **Compliance Trends**:
   - Update sprint/phase scores
   - Update category scores
   - Note trend direction (⬆️ ⬇️ →)

6. **Generate Summary Report**:

   ## Audit Summary

   **Audit Date**: [timestamp]
   **Scope**: [What was audited]
   **Commits Reviewed**: [commit SHAs]

   ### Compliance Scores
   - Overall: X%
   - Breaking Changes: X
   - Minor Discrepancies: X
   - Drift Items Detected: X

   ### Critical Findings
   1. [Breaking change or critical issue]
   2. [Next critical issue]

   ### Recommended Actions (Prioritized)
   1. **URGENT**: [Fix breaking change]
   2. **HIGH**: [Address security/compliance issue]
   3. **MEDIUM**: [Fix minor discrepancy]
   4. **LOW**: [Documentation improvement]

   ### Compliance Trend
   - Previous audit: X%
   - Current audit: X%
   - Trend: ⬆️ Improving / ⬇️ Declining / → Stable

**Be EXTREMELY thorough**: Check EVERY field name, type, nesting, default value character-by-character. Do not assume compliance - verify everything.

Start audit now.`
})
```

---

## Audit Workflow

### Step-by-Step

```bash
# 1. You're about to commit code changes
git add backend/app/api/v1/endpoints/patient_search.py
git add backend/app/schemas/patient_search.py

# 2. Spawn audit agent (before commit)
# Use Task tool with prompt above

# 3. Audit agent analyzes:
# - Reads Sprint 1 PRD
# - Reads patient_search.py implementation
# - Compares field-by-field
# - Generates findings

# 4. Audit agent reports:
## Audit Summary
Compliance: 95%
Breaking Changes: 0
Minor Discrepancies: 3 (gender/department null, sourceValue uses pretty_name)
Drift Items: 0

# 5. Audit agent updates AUDIT.md:
# - Updates "Patient Search API" section
# - Adds compliance check table
# - Lists minor discrepancies
# - Updates overall score

# 6. You read AUDIT.md to review findings

# 7. Address critical issues (if any)

# 8. Update CONTEXT.md with technical changes

# 9. Commit with both files updated
git add CONTEXT.md AUDIT.md
git commit -m "feat: implement patient search API (PRD-compliant, audited)"

# 10. Pre-commit hook verifies both files modified
✅ CONTEXT.md is being updated
✅ AUDIT.md is being updated
✅ Commit proceeds
```

---

## Audit Scope Levels

### Quick Audit (5-10 minutes)

**Scope**: Recent changes only
**Use when**: Before committing feature changes

**Audits**:
- Files modified in current commit
- Relevant PRD section
- Endpoint/schema compliance only

**Example**:
```typescript
Task({
  description: "Quick audit of patient search changes",
  prompt: "Audit recent changes to patient search endpoint against Sprint 1 PRD. Focus on endpoint path, request/response schemas. Update AUDIT.md 'Patient Search API' section only."
})
```

### Full Sprint Audit (30-60 minutes)

**Scope**: All features in a Sprint
**Use when**: Sprint completion, weekly review

**Audits**:
- All endpoints in Sprint
- All schemas, services, models
- Complete PRD coverage
- Trend analysis

**Example**:
```typescript
Task({
  description: "Full Sprint 1 audit",
  prompt: "Audit ALL Sprint 1 features (patient search, timeline, highlights) against Sprint 1 PRD. Check every endpoint, schema, error response. Update all relevant AUDIT.md sections and compliance trends."
})
```

### Comprehensive Phase Audit (1-2 hours)

**Scope**: Entire phase (e.g., Phase 3 - Document Management)
**Use when**: Phase completion, major milestone

**Audits**:
- All features in phase
- Integration points
- Performance benchmarks
- Security compliance
- Historical drift review

**Example**:
```typescript
Task({
  description: "Comprehensive Phase 3 audit",
  prompt: "Audit ALL Phase 3 work (document upload, encryption, deduplication, background processing, patient aggregation) against Phase 3 spec. Check HIPAA compliance, encryption, audit logging. Review ALL 12 tasks. Generate comprehensive compliance report."
})
```

---

## What Audit Agent Checks

### API Endpoints

```python
# PRD Specification
POST /api/v1/patients/search

# Audit Checks
✅ Path matches exactly: /api/v1/patients/search
✅ Method is POST (not GET, PUT, DELETE)
✅ No extra path parameters added
✅ Endpoint exists and is accessible
```

### Request Schemas

```python
# PRD Specification
{
  "concept": "string",
  "pagination": {
    "page": 1,
    "pageSize": 20
  }
}

# Audit Checks
✅ Field "concept" exists (not "query")
✅ Field "concept" is type string (not number)
✅ Field "concept" is required (not optional)
✅ Field "pagination" is nested object (not flat)
✅ Nested field "page" is number (not string)
✅ Nested field "pageSize" is camelCase (not page_size)
✅ Default value "pageSize": 20 matches PRD
```

### Response Schemas

```python
# PRD Specification
{
  "results": [...],
  "total": 42,
  "queryTimeMs": 123
}

# Audit Checks
✅ Field "results" is array (not object)
✅ Field "total" exists (not "total_count")
✅ Field "queryTimeMs" is camelCase (not query_time_ms)
✅ No extra top-level fields added
✅ Nested object structure matches PRD
```

### Error Responses

```python
# PRD Specification
400: { "error": { "code": "INVALID_CONCEPT", "message": "..." } }

# Audit Checks
✅ HTTP status 400 returned for invalid input
✅ Error schema matches { error: { code, message } }
✅ Error code "INVALID_CONCEPT" used (not "InvalidConcept")
✅ Error documented in OpenAPI spec
✅ All error scenarios from PRD handled
```

### Security & Compliance

```python
# PRD Specification
- Authentication: Required (JWT)
- Audit Logging: All patient data access

# Audit Checks
✅ Endpoint requires authentication
✅ JWT token validation present
✅ Audit log entry created on access
✅ Audit log includes user ID, patient ID, timestamp
✅ PHI not exposed in application logs
✅ Encryption requirements met
```

---

## Drift Detection

### What is Drift?

**Drift** = Implementation was compliant, then gradually diverged from PRD over time.

**Causes**:
- Incremental changes without PRD review
- "Quick fixes" that change API contract
- Refactoring that alters field names
- Adding features not in PRD
- Removing fields specified in PRD

### How Audit Agent Detects Drift

```bash
# Week 1: Compliant
Endpoint: POST /api/v1/patients/search
Request: { "concept": "..." }
Response: { "results": [...], "total": 42 }
✅ Matches PRD

# Week 3: Drift introduced
Endpoint: POST /api/v1/patients/search  # Same
Request: { "concept": "...", "debug": true }  # Extra field added
Response: { "results": [...], "count": 42 }  # Field renamed!
⚠️ DRIFT DETECTED: Response field "total" → "count"

# Audit agent documents:
## Drift Detection Log
### Active Drift Items
1. **Patient Search Response Drift** (Detected 2025-11-25)
   - Field renamed: "total" → "count"
   - Commit: abc123f
   - Severity: 🔴 BREAKING CHANGE
   - Action: Revert to "total" immediately
```

### Drift Prevention

**Continuous auditing** (audit agent reviews weekly):
- Catches drift early (days, not months)
- Documents when drift occurred (commit SHA)
- Tracks resolution

**Git hooks**:
- Pre-commit audit requirement
- AUDIT.md must be updated
- Forces regular review

---

## AUDIT.md Structure

### Sections Maintained by Audit Agent

1. **Current Compliance Status** - Overall scores table
2. **Feature-by-Feature Audit** - Detailed compliance checks
3. **Drift Detection Log** - Active and historical drift
4. **Compliance Trends** - Score trends over time

### Update Frequency

| Section | Update Frequency | Updated By |
|---------|------------------|------------|
| Current Compliance Status | Every audit | Audit Agent |
| Feature-by-Feature Audit | Per feature change | Audit Agent |
| Drift Detection Log | When drift detected | Audit Agent |
| Compliance Trends | Weekly/Sprint end | Audit Agent |

---

## Integration with Other Validation

### Validation Layers

```
Layer 1: prd-compliance-checker (skill)  → Quick checklist for new code
Layer 2: Validation Agent              → Deep validation of new code
Layer 3: Audit Agent (this skill)      → Continuous review of ALL code
Layer 4: Git Hooks                     → Enforce AUDIT.md updates
Layer 5: CI/CD                         → Automated contract tests
```

**Key Difference**:
- **Validation Agent**: Validates NEW code before commit
- **Audit Agent**: Reviews ALL code (new + existing) continuously

### When to Use Each

| Scenario | Validation Agent | Audit Agent |
|----------|------------------|-------------|
| Implementing new feature | ✅ Use before commit | ✅ Use after implementation |
| Weekly review | ❌ Not needed | ✅ Full audit |
| Sprint completion | ❌ Not needed | ✅ Comprehensive audit |
| Suspected drift | ❌ Not designed for this | ✅ Drift detection |
| Pre-commit hook | ✅ For new files | ✅ Update AUDIT.md |

---

## Best Practices

### ✅ DO

- **Run audit agent weekly** during active development
- **Read AUDIT.md before committing** to catch drift early
- **Address breaking changes immediately** (don't defer)
- **Document minor discrepancies** for future sprints
- **Update AUDIT.md thoroughly** (not just timestamp)
- **Use audit findings to improve** implementation workflow

### ❌ DON'T

- **Skip audit before commit** (git hook will block anyway)
- **Ignore drift items** (they compound over time)
- **Defer breaking changes** (fix immediately)
- **Manually edit compliance scores** (let audit agent calculate)
- **Commit without reading AUDIT.md** (defeats the purpose)
- **Update AUDIT.md without running audit agent** (data must be accurate)

---

## Example: Full Audit Workflow

### Scenario: Implementing Sprint 1 Patient Search

```bash
# 1. Implement feature
# ... write code ...

# 2. Before commit: Spawn audit agent
Task({
  description: "Audit patient search implementation",
  model: "sonnet",
  prompt: "Audit patient search endpoint against Sprint 1 PRD..."
})

# 3. Audit agent analyzes and reports
## Audit Summary
Compliance: 95%
Breaking Changes: 0
Minor Discrepancies: 3 (gender null, department null, sourceValue)

# 4. Read AUDIT.md to review findings
cat AUDIT.md
# Shows: Patient Search API section updated
# Compliance: 95%
# Issues: 3 minor (documented as pending enhancements)

# 5. Update CONTEXT.md with technical details
# Document what changed, why, how

# 6. Commit with both files
git add AUDIT.md CONTEXT.md backend/app/
git commit -m "feat(patient-search): implement search API (95% PRD-compliant)"

# 7. Pre-commit hook verifies
✅ CONTEXT.md is being updated
✅ AUDIT.md is being updated
✅ Commit proceeds

# 8. Weekly: Run full Sprint audit
Task({
  description: "Full Sprint 1 audit",
  prompt: "Audit ALL Sprint 1 features against PRD..."
})

# 9. Sprint end: Comprehensive review
# Audit agent updates compliance trends
# Documents lessons learned
# Provides recommendations for Sprint 2
```

---

## Troubleshooting

### "Audit agent taking too long"

**Solution**: Use quick audit for commits, full audit weekly

```typescript
// Quick audit (5-10 min)
Task({
  description: "Quick audit of recent changes",
  prompt: "Audit only files modified in current commit against relevant PRD section..."
})

// Full audit (30-60 min)
Task({
  description: "Full Sprint audit",
  prompt: "Audit ALL Sprint features comprehensively..."
})
```

### "AUDIT.md shows 70% compliance - what do I do?"

**Solution**: Prioritize by severity

1. **Fix breaking changes first** (critical)
2. **Address security issues** (high priority)
3. **Document minor discrepancies** (track for future)
4. **Plan improvement sprints** (gradual increase)

### "Drift detected - how to resolve?"

**Solution**: Document, fix, re-audit

```bash
# 1. Audit agent detected drift
Drift: Response field "total" → "count"

# 2. Fix immediately
# Change back to "total"

# 3. Re-run audit to confirm
Task({ prompt: "Re-audit patient search after fixing drift..." })

# 4. Update AUDIT.md
# Move drift from "Active" to "Historical (Resolved)"

# 5. Commit fix
git commit -m "fix(patient-search): revert drift - restore 'total' field"
```

---

## Success Metrics

**This skill is successful when**:
- ✅ AUDIT.md stays current (updated with every commit)
- ✅ Drift detected early (within days, not weeks)
- ✅ Compliance scores trend upward (⬆️)
- ✅ Breaking changes resolved immediately
- ✅ Implementation agents read AUDIT.md before committing
- ✅ No surprises in production (all issues documented)

---

## References

- **AUDIT.md**: PRD compliance audit trail (project root)
- **CONTEXT.md**: Technical project memory
- **prd-compliance-checker skill**: Validation for new code
- **PRD Location**: `.specify/sprints/` and `.specify/phases/`
- **Validation Script**: `./scripts/validate-code.sh --prd-check`

---

**Last Updated**: 2025-11-18
**Version**: 1.0.0
**Maintained By**: AI Assistant (Claude Code)
