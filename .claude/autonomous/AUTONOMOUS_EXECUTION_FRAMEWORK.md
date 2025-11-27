# Autonomous Execution Framework for CogStack NLP Roadmap

**Version**: 1.0.0
**Date**: 2025-11-17
**Purpose**: Enable Claude Code to autonomously implement the complete 69-week roadmap with minimal human intervention

**Framework**: Hybrid AB Method + RIPER + TSK + Spec-Kit
**Target**: Complete MVP (Phases 0-7, 90 tasks, 388 hours) → Sprints 2-9.5 → Production deployment

---

## Executive Summary

**What This Enables**: Claude Code will autonomously execute the entire 69-week roadmap by:
1. **Decomposing** each sprint/phase into missions (using existing task lists)
2. **Executing** missions in parallel using specialized sub-agents (our 8 healthcare skills)
3. **Validating** outputs through automated review cycles (RIPER Review phase)
4. **Committing** working code with comprehensive documentation
5. **Progressing** through phases without human intervention (except Go/No-Go decisions)

**Human Intervention Points** (minimal):
- ✅ Go/No-Go decisions (Week 0 Meditech verification, Sprint start approvals)
- ✅ UAT sign-off (end of each sprint)
- ✅ Production deployment approval (end of Sprint 9.5)

**Everything Else**: Fully autonomous

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Autonomous Execution Controller (AEC)                          │
│ - Reads mission queue from .claude/autonomous/mission-queue.md │
│ - Spawns specialized agents for each mission                    │
│ - Monitors progress via .claude/autonomous/progress.json       │
│ - Auto-commits on mission completion                            │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ RIPER Cycle (per mission)                                       │
│                                                                  │
│  Research → Innovate → Plan → Execute → Review                  │
│     ↓          ↓         ↓        ↓         ↓                   │
│  Read spec  Design    Create   Write    Validate                │
│  + code     solution  tasks    code     + test                  │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ Specialized Sub-Agents (our 8 healthcare skills)                │
│                                                                  │
│  ├─ healthcare-compliance-checker (auto-invoked on PHI code)    │
│  ├─ medcat-meta-annotations (auto-invoked on NLP queries)       │
│  ├─ vue3-component-reuse (auto-invoked on UI tasks)             │
│  ├─ fhir-r4-mapper (auto-invoked Sprint 6 FHIR tasks)           │
│  ├─ spec-kit-enforcer (auto-invoked before coding)              │
│  ├─ infrastructure-expert (auto-invoked on Docker/DB tasks)     │
│  └─ [2 more planning skills]                                    │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ Progress Tracking & Auto-Commit                                 │
│ - Updates .claude/autonomous/progress.json after each mission   │
│ - Commits code with detailed message (WHO/WHAT/WHY)             │
│ - Updates CONTEXT.md automatically (git hook enforces)          │
│ - Pushes to feature branch (git branch: autonomous/phase-X)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Mission Queue Structure

Missions are extracted from:
1. **MVP Tasks**: `.specify/tasks/clinical-care-tools-base-tasks.md` (90 tasks)
2. **Sprint 2-9 Specs**: `.specify/specifications/sprint-*.md` (8 sprint specs)
3. **Hardening Tasks**: Sprint 5.5 + 9.5 (to be created)

