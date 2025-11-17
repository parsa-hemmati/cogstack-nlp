---
name: spec-kit-enforcer
description: Enforces Spec-Kit workflow (Constitution → Specification → Plan → Tasks → Implementation) for new features. Use when user requests a new feature, starting implementation, or before writing code. Checks for missing specifications, incomplete plans, or tasks not created. Prevents "code first, document later" anti-pattern and ensures alignment with project constitution.
---

# Spec-Kit Enforcer

Ensures the Spec-Kit framework is followed for all new feature development, preventing "code first, document later" anti-pattern.

## Spec-Kit workflow

```
1. Constitution → 2. Specification → 3. Plan → 4. Tasks → 5. Implementation
```

**Required files** for each feature:
- `.specify/specifications/{feature-name}.md`
- `.specify/plans/{feature-name}-plan.md`
- `.specify/tasks/{feature-name}-tasks.md`

## When to invoke this skill

Activate automatically when:
- User requests a new feature
- About to start coding a new component
- Creating API endpoints or database schemas
- Implementing any feature mentioned in PROJECT_PLAN.md

**Before writing any code**, verify the Spec-Kit workflow is complete.

## Quick verification checklist

```
Spec-Kit Checklist:
- [ ] Constitution review completed
- [ ] Specification exists (.specify/specifications/{feature}.md)
- [ ] Plan exists (.specify/plans/{feature}-plan.md)
- [ ] Tasks exist (.specify/tasks/{feature}-tasks.md)
- [ ] Tasks broken into 1-2 hour chunks
- [ ] Specification aligns with constitution principles
- [ ] All tasks have acceptance criteria
```

## Step-by-step workflow enforcement

### Step 1: Review Constitution

**Before ANY feature work**, review:
```bash
cat .specify/constitution/project-constitution.md
```

**Check alignment** with 10 core principles:
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

**Ask**: Does this feature align with these principles?

---

### Step 2: Check for Existing Specification

**Search**:
```bash
ls .specify/specifications/

# Look for feature name
find .specify/specifications -name "*{feature-keyword}*.md"
```

**If specification EXISTS**: Read it completely before coding

**If specification DOES NOT exist**: Create it first (see template below)

---

### Step 3: Verify Specification Contents

**Required sections** in every specification:

```markdown
# Specification: {Feature Name}

## Context
- Why is this needed?
- What problem does it solve?
- Business value?

## Goals
- Primary goals (3-5 items)

## Non-Goals
- What is explicitly out of scope?

## User Stories
- As a {role}, I want to {action}, so that {benefit}
- Include acceptance criteria

## Requirements
### Functional Requirements
- FR1: {Description with measurable criteria}

### Non-Functional Requirements
- NFR1: Performance (e.g., <500ms response time)
- NFR2: Security (e.g., RBAC, encryption)
- NFR3: Accessibility (e.g., WCAG 2.1 AA)

## Constraints
- Technical, regulatory, organizational constraints

## Acceptance Criteria
- [ ] Measurable definition of "done"
- [ ] Test coverage requirements
- [ ] Performance benchmarks

## Alignment with Constitution
- Which principles does this address?
- Which non-negotiables are met?
```

**Validation**:
```bash
# Check specification exists and has required sections
grep -q "## Context" .specify/specifications/{feature}.md
grep -q "## Requirements" .specify/specifications/{feature}.md
grep -q "## Acceptance Criteria" .specify/specifications/{feature}.md
```

---

### Step 4: Check for Technical Plan

**Search**:
```bash
ls .specify/plans/

# Look for plan matching specification
find .specify/plans -name "*{feature}*-plan.md"
```

**Required sections** in technical plan:

```markdown
# Technical Plan: {Feature Name}

## Architecture
- High-level diagram
- Component interactions
- Data flows

## Technology Choices
- Libraries/frameworks to use
- Rationale for each choice

## Implementation Phases
- Phase 1, Phase 2, etc.

## API Design
- Endpoint specifications (OpenAPI format preferred)
- Request/response examples

## Data Model
- Database schema changes
- Elasticsearch index updates

## Testing Strategy
- Unit tests (what to test)
- Integration tests (scenarios)
- E2E tests (user workflows)

## Deployment
- Infrastructure changes
- Rollout strategy
- Rollback plan

## Risks
- Technical risks + mitigation
```

---

### Step 5: Verify Task Breakdown

**Search**:
```bash
ls .specify/tasks/

find .specify/tasks -name "*{feature}*-tasks.md"
```

**Task requirements**:
- Each task completable in 1-2 hours
- Independent tasks can be done in parallel
- Dependencies clearly noted
- Acceptance criteria specific and testable

