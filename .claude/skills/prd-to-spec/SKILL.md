---
name: prd-to-spec
description: Converts Product Requirement Documents (PRDs) to Spec-Kit specifications following project constitution principles. Use when transforming Sprint PRDs into actionable specifications, creating plans from requirements, or breaking down features into tasks. Ensures alignment with Patient Safety First, Privacy by Design, and other constitutional principles. Guides spec → plan → tasks workflow.
---

# PRD to Spec-Kit Converter Expert Skill

## When to use this skill

Activate when:
- Converting Sprint PRDs to Spec-Kit specifications
- Creating technical plans from specifications
- Breaking specifications into task lists
- Validating specs align with project constitution
- Starting implementation of a new feature (spec-first approach)
- Reviewing existing specs for constitutional compliance

## Spec-Kit Framework Overview

**Philosophy**: Specifications before code. Specs are primary design artifacts, not scaffolding.

**Workflow**:
```
Constitution (one-time)
  ↓
Specification (.specify/specifications/{name}.md)
  ↓ (what + why)
Technical Plan (.specify/plans/{name}-plan.md)
  ↓ (how)
Task List (.specify/tasks/{name}-tasks.md)
  ↓ (step-by-step)
Implementation (code)
```

## PRD Format (Input)

**Typical PRD Structure** (from Sprint 1 example):
```markdown
# PRD: Sprint X - Feature Name

## 1. Objective
Success definition, business value

## 2. Background & Context
Problem statement, solution, business value

## 3. User Stories
As a {role}, I want to {action}, so that {benefit}
Acceptance criteria per story

## 4. Functional Requirements
FR1, FR2, ... (with schemas, endpoints)

## 5. Non-Functional Requirements
Performance, security, reliability, scalability

## 6. Acceptance Criteria
Measurable definition of "done"

## 7. Testing Strategy
Unit, integration, E2E, performance tests

## 8. Dependencies
External services, data requirements, infrastructure

## 9. Risks & Mitigation
High-risk items, assumptions

## 10. Success Metrics
Launch criteria, post-launch metrics

## 11. Open Questions
Unresolved design decisions
```

## Spec-Kit Specification Format (Output)

**Template** (`.specify/specifications/{feature-name}.md`):
```markdown
# Specification: {Feature Name}

## Context
Why is this feature needed?
What problem does it solve?
Business value?

## Goals
- Primary goals (3-5 items)
- Secondary goals (optional)

## Non-Goals
- What is explicitly out of scope?
- Prevents scope creep

## User Stories
- As a {role}, I want to {action}, so that {benefit}
  - **Acceptance Criteria**:
    - [ ] Criterion 1
    - [ ] Criterion 2

## Requirements

### Functional Requirements
- **FR1**: {Description with measurable criteria}
- **FR2**: ...

### Non-Functional Requirements
- **NFR1: Performance** - Response time <500ms (p95)
- **NFR2: Security** - RBAC, encryption at rest/transit
- **NFR3: Accessibility** - WCAG 2.1 AA compliance

## Constraints
- Technical constraints (e.g., must integrate with MedCAT Service)
- Regulatory constraints (HIPAA, GDPR)
- Organizational constraints (team size, timeline)

## Acceptance Criteria
- [ ] Measurable definition of "done"
- [ ] Test coverage >= 85%
- [ ] Performance benchmarks met
- [ ] Security review passed

## Alignment with Constitution
Reference specific principles from `.specify/constitution/project-constitution.md`:
- **Patient Safety First**: How this meets 90%+ accuracy requirement
- **Privacy by Design**: Audit logging, encryption, RBAC
- **Evidence-Based Development**: Validation plan with clinicians
- **Transparency**: Confidence scores, explainability

## Open Questions
- Q1: {Question}
  - **Status**: Resolved / Pending
  - **Answer**: {Decision + rationale}
```

## Conversion Process

### Step 1: Extract Context and Goals

**From PRD**:
- Section 1 (Objective) → **Context + Goals**
- Section 2 (Background) → **Context**
- Section 10 (Success Metrics) → **Goals**

**Example**:

**PRD Input**:
```markdown
## 1. Objective
Build core patient search capability that enables clinicians to find patients
based on medical concepts extracted from clinical notes using MedCAT NLP.

**Success Definition**: Clinicians can find relevant patients within 500ms
by searching for medical conditions/concepts.

## 2. Background & Context
### Problem Statement
Finding patients with specific medical conditions requires:
- Manual chart review (time-consuming, error-prone)
- Reliance on structured data codes (incomplete)

### Business Value
- Time Savings: Reduce patient identification time from hours to seconds
- Quality Improvement: Identify all relevant patients
```

**Spec Output**:
```markdown
## Context
Clinicians currently spend hours manually reviewing charts to identify patients
with specific medical conditions. This process is time-consuming, error-prone,
and limited to structured data codes which are often incomplete or outdated.

This feature enables clinicians to search free-text clinical notes using
MedCAT's NLP capabilities, reducing patient identification time from hours
to seconds and improving quality by finding all relevant patients.

## Goals
- Enable sub-500ms patient search by medical concept
- Reduce patient identification time by 95% (hours → seconds)
- Improve patient capture rate by 30% (vs structured data only)
- Foundation for cohort building and quality improvement workflows
```

### Step 2: Extract User Stories

**From PRD**:
- Section 3 (User Stories) → **User Stories**
- Keep acceptance criteria as checklist items

**Example**:

**PRD Input**:
```markdown
## 3.1 Core Search Functionality
**As a** clinician
**I want to** search for patients by medical condition/concept
**So that** I can quickly identify relevant patients for review

**Acceptance Criteria**:
- Given I enter "atrial flutter" in search box
- When I click Search
- Then I see list of patients with that concept in their notes
- And results appear within 500ms
- And each result shows patient demographics + concept highlights

**Priority**: P0
```

**Spec Output**:
```markdown
## User Stories

### US1: Search Patients by Concept
As a clinician, I want to search for patients by medical condition/concept,
so that I can quickly identify relevant patients for review.

**Acceptance Criteria**:
- [ ] User can enter concept in search box (min 3 chars)
- [ ] Results appear within 500ms (p95)
- [ ] Results show patient demographics (MRN, age, gender, department)
- [ ] Results highlight matching concepts in context
- [ ] Results sorted by relevance (default)

**Priority**: P0
```

### Step 3: Extract Requirements

**From PRD**:
- Section 4 (Functional Requirements) → **Functional Requirements**
- Section 5 (Non-Functional Requirements) → **Non-Functional Requirements**
- Section 8 (Dependencies) → **Constraints**

**Filtering Logic**:
- Keep high-level requirements (what, not how)
- Move implementation details (API schemas, DB schemas) to **Technical Plan**
- Extract performance targets as **NFRs**

**Example**:

**PRD Input**:
```markdown
## 4. Functional Requirements
### 4.1 Search Input
**Input Schema**:
```typescript
interface PatientSearchQuery {
  concept: string
  filters?: {
    temporal?: 'current' | 'historical' | 'all'
    includeNegated?: boolean
    includeFamily?: boolean
  }
}
```

### 4.2 Search Output
Returns list of patients with matching annotations
```

**Spec Output (Functional Requirements)**:
```markdown
### Functional Requirements
- **FR1**: Search by medical concept (free text, minimum 3 characters)
- **FR2**: Filter by temporal context (current, historical, all)
- **FR3**: Exclude negated conditions (e.g., "No history of diabetes")
- **FR4**: Exclude family history (e.g., "Mother has cancer")
- **FR5**: Return patient demographics + matching annotations
- **FR6**: Support pagination (default 20 results per page, max 100)
```

**Plan Output (Implementation Details)**:
```markdown
## API Design

### Endpoint: Search Patients
```http
POST /api/v1/patients/search
```

**Request Schema**:
```typescript
interface PatientSearchQuery {
  concept: string
  filters?: {
    temporal?: 'current' | 'historical' | 'all'
    includeNegated?: boolean
    includeFamily?: boolean
  }
  pagination?: { page: number, pageSize: number }
}
```
```

### Step 4: Extract Constraints

**From PRD**:
- Section 8 (Dependencies) → **Constraints**
- Section 9 (Risks/Assumptions) → **Constraints**

**Example**:

**PRD Input**:
```markdown
## 8. Dependencies
### 8.1 External Services
**MedCAT Service**:
- Required: Yes (critical path)
- Version: >= 2.0
- Endpoint: http://medcat-service:5000/api/process
- Performance: < 200ms per document

### 8.2 Data Requirements
**Patient Data**:
- Minimum: 1,000 patients for testing
- Annotations: Pre-processed with MedCAT
```

**Spec Output**:
```markdown
## Constraints

### Technical Constraints
- Must integrate with existing MedCAT Service (v2.0+)
- Requires Elasticsearch 8.0+ for patient search
- Patient data must be pre-annotated with MedCAT (CUIs + meta-annotations)
- MedCAT Service must respond within 200ms per document

### Regulatory Constraints
- HIPAA compliance: Audit logging for all patient searches
- GDPR Article 32: Encryption in transit (TLS 1.3) and at rest (AES-256)
- Minimum necessary standard: Return only patient ID and demographics (no full records)

### Organizational Constraints
- Team size: 1-3 developers (sequential development acceptable)
- Timeline: 2 weeks (Sprint 1)
- Test environment must mirror production infrastructure
```

### Step 5: Validate Constitutional Alignment

**Check each constitutional principle**:
1. Patient Safety First
2. Privacy by Design
3. Evidence-Based Development
4. Modularity and Composability
5. Open Standards and Interoperability
6. Transparency and Explainability
7. Performance and Scalability
8. Developer Experience
9. Clinical Workflow Integration
10. Continuous Improvement

**Example**:

**Spec Output**:
```markdown
## Alignment with Constitution

### 1. Patient Safety First ✓
- **Accuracy**: Meta-annotation filtering ensures 95% precision (vs 60% without)
- **Validation**: Search results show confidence scores (user can judge reliability)
- **Fallback**: If MedCAT Service unavailable, return cached results with warning

### 2. Privacy by Design ✓
- **Audit Logging**: All searches logged with user ID, timestamp, query, IP
- **Encryption**: TLS 1.3 in transit, AES-256 at rest (PostgreSQL)
- **RBAC**: Only users with `clinician` role can access patient search
- **Minimum Necessary**: Return patient ID + demographics only (not full charts)

### 3. Evidence-Based Development ✓
- **Validation Plan**: Usability testing with 10 clinicians before GA
- **Performance Targets**: <500ms response time (p95) - defined upfront
- **Success Metrics**: Time savings (baseline: 2 hours manual search, target: <5 minutes)

### 4. Transparency and Explainability ✓
- **Confidence Scores**: Display MedCAT confidence for each annotation
- **Source Context**: Click annotation to view source document
- **Filter Clarity**: UI shows which meta-annotation filters are active

### 7. Performance and Scalability ✓
- **Response Time**: <500ms (p95) meets constitutional requirement
- **Load Testing**: Test to 10x expected peak (1000 concurrent searches)
- **Horizontal Scaling**: Stateless API enables load balancing

### 8. Developer Experience ✓
- **Test Coverage**: Minimum 85% (constitutional standard: 80%+)
- **API Documentation**: OpenAPI 3.0 spec included in plan
- **Consistent Patterns**: Follows existing MedCAT Service API conventions
```

### Step 6: Extract Acceptance Criteria

**From PRD**:
- Section 6 (Acceptance Criteria) → **Acceptance Criteria**
- Section 10 (Success Metrics / Launch Criteria) → **Acceptance Criteria**

**Make criteria SMART** (Specific, Measurable, Achievable, Relevant, Time-bound):

**Example**:

**PRD Input**:
```markdown
## 6. Acceptance Criteria
### 6.1 Functional Acceptance
- Search by concept works
- Temporal filter works
- Results appear quickly

### 6.2 Testing Acceptance
- Unit tests written
- Integration tests written
```