**Mission Format**:
```yaml
mission_id: mvp-phase-0-task-1
phase: mvp-phase-0
task_number: 1
title: "Setup project directory structure"
spec_file: .specify/specifications/clinical-care-tools-base-app.md
spec_section: "Phase 0: Environment Setup"
estimated_hours: 2
dependencies: []
status: pending  # pending | in_progress | completed | blocked

riper_cycle:
  research:
    - Read MVP spec Phase 0
    - Review existing directory structures in similar projects
    - Check CLAUDE.md for project structure requirements
  innovate:
    - Design directory structure following Spec-Kit conventions
    - Ensure compliance with HIPAA/GDPR (no PHI in logs directory)
  plan:
    - Create task list: mkdir commands, .gitkeep files, README placement
  execute:
    - Create directories: backend/, frontend/, docs/, .specify/, .claude/
    - Add .gitkeep files to empty directories
    - Create README.md stubs
  review:
    - Verify directory structure matches spec
    - Check CONTEXT.md updated
    - Run git status (no unexpected files)

sub_agents:
  - infrastructure-expert (guidance on Docker, directory structure)

output:
  code_files: []
  documentation: [README.md updates, CONTEXT.md entry]
  tests: []

success_criteria:
  - All required directories exist
  - No errors in git status
  - CONTEXT.md updated with directory structure ADR
```

---

## Autonomous Execution Phases

### **Phase 0: Initialization (1 day)**

**Autonomous Actions**:
1. Read complete roadmap: `.specify/PRODUCT_ROADMAP.md`
2. Read MVP specification: `.specify/specifications/clinical-care-tools-base-app.md`
3. Read MVP technical plan: `.specify/plans/clinical-care-tools-base-plan.md`
4. Read MVP task list: `.specify/tasks/clinical-care-tools-base-tasks.md`
5. Generate mission queue: Extract all 90 MVP tasks → YAML format → `.claude/autonomous/mission-queue.yaml`
6. Initialize progress tracker: `.claude/autonomous/progress.json` (0/90 tasks complete)
7. Create feature branch: `git checkout -b autonomous/mvp-phase-0`

**Human Checkpoint**: None (fully autonomous)

---

### **Phase 1-7: MVP Execution (14 weeks, 90 tasks)**

**Autonomous Loop** (per task):

```python
for mission in mission_queue.filter(status='pending'):
    # 1. RESEARCH
    read(mission.spec_file, mission.spec_section)
    read_related_code(mission.dependencies)
    activate_skill('spec-kit-enforcer')  # Ensures spec exists

    # 2. INNOVATE
    design_solution(mission.requirements)
    check_architecture_fit(solution, existing_code)
    activate_skill_if_needed(mission.domain)  # Auto-activate healthcare skills

    # 3. PLAN
    create_subtasks(solution)
    estimate_time(subtasks)
    check_dependencies(subtasks, mission_queue)

    # 4. EXECUTE
    for subtask in subtasks:
        write_code(subtask)
        if involves_phi():
            activate_skill('healthcare-compliance-checker')
        if involves_nlp():
            activate_skill('medcat-meta-annotations')
        if involves_ui():
            activate_skill('vue3-component-reuse')

    # 5. REVIEW
    run_tests(mission.code_files)
    validate_compliance(mission)
    update_context_md(mission, decisions_made)

    # 6. COMMIT & PROGRESS
    git_commit_with_details(mission)
    update_progress_tracker(mission.mission_id, status='completed')

    # 7. NEXT
    mission.status = 'completed'
    save(mission_queue)
```

**Human Checkpoints**:
- **End of Phase 0** (Week 1): Review directory structure, approve to continue → 5 minutes
- **End of Phase 3** (Week 5): Review document upload + PHI extraction (critical) → 30 minutes
- **End of Phase 7** (Week 14): UAT testing before Sprint 2 → 2 hours

---

### **Phase 8: Sprint 2-9 Execution (Weeks 15-66)**

**Autonomous Actions** (per sprint):
1. Read sprint spec: `.specify/specifications/sprint-X-*.md`
2. Generate mission queue for sprint (if no task list exists, create from spec)
3. Execute RIPER cycle for each mission
4. Auto-commit after each mission
5. Sprint demo preparation (auto-generate changelog from commits)

**Human Checkpoints** (per sprint):
- **Sprint kickoff** (Week X): Approve sprint start → 15 minutes
- **Sprint demo** (End of sprint): UAT with clinicians → 2 hours
- **Go/No-Go for next sprint**: Based on UAT feedback → 30 minutes