**Template**:
```markdown
# Tasks: {Feature Name}

## Task 1: {Short Description}
**Goal**: {What this accomplishes}
**Prerequisites**: {What must exist first}
**Steps**:
1. {Specific action}
2. {Specific action}
**Acceptance**: {How to verify}
**Estimated Time**: {Duration}
```

---

### Step 6: Implement Task-by-Task

**For EACH task**:
1. ✅ Read task description completely
2. ✅ Write tests FIRST (TDD)
3. ✅ Implement to pass tests
4. ✅ Refactor if needed
5. ✅ Document changes in code comments
6. ✅ Update task status (completed)
7. ✅ **Update CONTEXT.md** (mandatory)
8. ✅ Commit with proper message

**Do NOT**:
- ❌ Skip ahead to future tasks
- ❌ Implement features not in spec
- ❌ Skip tests ("I'll add them later")
- ❌ Leave TODOs without creating tasks
- ❌ Skip CONTEXT.md update

## Enforcement workflow

When user requests a feature:

**Example**: "Implement patient search"

**Enforcer action**:

```
1. Check: Does specification exist?
   → Run: find .specify/specifications -name "*patient-search*.md"
   → If NO: "Specification not found. Creating specification first..."
   → If YES: "Found specification: .specify/specifications/patient-search.md"

2. Check: Does plan exist?
   → Run: find .specify/plans -name "*patient-search*-plan.md"
   → If NO: "Plan not found. Creating technical plan..."
   → If YES: "Found plan: .specify/plans/patient-search-plan.md"

3. Check: Do tasks exist?
   → Run: find .specify/tasks -name "*patient-search*-tasks.md"
   → If NO: "Tasks not found. Breaking down into tasks..."
   → If YES: "Found tasks: .specify/tasks/patient-search-tasks.md"

4. Read task list
   → Display first incomplete task
   → Ask: "Ready to implement Task 1: {task description}?"

5. Before coding:
   → Remind: "Write tests FIRST (TDD approach)"
   → Remind: "Update CONTEXT.md when complete"
```

## Creating missing artifacts

### If specification is missing:

```markdown
I notice there's no specification for {feature}. Following Spec-Kit workflow, we need to create:

1. Specification (.specify/specifications/{feature}.md)
2. Technical Plan (.specify/plans/{feature}-plan.md)
3. Task Breakdown (.specify/tasks/{feature}-tasks.md)

Should I help create these documents first, or would you like to create them yourself?

Here's a starting template for the specification:
[Include template from Step 3 above]
```

### If plan is missing:

```markdown
Found specification, but no technical plan. Creating plan now...

Based on the specification, I'll create a technical plan covering:
- Architecture and component interactions
- Technology choices
- API design
- Data model
- Testing strategy

Would you like to review the plan before we proceed to task breakdown?
```

### If tasks are missing:

```markdown
Specification and plan exist. Now breaking down into tasks...

Based on the plan, I'll create tasks that are:
- Completable in 1-2 hours each
- Testable with clear acceptance criteria
- Ordered by dependencies

Task breakdown will be in .specify/tasks/{feature}-tasks.md
```

## Constitution alignment check

Before implementing any feature, verify alignment:

```
Constitution Alignment:
- [ ] Patient Safety: Does this protect patient safety?
- [ ] Privacy: Does this handle PHI correctly?
- [ ] Evidence-Based: Is this based on clinical evidence/need?
- [ ] Modular: Is this a reusable component?
- [ ] Interoperable: Does this use open standards?
- [ ] Transparent: Are decisions explainable?
- [ ] Performant: Does this meet performance requirements?
- [ ] Developer-Friendly: Is this maintainable?
- [ ] Clinical Workflow: Does this fit clinical workflows?
- [ ] Continuous Improvement: Can this be iterated?
```

**If any checkmark is missing**: Stop and address before coding.

## Example enforcement scenarios

### Scenario 1: User jumps straight to coding

**User**: "Let's implement patient search API"

**Enforcer**:
```
Checking Spec-Kit workflow...

✗ Specification not found
✗ Plan not found
✗ Tasks not found

Following Spec-Kit framework, we need to create these documents before coding.

Would you like me to:
A) Create the specification based on docs/prd/sprint-1-patient-search.md
B) Guide you through creating the specification
C) Proceed without specification (not recommended)
```

### Scenario 2: Specification exists, but incomplete

**User**: "Start implementing the search endpoint"

**Enforcer**:
```
Found specification: .specify/specifications/patient-search.md

Reviewing specification...

✓ Context section present
✓ Goals defined
✗ Missing: Non-functional requirements (performance, security)
✗ Missing: Acceptance criteria

The specification is incomplete. Should we:
A) Complete the specification first
B) Proceed with incomplete spec (not recommended)
```

