# Spec-Kit: Specification-Driven Development

**Framework**: [GitHub Spec-Kit](https://github.com/github/spec-kit)
**Purpose**: Enable AI agents to build features systematically from detailed specifications

---

## Overview

This directory contains **specifications as executable artifacts** for the CogStack NLP Full Potential UI project. Instead of jumping directly to code, we create detailed specs that guide AI agents in generating working implementations.

**Philosophy**: Specifications are not discardable scaffolding—they are the primary design artifact.

---

## Directory Structure

```
.specify/
├── README.md                    # This file
├── constitution/                # Project principles and governance
│   └── project-constitution.md  # Core values, principles, decision-making
├── specifications/              # Feature requirements (WHAT and WHY)
│   ├── fhir-integration.md
│   ├── meta-annotations-ui.md
│   └── compliance-dashboard.md
├── plans/                       # Technical implementation strategies (HOW)
│   ├── fhir-integration-plan.md
│   └── meta-annotations-ui-plan.md
└── tasks/                       # Actionable task breakdowns
    ├── fhir-integration-tasks.md
    └── meta-annotations-ui-tasks.md
```

---

## How to Use Spec-Kit

### Step 1: Establish Constitution (One-Time)

**File**: `.specify/constitution/project-constitution.md`

**Purpose**: Define guiding principles that inform all decisions.

**Contents**:
- Vision and mission
- Core principles (e.g., "Privacy by Design", "Patient Safety First")
- Non-negotiable requirements
- Technology constraints
- Governance structure

**When to Update**: Annually, or when major strategic changes occur.

---

### Step 2: Write Specification (Per Feature)

**Location**: `.specify/specifications/{feature-name}.md`

**Purpose**: Define **WHAT** needs to be built and **WHY**.

**Template**:

```markdown
# Specification: {Feature Name}

## Context
Why is this feature needed? What problem does it solve?

## Goals
- What are the desired outcomes?
- What does success look like?

## Non-Goals
- What is explicitly out of scope?

## User Stories
- As a {role}, I want to {action}, so that {benefit}

## Requirements
- Functional requirements
- Non-functional requirements (performance, security, etc.)
- Constraints (technical, regulatory, organizational)

## Acceptance Criteria
- Measurable criteria for "done"
- How will we validate it works?

## Open Questions
- Unresolved design decisions
- Areas needing clarification
```

**Example**: See `.specify/specifications/fhir-integration.md`

---

### Step 3: Create Technical Plan (Per Feature)

**Location**: `.specify/plans/{feature-name}-plan.md`

**Purpose**: Define **HOW** to implement the specification.

**Template**:

```markdown
# Technical Plan: {Feature Name}

## Architecture
- High-level architecture diagram
- Component interactions
- Data flows

## Technology Stack
- Frameworks, libraries, tools
- Rationale for choices

## Implementation Approach
- Phases of development
- Dependencies
- Risk mitigation

## API Design
- Endpoint specifications
- Request/response examples
- Error handling

## Data Model
- Database schema
- Data structures

## Testing Strategy
- Unit tests
- Integration tests
- E2E tests

## Deployment Plan
- Infrastructure requirements
- Rollout strategy
- Rollback procedures
```

**Example**: See `.specify/plans/fhir-integration-plan.md`

---

### Step 4: Break into Tasks (Per Feature)

**Location**: `.specify/tasks/{feature-name}-tasks.md`

**Purpose**: Create actionable, ordered tasks for AI agents or developers.

**Template**:

```markdown
# Tasks: {Feature Name}

## Task 1: {Description}
- **Goal**: {What this accomplishes}
- **Prerequisites**: {What must be done first}
- **Steps**:
  1. {Specific action}
  2. {Specific action}
- **Acceptance**: {How to verify it's done}
- **Estimated Time**: {Duration}

## Task 2: {Description}
...
```

**Example**: See `.specify/tasks/fhir-integration-tasks.md`

---

### Step 5: Implement (AI Agent)

**Command**: `/speckit.implement {feature-name}`

**Process**:
1. Agent reads constitution, specification, plan, and tasks
2. Implements feature systematically, task by task
3. Tests each task against acceptance criteria
4. Documents decisions and deviations
5. Updates specs if requirements change

---

## Workflow Example

### Scenario: Add FHIR Integration Feature

**1. Write Specification**

```bash
# Create specification
nano .specify/specifications/fhir-integration.md

# Contents:
- Context: Need to integrate with FHIR-compliant EHR systems
- Goals: Expose NLP results as FHIR Observations
- Requirements: FHIR R4 compliance, support for DocumentReference input
- Acceptance Criteria: Successfully create FHIR Observation from MedCAT output
```

**2. Get Clarification** (Optional)

```
User: "Should we support FHIR R5?"
Agent: "Specification says R4. R5 is in draft status. Recommend R4 for stability, with R5 as future roadmap item."
User: "Agreed. Update spec to clarify R4 only for v1."
```

**3. Create Technical Plan**

```bash
# Agent creates plan based on spec
.specify/plans/fhir-integration-plan.md

# Contents:
- Architecture: FastAPI service + FHIR client library
- Tech Stack: fhir.resources (Python), HAPI FHIR test server
- Implementation: 3 phases (read DocumentReference, process with MedCAT, write Observation)
```

**4. Generate Tasks**

```bash
# Agent breaks plan into tasks
.specify/tasks/fhir-integration-tasks.md

# Tasks:
1. Set up HAPI FHIR test server
2. Create FHIR client wrapper
3. Implement DocumentReference → text extraction
4. Integrate MedCAT processing
5. Map MedCAT output → FHIR Observation
6. Write integration tests
7. Deploy and validate
```

**5. Implement**

```
Agent: "Starting Task 1: Set up HAPI FHIR test server"
Agent: [Creates docker-compose.yml, starts HAPI FHIR]
Agent: "Task 1 complete. Verified FHIR server accessible at http://localhost:8080/fhir"

Agent: "Starting Task 2: Create FHIR client wrapper"
Agent: [Writes fhir_client.py, adds to project]
Agent: "Task 2 complete. Tests passing (15/15)"

...
```

---

## Best Practices

### 1. Start with Why

Every specification should answer:
- **Why is this needed?** (Business value, user pain point)
- **Why now?** (Prioritization rationale)
- **Why this approach?** (Alternatives considered)

---

### 2. Make Specifications Testable

**Bad**:
```markdown
- System should be fast
```

**Good**:
```markdown
- P95 API response time < 500ms
- Search results returned in < 500ms for queries with <1000 results
- Tested with 500 concurrent users
```

---

### 3. Document Decisions

**Use Architecture Decision Records (ADRs)**:

```markdown
## ADR 001: Use FHIR R4 Over R5

**Date**: 2025-01-07
**Status**: Accepted

**Context**: Need to choose FHIR version.

**Decision**: Use FHIR R4.

**Rationale**:
- R4 is stable and widely adopted
- R5 is still in ballot (draft)
- All major EHRs support R4

**Consequences**:
- May need migration path to R5 in future
- R4 limitations accepted (e.g., no R5 subscriptions)
```

Store in `.specify/specifications/{feature}/adr/`

---

### 4. Keep Specs Updated

**Specifications are living documents**:
- Update when requirements change
- Document deviations from original plan
- Link to implementation PRs
- Version specifications (like code)

---

### 5. Review Regularly

**Specification Reviews**:
- **Who**: Product Owner, Tech Lead, Relevant SMEs
- **When**: Before implementation starts
- **Checklist**:
  - [ ] Aligns with constitution
  - [ ] Clear acceptance criteria
  - [ ] Dependencies identified
  - [ ] Risks documented
  - [ ] Stakeholder sign-off

---

## AI Agent Commands

### Available Commands

```bash
# Establish or review project constitution
/speckit.constitution

# Write a specification for a feature
/speckit.specify {feature-name}

# Create technical plan from specification
/speckit.plan {feature-name}

# Generate task breakdown from plan
/speckit.tasks {feature-name}

# Implement feature from tasks
/speckit.implement {feature-name}

# Review and refine existing spec
/speckit.review {feature-name}
```

---

## Examples

### Example 1: FHIR Integration

- **Specification**: `.specify/specifications/fhir-integration.md`
- **Plan**: `.specify/plans/fhir-integration-plan.md`
- **Tasks**: `.specify/tasks/fhir-integration-tasks.md`

### Example 2: Meta-Annotations UI

- **Specification**: `.specify/specifications/meta-annotations-ui.md`
- **Plan**: `.specify/plans/meta-annotations-ui-plan.md`
- **Tasks**: `.specify/tasks/meta-annotations-ui-tasks.md`

---

## FAQ

### Q: When should I create a specification?

**A**: For any non-trivial feature (>4 hours of work) or architectural change.

**Exceptions**: Bug fixes, minor UI tweaks, documentation updates usually don't need full specs.

---

### Q: Can specifications change after implementation starts?

**A**: Yes, but document why:
- Add "Change Log" section to specification
- Link to relevant issues/PRs
- Update version number

---

### Q: What if an AI agent deviates from the plan?

**A**: Document deviations in plan:

```markdown
## Deviations from Original Plan

### Deviation 1: Used PostgreSQL instead of MongoDB

**Reason**: Discovered MongoDB license incompatible with Elastic License 2.0

**Impact**: Required rewriting data layer

**Approved By**: Tech Lead (2025-01-10)
```

---

### Q: How detailed should tasks be?

**A**: Detailed enough that an AI agent can complete without ambiguity.

**Rule of thumb**: Each task should be completable in one AI session (≈1 hour).

---

## Contributing

**To add a new feature specification**:

1. Copy template: `cp .specify/templates/specification-template.md .specify/specifications/my-feature.md`
2. Fill in all sections
3. Submit for review (PR to `.specify/specifications/`)
4. Get approval from Product Owner
5. Create plan and tasks
6. Begin implementation

---

## Related Resources

- [Spec-Kit GitHub Repository](https://github.com/github/spec-kit)
- [Project Constitution](./constitution/project-constitution.md)
- [CogStack NLP Documentation](../docs/)

---

**Questions?** Open an issue or contact the Tech Lead.