**Special Checkpoints**:
- **Week 0 (Before Sprint 6)**: Meditech API verification (manual, see checklist) → 7 days
- **Sprint 6 (Week 37-48)**: Mid-sprint review (Week 43) for Meditech write operations → 1 hour

---

### **Phase 9: Hardening & Deployment (Weeks 67-69)**

**Autonomous Actions**:
1. Implement monitoring stack (Prometheus + Grafana)
2. Create user training materials (video tutorials, user guide)
3. Test disaster recovery (backup restore, rollback procedures)
4. Implement resilience patterns (circuit breakers, fallbacks)

**Human Checkpoints**:
- **Production deployment approval** (End of Week 69): Final sign-off → 4 hours
- **Go-live monitoring** (Week 70+): Monitor for issues → Ongoing

---

## Autonomous Decision-Making Framework

### **When to Auto-Proceed** (No Human Input Needed)

✅ **Implementation decisions**:
- Which library to use (choose based on: popularity, maintenance, license, Spec-Kit principles)
- How to structure code (follow: PEP 8, Vue style guide, CLAUDE.md conventions)
- Which database schema (follow: Technical Plan, normalize to 3NF, use UUIDs)

✅ **Testing decisions**:
- What to test (follow: 80% coverage requirement, critical paths 100%)
- How to test (follow: pytest for backend, vitest for frontend)

✅ **Refactoring decisions**:
- When to refactor (if: code duplication >3 instances, function >50 lines, cyclomatic complexity >10)
- How to refactor (follow: Extract Method, Extract Class, DRY principles)

### **When to Block & Ask Human** (Stop Autonomous Execution)

❌ **Architecture changes** not in spec:
- Adding new database (spec says PostgreSQL only)
- Changing deployment model (spec says single workstation, not cloud)
- Adding new external service (spec says CogStack-ModelServe, adding others needs approval)

❌ **Compliance questions**:
- Ambiguous PHI handling (e.g., "Is patient age considered PHI?")
- Regulatory interpretation (e.g., "Does this violate GDPR Article 17?")

❌ **Security concerns**:
- Potential vulnerability discovered (e.g., "This allows SQL injection, but spec doesn't mention fix")
- Unencrypted PHI (e.g., "Spec says store in BYTEA, should we encrypt?")

❌ **Scope creep**:
- Task requires feature not in spec (e.g., "To implement this, we need a notification system not in MVP spec")
- User story interpretation ambiguous (e.g., "Does 'clinician' include pharmacists?")

### **Decision Tree** (Auto vs Human)

```
Is decision explicitly covered in spec/plan/tasks?
├─ YES → Auto-proceed with decision documented in commit message
└─ NO → Is it a minor implementation detail? (library choice, variable naming, test approach)
    ├─ YES → Auto-proceed with rationale in commit message
    └─ NO → Is it a compliance/security/architecture concern?
        ├─ YES → BLOCK: Create `.claude/autonomous/blockers/blocker-XXX.md`, notify human
        └─ NO → Auto-proceed with detailed documentation, mark for review
```

---

## Progress Tracking & Monitoring

### **Progress File**: `.claude/autonomous/progress.json`

