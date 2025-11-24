# Git Hook-Based Autonomous Development Orchestration

**Version**: 2.0.0 (Git Hook Architecture)
**Replaces**: Autonomous-config.yaml loop (v1.0.0)
**Architecture**: Event-driven (git hooks trigger agents)

---

## 🎯 Core Concept

Instead of a custom autonomous loop, use **git hooks as the orchestration layer**:

- **Git commits** = events that trigger agents
- **AUDIT.md** = work queue (blocking todos = not done yet)
- **Hooks** = quality gates (enforce workflow)
- **Agents** = autonomous workers (fix issues, implement tasks)

This follows the **CI/CD pattern** (like GitHub Actions, but for development).

---

## 🔄 The Autonomous Cycle

```
┌─────────────────────────────────────────────────────────────┐
│                  DEVELOPER AGENT                            │
│         (Human or AI implements task)                       │
└────────────────┬────────────────────────────────────────────┘
                 ▼
         ┌───────────────┐
         │  git add .    │  Stage changes
         │  git commit   │  Attempt commit
         └───────┬───────┘
                 ▼
    ┌────────────────────────────┐
    │   PRE-COMMIT HOOK          │
    │   (.git-hooks/pre-commit)  │
    └────────────┬───────────────┘
                 │
      ┌──────────┴──────────┐
      │ Check AUDIT.md      │
      │ for blocking todos  │
      └──────────┬──────────┘
      🚨 BLOCKING│  ✅ CLEAR
                 │
      ┌──────────┴──────────┐
      │ Blocking issues?    │
      └──────────┬──────────┘
      YES ▼      │ NO
  ┌──────────────────┐ │
  │ DEVELOPMENT      │ │
  │ AGENT (Auto-fix) │ │
  │ development-     │ │
  │ agent.sh         │ │
  └────┬─────────────┘ │
       │               │
       │ Fix issues    │
       │ Stage files   │
       │ Update AUDIT  │
       │               │
       └───┬───────────┘
           ▼
   ┌───────────────┐
   │ COMMIT SUCCEEDS│
   └───────┬───────┘
           ▼
┌──────────────────────────┐
│  POST-COMMIT HOOK        │
│  (.git-hooks/post-commit)│
└──────────┬───────────────┘
           ▼
   ┌───────────────┐
   │ AUDITOR AGENT │  Spawn in background
   │ (post-commit) │  Check PRD compliance
   └───────┬───────┘
           ▼
   ┌───────────────┐
   │ Update AUDIT  │  Compliance score + todos
   │ .md           │  ✅ CLEAR or 🚨 BLOCKING
   └───────┬───────┘
           │
      ┌────┴────┐
      │  AUDIT  │
      │ Status? │
      └────┬────┘
    BLOCKING ▼  │ CLEAR
   ┌──────────┐ │
   │ Next     │ │
   │ commit   │ │
   │ attempt  │ │
   │ triggers │ │
   │ auto-fix │ │
   └──────────┘ │
       ▲        │
       │        ▼
       │   ┌───────────────┐
       │   │ LOAD NEXT     │
       │   │ TASK          │
       │   │ load-next-    │
       │   │ task.sh       │
       │   └───────┬───────┘
       │           ▼
       │   ┌───────────────┐
       │   │ DEVELOPMENT   │
       │   │ AGENT         │
       │   │ (Next task)   │
       │   └───────┬───────┘
       │           │
       │           ▼
       └───── git commit
              (cycle repeats)
```

---

## 📋 Hook Responsibilities

### 1. **pre-commit** (.git-hooks/pre-commit)

**When**: Before every commit
**Checks**:
- ✅ CONTEXT.md updated (dual-file requirement with AUDIT.md)
- ✅ AUDIT.md updated
- ✅ AUDIT.md status is ✅ CLEAR (not 🚨 BLOCKING)
- ✅ No console.log / debugger statements
- ✅ No TODO comments (use tasks)

**If AUDIT.md shows BLOCKING**:
```bash
if AUDIT.md status == "🚨 BLOCKING":
    if autonomous_mode.enabled:
        # Trigger development agent to auto-fix
        bash .git-hooks/development-agent.sh
        if fix_successful:
            allow_commit()  # Fixes applied, commit proceeds
        else:
            block_commit()  # Can't fix, manual intervention
    else:
        block_commit()  # Manual mode, require human fix
```

