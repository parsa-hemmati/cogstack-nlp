# Task Delegation Patterns for Autonomous Loop

**Version**: 2.0.0 (Enhanced with Agent-to-Agent Delegation)
**Date**: 2025-11-21
**Purpose**: Define how agents create tasks for each other to form a never-ending autonomous loop

---

## Overview

The autonomous loop v2.0 introduces **agent-to-agent task delegation** where agents create work for each other, forming a continuous development cycle that doesn't stop until a module is fully complete, tested, documented, and compliant.

**Key Principle**: Every agent that completes work MUST create follow-up tasks for other agents.

---

## Delegation Rules

### Rule 1: Developer → Auditor + Tester + Documentation

**When**: Developer completes implementation task

**Must Create**:
- ✅ **Auditor task**: Review for HIPAA/GDPR compliance
- ✅ **Tester task**: Run tests and validate coverage
- ✅ **Documentation task**: Update docs (if API/schema changed)

**Example**:
```bash
# Developer completes task #5: Implement patient search API

# Before committing, create follow-up tasks:
bash .claude/scripts/add-task.sh "auditor" "Review patient search API for PHI exposure" "P0"
bash .claude/scripts/add-task.sh "tester" "Run integration tests for patient search" "P0"
bash .claude/scripts/add-task.sh "documentation" "Document patient search API endpoints" "P1"

# Then commit (pre-commit hook validates delegation happened)
git add .
git commit -m "feat(search): Task #5 - Implement patient search API

Created follow-up tasks:
- #6 [auditor] - Compliance review
- #7 [tester] - Integration tests
- #8 [documentation] - API docs"
```

**Pre-commit Hook Enforcement**:
```bash
# Hook checks TASK_QUEUE.md diff
# If developer completed task but didn't create auditor/tester tasks → BLOCK COMMIT
❌ DELEGATION REQUIRED: Developer completed task(s) but created NO follow-up tasks!

Developer must create tasks for:
  • [auditor] - Review changes for HIPAA/GDPR compliance
  • [tester] - Run tests and validate coverage
  • [documentation] - Update docs (if API/schema changed)
```

---

### Rule 2: Auditor → Developer (if issues found)

**When**: Auditor finds compliance violations

**Must Create**:
- ✅ **Developer task**: Fix compliance issues

**Example**:
```bash
# Auditor completes task #6: Review patient search API
# Findings: PHI in logs, missing audit trail

# Create developer task to fix:
bash .claude/scripts/add-task.sh "developer" "Fix patient search PHI logging (audit findings)" "P0"

git commit -m "audit(search): Task #6 - Found 2 compliance issues

Issues:
- PHI in application logs (BLOCKING)
- Missing audit trail for search queries

Created fix task:
- #9 [developer] - Fix compliance issues"
```

---

### Rule 3: Tester → Developer (if tests fail)

**When**: Tester finds failing tests or low coverage

**Must Create**:
- ✅ **Developer task**: Fix test failures
- ✅ **Developer task**: Add tests for uncovered code

**Example**:
```bash
# Tester completes task #7: Run integration tests
# Results: 3 tests failing, coverage 72% (below 85% threshold)

# Create developer tasks:
bash .claude/scripts/add-task.sh "developer" "Fix 3 failing patient search integration tests" "P0"
bash .claude/scripts/add-task.sh "developer" "Add tests to reach 85% coverage for search module" "P1"

git commit -m "test(search): Task #7 - Found test failures

Failures:
- test_search_with_invalid_concept (AssertionError)
- test_search_with_empty_query (500 error)
- test_search_pagination_edge_case (IndexError)

Coverage: 72% (threshold: 85%)

Created fix tasks:
- #10 [developer] - Fix failing tests
- #11 [developer] - Add coverage tests"
```

---

### Rule 4: Documentation → Developer (if examples needed)

**When**: Documentation agent needs runnable code examples

**Must Create**:
- ✅ **Developer task**: Create code examples

**Example**:
```bash
# Documentation agent completes task #8: Document patient search API
# Needs: Runnable Python/TypeScript examples

# Create developer task:
bash .claude/scripts/add-task.sh "developer" "Create code examples for patient search docs" "P2"

git commit -m "docs(search): Task #8 - API documentation complete

Created example task:
- #12 [developer] - Add runnable examples"
```

---

### Rule 5: Architecture Designer → Task Definer

**When**: Architecture design complete

**Must Create**:
- ✅ **Task Definer task**: Break design into implementable tasks