```json
{
  "roadmap_version": "2.0.0",
  "start_date": "2025-11-17",
  "current_phase": "mvp-phase-0",
  "total_missions": 90,
  "completed_missions": 5,
  "blocked_missions": 0,
  "estimated_completion": "2026-07-15",

  "missions": [
    {
      "mission_id": "mvp-phase-0-task-1",
      "title": "Setup project directory structure",
      "status": "completed",
      "started_at": "2025-11-17T10:00:00Z",
      "completed_at": "2025-11-17T12:00:00Z",
      "actual_hours": 2.0,
      "estimated_hours": 2.0,
      "commit_sha": "abc123f",
      "sub_agents_used": ["infrastructure-expert"],
      "blockers": []
    },
    {
      "mission_id": "mvp-phase-0-task-2",
      "title": "Download MedCAT models",
      "status": "in_progress",
      "started_at": "2025-11-17T12:15:00Z",
      "estimated_hours": 3.0,
      "sub_agents_used": [],
      "blockers": []
    }
  ],

  "metrics": {
    "velocity": 2.0,  // missions per day
    "accuracy": 0.95,  // estimated_hours / actual_hours
    "blocker_rate": 0.02,  // blocked_missions / total_missions
    "rework_rate": 0.05  // missions requiring rework / completed_missions
  },

  "checkpoints": [
    {
      "checkpoint_id": "mvp-phase-0-review",
      "scheduled_date": "2025-11-24",
      "status": "pending",
      "type": "human_review",
      "required_action": "Review directory structure, approve to continue"
    }
  ]
}
```

### **Daily Status Report** (Auto-Generated)

Saved to: `.claude/autonomous/reports/daily-YYYY-MM-DD.md`

```markdown
# Autonomous Execution Daily Report - 2025-11-17

## Summary
- **Missions Completed Today**: 5
- **Current Phase**: MVP Phase 0 (Environment Setup)
- **Progress**: 5/90 missions (5.6%)
- **On Track**: ✅ YES (estimated completion: 2026-07-15)

## Missions Completed
1. ✅ mvp-phase-0-task-1: Setup project directory structure (2.0h)
2. ✅ mvp-phase-0-task-2: Download MedCAT models (3.2h, estimated 3.0h)
3. ✅ mvp-phase-0-task-3: Configure Docker Compose (4.1h, estimated 4.0h)
4. ✅ mvp-phase-0-task-4: Setup PostgreSQL database (2.8h, estimated 3.0h)
5. ✅ mvp-phase-0-task-5: Setup Redis (1.5h, estimated 2.0h)

## Missions In Progress
- 🔄 mvp-phase-0-task-6: Setup CogStack-ModelServe (1.5h / 5.0h estimated)

## Blockers
- None

## Decisions Made (Auto)
1. **Docker Compose version**: Chose v2.23.0 (latest stable, supports profiles)
2. **PostgreSQL version**: Chose 15.5 (per spec: PostgreSQL 15+)
3. **Redis persistence**: Enabled RDB + AOF (per spec: durability required)

## Sub-Agents Activated
- infrastructure-expert: 5 times (Docker, PostgreSQL, Redis setup)
- spec-kit-enforcer: 5 times (verified spec before each task)

## Next 24 Hours
- Complete mvp-phase-0-task-6: Setup CogStack-ModelServe (3.5h remaining)
- Start mvp-phase-0-task-7: Create git hooks (2.0h estimated)
- **Checkpoint**: End of Phase 0 review (scheduled 2025-11-24)
```

---

## Auto-Commit Message Format

