# AI Assistant Guide for CogStack NLP

**Version**: 1.6.0
**Last Updated**: 2025-11-18
**Purpose**: Guide AI assistants (Claude Code, GitHub Copilot, etc.) on project conventions and best practices

---

## 🎯 Project Overview

**Project**: CogStack NLP Full Potential UI
**Domain**: Healthcare Natural Language Processing
**Tech Stack**: Vue 3, TypeScript, FastAPI, PostgreSQL, Elasticsearch, Docker
**Compliance**: HIPAA, GDPR, 21 CFR Part 11

**Mission**: Build a comprehensive, modular platform that leverages MedCAT's full NLP capabilities to transform healthcare research, delivery, and governance.

---

## 🧠 CRITICAL: Read CONTEXT.md First!

**⚠️ MANDATORY**: Before starting ANY work, read [CONTEXT.md](CONTEXT.md)

**CONTEXT.md is the project's living memory** containing:
- Current system state (what's implemented, what's not)
- Architecture Decision Records (ADRs)
- Recent changes and why they were made
- Integration points and dependencies
- Known issues and technical debt
- Key design patterns and conventions

**Why this matters**: Prevents context loss between sessions, ensures you have complete picture before coding.

**Update requirement**: BOTH CONTEXT.md AND AUDIT.md MUST be updated with EVERY code commit (no exceptions).
- **CONTEXT.md** = Technical memory (what changed, why, how)
- **AUDIT.md** = Compliance audit (PRD alignment, drift detection)

**Read it now**: [CONTEXT.md](CONTEXT.md) (15-20 minutes)

---

## 📊 Session Management & Context Preservation

**⚠️ CRITICAL**: Monitor context usage throughout the session to prevent abrupt cutoffs

### ⛔ BEFORE Starting ANY Big Task - CHECK CONTEXT FIRST!

**🔴 MANDATORY CHECK**: Before starting ANY significant task (creating plans, task breakdowns, major implementations), check your current context usage:

```
Current token usage visible in system messages:
Token usage: X/200000; Y remaining
```

**Decision Tree**:

**If ≥70% used** (≤30% remaining):
- ❌ **DO NOT start big task**
- ✅ **Create session summary immediately** (using template below)
- ✅ **Generate continuation prompt for user**
- ✅ **Tell user**: "Context at 70%. I recommend starting a fresh session for this large task. I've prepared a detailed continuation prompt for you."
- ✅ **Start NEW session** with the continuation prompt

**If 50-70% used** (30-50% remaining):
- ⚠️ **Proceed with caution**
- ✅ **Warn user**: "Context at X%. This task may require summarizing mid-way. Recommend breaking into smaller chunks or starting fresh session."
- ✅ **Check context every 10% during task**
- ✅ **Prepare to summarize at 80%**

**If <50% used** (>50% remaining):
- ✅ **Safe to proceed** with big task
- ✅ **Still check context periodically** (every major step)

**Examples of "Big Tasks"**:
- Creating technical plans (3,000+ lines)
- Creating task breakdowns (2,000+ lines)
- Implementing full features (multiple files)
- Major refactoring (touching many files)
- Writing comprehensive documentation

**This prevents**:
- Running out of context mid-task (frustrating!)
- Losing work progress (incomplete commits)
- Context amnesia (forgetting decisions made earlier)
- User having to repeat context in new session

### When to Summarize

**Trigger**: When context usage reaches **≥80%** (≤20% remaining)

**Check context usage regularly**:
- Look for `<budget:token_budget>` or token usage indicators in system messages
- Example: "Token usage: 160000/200000" means 80% used → **TIME TO SUMMARIZE**
- **PROACTIVE**: Check at start of every major task, not just when low

### How to Create Session Summary

When context is running low, **PROACTIVELY** create a comprehensive summary following this structure:

```markdown
## Session Summary for Continuation

### 1. Current Objective
[What we're working on - be specific]

Example: "Creating Technical Plan for Clinical Care Tools Base Application"

### 2. Work Completed This Session
[List everything accomplished with specific details]

- ✅ Created 3 implementation workflow skills (spec-to-tech-plan, tech-plan-to-tasks, infrastructure-expert)
- ✅ Enhanced base app specification with 5 CRITICAL sections (v1.1.0)
- ✅ Updated CLAUDE.md and CONTEXT.md with new skills
- ✅ Added git hooks for quality enforcement (commit-msg, prepare-commit-msg)

### 3. Current State
[Describe the exact state of the project right now]

- Base app specification: Complete (v1.1.0) at `.specify/specifications/clinical-care-tools-base-app.md`
- Implementation skills: 8 skills covering full Spec-Kit workflow
- Git hooks: Installed and tested (pre-commit, commit-msg, prepare-commit-msg)
- Next phase: Ready to create Technical Plan

### 4. Files Modified/Created
[List all files touched with brief description]

**Created**:
- `.claude/skills/spec-to-tech-plan/SKILL.md` - Technical plan generation guidance
- `.claude/skills/tech-plan-to-tasks/SKILL.md` - Task breakdown guidance
- `.claude/skills/infrastructure-expert/SKILL.md` - Infrastructure patterns
- `.git-hooks/commit-msg` - Commit message format enforcement
- `.git-hooks/prepare-commit-msg` - Commit message template

**Modified**:
- `CLAUDE.md` - Updated to v1.2.0 with 8 skills
- `CONTEXT.md` - Updated current phase status
- `.git-hooks/README.md` - Documented all hooks

**Commits**: 645c303b, ccf3311d

### 5. Immediate Next Steps
[Clear, actionable steps for the next session]

**Next Task**: Create Technical Plan for Clinical Care Tools Base Application

**Steps**:
1. Read base app specification: `.specify/specifications/clinical-care-tools-base-app.md`
2. Use `spec-to-tech-plan` skill to guide technical plan creation
3. Create `.specify/plans/clinical-care-tools-base-plan.md`
4. Include: API design, database schema, testing strategy, deployment architecture
5. Get user approval before proceeding to task breakdown

### 6. Important Context
[Any decisions, constraints, or key information for the next session]

**Key Decisions**:
- Deployment: Single workstation with RDP access (not cloud)
- Storage: RTF files (~50KB) in PostgreSQL BYTEA
- Models: Shared MedCAT models volume (all users)
- PHI Handling: Store identifiable PHI, extract via MedCAT
- Retention: 8 years for clinical records (NHS compliance)

**Constraints**:
- Must follow Spec-Kit workflow (no code before plan + tasks)
- HIPAA/GDPR compliance required
- CONTEXT.md must be updated with every commit

### 7. Open Questions/Blockers
[Anything that needs user input or decision]

- None currently - ready to proceed with Technical Plan

### 8. References
[Links to key files/documentation]

- Specification: `.specify/specifications/clinical-care-tools-base-app.md` (v1.1.0)
- Skills: `.claude/skills/README.md` (8 skills documented)
- Constitution: `.specify/constitution/project-constitution.md`
- CONTEXT.md: Recent changes and ADRs
```