**Example**:
```bash
# Architecture designer completes task #1: Design de-identification module
# Output: Technical plan in .specify/plans/

# Create task-definer task:
bash .claude/scripts/add-task.sh "task-definer" "Break down de-identification plan into tasks" "P0"

git commit -m "arch(deid): Task #1 - Architecture design complete

Created:
- .specify/plans/de-identification-plan.md

Next:
- #2 [task-definer] - Create task breakdown"
```

---

### Rule 6: Task Definer → Developer (multiple)

**When**: Task breakdown complete

**Must Create**:
- ✅ **Multiple developer tasks**: One per implementation task

**Example**:
```bash
# Task definer completes task #2: Break down de-identification plan
# Output: 12 tasks in .specify/tasks/

# Create developer tasks (1-12):
for i in {1..12}; do
    bash .claude/scripts/add-task.sh "developer" "Deid Task 1.$i (see tasks file)" "P1"
done

git commit -m "plan(deid): Task #2 - Task breakdown complete (12 tasks)

Created:
- .specify/tasks/de-identification-tasks.md

Next:
- #3-14 [developer] - Implementation tasks"
```

---

## Continuous Loop Cycle

```
┌─────────────────────────────────────────────────────┐
│         NEVER-ENDING AUTONOMOUS LOOP                │
└─────────────────────────────────────────────────────┘

1. [developer] implements feature
   ↓ creates tasks for
2. [auditor] + [tester] + [documentation]
   ↓ auditor finds issues
3. [developer] fixes issues
   ↓ creates tasks for
4. [auditor] re-reviews + [tester] re-tests
   ↓ tester finds failures
5. [developer] fixes tests
   ↓ creates tasks for
6. [tester] validates fixes
   ↓ all pass
7. [documentation] updates docs
   ↓ needs examples
8. [developer] adds examples
   ↓ creates tasks for
9. [auditor] final compliance check
   ↓ all pass
10. ✅ MODULE COMPLETE

→ Loop continues for next module
```

---

## Pre-commit Hook Validation

The enhanced pre-commit hook (`pre-commit-task-delegation.sh`) enforces delegation:

**Validation Logic**:
```bash
1. Check if TASK_QUEUE.md modified
2. Count completed tasks (✅)
3. Count new pending tasks ([ ])
4. If completed > 0 AND new == 0 → BLOCK
5. Check agent type rules:
   - developer completed → auditor/tester must exist
   - auditor completed → developer (if issues)
   - tester completed → developer (if failures)
```

**Install**:
```bash
chmod +x .git-hooks/pre-commit-task-delegation.sh
ln -sf ../../.git-hooks/pre-commit-task-delegation.sh .git/hooks/pre-commit-task-delegation
```

---

## Worktree-Based Parallel Development

**Problem**: Single worktree = sequential development

**Solution**: Multiple worktrees for modular parallel development

### Create Module Worktree

```bash
# Create worktree for de-identification module
bash .claude/scripts/ccpm-worktree.sh create de-identification develop

# Output:
🌳 Creating worktree for module: de-identification
Worktree created at: ../worktrees/de-identification
Branch: feature/de-identification

# Isolated task queue created:
../worktrees/de-identification/.claude/TASK_QUEUE.md
```

### Parallel Development

```bash
# Main repo: Working on patient search
cd /home/user/cogstack-nlp
bash .claude/scripts/add-task.sh "developer" "Add filters to search" "P1"
git commit -m "chore: add search filter task"
# → Post-commit spawns agents

# Worktree 1: De-identification module
cd ../worktrees/de-identification
bash .claude/scripts/add-task.sh "developer" "Implement PHI redaction" "P1"
git commit -m "chore: add redaction task"
# → Post-commit spawns agents IN THIS WORKTREE

# Worktree 2: Clinical coding module
cd ../worktrees/clinical-coding
bash .claude/scripts/add-task.sh "developer" "ICD-10 extraction" "P1"
git commit -m "chore: add ICD-10 task"
# → Post-commit spawns agents IN THIS WORKTREE

# 3 autonomous loops running in parallel! 🚀
```

### Merge Completed Module

```bash
# When all tasks complete in worktree
bash .claude/scripts/ccpm-worktree.sh status de-identification
# Pending: 0, Completed: 15

# Merge back to develop
bash .claude/scripts/ccpm-worktree.sh merge de-identification

# Remove worktree
bash .claude/scripts/ccpm-worktree.sh remove de-identification
```

---

## Real-World Example: Full Module Lifecycle