**Template**:
```
<type>(<scope>): <mission title>

Mission: <mission_id>
Phase: <phase_name>
Estimated: <estimated_hours>h | Actual: <actual_hours>h

Changes:
- <bullet list of specific changes>

RIPER Cycle:
Research: <what was researched>
Innovate: <design decisions made>
Plan: <tasks created>
Execute: <code written>
Review: <tests passed, validation completed>

Sub-Agents Used:
- <agent-name>: <why activated>

Tests:
- Test coverage: X%
- X unit tests, Y integration tests
- All tests passing: ✅ / ⚠️ (with details)

CONTEXT.md Updates:
- Updated 'Recent Changes' with entry
- [If applicable] Added ADR-XXX for <decision>
- [If applicable] Moved feature to 'Implemented'

🤖 Autonomous Mission Execution via [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Blocker Management

When autonomous execution blocks:

1. **Create blocker file**: `.claude/autonomous/blockers/blocker-XXX.md`
   ```markdown
   # Blocker: <Title>

   **Mission ID**: <mission_id>
   **Created**: <timestamp>
   **Status**: pending_human_input

   ## Issue
   <Description of what blocked autonomous execution>

   ## Context
   - Spec file: <path>
   - Code file: <path>
   - Relevant section: <quote from spec>

   ## Question for Human
   <Specific question that needs answer>

   ## Options Considered
   1. Option A: <description> (Pros: X, Cons: Y)
   2. Option B: <description> (Pros: X, Cons: Y)

   ## Recommended Action
   <Claude's recommendation with rationale>

   ## Impact if Not Resolved
   - Blocks missions: <list of mission IDs>
   - Timeline impact: +X days
   ```

2. **Update progress.json**: Mark mission as `blocked`

3. **Notify human**: Update `.claude/autonomous/reports/daily-YYYY-MM-DD.md` with blocker section

4. **Continue with unblocked missions**: Skip blocked mission, proceed with independent missions

---

## Human Review Protocol

### **End-of-Phase Reviews** (15-30 minutes each)

**What Human Reviews**:
1. **Code Quality**:
   - Does code follow CLAUDE.md conventions?
   - Are tests comprehensive (80% coverage)?
   - Is CONTEXT.md updated properly?

2. **Compliance**:
   - No PHI in logs (run: `grep -r "patient_name\|mrn\|dob" backend/logs`)
   - Audit logging present (check: `audit_logs` table has entries)
   - Encryption enforced (check: `DATABASE_URL` has `sslmode=require`)

3. **Functionality**:
   - Run application: `docker-compose up`
   - Test user flow: Create user → Create project → Upload document
   - Verify: No errors in console, audit logs created

**Approval Actions**:
- ✅ **Approve**: Update progress.json (`checkpoint.status = 'approved'`), autonomous execution continues
- ⚠️ **Request Changes**: Create `.claude/autonomous/feedback/phase-X-feedback.md`, autonomous execution pauses
- ❌ **Reject & Rollback**: `git reset --hard <last-good-commit>`, autonomous execution pauses for discussion

---

## Success Metrics

**Autonomous Execution is Successful If**:

1. **Velocity**: ≥80% of estimated timeline (69 weeks → ≤86 weeks actual)
2. **Quality**: ≥80% test coverage maintained throughout
3. **Compliance**: Zero PHI exposure incidents (audit log review clean)
4. **Blocker Rate**: <10% of missions blocked (human intervention needed)
5. **Rework Rate**: <20% of missions require rework after review
6. **Human Time**: <40 hours total human review time (vs 2,130 hours dev time = 2% human effort)

**Target**: **98% autonomous** (40h human / 2,130h total = 1.9% human time)

---

## Initialization Command

To start autonomous execution:

```bash
# 1. Generate mission queue from existing tasks
claude-code autonomous init --roadmap=.specify/PRODUCT_ROADMAP.md

# 2. Start autonomous execution (MVP Phase 0)
claude-code autonomous start --phase=mvp-phase-0 --mode=autonomous

# 3. Monitor progress (optional, runs in background)
claude-code autonomous monitor --watch
```

**What Happens**:
1. Reads MVP task list: `.specify/tasks/clinical-care-tools-base-tasks.md`
2. Converts tasks to missions: `.claude/autonomous/mission-queue.yaml`
3. Creates feature branch: `git checkout -b autonomous/mvp-phase-0`
4. Starts RIPER cycle for first mission
5. Activates sub-agents as needed
6. Commits on mission completion
7. Continues to next mission
8. Stops at first human checkpoint (End of Phase 0)

---

**Status**: ✅ Framework Defined, Ready for Implementation
**Next Step**: Create mission queue from MVP tasks + implement autonomous controller
**Estimated Setup Time**: 4 hours
**Estimated ROI**: 2,090 hours saved (2,130 total - 40 human review = 2,090 autonomous hours)