**Spec Output (Better)**:
```markdown
## Acceptance Criteria

### Functional Acceptance
- [ ] User can search patients by concept ("atrial flutter") and receive results
- [ ] Temporal filter ("Current only") excludes historical mentions (verified with test data)
- [ ] Negation filter excludes "No history of X" (verified with test data)
- [ ] Family history filter excludes "Mother has X" (verified with test data)
- [ ] 95% of searches complete within 500ms (load tested with 100 concurrent users)
- [ ] Results display patient demographics (MRN, age, gender, department)
- [ ] Clicking annotation shows source document with highlighted text

### Non-Functional Acceptance
- [ ] All patient searches logged to audit trail (user ID, timestamp, query, result count)
- [ ] Authentication required (unauthenticated requests return 401)
- [ ] Authorization enforced (only `clinician` role can search patients)
- [ ] Encryption verified (TLS 1.3 in transit via SSL Labs test)

### Testing Acceptance
- [ ] Unit test coverage >= 85% (measured by pytest-cov)
- [ ] 15+ unit tests for search service logic
- [ ] 5+ integration tests for API endpoint
- [ ] 1 E2E test for complete search workflow (Playwright)
- [ ] Load test passed (100 concurrent users, <500ms p95, 0% error rate)

### Quality Acceptance
- [ ] Code review approved by 1+ developer
- [ ] Security review passed (Snyk scan, 0 critical vulnerabilities)
- [ ] Usability testing with 3+ clinicians (SUS score >68)
- [ ] Documentation updated (API spec, user guide, CONTEXT.md)
```

## Step 7: Document Open Questions

**From PRD**:
- Section 11 (Open Questions) → **Open Questions**
- Add status tracking (Resolved / Pending)

**Example**:

**PRD Input**:
```markdown
## 11. Open Questions
1. **Q**: What should happen when MedCAT service is down?
   **A**: Return cached results with warning banner.

2. **Q**: How should we handle concept ambiguity (e.g., "MI" matches multiple concepts)?
   **A**: Show all matching concepts with radio buttons.
```

**Spec Output**:
```markdown
## Open Questions

### Q1: MedCAT Service Downtime Behavior
**Question**: What should happen when MedCAT Service is unavailable?

**Status**: ✅ Resolved

**Decision**: Return cached results (Redis, 5-minute TTL) with warning banner:
"Using cached data - MedCAT Service unavailable"

**Rationale**:
- Aligns with "Performance and Scalability" principle (graceful degradation)
- Better UX than complete failure
- 5-minute cache acceptable for most use cases

**Implementation**: See Technical Plan Section 4.3 (Error Handling)

---

### Q2: Concept Ambiguity Handling
**Question**: How handle ambiguous search terms (e.g., "MI" = Myocardial Infarction OR Mitral Insufficiency)?

**Status**: ✅ Resolved

**Decision**: Show concept disambiguation UI:
1. Search "MI" → MedCAT returns multiple CUIs
2. Display radio buttons: ○ Myocardial Infarction (C0027051) ○ Mitral Insufficiency (C0026266)
3. User selects → search with specific CUI

**Rationale**:
- Aligns with "Transparency and Explainability" (user understands what's being searched)
- Prevents false positives from searching all CUIs
- Common pattern in medical search UIs

**Implementation**: See Technical Plan Section 5.2 (Concept Disambiguation)
```

## Constitutional Compliance Checklist

When converting PRD → Spec, verify:

**Patient Safety First**:
- [ ] Accuracy requirements defined (e.g., 90%+ for safety-critical)
- [ ] Confidence thresholds specified
- [ ] Fallback to manual process if confidence low
- [ ] Manual review for safety-critical alerts

**Privacy by Design**:
- [ ] No PHI in logs (spec explicitly forbids)
- [ ] Encryption at rest and in transit (AES-256, TLS 1.3)
- [ ] RBAC enforced at API level
- [ ] Audit logging for all PHI access
- [ ] Data retention policy defined

**Evidence-Based Development**:
- [ ] Acceptance criteria measurable
- [ ] Validation plan with real users (min 10)
- [ ] Performance benchmarks defined upfront
- [ ] A/B testing or pilot deployment plan (if applicable)

**Modularity and Composability**:
- [ ] Services communicate via documented APIs
- [ ] No direct database access between services
- [ ] Independent deployment possible

**Open Standards and Interoperability**:
- [ ] Concepts mapped to SNOMED-CT or LOINC
- [ ] FHIR R4 compliance (if applicable)
- [ ] No proprietary data formats for export