### Creating Continuation Prompt

**After creating summary**, generate a continuation prompt following **Claude 4 best practices** (see [docs](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)):

```markdown
## Continuation Prompt for Next Session

This session is being continued from a previous conversation that ran out of context.

**Previous Session Summary**:

[Paste the session summary here]

**Your task**: Continue from where we left off.

**Immediate next steps**:
1. Read CONTEXT.md to understand current project state
2. Review base app specification at `.specify/specifications/clinical-care-tools-base-app.md`
3. Begin creating Technical Plan using `spec-to-tech-plan` skill
4. Save plan to `.specify/plans/clinical-care-tools-base-plan.md`
5. Get user approval before proceeding

**Important**:
- Follow Spec-Kit workflow strictly (Constitution → Spec → Plan → Tasks → Code)
- Use the 8 implementation skills (they activate automatically)
- Update CONTEXT.md with every commit (git hooks enforce this)
- Maintain HIPAA/GDPR compliance throughout

**Ask the user**: "I've reviewed the context. Ready to create the Technical Plan for the Clinical Care Tools Base Application. Should I proceed?"
```

### Best Practices for Continuation Prompts

Following [Claude 4 best practices](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices):

**DO**:
- ✅ **Be specific**: Include exact file paths, commit SHAs, version numbers
- ✅ **Provide structure**: Use clear sections (Summary, Context, Next Steps)
- ✅ **Reference artifacts**: Link to files, specs, documentation
- ✅ **State current phase**: Where are we in the workflow?
- ✅ **List decisions made**: Architecture choices, constraints, rationale
- ✅ **Include open questions**: What needs user input?
- ✅ **Provide immediate action**: Clear first step for the new session

**DON'T**:
- ❌ **Be vague**: "Continue working on the project" is not helpful
- ❌ **Omit context**: Assume the next session will remember everything
- ❌ **Skip file paths**: Always include specific file locations
- ❌ **Forget constraints**: Healthcare compliance, deployment model, etc.
- ❌ **Leave open loops**: Document all decisions and their rationale

### Example Workflow

**At 80% context usage** (160k/200k tokens):

1. **Stop current work** (finish current commit if possible)
2. **Create session summary** using template above
3. **Generate continuation prompt** with full context
4. **Save summary** (optional: commit to repo as `.specify/sessions/YYYY-MM-DD-summary.md`)
5. **Share with user**: "Context running low. I've created a summary for the next session. Here's what we accomplished..."

### Checking Context Usage

**System messages show token usage**:
```
<budget:token_budget>200000</budget:token_budget>
Token usage: 160000/200000; 40000 remaining
```

**Calculate percentage**:
- Used: 160000 / 200000 = 80% ✅ **TIME TO SUMMARIZE**
- Remaining: 40000 / 200000 = 20%

**Thresholds**:
- **≥70% used** (≤30% remaining): **⛔ DO NOT START BIG TASKS** - Recommend new session to user
- **≥80% used** (≤20% remaining): **CREATE SUMMARY NOW** - Stop work, summarize immediately
- **≥90% used** (≤10% remaining): **URGENT** - Summarize immediately, high risk of cutoff
- **≥95% used** (≤5% remaining): **CRITICAL** - May be cut off mid-response, summarize instantly

### Preventing Context Loss

**Throughout the session**:
1. **Update CONTEXT.md frequently** - Git hooks enforce this, but do it proactively
2. **Commit often** - Atomic commits preserve state
3. **Document decisions** - ADRs in CONTEXT.md for architecture choices
4. **Reference specs** - Always link to specification files
5. **Track progress** - Use TodoWrite tool to maintain task list

**This prevents**:
- Lost context between sessions
- Repeated questions or work
- Inconsistent decisions
- Missing implementation details

---

## 🛠️ Custom Healthcare NLP Skills

**10 specialized skills** are available to assist with healthcare-specific development. They **activate automatically** based on context—you don't need to invoke them explicitly.

### Available Skills

#### 🔴 Priority 1 (Critical - Safety & Accuracy)

**`healthcare-compliance-checker`** - HIPAA/GDPR compliance validation
- **Activates when**: Working with patient data, authentication, API endpoints, logging
- **What it does**: Catches PHI in logs, validates audit logging, checks encryption, verifies RBAC
- **Why critical**: Prevents regulatory violations and patient privacy breaches

**`medcat-meta-annotations`** - NLP accuracy (60% → 95% precision)
- **Activates when**: Processing NLP results, building queries, displaying medical concepts
- **What it does**: Explains 4 meta-annotations (Negation, Experiencer, Temporality, Certainty), provides filtering patterns
- **Why critical**: Eliminates false positives (family history, negated conditions, hypotheticals)

#### 🟡 Priority 2 (Highly Recommended)

**`vue3-component-reuse`** - Leverage 65 existing Vue components
- **Activates when**: Building UI features, forms, tables, modals, charts
- **What it does**: Searches MedCAT Trainer for reusable patterns, provides Composition API examples
- **Why useful**: Saves hours by reusing proven patterns

**`fhir-r4-mapper`** - FHIR R4 integration patterns
- **Activates when**: Implementing FHIR integration, clinical decision support, EHR interoperability
- **What it does**: Maps MedCAT output to FHIR resources, provides CDS Hooks patterns
- **Why useful**: Required for EHR integration (Sprint 3+)

#### 🟢 Priority 3 (Quality Assurance)

**`prd-compliance-checker`** - PRD validation
- **Activates when**: Modifying API endpoints, changing schemas, implementing Sprint PRDs
- **What it does**: Validates API implementation against PRD specifications, detects breaking changes (field names, types, structure)
- **Why useful**: Prevents API contract drift, catches PRD discrepancies early (during development, not after)

**`spec-kit-enforcer`** - Workflow enforcement
- **Activates when**: Starting new features, before writing code
- **What it does**: Ensures Spec-Kit framework followed, checks for specifications
- **Why useful**: Prevents "code first, document later" anti-pattern

#### 🔵 Priority 4 (Implementation Workflow)

**`spec-to-tech-plan`** - Technical plan generation
- **Activates when**: Converting specifications to technical plans, architecture design
- **What it does**: Creates API designs, database schemas, testing strategies, deployment architecture
- **Why useful**: Ensures complete planning before implementation

**`tech-plan-to-tasks`** - Task breakdown
- **Activates when**: Breaking down plans, creating task lists, estimating work
- **What it does**: Converts plans into 1-2 hour tasks with TDD approach, clear acceptance criteria
- **Why useful**: Enables granular tracking and parallel development

**`infrastructure-expert`** - Infrastructure implementation
- **Activates when**: Setting up Docker, PostgreSQL, authentication, audit logging
- **What it does**: Provides production-ready patterns for infrastructure, security, backups
- **Why useful**: Battle-tested healthcare infrastructure patterns

### How Skills Work

Skills are **model-invoked** (automatic activation) and work together across the full development lifecycle:

```
Example: "Build patient search feature"

Planning Phase:
✓ spec-kit-enforcer - Ensures specification exists
✓ spec-to-tech-plan - Creates API design, database schema, testing strategy
✓ tech-plan-to-tasks - Breaks into 8-12 implementable tasks (1-2 hours each)

Implementation Phase:
✓ infrastructure-expert - Guides Docker, PostgreSQL, auth, audit logging
✓ medcat-meta-annotations - Ensures proper NLP filtering (95% precision)
✓ healthcare-compliance-checker - Validates PHI handling, audit logging
✓ prd-compliance-checker - Validates API schema matches PRD (no drift)

Integration Phase:
✓ vue3-component-reuse - Finds existing UI patterns
✓ fhir-r4-mapper - Adds FHIR export capability

Result: Complete, compliant, production-ready implementation
```

**Complete Workflow Coverage**:
- **Spec → Plan → Tasks → Code** (full Spec-Kit lifecycle)
- **Safety & Compliance** (HIPAA, GDPR, patient safety)
- **NLP Accuracy** (meta-annotation filtering)
- **Infrastructure** (Docker, auth, audit, backups)

**Location**: `.claude/skills/`
**Documentation**: [.claude/skills/README.md](.claude/skills/README.md)

**For detailed guidance on each skill, they will automatically activate when relevant.**

---

## ⚠️ CRITICAL: Patient Safety & Compliance

### Non-Negotiable Requirements

**BEFORE writing ANY code, confirm:**

1. **Patient Safety**: Will this code handle clinical data?
   - ✅ If yes: Validate accuracy requirements (90%+ for safety-critical)
   - ✅ Consider false positive/negative impact
   - ✅ Add confidence thresholds and manual review checkpoints

2. **Privacy**: Will this code access PHI/PII?
   - ✅ If yes: Ensure audit logging
   - ✅ Validate encryption (TLS 1.3 in transit, AES-256 at rest)
   - ✅ Implement minimum necessary access control

3. **Compliance**: Does this involve patient data?
   - ✅ If yes: Review [compliance framework](docs/compliance/healthcare-compliance-framework.md)
   - ✅ Add HIPAA/GDPR audit trail
   - ✅ Document data flows

**If any answer is "yes" but you're unsure about compliance, STOP and ask the user for guidance.**

---

## 🛡️ Code Quality & Validation (MANDATORY)

**⚠️ CRITICAL**: This project has **5 layers of validation** to ensure code integrity and PRD compliance. You MUST use them proactively.

### The 5-Layer Validation Framework

```
Layer 1: Pre-Commit Hook (Automatic)     → Every commit
Layer 2: Validation Script (Manual)      → Before phase completion
Layer 3: Validation Agent (AI-powered)   → Complex features
Layer 4: PRD Compliance Check (Manual)   → API changes
Layer 5: CI/CD Pipeline (Automatic)      → Every push
```

**Documentation**: See `.claude/SAFEGUARDS.md`, `.claude/VALIDATION_CHECKLIST.md`, and `.claude/skills/prd-compliance-checker/SKILL.md`

---

### When to Use Each Layer

#### Layer 1: Pre-Commit Hook (Automatic - No Action Needed)

**Runs automatically** on every `git commit`. You don't invoke this - it just works.

**What it does**:
- ✅ Enforces CONTEXT.md updates
- ✅ Validates Python syntax
- ✅ **Runs tests on modified test files**
- ✅ Blocks commits with failing tests

**If it fails**:
```bash
# Fix the issues shown
# Then re-commit
git add .
git commit -m "fix: address validation issues"
```

---

#### Layer 2: Validation Script (Manual - Use Before Major Milestones)

**⚠️ MANDATORY: Run before completing any phase or major feature**

**When to run**:
- ✅ Before committing a completed phase
- ✅ After implementing 3+ related tasks
- ✅ Before creating a pull request
- ✅ When you've written >500 lines of code

**How to run**:
```bash
# Full validation (recommended)
./scripts/validate-code.sh --full

# Quick check (syntax only)
./scripts/validate-code.sh --quick

# Auto-fix formatting issues
./scripts/validate-code.sh --fix
```

**What it checks**:
1. Python syntax (all files)
2. Import validation
3. Type checking (mypy)
4. Code formatting (black)
5. **Full test suite** with coverage
6. TypeScript types
7. ESLint
8. Security (secrets, SQL injection)

**Example workflow**:
```python
# You just completed Phase 2 tasks

# 1. Run full validation
./scripts/validate-code.sh --full

# 2. Fix any issues found
# ... make fixes ...

# 3. Re-run to verify
./scripts/validate-code.sh --full

# 4. Commit when passing
git add .
git commit -m "feat: Phase 2 complete"
```

---

#### Layer 3: Validation Agent (AI-Powered - Use for Complex Features)

**⚠️ MANDATORY: Spawn validation agent for:**
- ✅ Complex features (>500 lines or >3 files)
- ✅ **BEFORE committing PHI-related code** (use `healthcare-compliance-checker`)
- ✅ Before phase completion (in addition to script)
- ✅ After major refactoring
- ✅ When implementing security-critical features

**How to invoke**:
Use the `Task` tool with `subagent_type="general-purpose"`:

```typescript
Task({
  subagent_type: "general-purpose",
  description: "Validate code quality",
  model: "sonnet", // Use sonnet for thorough validation
  prompt: `You are a code quality validation agent. Your task is to thoroughly validate the code.

**Context**: I just implemented [describe feature]

**Files to check**: [list files]

**Validation tasks:**
1. **Python Backend**:
   - Check syntax and imports
   - Verify type annotations
   - Look for security issues (SQL injection, XSS)
   - Check for hardcoded secrets

2. **HIPAA Compliance** (if PHI-related):
   - No PHI in application logs
   - Audit logging for all PHI access
   - Encryption in transit/at rest
   - RBAC enforcement

3. **Testing**:
   - Check if tests exist for new code
   - Verify test fixtures work
   - Check for missing edge cases

4. **Code Quality**:
   - Look for code smells
   - Check for unused imports
   - Verify error handling

**Report format:**

## Validation Results

### Critical Issues (blocking):
[List issues that prevent code from running]

### Warnings (non-blocking):
[List issues that should be fixed]

### Summary:
- Total files checked: X
- Critical issues: X
- Warnings: X
- Status: PASS/FAIL

**For EACH issue, provide:**
- File path and line number
- Issue type
- Exact error message
- Suggested fix

Start your validation now.`
})
```

**Special: Healthcare Compliance Checker**

For **ANY code touching patient data**, also invoke the `healthcare-compliance-checker` skill:

```typescript
Skill({
  skill: "healthcare-compliance-checker"
})
```

This skill automatically activates for PHI-related code, but invoke it explicitly before committing:
- API endpoints handling patient data
- Database schema changes
- Authentication/authorization changes
- Logging additions
- Any code accessing PHI

---

#### Layer 4: PRD Compliance Check (BLOCKING for AI Agents)

**⚠️ MANDATORY & BLOCKING: Required when modifying API endpoints or schemas**

