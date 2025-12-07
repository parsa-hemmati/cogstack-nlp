# PRD Compliance Checker Skill

**Version**: 1.0.0
**Last Updated**: 2025-11-18
**Type**: Quality Assurance / Validation
**Activation**: Model-invoked (automatic when modifying API-related files)

---

## Purpose

Prevents API implementation drift from Product Requirement Documents (PRDs) by providing guidance on validating compliance during development.

**Problem Solved**: Catches PRD discrepancies early (during development) rather than late (after commit/review).

**Use When**:
- Modifying API endpoint files (`backend/app/api/v1/endpoints/*.py`)
- Changing request/response schemas (`backend/app/schemas/*.py`)
- Updating service layer for API features (`backend/app/services/*_service.py`)
- Implementing Sprint PRD requirements

---

## Activation Context

This skill **automatically activates** when you are:

1. **Implementing API Endpoints**
   - Creating new routes
   - Modifying existing endpoint parameters
   - Changing HTTP methods or paths

2. **Modifying Schemas**
   - Adding/removing Pydantic models
   - Changing field names or types
   - Updating nested object structures

3. **Working on Sprint Features**
   - Implementing PRD specifications
   - Adding new API functionality
   - Refactoring API contracts

---

## Quick Compliance Checklist

Before committing API changes, verify:

### ✅ Endpoint Compliance

- [ ] **Path matches PRD** - Exact path from specification
- [ ] **HTTP method matches PRD** - GET/POST/PUT/DELETE/PATCH
- [ ] **Path parameters match PRD** - `/patients/{mrn}` not `/patients/{id}`
- [ ] **Query parameters match PRD** - Names, types, defaults

**Example**:
```
PRD: POST /api/v1/patients/search?includeAnnotations=true
Code: POST /api/v1/patients/search?include_annotations=true  ❌ MISMATCH
```

---

### ✅ Request Schema Compliance

- [ ] **Field names match PRD** - Exact case (camelCase vs snake_case)
- [ ] **Nested structure matches PRD** - Flat vs nested objects
- [ ] **Required/optional fields match PRD** - Don't make optional fields required
- [ ] **Field types match PRD** - String vs number vs boolean vs object vs array
- [ ] **Enum values match PRD** - "current" | "historical" not "Current" | "Historical"

**Example**:
```
PRD: { "pagination": { "page": 1, "pageSize": 20 } }
Code: { "page": 1, "page_size": 20 }  ❌ MISMATCH (flat, snake_case)
```

---

### ✅ Response Schema Compliance

- [ ] **Success response structure matches PRD** - Field names, nesting
- [ ] **Array wrapper matches PRD** - `results` array vs direct array
- [ ] **Metadata fields match PRD** - `total`, `page`, `pageSize`, `queryTimeMs`
- [ ] **Nested objects match PRD** - `demographics`, `annotations`, etc.
- [ ] **Field naming convention matches PRD** - camelCase throughout

**Example**:
```
PRD: { "results": [...], "total": 42, "queryTimeMs": 123 }
Code: { "data": [...], "total_count": 42, "query_time": 123 }  ❌ MISMATCH
```

---

### ✅ Error Response Compliance

- [ ] **HTTP status codes match PRD** - 400, 401, 403, 404, 422, 500
- [ ] **Error schema matches PRD** - `{ "error": { "code": "...", "message": "..." } }`
- [ ] **Error codes match PRD** - `INVALID_CONCEPT` not `InvalidConcept`
- [ ] **Error messages documented** - All error scenarios from PRD

**Example**:
```
PRD: 400 { "error": { "code": "INVALID_FILTER", "message": "..." } }
Code: 400 { "detail": "Invalid filter" }  ❌ MISMATCH
```

---

### ✅ Authentication & Authorization Compliance

- [ ] **Auth requirement matches PRD** - Public vs authenticated vs role-based
- [ ] **Required roles match PRD** - `researcher` vs `clinician` vs `admin`
- [ ] **Token type matches PRD** - Bearer JWT vs API key
- [ ] **RBAC enforcement implemented** - `require_role()` dependency

---

### ✅ Pagination & Filtering Compliance