**Result**: Enforces quality gate (can't commit with blocking issues)

---

### 2. **post-commit** (.git-hooks/post-commit)

**When**: After every successful commit
**Action**:
1. Check if autonomous mode enabled (`.claude/autonomous-config.yaml`)
2. Spawn auditor agent (background process)
3. Auditor updates AUDIT.md with:
   - Compliance score (0-100%)
   - Commit status (✅ CLEAR or 🚨 BLOCKING)
   - Blocking todos (if issues found)
4. If AUDIT.md shows ✅ CLEAR → Load next task

**Auditor Prompt** (auto-generated):
```markdown
# Auditor Agent - Post-Commit Review

Commit: abc1234 - feat(highlights): implement backend API

## Check Against PRD
- Read: .specify/specifications/patient-search.md
- Compare implementation vs PRD:
  - Endpoint paths match?
  - Field names match?
  - Request/response structure match?
  - Breaking changes?

## Update AUDIT.md
- Compliance score: X%
- Commit status: ✅ CLEAR or 🚨 BLOCKING
- List blocking todos (if any)
```

**Result**: Automatic PRD compliance check after every commit

---

### 3. **development-agent.sh**

**When**: Triggered by pre-commit hook when AUDIT.md shows blocking todos
**Action**:
1. Extract blocking todos from AUDIT.md
2. Check retry count (max 3 attempts per unique issue)
3. Spawn development agent with todo list
4. Agent fixes issues, stages files, updates AUDIT.md
5. Pre-commit hook allows commit (fixes applied)

**Development Agent Prompt** (auto-generated):
```markdown
# Development Agent - Auto-fix Blocking Issues

Retry: 1/3

## Blocking Todos from AUDIT.md
- [ ] **TODO-1**: Field name mismatch: response.total → response.pagination.totalResults
  - **File**: backend/app/schemas/patient_search.py:45
  - **Expected**: pagination.totalResults (nested)
  - **Actual**: total (flat)
  - **Fix**: Create PaginationInfo schema, update response

## Your Task
1. Fix each todo
2. Stage files (git add .)
3. Update AUDIT.md (mark todos as [x] completed)
4. Exit 0 (commit proceeds)
```

**Result**: Automatic issue fixing with retry limits

---

### 4. **load-next-task.sh**

**When**: Triggered by post-commit hook when AUDIT.md shows ✅ CLEAR
**Action**:
1. Read CONTEXT.md to find current task
2. Find next pending task from `.specify/tasks/*.md`
3. Read task specification
4. Create development agent prompt
5. Prompt user (or auto-spawn agent in future)

**Development Agent Prompt** (auto-generated):
```markdown
# Development Agent - Next Task

Current Task: Task 4.3 (COMPLETED)
Next Task: Task 4.4 - Frontend Search Component

## Task Specification
[Full task spec from .specify/tasks/phase-4-tasks.md]

## Workflow
1. READ specification
2. PLAN implementation
3. IMPLEMENT (write code)
4. TEST (write tests)
5. UPDATE (CONTEXT.md)
6. COMMIT (triggers post-commit → auditor → cycle repeats)
```

**Result**: Automatic task progression

---

## 🛡️ Safety Mechanisms

### 1. Retry Limits (Prevent Infinite Loops)
```bash
# Max 3 attempts to fix same issue
if retry_count >= 3:
    exit_with_error("MAX_RETRIES_EXCEEDED")
    # Requires manual intervention
```

### 2. Dual-File Requirement (Enforce Documentation)
```bash
# Both CONTEXT.md AND AUDIT.md must be updated
if code_changes && (!context_updated || !audit_updated):
    block_commit()
```

### 3. Blocking Status Check (Quality Gate)
```bash
# Can't commit with blocking issues (unless auto-fixed)
if AUDIT.md status == "🚨 BLOCKING":
    if auto_fix_fails:
        block_commit()
```

### 4. Configuration-Based Behavior
```yaml
# .claude/autonomous-config.yaml
loop:
  enabled: true  # Enable autonomous mode

auto_fix:
  enabled: true  # Allow auto-fixing
  max_retries_per_issue: 3  # Retry limit

tasks:
  auto_load_next: true  # Continue to next task
```

---

## 📊 AUDIT.md as Work Queue

AUDIT.md serves as the **central work queue**:

### ✅ CLEAR Status (No Work)
```markdown
### Commit Status: ✅ CLEAR

**All checks passed** - No issues found

---

### Overall Score: ✅ 100% Compliant
```

**Action**: Post-commit hook loads next task

---

### 🚨 BLOCKING Status (Work Pending)
```markdown
### Commit Status: 🚨 BLOCKING: 2 issues

**Blocking Issues Found** - 2 issues requiring fixes

#### Blocking Todos (Development Agent will auto-fix these):
- [ ] **TODO-1**: Field name mismatch
  - **File**: backend/app/schemas/patient_search.py:45
  - **Expected**: pagination.totalResults
  - **Actual**: total
  - **Fix**: Create PaginationInfo schema

- [ ] **TODO-2**: Missing await keyword
  - **File**: frontend/src/composables/usePatientSearch.ts:68
  - **Expected**: await searchPatients(request)
  - **Actual**: searchPatients(request)
  - **Fix**: Add await keyword

**Action**: Development agent will be triggered on next commit attempt.

---

### Overall Score: ⚠️ 95% Compliant (2 minor issues)
```

**Action**: Pre-commit hook triggers development agent → fixes applied → commit proceeds → post-commit auditor verifies

---

## 🎬 Example Session

### User Implements Task 4.3

```bash
# 1. User (or AI) writes code
vim backend/app/services/patient_search_service.py
vim backend/tests/unit/test_patient_search.py

# 2. User updates CONTEXT.md
vim CONTEXT.md

# 3. User stages and commits
git add .
git commit -m "feat(search): implement patient search service"

# 4. PRE-COMMIT HOOK RUNS
🔍 Checking CONTEXT.md... ✅
🔍 Checking AUDIT.md... ✅ (already updated from previous audit)
🔍 Checking AUDIT.md status... ✅ CLEAR
✅ All checks passed

# 5. COMMIT SUCCEEDS
[autonomous/mvp-execution abc1234] feat(search): implement patient search service

# 6. POST-COMMIT HOOK RUNS
🔍 Spawning auditor agent...
📝 Auditor prompt saved to: .git-hooks/tmp/auditor-prompt-abc1234.txt
🚀 Auditor will update AUDIT.md with compliance results

# 7. AUDITOR AGENT RUNS (background)
# ... analyzes code vs PRD ...
# ... updates AUDIT.md ...

# 8. AUDITOR FINDS 2 ISSUES
AUDIT.md updated with:
  Commit Status: 🚨 BLOCKING: 2 issues
  TODO-1: Field name mismatch
  TODO-2: Missing await keyword

# 9. USER ATTEMPTS NEXT COMMIT
git commit -m "feat(search): add filtering logic"

# 10. PRE-COMMIT HOOK RUNS
🔍 Checking AUDIT.md status... 🚨 BLOCKING (2 issues)
🤖 Autonomous mode enabled - Triggering development agent...

# 11. DEVELOPMENT AGENT RUNS
📋 Extracting blocking todos from AUDIT.md...
Found 2 blocking todos
🚀 Spawning development agent to fix...
# ... agent fixes both issues ...
# ... stages files ...
# ... updates AUDIT.md: ✅ CLEAR ...
✅ Development agent fixed issues

# 12. COMMIT PROCEEDS
[autonomous/mvp-execution def5678] feat(search): add filtering logic (auto-fixed issues)

# 13. POST-COMMIT HOOK RUNS AGAIN
🔍 Spawning auditor agent...

# 14. AUDITOR VERIFIES FIXES
AUDIT.md updated with:
  Commit Status: ✅ CLEAR
  Overall Score: ✅ 100% Compliant

# 15. LOAD NEXT TASK
🔄 Loading next task...
Next task: Task 4.4 - Frontend Search Component
Prompt saved to: .git-hooks/tmp/next-task-prompt-1234567890.txt

# 16. CYCLE REPEATS
# User (or AI) implements Task 4.4...
```

---

## 🚀 Advantages vs Custom Loop

| Aspect | Custom Loop (v1.0) | Git Hooks (v2.0) |
|--------|-------------------|------------------|
| **Architecture** | Single orchestrator | Event-driven (git hooks) |
| **Trigger Mechanism** | Explicit loop iteration | Git commits (natural workflow) |
| **State Management** | Loop state file | AUDIT.md + CONTEXT.md |
| **Quality Gates** | Manual checks | Enforced by hooks (can't bypass) |
| **Integration** | Custom implementation | Native git workflow |
| **CI/CD Pattern** | Custom | Follows industry standard |
| **Debugging** | Loop logs | Git history + hook logs |
| **Configuration** | autonomous-config.yaml | Same + hook scripts |
| **Extensibility** | Add to loop | Add more hooks |
| **Failure Handling** | Loop exit | Commit blocked, retry |

**Winner**: Git hooks (v2.0) - More robust, follows industry patterns

---

## 📁 File Structure

```
.git-hooks/
├── pre-commit                  # Quality gate (check AUDIT.md status)
├── post-commit                 # Spawn auditor after commits
├── development-agent.sh        # Auto-fix blocking todos
├── load-next-task.sh          # Load next task from spec
├── autonomous.log             # Event log
└── tmp/                       # Temporary prompt files
    ├── auditor-prompt-*.txt
    ├── dev-agent-prompt-*.txt
    └── next-task-prompt-*.txt

.claude/
├── autonomous-config.yaml     # Configuration
└── GIT_HOOK_ORCHESTRATION.md # This file (architecture docs)

AUDIT.md                       # Work queue (blocking todos)
CONTEXT.md                     # Project state
```

---

## ⚙️ Configuration

All behavior controlled by `.claude/autonomous-config.yaml`:

```yaml
loop:
  enabled: true  # Enable autonomous mode

auto_fix:
  enabled: true  # Allow development agent to auto-fix
  max_retries_per_issue: 3  # Retry limit
  fix_auditor_issues: true
  fix_test_failures: true

audit:
  run_on_every_change: true  # Post-commit hook spawns auditor
  blocking_threshold: 95  # Minimum compliance to allow commit

tasks:
  auto_load_next: true  # Load next task after current completes
  source_priority:
    - "specification"  # Tasks from .specify/tasks/

commits:
  require_dual_file_update: true  # CONTEXT.md + AUDIT.md mandatory
```

---

## 🔮 Future Enhancements

### Phase 1 (Current): Manual Agent Spawn
- Hooks generate prompts → User pastes into Claude Code

### Phase 2: Claude Code CLI Integration
```bash
# Hooks auto-spawn agents
claude-code agent spawn --prompt-file .git-hooks/tmp/auditor-prompt.txt --background

# Development agent auto-fixes
claude-code agent spawn --prompt-file .git-hooks/tmp/dev-agent-prompt.txt --wait
```

### Phase 3: Full Autonomous Development
```bash
# User starts development
git commit -m "Start Phase 4"

# Hooks + agents handle everything
# ... 2 hours later ...

# Phase 4 complete (8 tasks, 8 commits, 46 tests, 100% PRD compliant)
```

---

## 📚 Related Documentation

- **Hooks**: `.git-hooks/README.md`
- **Configuration**: `.claude/autonomous-config.yaml`
- **Skills**: `.claude/skills/autonomous-developer/SKILL.md`
- **Quick Start**: `.claude/START_AUTONOMOUS_MODE.md`

---

## ✅ Summary

**Key Innovation**: Use git hooks as orchestration layer instead of custom loop

**Benefits**:
- ✅ Event-driven (commits trigger agents)
- ✅ Quality gates enforced (can't commit with blocking issues)
- ✅ AUDIT.md as work queue (blocking todos = work pending)
- ✅ Follows CI/CD pattern (industry standard)
- ✅ Natural integration with git workflow

**Workflow**:
```
Developer → Commit → Pre-commit (check AUDIT.md) → Post-commit (spawn auditor) → AUDIT.md updated → Next commit (auto-fix if needed) → Cycle repeats
```

**Result**: Fully autonomous recursive development loop using git hooks! 🎉