**When it triggers** (automatic blocking):
- 🚫 **BLOCKS commits** with API endpoint changes
- 🚫 **BLOCKS commits** with schema changes (request/response)
- 🚫 **BLOCKS pushes** with API service layer changes

**AI Agent Workflow** (when hook triggers):
```bash
# 1. Hook detects API changes and BLOCKS the commit/push
# 2. Hook displays validation instructions
# 3. Run validation agent prompt generator:
./scripts/validate-code.sh --prd-check

# 4. Copy the generated Task(...) prompt
# 5. Paste into current AI session to spawn validation agent
# 6. Wait for validation results
# 7. If breaking changes found → Fix them
# 8. Re-run validation to confirm fixes
# 9. Answer 'y' when hook asks: "Has PRD validation PASSED?"
# 10. Commit/push proceeds
```

**What it checks**:
1. **Endpoint Compliance**: Path, method, parameters match PRD exactly
2. **Request Schema**: Field names, types, nesting match PRD
3. **Response Schema**: Field names (camelCase!), structure match PRD
4. **Error Responses**: HTTP codes, error schema match PRD
5. **Authentication**: Auth requirements match PRD
6. **Performance**: Response time targets noted

**Why critical**:
- Prevents API contract drift
- Avoids breaking frontend integration
- Catches mismatches early (during development, not after)
- Reduces back-and-forth with frontend team

**Example workflow**:
```python
# You just implemented POST /api/v1/patients/search

# 1. Run quick checklist
# Read: .specify/sprints/sprint-1-prd.md
# Compare field names: concept vs query? ✅ concept matches!
# Compare pagination: nested { pagination: {...} } vs flat? ✅ nested matches!

# 2. OR spawn validation agent for deep check
./scripts/validate-code.sh --prd-check
# Agent compares ALL fields character-by-character
# Reports: 0 breaking changes found ✅

# 3. Commit with confidence
git add .
git commit -m "feat(patient-search): implement search endpoint (PRD-compliant)"
```

**Git Hooks (BLOCKING)**:
- **Pre-commit hook**: BLOCKS commits with API endpoint or schema changes
- **Pre-push hook**: BLOCKS pushes with API service layer changes
- Both hooks require answering 'y' to "Has PRD validation PASSED with 0 breaking changes?"
- **Cannot bypass** without `--no-verify` (strongly discouraged in AI agent workflow)

**Skill Activation**:
The `prd-compliance-checker` skill automatically activates when you modify:
- `backend/app/api/v*/endpoints/*.py` (API endpoints)
- `backend/app/schemas/*.py` (Request/response schemas)
- `backend/app/services/*_service.py` (Service layer for API features)

The skill provides quick checklist and guidance. Hooks enforce mandatory validation.

**Documentation**: See `.claude/skills/prd-compliance-checker/SKILL.md` for comprehensive guide

---

#### Layer 5: CI/CD Pipeline (Automatic - No Action Needed)

**Runs automatically** when you push to GitHub. You don't invoke this.

**What it does**:
- ✅ Full test suite with coverage
- ✅ Security scanning (Trivy, TruffleHog)
- ✅ Type checking, linting, build verification

**View results**: GitHub → Actions tab

---

### Validation Workflow (Step-by-Step)

**For EVERY task/feature you implement:**

```bash
# 1. Implement the feature
# ... write code ...

# 2. BEFORE committing complex features (>500 lines):
#    Spawn validation agent (see prompt above)

# 3. BEFORE committing PHI-related code:
#    Invoke healthcare-compliance-checker skill

# 4. Fix any critical issues found by agent

# 5. Run validation script before major commits
./scripts/validate-code.sh --full

# 6. Fix any issues found

# 7. Commit (pre-commit hook runs automatically)
git add .
git commit -m "feat: your feature"
# → Hook validates syntax, tests, CONTEXT.md

# 8. If hook fails, fix issues and re-commit

# 9. Push to GitHub (CI/CD runs automatically)
git push
```

**For phase completion:**

```bash
# 1. Complete all tasks in the phase

# 2. Run full validation script
./scripts/validate-code.sh --full

# 3. Spawn validation agent for comprehensive review
# (Use Task tool with prompt above)

# 4. Fix ALL critical issues and warnings

# 5. Re-validate
./scripts/validate-code.sh --full

# 6. Commit phase completion
git add .
git commit -m "feat: Phase X complete"

# 7. Update CONTEXT.md with phase completion notes

# 8. Push to GitHub
git push
```

---

### Quick Reference: When to Validate

| Scenario | Layer 1 | Layer 2 | Layer 3 | Layer 4 | Layer 5 |
|----------|---------|---------|---------|---------|---------|
| Small bug fix (<50 lines) | ✅ Auto | ❌ Skip | ❌ Skip | ❌ Skip | ✅ Auto |
| Medium feature (50-500 lines) | ✅ Auto | ✅ Run | ❌ Optional | ❌ Skip | ✅ Auto |
| Complex feature (>500 lines) | ✅ Auto | ✅ Run | **✅ MUST** | ❌ Skip | ✅ Auto |
| **New API endpoint** | ✅ Auto | ✅ Run | **✅ MUST** | **✅ MUST** | ✅ Auto |
| **Schema changes (API)** | ✅ Auto | ✅ Run | **✅ MUST** | **✅ MUST** | ✅ Auto |
| PHI-related code | ✅ Auto | ✅ Run | **✅ MUST** | ❌ Skip | ✅ Auto |
| Phase completion | ✅ Auto | **✅ MUST** | **✅ MUST** | ✅ Run | ✅ Auto |
| Major refactoring | ✅ Auto | ✅ Run | **✅ MUST** | ❌ Skip | ✅ Auto |

**Legend**:
- ✅ Auto = Runs automatically
- ✅ Run = You must run manually
- ✅ MUST = Required, don't skip
- ❌ Skip = Not needed
- ❌ Optional = Use if unsure

**Note**: Layer 4 (PRD Compliance) is MANDATORY for all API-related changes to prevent contract drift.

---

### Example: Implementing a Complex Feature

```python
# Scenario: Implementing Task 2.5 (User Search API)

# Step 1: Implement the feature
# ... write backend/app/api/v1/endpoints/users.py search endpoint ...
# ... write tests in backend/tests/integration/test_user_search.py ...

# Step 2: BEFORE committing, spawn validation agent
# Use Task tool:
Task({
  subagent_type: "general-purpose",
  description: "Validate user search API",
  prompt: "Validate backend/app/api/v1/endpoints/users.py and tests/integration/test_user_search.py for syntax, security, test coverage..."
})

# Step 3: Agent reports back
# - ✅ Syntax valid
# - ✅ Imports resolve
# - ⚠️  Missing test for empty search query
# - ⚠️  No SQL injection check (using ORM, safe)

# Step 4: Fix critical issues
# ... add test for empty search query ...

# Step 5: Run validation script
./scripts/validate-code.sh --full
# → All checks pass

# Step 6: Commit
git add .
git commit -m "feat(user-mgmt): add user search API"
# → Pre-commit hook runs
# → Tests pass
# → Commit succeeds

# Step 7: Push
git push
# → CI/CD pipeline runs
# → All checks pass
```