**Transparency and Explainability**:
- [ ] Confidence scores displayed
- [ ] Source document references provided
- [ ] Model limitations documented

**Performance and Scalability**:
- [ ] P95 latency targets defined (<500ms user-facing, <200ms API)
- [ ] Load testing to 10x expected peak
- [ ] Horizontal scaling supported

**Developer Experience**:
- [ ] Test coverage >= 80% (critical paths: 100%)
- [ ] API changes include OpenAPI specs
- [ ] Documentation updated

**Clinical Workflow Integration**:
- [ ] Min 3 clinicians involved in design
- [ ] Usability testing on real workflows
- [ ] Task completion time <2 minutes for common operations

**Continuous Improvement**:
- [ ] Model accuracy tracking plan
- [ ] User feedback collection mechanism
- [ ] Release notes plan

## Example: PRD → Spec Conversion (Condensed)

**PRD**: Sprint 1 - Patient Search & Discovery (docs/prd/sprint-1/patient-search-discovery.md)

**Generated Spec** (`.specify/specifications/patient-search.md`):

```markdown
# Specification: Patient Search by Medical Concept

## Context
Clinicians spend hours manually reviewing charts to identify patients with
specific conditions. This feature enables NLP-powered search across clinical
notes, reducing identification time from hours to seconds.

## Goals
- Sub-500ms concept-based patient search
- 95% precision via meta-annotation filtering
- Foundation for cohort building workflows

## Non-Goals
- Patient-facing search (this is for clinicians only)
- Full-text search (concept-based only)
- Historical record search (current system data only)

## User Stories
### US1: Search by Concept
As a clinician, I want to search patients by medical concept, so that I
can identify relevant patients quickly.

**Acceptance Criteria**:
- [ ] Search completes in <500ms (p95)
- [ ] Results show demographics + annotations
- [ ] Concepts highlighted in context

### US2: Filter by Temporal Context
As a clinician, I want to filter by current vs historical conditions, so
that I find patients with active conditions.

**Acceptance Criteria**:
- [ ] "Current only" filter excludes historical mentions
- [ ] Filter updates results in <200ms

## Requirements
### Functional Requirements
- **FR1**: Search by medical concept (free text, min 3 chars)
- **FR2**: Filter by temporal context (current/historical/all)
- **FR3**: Exclude negated conditions
- **FR4**: Exclude family history
- **FR5**: Pagination (20 per page, max 100)

### Non-Functional Requirements
- **NFR1: Performance** - <500ms response (p95), <200ms filter updates
- **NFR2: Security** - RBAC (`clinician` role), audit logging, TLS 1.3
- **NFR3: Accuracy** - 95% precision via meta-annotation filtering
- **NFR4: Scalability** - 100 concurrent users, horizontal scaling

## Constraints
### Technical Constraints
- MedCAT Service v2.0+ required
- Elasticsearch 8.0+ required
- Patient data pre-annotated with MedCAT

### Regulatory Constraints
- HIPAA: Audit all searches (user, timestamp, query)
- GDPR Article 32: Encrypt in transit/rest
- Minimum necessary: Return only ID + demographics

## Acceptance Criteria
- [ ] Search functional (verified with test data)
- [ ] 95% searches <500ms (load tested, 100 users)
- [ ] Test coverage >= 85%
- [ ] Security review passed
- [ ] Usability tested with 3+ clinicians

## Alignment with Constitution
- **Patient Safety**: 95% precision via meta-annotations
- **Privacy**: Audit logging, encryption, RBAC
- **Transparency**: Confidence scores, source context
- **Performance**: <500ms meets target

## Open Questions
### Q1: MedCAT Service Downtime?
**Status**: ✅ Resolved
**Decision**: Return cached results with warning
```

**Next**: Create Technical Plan (`.specify/plans/patient-search-plan.md`)

## Next Steps

After creating specification:
1. **Review with stakeholders** (clinicians, product owner, compliance)
2. **Update specification** based on feedback
3. **Create technical plan** (`.specify/plans/{name}-plan.md`)
4. **Create task list** (`.specify/tasks/{name}-tasks.md`)
5. **Begin implementation** (code with tests)
6. **Update CONTEXT.md** before each commit (git hook enforces)