### Scenario 3: Everything in order

**User**: "Implement patient search"

**Enforcer**:
```
✓ Specification: .specify/specifications/patient-search.md
✓ Plan: .specify/plans/patient-search-plan.md
✓ Tasks: .specify/tasks/patient-search-tasks.md

Reading task list...

Next task: Task 3: Implement Elasticsearch query builder

Prerequisites met:
✓ Task 1: Complete (Database schema created)
✓ Task 2: Complete (API endpoint scaffold)

Ready to implement Task 3. Reminder:
- Write tests FIRST
- Update CONTEXT.md when complete
- Commit with proper message format

Proceeding with implementation...
```

## Integration with other skills

Works with:
- `healthcare-compliance-checker`: Specifications must address compliance
- `medcat-meta-annotations`: Specifications should mention meta-annotation filtering
- `vue3-component-reuse`: UI tasks should reference existing components
- `fhir-r4-mapper`: FHIR integration needs specification

## File structure reference

```
.specify/
├── README.md                          # Spec-Kit framework guide
├── constitution/
│   └── project-constitution.md        # 10 core principles
├── specifications/
│   ├── patient-search.md              # Example spec
│   └── meta-annotations-ui.md         # Example spec
├── plans/
│   ├── patient-search-plan.md         # Technical plans
│   └── fhir-integration-plan.md
└── tasks/
    ├── patient-search-tasks.md        # Task breakdowns
    └── timeline-view-tasks.md
```

## Common anti-patterns to prevent

### Anti-pattern 1: "I'll document it later"

```
User: "Let's just code it quickly, I'll add docs later"

Enforcer: "Following Spec-Kit framework, documentation comes BEFORE code.
This ensures:
- Clear requirements (avoid rework)
- Stakeholder alignment
- Compliance documentation
- AI context preservation

Estimated time to create spec: 30-60 minutes
Time saved by avoiding rework: 4-8 hours

Should we create the specification first?"
```

### Anti-pattern 2: Vague specifications

```
Specification says: "Build a good search feature"

Enforcer: "This specification is too vague. Missing:
- Measurable acceptance criteria
- Performance requirements
- Security requirements
- API contract details

Would you like help making this specification more specific?"
```

### Anti-pattern 3: Skipping constitution review

```
User: "Just implement it"

Enforcer: "Have you reviewed the project constitution?
This feature involves patient data, so we need to verify:
- Patient Safety First (principle #1)
- Privacy by Design (principle #2)
- Healthcare Standards (principle #5)

Should we review constitution alignment first?"
```

## Quick commands for verification

```bash
# Check if spec exists for a feature
find .specify/specifications -name "*{keyword}*.md"

# Check if plan exists
find .specify/plans -name "*{keyword}*.md"

# Check if tasks exist
find .specify/tasks -name "*{keyword}*.md"

# List all specifications
ls .specify/specifications/

# Read constitution
cat .specify/constitution/project-constitution.md

# Validate specification structure (check for required sections)
grep "## Context\|## Requirements\|## Acceptance" .specify/specifications/{feature}.md
```

## Checklist before allowing implementation

```
Pre-Implementation Checklist:
- [ ] Constitution reviewed and aligned
- [ ] Specification exists and complete
- [ ] Plan exists with architecture and tech choices
- [ ] Tasks exist with 1-2 hour granularity
- [ ] Current task has clear acceptance criteria
- [ ] Prerequisites for current task are met
- [ ] Test strategy is defined
- [ ] CONTEXT.md will be updated after completion
```

**Only proceed to implementation when ALL boxes are checked.**

## Remember

Spec-Kit is not bureaucracy—it's:
- **Risk mitigation** (avoid building wrong thing)
- **Context preservation** (AI assistants understand intent)
- **Compliance documentation** (required for healthcare)
- **Team alignment** (everyone understands the goal)
- **Quality assurance** (acceptance criteria defined upfront)

**The time spent on specification saves 5-10x the time in implementation and rework.**

## When to be flexible

Exceptions to strict enforcement:
- Bug fixes (don't need full spec)
- Trivial changes (<30 min, no new features)
- Documentation updates
- Configuration changes
- Urgent production issues

For these cases, skip to implementation but still update CONTEXT.md.

## Resources

**Spec-Kit framework guide**: [.specify/README.md](../../.specify/README.md)

**Constitution**: [.specify/constitution/project-constitution.md](../../.specify/constitution/project-constitution.md)

**Example specification**: [.specify/specifications/meta-annotations-ui.md](../../.specify/specifications/meta-annotations-ui.md)

**Project guide**: [CLAUDE.md](../../CLAUDE.md)