---

### What If Validation Fails?

**Pre-commit hook fails:**
```bash
# Read the error message carefully
# Fix the issue (syntax error, failing test, missing CONTEXT.md update)
# Re-commit
git add .
git commit -m "fix: address validation issue"
```

**Validation script fails:**
```bash
# Run with full output
./scripts/validate-code.sh --full 2>&1 | less

# Fix issues one by one:
# 1. Syntax errors first
# 2. Failing tests second
# 3. Warnings last

# Re-run to verify
./scripts/validate-code.sh --full
```

**Validation agent finds issues:**
```bash
# Agent reports critical issues

# Fix each issue:
# 1. Read file path and line number
# 2. Apply suggested fix
# 3. Verify fix works

# Re-spawn agent to verify
# (Use same Task prompt)
```

---

### Bypassing Validation (EMERGENCY ONLY)

**Never bypass on main/develop branches!**

Only bypass pre-commit hook if:
- ✅ Committing work-in-progress on feature branch
- ✅ Documentation-only changes
- ✅ Emergency hotfix (fix tests immediately after)

```bash
# Bypass pre-commit hook (not recommended)
git commit --no-verify -m "wip: work in progress"

# Then fix tests/issues in next commit
```

**Never bypass**:
- ❌ To skip failing tests
- ❌ To avoid fixing syntax errors
- ❌ To skip CONTEXT.md updates
- ❌ On main or develop branches

---

## 📋 Workflow: Spec-Kit Framework

### Overview