```bash
### Phase 1: Architecture (Main Repo)
bash .claude/scripts/add-task.sh "architecture-designer" "Design de-identification module" "P0"
git commit -m "chore: start deid module design"
# → architecture-designer spawns, creates technical plan

### Phase 2: Task Planning (Main Repo)
# Architecture designer completed, created task-definer task
bash .claude/scripts/add-task.sh "task-definer" "Break down deid plan into tasks" "P0"
git commit -m "arch(deid): design complete"
# → task-definer spawns, creates 12 developer tasks

### Phase 3: Create Worktree for Isolated Development
bash .claude/scripts/ccpm-worktree.sh create de-identification develop
cd ../worktrees/de-identification

### Phase 4: Import Tasks to Worktree
# Copy 12 tasks from main repo to worktree TASK_QUEUE.md
# (or create new tasks in worktree)

### Phase 5: Autonomous Development (Worktree)
git commit -m "chore: add 12 deid implementation tasks"
# → developer agents spawn, start working

# Developer completes Task 1
git commit -m "feat(deid): Task 1 - PHI detection model

Created follow-up tasks:
- #13 [auditor] - Review PHI detection
- #14 [tester] - Test PHI detection accuracy"

# → auditor + tester spawn

# Auditor finds issue
git commit -m "audit(deid): Task 13 - Found PHI in logs

Created fix task:
- #15 [developer] - Remove PHI from logs"

# → developer spawns to fix

# Developer fixes issue
git commit -m "fix(deid): Task 15 - Remove PHI from logs

Created re-review tasks:
- #16 [auditor] - Re-review PHI logging"

# → auditor re-reviews

# Tester runs tests
git commit -m "test(deid): Task 14 - All tests passing, 92% coverage ✅"

# Loop continues until all 12 tasks + audits + tests complete

### Phase 6: Merge Module (Back to Main Repo)
cd /home/user/cogstack-nlp
bash .claude/scripts/ccpm-worktree.sh merge de-identification
bash .claude/scripts/ccpm-worktree.sh remove de-identification

### Phase 7: Continue with Next Module
bash .claude/scripts/ccpm-worktree.sh create clinical-coding develop
# Repeat...
```

---

## Benefits of Enhanced Loop

**v1.6.0 (Original)**:
- ✅ Concurrent agent spawning (up to 6)
- ✅ Git-native orchestration
- ✅ Atomic task claiming
- ❌ Manual task delegation
- ❌ Single worktree (sequential modules)

**v2.0.0 (Enhanced)**:
- ✅ All v1.6.0 benefits
- ✅ **Enforced task delegation** (pre-commit hook)
- ✅ **Agent-to-agent communication** (via tasks)
- ✅ **Never-ending loop** (agents create work for each other)
- ✅ **Parallel module development** (worktrees)
- ✅ **Isolated task queues** (per-worktree)

**Time to Complete Module**:
- Manual (sequential): ~40 hours
- v1.6.0 (concurrent): ~15 hours
- v2.0.0 (delegated + parallel): ~6 hours 🚀

---

## Troubleshooting

### Pre-commit Hook Blocks Commit

**Error**:
```
❌ DELEGATION REQUIRED: Developer completed task(s) but created NO follow-up tasks!
```

**Fix**:
```bash
# Add auditor task
bash .claude/scripts/add-task.sh "auditor" "Review changes for compliance" "P0"

# Add tester task
bash .claude/scripts/add-task.sh "tester" "Run tests and validate coverage" "P0"

# Stage updated TASK_QUEUE.md
git add .claude/TASK_QUEUE.md

# Retry commit
git commit --amend --no-edit
```

### Worktree Merge Conflicts

**Error**:
```
CONFLICT (content): Merge conflict in CONTEXT.md
```

**Fix**:
```bash
# Resolve conflicts manually
vim CONTEXT.md

# Mark resolved
git add CONTEXT.md

# Complete merge
git merge --continue
```

### Loop Not Spawning Agents

**Check**:
```bash
# Verify post-commit hook installed
ls -la .git/hooks/post-commit

# Check hook log
tail -f .claude/logs/agent-loop.log

# Verify tasks exist
grep "^\- \[ \]" .claude/TASK_QUEUE.md
```

---

## Next Steps

1. **Install enhanced pre-commit hook**:
   ```bash
   chmod +x .git-hooks/pre-commit-task-delegation.sh
   ln -sf ../../.git-hooks/pre-commit-task-delegation.sh .git/hooks/pre-commit-task-delegation
   ```

2. **Create first module worktree**:
   ```bash
   bash .claude/scripts/ccpm-worktree.sh create your-module-name develop
   ```

3. **Start delegating tasks**:
   - Every developer task → create auditor + tester tasks
   - Every auditor finding → create developer fix task
   - Every test failure → create developer debug task

4. **Monitor parallel loops**:
   ```bash
   bash .claude/scripts/ccpm-worktree.sh list
   bash .claude/scripts/ccpm-worktree.sh status your-module-name
   ```

**The never-ending autonomous loop is now active! 🚀**