- [ ] **Pagination parameters match PRD** - `page`, `pageSize` vs `offset`, `limit`
- [ ] **Default values match PRD** - `pageSize=20` not `page_size=10`
- [ ] **Max page size matches PRD** - `pageSize <= 100` not `<= 50`
- [ ] **Filter parameters match PRD** - Boolean flags vs enum values
- [ ] **Sort options match PRD** - `relevance` | `name` | `lastUpdated`

---

### ✅ Performance Requirements Compliance

- [ ] **Response time target met** - PRD specifies `<500ms`, verify with load test
- [ ] **Pagination implemented** - Don't return unbounded arrays
- [ ] **Database indexes created** - For filter fields, sort fields
- [ ] **N+1 queries avoided** - Use eager loading, joins

---

## Deep Validation: Spawn Validation Agent

For comprehensive PRD compliance checking, spawn a validation agent:

### When to Run Deep Validation

**Before committing**:
- New API endpoints (always)
- Schema changes affecting API contract (always)
- Breaking changes to existing endpoints (always)

**Before creating PR**:
- Completing Sprint implementation
- Major refactoring of API layer

### How to Spawn Validation Agent

Use the `Task` tool with this prompt template:

```typescript
Task({
  subagent_type: "general-purpose",
  description: "Validate PRD compliance",
  model: "sonnet", // Use sonnet for thorough validation
  prompt: `You are a PRD compliance validation agent. Your task is to comprehensively compare the implementation against the Product Requirement Document.

**Context**: I just implemented [describe feature/endpoint]

**PRD Location**: .specify/sprints/sprint-[N]-prd.md (Section: [section name])

**Files to Validate**:
- Backend endpoint: backend/app/api/v1/endpoints/[name].py
- Request schema: backend/app/schemas/[name].py
- Response schema: backend/app/schemas/[name].py
- Service layer: backend/app/services/[name]_service.py

**Validation Tasks**:

1. **Read PRD specification completely**
   - Find the relevant feature section
   - Extract exact API contract (endpoints, schemas, errors)
   - Note all requirements (functional, non-functional)

2. **Read implementation files completely**
   - Endpoint paths, methods, parameters
   - Request/response Pydantic models
   - Service layer logic
   - Error handling

3. **Compare Implementation vs PRD**

   **Endpoints**:
   - [ ] Path matches (exact string)
   - [ ] HTTP method matches
   - [ ] Path parameters match (names, types)
   - [ ] Query parameters match (names, types, defaults)

   **Request Schema**:
   - [ ] Field names match (case-sensitive)
   - [ ] Field types match
   - [ ] Nested structure matches
   - [ ] Required/optional matches
   - [ ] Enum values match
   - [ ] Default values match

   **Response Schema**:
   - [ ] Success response structure matches
   - [ ] Field names match (case-sensitive)
   - [ ] Nested objects match
   - [ ] Array structures match
   - [ ] Metadata fields match

   **Error Responses**:
   - [ ] HTTP status codes match
   - [ ] Error schema matches
   - [ ] Error codes match
   - [ ] All error scenarios documented

   **Authentication**:
   - [ ] Auth requirement matches (public/authenticated/RBAC)
   - [ ] Required roles match

   **Performance**:
   - [ ] Response time requirement noted
   - [ ] Pagination implemented if required