This project uses **[Spec-Kit](https://github.com/github/spec-kit)** for specification-driven development.

**Core Principle**: Write specifications before code.

### Mandatory Process

#### 0. Read CONTEXT.md FIRST (Every Session!)

**⚠️ STEP ZERO - ALWAYS START HERE**

```bash
# Read this file at the start of EVERY session
cat CONTEXT.md

# Pay special attention to:
# - Recent Changes (last 3-5 entries)
# - Current System State (what's implemented)
# - Work In Progress (active development)
# - Relevant ADRs (architecture decisions)
```

**What CONTEXT.md tells you:**
- What's implemented vs what's planned
- Recent changes and why they were made
- Architecture decisions with rationale (ADRs)
- Integration points and how to use them
- Known issues and technical debt
- Design patterns to follow

**Time investment**: 15-20 minutes
**Return**: Complete context, no repeated questions, consistent decisions

**Update requirement**: You MUST update BOTH CONTEXT.md AND AUDIT.md before committing code (git hook enforces dual-file requirement)

---

#### 1. Read the Constitution SECOND

**After reading CONTEXT.md, review principles:**

```bash
# Read this file
.specify/constitution/project-constitution.md
```

**Key Principles** (memorize these):
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

**Principle Application**:
- If a principle conflicts with a request, cite the principle and explain the conflict
- Suggest alternatives that align with principles
- Document any approved deviations

---

#### 2. Check for Existing Specification

**Before writing code, check:**

```bash
# Does a spec exist?
ls .specify/specifications/*.md

# Does a plan exist?
ls .specify/plans/*.md

# Does a task list exist?
ls .specify/tasks/*.md
```

**If spec exists**: Read it completely before coding
**If spec doesn't exist**: Create it first (see workflow below)

---

#### 3. Create Specification (For New Features)

**When**: Feature will take >4 hours or involves architecture changes

**Template Location**: `.specify/specifications/meta-annotations-ui.md` (use as example)

**Required Sections**:
```markdown
# Specification: {Feature Name}

## Context
- Why is this needed?
- What problem does it solve?
- Business value?

## Goals
- Primary goals (3-5 items)
- Secondary goals (optional)

## Non-Goals
- What is explicitly out of scope?

## User Stories
- As a {role}, I want to {action}, so that {benefit}
- Include acceptance criteria for each story

## Requirements
### Functional Requirements
- FR1: {Description with measurable criteria}
- FR2: ...

### Non-Functional Requirements
- NFR1: Performance (e.g., <500ms response time)
- NFR2: Security (e.g., RBAC, encryption)
- NFR3: Accessibility (e.g., WCAG 2.1 AA)

## Constraints
- Technical constraints
- Regulatory constraints
- Organizational constraints

## Acceptance Criteria
- [ ] Measurable definition of "done"
- [ ] Test coverage requirements
- [ ] Performance benchmarks

## Alignment with Constitution
- Which principles does this address?
- Which non-negotiables are met?
```

**Save to**: `.specify/specifications/{feature-name}.md`

**Get approval**: Ask user to review before proceeding

---

#### 4. Create Technical Plan

**After spec approval:**

**Template**:
```markdown
# Technical Plan: {Feature Name}

## Architecture
- High-level diagram (use ASCII or mermaid)
- Component interactions
- Data flows

## Technology Choices
- Libraries/frameworks to use
- Rationale for each choice
- Alternatives considered

## Implementation Phases
- Phase 1: {Description}
- Phase 2: ...

## API Design
- Endpoint specifications (OpenAPI format preferred)
- Request/response examples
- Error codes

## Data Model
- Database schema changes
- Elasticsearch index updates
- Data structures

## Testing Strategy
- Unit tests (what to test)
- Integration tests (scenarios)
- E2E tests (user workflows)
- Performance tests (load, stress)

## Deployment
- Infrastructure changes
- Rollout strategy
- Rollback plan

## Risks
- Technical risks + mitigation
- Timeline risks + buffers
```

**Save to**: `.specify/plans/{feature-name}-plan.md`

---

#### 5. Create Task List

**After plan approval:**

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

## Task 2: ...
```

**Task Guidelines**:
- Each task completable in 1-2 hours
- Independent tasks can be done in parallel
- Dependencies clearly noted
- Acceptance criteria specific and testable

**Save to**: `.specify/tasks/{feature-name}-tasks.md`

---

#### 6. Implement Task-by-Task

**For EACH task:**

1. **Read task description completely**
2. **Write tests FIRST** (TDD approach)
3. **Implement to pass tests**
4. **Refactor if needed** (tests still pass)
5. **Document changes** in code comments
6. **Update task status** (completed)
7. **Update CONTEXT.md** (mandatory - see below)
8. **Commit with proper message** (see format below)

**Do NOT**:
- ❌ Skip ahead to future tasks
- ❌ Implement features not in spec
- ❌ Skip tests ("I'll add them later")
- ❌ Leave TODOs without creating tasks
- ❌ **Skip CONTEXT.md update** (git hook will block commit!)

---

#### 7. Update CONTEXT.md (Before Committing!)

**⚠️ MANDATORY: Update CONTEXT.md with EVERY code commit**

**What to update** (use this checklist):

```markdown
✅ Recent Changes Section
Add entry following this format:

### [Date] - [Feature/Change Name]

**Commits**: [commit SHA] - [brief description]

**Added**: What was added
**Changed**: What was changed
**Removed**: What was removed (if applicable)

**Why**: Rationale for changes
**Impact**: How this affects the system
**Migration Notes**: What users/developers need to do

✅ Implemented Features Section
Move feature from "Planned" to "Implemented" if complete
OR update "In Progress" if still working

✅ Architecture Decision Records (if applicable)
Create ADR if you made significant decision:
- Technology choice
- Design pattern selection
- Integration approach
- Performance optimization strategy

✅ Integration Points (if applicable)
Document new services, APIs, or external dependencies

✅ Technical Debt (if applicable)
Note any shortcuts taken and why:
- Skipped optimization for MVP
- Hardcoded value (refactor later)
- Missing edge case handling

✅ Known Issues (if bugs discovered)
Document issues found during development

✅ Design Patterns (if new pattern introduced)
Document pattern with example and rationale
```

**Example Good Update**:
```markdown
### 2025-01-08 - Patient Search API Implementation

**Commits**: abc123f - Implement patient search with meta-annotations

**Added**:
- POST /api/v1/patients/search endpoint (FastAPI)
- PatientSearchService class with MedCAT integration
- Elasticsearch query builder for meta-annotation filtering
- 15 unit tests, 5 integration tests (92% coverage)

**Changed**:
- None (new feature)

**Removed**:
- None

**Why**:
- Implements Sprint 1 requirement (patient search & discovery)
- Leverages meta-annotations (Negation, Temporality, Experiencer)
- Provides foundation for cohort identification
- Aligns with "Transparency" principle (confidence scores shown)

**Impact**:
- ✅ Core search functionality now available
- ✅ 95% precision (vs 60% without meta-annotations)
- ✅ Response time: 450ms (below 500ms target)
- ⚠️ Requires MedCAT service running at localhost:5000
- ⚠️ Elasticsearch index 'patients' must exist

**Migration Notes**:
- Start MedCAT service: `docker-compose up medcat-service`
- Create ES index: `python scripts/create_es_index.py`
- Run migrations: `alembic upgrade head`

**Technical Debt**:
- Hardcoded MedCAT URL (TODO: move to config)
- Missing pagination for large result sets (add in Sprint 2)

**Design Pattern Introduced**:
- Repository pattern for Elasticsearch access
- Service layer for business logic
- Dependency injection for MedCAT client
```

**Example Bad Update** (Don't do this):
```markdown
### 2025-01-08 - Updates

**Added**: Stuff
**Changed**: Things
**Why**: Because
```

**Enforcement**: Git hook will reject commits without meaningful CONTEXT.md updates!

---

## 💻 Code Standards

### Python (Backend)

**Style**: [PEP 8](https://pep8.org/) + [Black](https://black.readthedocs.io/)

```python
# Good
from typing import List, Optional
from pydantic import BaseModel

class PatientSearchQuery(BaseModel):
    """Search query for patient cohort identification.

    Attributes:
        concept: Medical concept to search for (SNOMED-CT or UMLS)
        filters: Optional meta-annotation filters
        limit: Maximum results to return (default 20)
    """
    concept: str
    filters: Optional[Dict[str, str]] = None
    limit: int = 20

async def search_patients(
    query: PatientSearchQuery,
    user: User = Depends(get_current_user)
) -> List[PatientResult]:
    """Search for patients matching concept query.

    Args:
        query: Search parameters
        user: Authenticated user (for audit logging)

    Returns:
        List of patient results with annotations

    Raises:
        HTTPException: 400 if invalid query, 403 if unauthorized
    """
    # Implementation
    pass
```

**Checklist**:
- [ ] Type hints for all function arguments and returns
- [ ] Docstrings (Google style) for classes and functions
- [ ] Pydantic models for all API schemas
- [ ] Async/await for I/O operations
- [ ] Error handling with proper HTTP status codes
- [ ] Audit logging for all PHI access

---

### TypeScript/Vue (Frontend)

**Style**: [Vue 3 Style Guide](https://vuejs.org/style-guide/) + ESLint + Prettier

```typescript
// Good
import { ref, computed, onMounted } from 'vue'
import type { PatientResult, SearchFilters } from '@/types'

interface Props {
  initialQuery?: string
  maxResults?: number
}

const props = withDefaults(defineProps<Props>(), {
  initialQuery: '',
  maxResults: 20
})

const emit = defineEmits<{
  search: [results: PatientResult[]]
  error: [message: string]
}>()

/**
 * Patient search composable
 * Handles search state, filtering, and API calls
 */
export function usePatientSearch() {
  const results = ref<PatientResult[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const search = async (query: string, filters?: SearchFilters) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.searchPatients({ query, filters })
      results.value = response.data
      emit('search', results.value)
    } catch (err) {
      error.value = err.message
      emit('error', err.message)
    } finally {
      isLoading.value = false
    }
  }

  return { results, isLoading, error, search }
}
```

**Checklist**:
- [ ] TypeScript for all new code (no `any` types)
- [ ] Composition API (not Options API)
- [ ] Composables for reusable logic
- [ ] Props and emits with types
- [ ] Accessibility attributes (ARIA labels, roles)
- [ ] Error boundaries for API calls

---

## 🧪 Testing Standards

### Minimum Coverage: 80%

**Critical paths: 100% coverage** (authentication, PHI access, clinical decisions)

### Test Pyramid

```
      /\
     /  \    E2E (10%)      - Full user workflows
    /----\
   /      \  Integration (30%) - API contracts, service interactions
  /--------\
 /          \ Unit (60%)      - Pure functions, components, services
```

### Python Tests (pytest)

```python
# tests/unit/services/test_patient_search_service.py
import pytest
from app.services.patient_search_service import PatientSearchService
from app.schemas.patient_search import PatientSearchQuery

@pytest.fixture
def search_service():
    return PatientSearchService()

@pytest.fixture
def mock_medcat_client(mocker):
    """Mock MedCAT service responses"""
    return mocker.patch('app.clients.medcat.MedCATClient')

def test_search_patients_by_concept(search_service, mock_medcat_client):
    """Test patient search returns correct results"""
    # Arrange
    query = PatientSearchQuery(concept="atrial flutter")
    mock_medcat_client.return_value.get_entities.return_value = [
        {"cui": "C0004238", "pretty_name": "Atrial Flutter"}
    ]

    # Act
    results = search_service.search(query)

    # Assert
    assert len(results) > 0
    assert results[0].concept_cui == "C0004238"

def test_search_patients_logs_audit_trail(search_service, mock_audit_logger):
    """Test PHI access is logged"""
    # Arrange
    query = PatientSearchQuery(concept="diabetes")

    # Act
    search_service.search(query, user_id="user-123")

    # Assert
    mock_audit_logger.info.assert_called_once()
    log_entry = mock_audit_logger.info.call_args[0][0]
    assert "user-123" in log_entry
    assert "diabetes" in log_entry
```

---

### TypeScript Tests (Vitest)

```typescript
// tests/unit/composables/usePatientSearch.test.ts
import { describe, it, expect, vi } from 'vitest'
import { usePatientSearch } from '@/composables/usePatientSearch'

describe('usePatientSearch', () => {
  it('should return results on successful search', async () => {
    // Arrange
    const mockApi = {
      searchPatients: vi.fn().mockResolvedValue({
        data: [{ id: '1', name: 'Test Patient' }]
      })
    }

    // Act
    const { search, results } = usePatientSearch(mockApi)
    await search('diabetes')

    // Assert
    expect(results.value).toHaveLength(1)
    expect(results.value[0].id).toBe('1')
  })

  it('should handle errors gracefully', async () => {
    // Arrange
    const mockApi = {
      searchPatients: vi.fn().mockRejectedValue(new Error('Network error'))
    }

    // Act
    const { search, error } = usePatientSearch(mockApi)
    await search('diabetes')

    // Assert
    expect(error.value).toBe('Network error')
  })
})
```

---

## 📝 Commit Message Format

### Required Format

```
<type>(<scope>): <short summary>

[Optional: Agent-generated code]

Changes:
- Bullet list of specific changes
- Each change on new line

Rationale:
- Why these changes were made
- Links to specs/issues if applicable

Tests:
- Test coverage: X%
- X unit tests, Y integration tests
- All tests passing

CONTEXT.md Updates:
- Updated "Recent Changes" with entry
- [If applicable] Added ADR-XXX for [decision]
- [If applicable] Moved feature to "Implemented"
- [If applicable] Noted technical debt: [description]

AUDIT.md Updates:
- Ran auditor subagent (quick/full/comprehensive audit)
- Updated compliance scores for affected features
- [If applicable] Documented drift items detected
- [If applicable] Updated compliance trends

[Optional for agent-generated code]
AI Context:
- Specification: .specify/specifications/{name}.md
- Task: {task description}
- Session: {date/time}
```

**⚠️ IMPORTANT**: BOTH "CONTEXT.md Updates" and "AUDIT.md Updates" sections are MANDATORY for code commits. Git hook enforces dual-file requirement.

### Type Values

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, missing semicolons)
- `refactor`: Code restructuring (no functional changes)
- `test`: Adding/updating tests
- `chore`: Maintenance (dependencies, tooling)
- `perf`: Performance improvements
- `security`: Security fixes

### Scope Values

- `patient-search`: Patient search feature
- `timeline`: Patient timeline view
- `fhir`: FHIR integration
- `auth`: Authentication/authorization
- `api`: API endpoints
- `ui`: User interface components
- `docs`: Documentation
- `config`: Configuration files
- `deps`: Dependencies

### Examples

**Good**:
```
feat(patient-search): add meta-annotation filtering

[Agent-generated code]

Changes:
- Added filter UI component for negation/temporality/experiencer
- Updated search API to accept meta-annotation filters
- Added Elasticsearch query builder for meta-annotation fields

Rationale:
- Implements Sprint 2 requirement (meta-annotations UI)
- Improves cohort precision from 60% to 95% (per spec)
- Aligns with "Transparency" principle (constitution)

Tests:
- Test coverage: 92%
- 15 unit tests for filter logic
- 5 integration tests for API
- All tests passing

AI Context:
- Specification: .specify/specifications/meta-annotations-ui.md
- Task: Sprint 2, Task 3 (Add filter UI)
- Session: 2025-01-07
```

**Bad**:
```
fix stuff
```

---

## 🔍 Code Review Checklist

### Before Requesting Human Review

**Run this checklist yourself:**

#### Functionality
- [ ] All acceptance criteria met (reference spec)
- [ ] Edge cases handled (empty inputs, large datasets, errors)
- [ ] No hardcoded values (use config/environment variables)
- [ ] Logging added for debugging (not excessive)

#### Security
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS prevention (sanitize outputs)
- [ ] Authentication/authorization checks
- [ ] No secrets in code (use environment variables)
- [ ] Audit logging for PHI access

#### Performance
- [ ] Database queries optimized (use indexes, avoid N+1)
- [ ] API calls cached where appropriate
- [ ] Large lists paginated
- [ ] No synchronous blocking in async code
- [ ] Memory leaks checked (subscriptions cleaned up)

#### Testing
- [ ] Test coverage ≥80% (critical paths 100%)
- [ ] All tests passing locally
- [ ] Unit tests for business logic
- [ ] Integration tests for API contracts
- [ ] E2E test for critical user flow (if applicable)

#### Documentation
- [ ] Code comments for complex logic
- [ ] API documentation updated (OpenAPI spec)
- [ ] README updated if needed
- [ ] Spec file updated if implementation differs

#### Accessibility
- [ ] Semantic HTML (not div soup)
- [ ] ARIA labels for interactive elements
- [ ] Keyboard navigation works
- [ ] Color contrast meets WCAG AA (use contrast checker)
- [ ] Focus indicators visible

#### Git Hygiene
- [ ] Commit message follows format
- [ ] No merge conflicts
- [ ] Branch up-to-date with main
- [ ] No debug code (console.log, breakpoints)
- [ ] .gitignore updated for new files

#### 🔴 Dual-File Update (MANDATORY)
- [ ] **CONTEXT.md updated** (required for ALL code commits)
  - [ ] Architecture changes documented (if applicable)
  - [ ] ADR added for major decisions
  - [ ] "Recent Changes" section updated
  - [ ] "Implemented Features" or "In Progress" updated
  - [ ] Integration points documented (if new services added)
  - [ ] Technical debt noted (if shortcuts taken)

- [ ] **AUDIT.md updated** (required for ALL code commits)
  - [ ] Ran auditor subagent (quick/full/comprehensive)
  - [ ] Updated compliance scores for affected features
  - [ ] Documented drift items (if detected)
  - [ ] Updated compliance trends (if changed)

**⚠️ NO COMMIT WITHOUT BOTH CONTEXT.MD AND AUDIT.MD UPDATES**

See [CONTEXT.md](CONTEXT.md) for technical memory and [AUDIT.md](AUDIT.md) for PRD compliance audit.

---

## 🚨 Common Pitfalls (Avoid These!)

### 1. Ignoring Meta-Annotations

**Wrong**:
```python
# Bad: Includes family history and negated mentions
results = cat.get_entities("Family history of diabetes. Patient denies chest pain.")
# Returns: ["diabetes", "chest pain"] → FALSE POSITIVES
```

**Right**:
```python
# Good: Filter by meta-annotations
entities = cat.get_entities(text)
active_patient_conditions = [
    ent for ent in entities
    if ent['meta_anns'].get('Negation') == 'Affirmed'
    and ent['meta_anns'].get('Experiencer') == 'Patient'
    and ent['meta_anns'].get('Temporality') in ['Current', 'Recent']
]
# Returns: [] → CORRECT (both are excluded)
```

**Learn more**: [Meta-Annotations Guide](docs/advanced/meta-annotations-guide.md)

---

### 2. Exposing PHI in Logs

**Wrong**:
```python
# Bad: PHI in application logs
logger.info(f"Processing patient {patient_name} (MRN: {mrn})")
```

**Right**:
```python
# Good: Patient ID only (no PII)
logger.info(f"Processing patient {patient_id}")
audit_logger.info({
    "user_id": user_id,
    "patient_id": patient_id,
    "action": "VIEW",
    "timestamp": datetime.now().isoformat()
})
```

---

### 3. Missing Audit Trails

**Wrong**:
```python
# Bad: No audit trail
def get_patient_data(patient_id: str):
    return db.query(Patient).filter_by(id=patient_id).first()