4. **Report Findings**

   Generate a report in this format:

   ## PRD Compliance Validation Report

   ### ✅ Compliant Items
   - [List all items that match PRD exactly]

   ### ⚠️ Breaking Changes (CRITICAL)
   - [List all items that differ from PRD and break compatibility]
   - **For each**: Provide exact PRD requirement vs actual implementation
   - **For each**: Suggest fix

   ### 📝 Minor Discrepancies (Non-Breaking)
   - [List all items that differ but don't break compatibility]
   - Examples: Missing optional fields, extra fields not in PRD

   ### ❌ Missing Features (Not Implemented)
   - [List all PRD requirements not yet implemented]

   ### 📊 Summary
   - Total checks: X
   - Compliant: X
   - Breaking changes: X
   - Minor discrepancies: X
   - Missing features: X
   - **Status**: PASS / FAIL

   ### 🔧 Recommended Actions
   1. [Specific action to fix breaking change #1]
   2. [Specific action to fix breaking change #2]
   ...

**Start validation now. Be extremely thorough - check EVERY field name, type, and structure.**`
})
```

---

## Manual Validation Steps

If you prefer manual validation (faster but less thorough):

### Step 1: Open PRD File

```bash
# Find the relevant PRD
ls .specify/sprints/

# Read the PRD section
cat .specify/sprints/sprint-1-prd.md | grep -A 50 "Patient Search"
```

### Step 2: Compare Endpoint Definition

**PRD Specification**:
```
POST /api/v1/patients/search
Request: { concept, filters, pagination, sort }
Response: { results, total, page, pageSize, queryTimeMs }
```

**Implementation**:
```bash
# Check endpoint path and method
grep -A 5 "@router.post" backend/app/api/v1/endpoints/patient_search.py
```

### Step 3: Compare Request Schema

```bash
# Check Pydantic model
grep -A 30 "class.*Request" backend/app/schemas/patient_search.py
```

Compare field names one-by-one against PRD.

### Step 4: Compare Response Schema

```bash
# Check Pydantic model
grep -A 30 "class.*Response" backend/app/schemas/patient_search.py
```

Compare field names, types, nesting against PRD.

### Step 5: Check for Breaking Changes

**Breaking Change Indicators**:
- ❌ Field renamed (PRD: `concept`, Code: `query`)
- ❌ Field type changed (PRD: `string`, Code: `number`)
- ❌ Required field made optional or vice versa
- ❌ Nested structure flattened or vice versa
- ❌ Enum values changed

**Non-Breaking Changes**:
- ✅ Added optional field not in PRD
- ✅ Added extra error code not in PRD
- ✅ More detailed documentation

---

## Integration with Validation Workflow

This skill works alongside the existing 4-layer validation framework:

**Layer 1: Pre-Commit Hook** (Automatic)
- Runs syntax checks, tests

**Layer 2: Validation Script** (Manual before milestones)
- `./scripts/validate-code.sh --full`

**Layer 3: PRD Compliance Checker** (This skill - Manual/Agent)
- Quick checklist or deep agent validation

**Layer 4: CI/CD Pipeline** (Automatic on push)
- Full test suite, security scans

---

## Common PRD Drift Patterns

Learn from past mistakes:

### 1. Field Naming Drift

**Pattern**: Python conventions (snake_case) applied instead of PRD (camelCase)

**Example**:
```python
# PRD specifies camelCase
class Response(BaseModel):
    total: int
    pageSize: int  # ✅ Matches PRD

# Common mistake
class Response(BaseModel):
    total: int
    page_size: int  # ❌ snake_case doesn't match PRD
```

**Prevention**: Always check PRD field names character-by-character

---

### 2. Structure Flattening Drift

**Pattern**: Nested objects in PRD implemented as flat structure

**Example**:
```python
# PRD specifies nested structure
class Request(BaseModel):
    pagination: Pagination  # ✅ Nested object

# Common mistake
class Request(BaseModel):
    page: int  # ❌ Flat structure
    page_size: int
```

**Prevention**: Check object nesting in PRD diagrams

---

### 3. Filter Logic Inversion Drift

**Pattern**: Boolean filter logic inverted (include vs exclude)

**Example**:
```python
# PRD specifies "include" semantics
includeNegated: bool = False  # False = exclude negated mentions ✅

# Common mistake
negationFilter: Literal["Affirmed", "Negated"] = "Affirmed"  # Different semantics ❌
```

**Prevention**: Understand filter semantics in PRD (include vs exclude)

---

### 4. Enum Value Drift

**Pattern**: Enum values use different case or format

**Example**:
```python
# PRD specifies lowercase string literals
temporal: Literal["current", "historical", "future"]  # ✅

# Common mistake
temporal: Literal["Current", "Historical", "Future"]  # ❌ Capitalized
```

**Prevention**: Check PRD examples for exact enum values

---

## Pre-Push Hook Integration

A git pre-push hook will automatically suggest PRD validation when API files change.

**Hook behavior**:
- Detects if `backend/app/api/`, `backend/app/schemas/`, or service files changed
- Suggests running PRD validation agent
- Provides exact command to run
- **Non-blocking**: Warns but doesn't abort push

**Manual override**: Push without validation using `git push --no-verify` (not recommended)

---

## Validation Script Enhancement

The validation script will be enhanced with a `--prd-check` flag:

```bash
# Run PRD compliance validation
./scripts/validate-code.sh --prd-check

# Spawns validation agent automatically
# Compares all API files against PRD specifications
# Generates compliance report
```

---

## Best Practices

### ✅ DO

- **Check PRD before coding** - Read the exact specification first
- **Validate early** - Use quick checklist during development
- **Deep validate before commit** - Spawn agent for new endpoints
- **Document deviations** - If you intentionally deviate from PRD, document in commit message
- **Update PRD if needed** - If PRD is wrong, update it (with user approval)

### ❌ DON'T

- **Assume PRD format** - Always check, don't guess field names
- **Use Python conventions** - Follow PRD naming (even if it's camelCase)
- **Skip validation for "small changes"** - Small changes can break contracts
- **Commit with known PRD drift** - Fix it before committing

---

## Example Usage

### Scenario: Implementing Patient Timeline Endpoint

**PRD Location**: `.specify/sprints/sprint-2-prd.md` (Timeline View section)

**Step 1**: Read PRD specification
```bash
cat .specify/sprints/sprint-2-prd.md | grep -A 100 "GET /api/v1/patients/{mrn}/timeline"
```

**Step 2**: Note exact API contract
- Path: `/api/v1/patients/{mrn}/timeline`
- Method: `GET`
- Path params: `mrn` (string)
- Query params: `startDate`, `endDate` (optional)
- Response: `{ events: [...], patient: {...} }`

**Step 3**: Implement endpoint

**Step 4**: Run quick checklist
- ✅ Path matches: `/api/v1/patients/{mrn}/timeline`
- ✅ Method matches: `GET`
- ✅ Path param: `mrn` (string)
- ✅ Query params: `startDate`, `endDate` (optional)
- ⚠️ Response field: `events` (check if array structure matches)

**Step 5**: Spawn validation agent (before commit)
```python
Task({
  subagent_type: "general-purpose",
  description: "Validate timeline endpoint PRD compliance",
  prompt: "Validate backend/app/api/v1/endpoints/patient_timeline.py against Sprint 2 PRD timeline section..."
})
```

**Step 6**: Fix any breaking changes found

**Step 7**: Commit with PRD compliance note
```
feat(timeline): implement patient timeline endpoint

Changes:
- Added GET /api/v1/patients/{mrn}/timeline endpoint
- Implemented event aggregation from documents
- Added timeline response schema

PRD Compliance:
- Validated against Sprint 2 PRD (Timeline View section)
- All endpoint parameters match PRD exactly
- Response schema matches PRD specification
- Validation agent report: 0 breaking changes
```

---

## Troubleshooting

### "I found a PRD discrepancy - what do I do?"

**If PRD is correct**:
1. Fix implementation to match PRD
2. Document the fix in commit message
3. Update CONTEXT.md with what was wrong

**If PRD is incorrect**:
1. Ask user for clarification
2. Update PRD with user approval
3. Document PRD change in CONTEXT.md
4. Implement according to updated PRD

---

### "The validation agent is taking too long"

**Solution**: Use quick checklist for routine changes, agent for complex changes

**Quick checklist suitable for**:
- Minor field additions (non-breaking)
- Documentation updates
- Internal refactoring (no API contract change)

**Agent validation required for**:
- New endpoints
- Schema changes
- Breaking changes
- Sprint completion

---

## Success Metrics

**This skill is successful when**:
- ✅ PRD drift caught during development (not after commit)
- ✅ Zero breaking changes in API contracts
- ✅ Frontend developers don't encounter unexpected API changes
- ✅ PRD and implementation stay aligned throughout sprints

---

## References

- **Related Skills**: `spec-kit-enforcer`, `healthcare-compliance-checker`
- **Validation Script**: `./scripts/validate-code.sh`
- **PRD Location**: `.specify/sprints/`
- **CLAUDE.md Section**: "Code Review Checklist"

---

**Last Updated**: 2025-11-18
**Version**: 1.0.0
**Maintained By**: AI Assistant (Claude Code)