```

**Right**:
```python
# Good: Audit every PHI access
def get_patient_data(
    patient_id: str,
    user: User = Depends(get_current_user)
):
    audit_log(
        user_id=user.id,
        action="VIEW_PATIENT",
        patient_id=patient_id,
        ip_address=request.client.host
    )
    return db.query(Patient).filter_by(id=patient_id).first()
```

---

### 4. Ignoring Performance Requirements

**Wrong**:
```python
# Bad: N+1 query problem
patients = db.query(Patient).all()
for patient in patients:
    patient.notes = db.query(Note).filter_by(patient_id=patient.id).all()
    # 1 query + N queries = slow!
```

**Right**:
```python
# Good: Eager loading
patients = db.query(Patient).options(
    joinedload(Patient.notes)
).all()
# 1 query = fast!
```

---

### 5. Skipping Tests

**Wrong**:
```python
# Bad: "I'll add tests later"
def calculate_risk_score(patient_data):
    # Complex logic here
    return score
# No tests = bugs in production
```

**Right**:
```python
# Good: Write tests FIRST (TDD)
def test_calculate_risk_score():
    # Arrange
    patient_data = {"age": 65, "conditions": ["diabetes", "hypertension"]}

    # Act
    score = calculate_risk_score(patient_data)

    # Assert
    assert 0 <= score <= 100
    assert score > 50  # High risk patient

# THEN implement the function
def calculate_risk_score(patient_data):
    # Implementation
    pass
```

---

## 📚 Key Documentation

### Must-Read Before Starting

1. **CONTEXT.md** (15-20 min): [CONTEXT.md](CONTEXT.md) - Living project memory (ALWAYS read first)
2. **Constitution** (15 min): [.specify/constitution/project-constitution.md](.specify/constitution/project-constitution.md)
3. **Spec-Kit Guide** (30 min): [.specify/README.md](.specify/README.md)
4. **Example Spec** (20 min): [.specify/specifications/meta-annotations-ui.md](.specify/specifications/meta-annotations-ui.md)
5. **Skills Overview** (10 min): [.claude/skills/README.md](.claude/skills/README.md) - Custom healthcare NLP skills

### Domain Knowledge

6. **Meta-Annotations** (1 hour): [docs/advanced/meta-annotations-guide.md](docs/advanced/meta-annotations-guide.md)
7. **FHIR Integration** (1 hour): [docs/integration/fhir-integration-guide.md](docs/integration/fhir-integration-guide.md)
8. **Compliance** (2 hours): [docs/compliance/healthcare-compliance-framework.md](docs/compliance/healthcare-compliance-framework.md)

### Development Guides

9. **Development Workflow** (1 hour): [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
10. **Agent Guidelines** (30 min): [docs/agents.md](docs/agents.md)
11. **Workflow Frameworks** (1 hour): [docs/WORKFLOW_FRAMEWORKS_GUIDE.md](docs/WORKFLOW_FRAMEWORKS_GUIDE.md)

---

## 🤔 Decision Framework

### When Unsure, Ask:

**Does this align with the constitution?**
- Check against 10 core principles
- If conflicts, cite principle and explain

**Is this the simplest solution?**
- YAGNI (You Aren't Gonna Need It)
- Don't over-engineer
- Build for now, design for future

**Can this wait?**
- MVP first, nice-to-haves later
- Reference spec priorities (P0, P1, P2)

**Is this documented?**
- Spec exists?
- Tests written?
- Comments added?

**Is this safe?**
- Patient safety considered?
- Privacy protected?
- Compliance maintained?

---

## 🆘 When You're Stuck

### Escalation Path

1. **Check documentation** (this file, specs, guides)
2. **Search codebase** (similar patterns elsewhere?)
3. **Review examples** (existing features doing similar things?)
4. **Ask user** (provide context, suggest options)

### Good Questions to Ask

**Good**:
```
"I'm implementing the FHIR integration (Task 3 in .specify/tasks/fhir-integration-tasks.md).

The spec says 'Map MedCAT output to FHIR Observations' but doesn't specify
whether to use valueBoolean (true/false for presence) or valueCodeableConcept
(structured code + text).

Options:
A) valueBoolean: Simpler, indicates presence only
B) valueCodeableConcept: More structured, includes SNOMED codes

FHIR R4 spec allows both. Which fits our use case better?"
```

**Bad**:
```
"How do I do FHIR?"
```

---

## 🎓 Learning Resources

### MedCAT / NLP
- [MedCAT GitHub](https://github.com/CogStack/MedCAT)
- [MedCAT Paper](https://arxiv.org/abs/2010.01165)
- [CogStack Docs](https://docs.cogstack.org)

### FHIR / Healthcare Standards
- [FHIR R4 Spec](https://hl7.org/fhir/R4/)
- [SMART on FHIR](https://docs.smarthealthit.org/)
- [CDS Hooks](https://cds-hooks.org/)

### Compliance
- [HIPAA](https://www.hhs.gov/hipaa)
- [GDPR](https://gdpr.eu/)
- [FDA 21 CFR Part 11](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application)

### Development
- [Vue 3 Docs](https://vuejs.org/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Elasticsearch Guide](https://www.elastic.co/guide/index.html)

---

## 📊 Success Metrics

**Your code is successful when:**

- ✅ All tests pass (including CI/CD)
- ✅ Code review approved (human + automated checks)
- ✅ Acceptance criteria met (per spec)
- ✅ Performance benchmarks met (per spec)
- ✅ No security vulnerabilities (Snyk scan passes)
- ✅ Documentation updated
- ✅ Deployed to staging without issues

**Your collaboration is successful when:**

- ✅ User doesn't need to repeat context
- ✅ Questions are specific and actionable
- ✅ Suggestions reference constitution/specs
- ✅ Changes are incremental and testable
- ✅ Commits tell a clear story

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.6.0 | 2025-11-18 | Dual-file requirement (CONTEXT.md + AUDIT.md), dedicated auditor subagent |
| 1.5.0 | 2025-11-18 | 5-layer validation framework with BLOCKING hooks for API changes |
| 1.0.0 | 2025-01-07 | Initial version |

---

## 🤝 Contributing to This Guide

**This guide should evolve!**

If you find:
- Unclear instructions
- Missing best practices
- Outdated information
- Better examples

**Action**: Update this file and commit with:
```
docs(claude): improve {section} guidance

- What was unclear/wrong
- What was changed
- Why it's better now
```

---

**Questions about this guide?** Open a discussion issue or ask the user.

**Ready to start?** Read the constitution, check for specs, and build amazing things! 🚀
