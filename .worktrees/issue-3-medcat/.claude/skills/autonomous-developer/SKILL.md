---
name: autonomous-developer
description: Fully autonomous development loop that builds features, audits against PRD, tests, debugs, and commits recursively without human intervention. Use when user says "autonomous mode", "continuous development", "build everything autonomously", or "don't stop until done". Orchestrates build → audit → test → debug → commit cycle. Exits only on: (1) all tasks complete + tests pass + 100% PRD compliant [SUCCESS], (2) breaking changes requiring architectural decisions [PAUSE], (3) max retries exceeded [BLOCKED], or (4) external dependency missing [ERROR]. Configurable via .claude/autonomous-config.yaml.
---

# Autonomous Developer Loop

**Purpose**: Fully autonomous feature development without human checkpoints.

## 🎯 When to Use This Skill

Activate this skill when the user wants **continuous, autonomous development**:

- "Build everything autonomously"
- "Don't stop for confirmation, just keep building"
- "Continuous development mode"
- "Auto-build, auto-test, auto-commit until done"
- "Recursive development cycle"

**Do NOT use** when:
- User wants step-by-step control
- Exploratory/research tasks (not implementation)
- Reviewing existing code without changes

---

## 🔄 The Autonomous Loop

```
┌─────────────────────────────────────────────────────────────┐
│  START: Load next task from .specify/tasks/                │
└────────────────┬────────────────────────────────────────────┘
                 ▼
         ┌───────────────┐
         │  1. BUILD     │  Implement current task
         │   PHASE       │  (write code, update files)
         └───────┬───────┘
                 ▼
         ┌───────────────┐
         │  2. AUDIT     │  Spawn auditor subagent (parallel)
         │   PHASE       │  Check PRD compliance
         └───────┬───────┘
                 ▼
         ┌───────────────┐
         │  3. DECISION  │  Auditor passed?
         │   POINT       │  Yes → Continue
         └───────┬───────┘  No → Auto-fix → Retry
                 │
      ┌──────────┴──────────┐
      │ Compliance < 95%?   │
      └──────────┬──────────┘
      YES ▼      │ NO
  ┌──────────┐  │
  │ AUTO-FIX │  │
  │ Issues   │  │
  └────┬─────┘  │
       │        │
       └────┬───┘
            ▼
    ┌───────────────┐
    │  4. TEST      │  Generate + run tests
    │   PHASE       │  (integration, security, frontend)
    └───────┬───────┘
            ▼
    ┌───────────────┐
    │  5. DECISION  │  All tests pass?
    │   POINT       │  Yes → Continue
    └───────┬───────┘  No → Auto-debug → Retry
            │
   ┌────────┴────────┐
   │ Tests failing?  │
   └────────┬────────┘
   YES ▼    │ NO
┌──────────┐│
│ AUTO-FIX ││
│ & RERUN  ││
└────┬─────┘│
     │      │
     └──┬───┘
        ▼
┌───────────────┐
│  6. COMMIT    │  Auto-commit (update CONTEXT.md + AUDIT.md)
│   PHASE       │  (if auto_commit: true)
└───────┬───────┘
        ▼
┌───────────────┐
│  7. NEXT TASK │  Load next from spec
│   or EXIT     │  Or exit if done/blocked
└───────┬───────┘
        │
        └─────► LOOP BACK TO STEP 1
```

---

## 📋 Autonomous Loop Workflow (Step-by-Step)

### **Iteration N** (e.g., Implementing Task 4.5)

#### **STEP 1: BUILD PHASE**
```yaml
Action: Implement current task from .specify/tasks/
Input: Task 4.5 - Frontend Highlights Panel
Process:
  - Read task specification
  - Write Vue component code
  - Update router
  - Add API integration
Output: New files created/modified
Log: "✅ Task 4.5 implementation complete"
```

#### **STEP 2: AUDIT PHASE** (Parallel if configured)
```yaml
Action: Spawn auditor subagent to check PRD compliance
Input: All changed files from Step 1
Process:
  - Compare implementation against .specify/specifications/patient-search.md
  - Check for breaking changes
  - Validate field names, types, structure
  - Calculate compliance score
Output: Auditor report with score + issues
Log: "Auditor score: 98% (2 minor issues)"
```

#### **STEP 3: DECISION POINT - Auditor Results**
```yaml
Condition: If auditor_score >= blocking_threshold (95%)
  → Continue to STEP 4 (Test Phase)

Condition: If auditor_score < 95% AND auto_fix.fix_auditor_issues = true
  → Trigger AUTO-FIX sub-loop:
     1. Parse auditor issues
     2. Apply fixes automatically
     3. Re-run auditor
     4. If fixed → Continue to STEP 4
     5. If max_retries exceeded (3) → EXIT with BLOCKED status

Condition: If breaking_changes_detected = true
  → EXIT with PAUSE status (require user decision)
```

**AUTO-FIX Example**:
```
Auditor Issue: "Field name mismatch: response.total should be response.pagination.totalResults"

Auto-Fix Strategy:
1. Locate schema file: backend/app/schemas/patient_search.py
2. Identify fix: Rename field `total` → `totalResults`, wrap in `pagination` object
3. Apply fix using Edit tool
4. Re-run auditor
5. Verify: Auditor now shows 100% compliance
6. Log: "✅ Auto-fixed: Field name mismatch (retry 1/3)"
```

#### **STEP 4: TEST PHASE**
```yaml
Action: Generate and run tests
Input: Implementation from Step 1
Process:
  - Check if tests exist for this feature
  - If missing → Auto-generate tests (using prd-test-generator skill)
  - Run pytest backend/tests/
  - Run npm run test:unit (frontend)
  - Collect results
Output: Test report (passed/failed counts, coverage)
Log: "Tests: 16 passed, 2 failed (coverage: 85%)"
```

#### **STEP 5: DECISION POINT - Test Results**
```yaml
Condition: If all_tests_pass AND coverage >= required_coverage
  → Continue to STEP 6 (Commit Phase)

Condition: If tests_fail AND auto_fix.fix_test_failures = true
  → Trigger AUTO-DEBUG sub-loop:
     1. Parse test failure messages
     2. Identify root cause
     3. Apply fix
     4. Re-run tests
     5. If fixed → Continue to STEP 6
     6. If max_retries exceeded (3) → EXIT with BLOCKED status

Condition: If external_dependency_missing (e.g., pytest not installed)
  → EXIT with ERROR status (can't auto-fix)
```

**AUTO-DEBUG Example**:
```
Test Failure:
  test_highlights_panel_rendering FAILED
  AssertionError: expected highlights.length > 0, got 0

Auto-Debug Strategy:
1. Read test file to understand expected behavior
2. Read implementation file to find bug
3. Identify: API call missing await keyword
4. Apply fix: Add `await` to async call
5. Re-run test
6. Verify: Test now passes
7. Log: "✅ Auto-fixed: Missing await in highlights API call (retry 1/3)"
```

#### **STEP 6: COMMIT PHASE**
```yaml
Condition: If commits.auto_commit = true
  → Auto-commit changes:
     1. Update CONTEXT.md with "Recent Changes" entry
     2. Update AUDIT.md with auditor score + status
     3. Stage files: git add .
     4. Commit with comprehensive message
     5. Log: "✅ Committed: feat(highlights): implement frontend highlights panel"

Condition: If commits.auto_commit = false
  → Skip commit, continue to next task
```

#### **STEP 7: NEXT TASK or EXIT**
```yaml
Check exit conditions:
  ✅ all_tasks_complete → Report SUCCESS, exit loop
  🚫 max_retries_exceeded → Report BLOCKED, exit loop
  ⚠️ breaking_changes → Report PAUSE, exit loop
  ❌ external_dependency_missing → Report ERROR, exit loop
  🔄 None of above → Load next task, GOTO STEP 1

Action: Load next task
  - Read .specify/tasks/*.md
  - Find next pending task
  - Log: "Loading Task 4.6 - Search History"
  - GOTO STEP 1
```

---

## 🛡️ Safety Mechanisms

### 1. **Max Iterations Limit**
```yaml
# Prevent infinite loops
loop.max_iterations: 100

Example:
  - After 100 iterations, force exit with report
  - User can adjust in .claude/autonomous-config.yaml
```

### 2. **Max Retries Per Issue**
```yaml
# Prevent infinite retry on same issue
auto_fix.max_retries_per_issue: 3

Example:
  - Issue: "Type error in patient_search.py:45"
  - Retry 1: Apply fix → Still fails
  - Retry 2: Try alternative fix → Still fails
  - Retry 3: Try another approach → Still fails
  - Retry 4: BLOCKED - Exit loop, report to user
```

### 3. **Rollback on Regression**
```yaml
# If fix makes things worse, rollback
auto_fix.rollback_on_regression: true

Example:
  - Before fix: Auditor 98%, Tests 90% pass
  - After fix: Auditor 95%, Tests 70% pass (WORSE!)
  - Action: git stash pop → Rollback to before fix
  - Report: "Fix caused regression, rolled back"
```

### 4. **Breaking Changes Detection**
```yaml
# Require user decision for architectural changes
loop.stop_on_breaking_changes: true

Example:
  - Auditor detects: "Endpoint path changed from /api/v1/search to /api/v2/search"
  - Classification: BREAKING CHANGE (frontend integration breaks)
  - Action: EXIT loop with PAUSE status
  - Report: "Breaking change detected, requires architectural decision"
```

### 5. **File/Line Limits**
```yaml
# Prevent runaway changes
safety.max_files_per_iteration: 10
safety.max_lines_per_iteration: 2000

Example:
  - Task modifies 15 files → Exceeds limit (10)
  - Action: Ask user for confirmation before proceeding
  - User can override with autonomous-config.yaml
```

---

## 📊 Reporting

### **Periodic Progress Report** (every 5 iterations)
```
─────────────────────────────────────────────────
🔄 AUTONOMOUS LOOP PROGRESS REPORT (Iteration 15)
─────────────────────────────────────────────────

Current Task: Task 4.6 - Search History

Progress:
  ✅ Tasks Completed: 3/8 (Task 4.3, 4.4, 4.5)
  🔄 Current Task: Task 4.6 (in progress)
  ⏳ Remaining Tasks: 4 (Task 4.7, 4.8, 5.1, 5.2)

Auditor:
  📊 Latest Score: 100%
  ✅ Compliance: PASS (no issues)

Tests:
  ✅ Unit Tests: 28 passed, 0 failed
  ✅ Integration Tests: 16 passed, 0 failed
  ✅ Security Tests: 8 passed, 0 failed
  📈 Coverage: 87% line, 75% branch

Auto-Fixes Applied:
  1. Field name mismatch (retry 1/3) → FIXED
  2. Missing await keyword (retry 1/3) → FIXED
  3. Import error in Vue component (retry 2/3) → FIXED

Commits:
  📦 Commits Made: 3
  🔀 Branch: autonomous/mvp-execution
  ⬆️ Auto-pushed: No (auto_push: false)

Time Elapsed: 45 minutes
Estimated Remaining: ~1.5 hours

Status: 🟢 HEALTHY (no blocking issues)

─────────────────────────────────────────────────
```

### **Exit Report** (when loop completes or exits)
```
═════════════════════════════════════════════════
🎉 AUTONOMOUS LOOP COMPLETE - EXIT REPORT
═════════════════════════════════════════════════

Exit Reason: ✅ SUCCESS - All tasks complete

Summary:
  ⏱️  Total Time: 2 hours 15 minutes
  🔄 Total Iterations: 32
  ✅ Tasks Completed: 8/8 (100%)
  📦 Commits Made: 8
  🧪 Tests Created: 46
  ✅ Tests Passing: 100%
  📊 Final Auditor Score: 100%

Breakdown by Task:
  Task 4.3 ✅ (15 min, 1 commit, 13 tests, 0 retries)
  Task 4.4 ✅ (25 min, 1 commit, 9 tests, 2 retries)
  Task 4.5 ✅ (18 min, 1 commit, 7 tests, 1 retry)
  Task 4.6 ✅ (20 min, 1 commit, 6 tests, 0 retries)
  Task 4.7 ✅ (30 min, 2 commits, 11 tests, 3 retries)
  Task 4.8 ✅ (22 min, 1 commit, 0 tests, 1 retry)
  Task 5.1 ✅ (16 min, 1 commit, 0 tests, 0 retries)
  Task 5.2 ✅ (14 min, 1 commit, 0 tests, 0 retries)

Issues Encountered:
  🔧 Auto-Fixed: 12 issues (100% success rate)
  🚫 Blocked: 0 issues
  ⚠️ Manual Review Needed: 0 issues

Code Statistics:
  📝 Files Modified: 42
  ➕ Lines Added: 3,842
  ➖ Lines Deleted: 218
  📊 Net Change: +3,624 lines

Quality Metrics:
  ✅ PRD Compliance: 100%
  ✅ Test Coverage: 89% line, 78% branch
  ✅ Security Tests: All passing (HIPAA compliant)
  ✅ No breaking changes introduced

Recommendations:
  1. Review commits and create pull request
  2. Run full test suite in Docker environment
  3. Deploy to staging for manual QA
  4. Update project documentation

Next Steps:
  - All Phase 4 tasks complete
  - Ready to begin Phase 5 (Timeline Visualization)
  - Run: "autonomous mode" to continue with Phase 5

═════════════════════════════════════════════════
```

---

## 🚀 How to Activate Autonomous Mode

### Method 1: Direct Invocation
User says:
```
"Enter autonomous mode and complete all Phase 4 tasks"
"Continuous development - don't stop until Phase 4 is done"
"Auto-build everything autonomously"
```

### Method 2: Configuration File
User edits `.claude/autonomous-config.yaml`:
```yaml
loop:
  enabled: true
  stop_on_success: false  # Keep going to next task
```

Then says:
```
"Start autonomous loop"
```

### Method 3: Slash Command (Future)
```
/autonomous start
/autonomous stop
/autonomous status
```

---

## 🔧 Configuration Options

All behavior controlled by `.claude/autonomous-config.yaml`.

**Key settings**:
- `loop.enabled` - Enable/disable autonomous mode
- `auto_fix.enabled` - Allow automatic issue fixing
- `commits.auto_commit` - Auto-commit without confirmation
- `testing.auto_generate_missing` - Auto-create tests
- `loop.max_iterations` - Safety limit
- `auto_fix.max_retries_per_issue` - Prevent infinite retries
- `audit.blocking_threshold` - Minimum PRD compliance to continue

See `.claude/autonomous-config.yaml` for full options.

---

## 🎯 Execution Strategy

When this skill is activated:

1. **Load configuration** from `.claude/autonomous-config.yaml`
2. **Initialize loop state**:
   ```json
   {
     "iteration": 0,
     "current_task": null,
     "retry_counts": {},
     "commits_made": 0,
     "issues_fixed": 0,
     "tests_created": 0,
     "start_time": "2025-11-18T10:00:00Z"
   }
   ```
3. **Load first task** from `.specify/tasks/*.md`
4. **Enter loop** (build → audit → test → debug → commit → next)
5. **Track state** in `.claude/autonomous-loop.log`
6. **Report periodically** (every 5 iterations)
7. **Exit on condition** (success/blocked/pause/error)
8. **Generate comprehensive report**

---

## ⚠️ Important Notes

### When to Use Autonomous Mode
✅ **Good use cases**:
- Implementing well-defined tasks from specifications
- Completing a full phase (e.g., Phase 4 Patient Search)
- Catching up on technical debt backlog
- Creating comprehensive test suites

❌ **Bad use cases**:
- Exploratory work (no clear spec)
- Research tasks (not implementation)
- Complex architectural decisions (require human judgment)
- First-time feature design (need spec first)

### Safety Considerations
1. **Always commit frequently** (per_task recommended)
2. **Review commits before pushing** (auto_push: false by default)
3. **Monitor loop.log** for issues
4. **Set conservative retry limits** (3 attempts recommended)
5. **Stop on breaking changes** (require user review)

### Limitations
- Cannot make architectural decisions (human required)
- Cannot resolve external dependencies (e.g., install pytest)
- Cannot handle ambiguous requirements (need spec clarification)
- Cannot access external systems (APIs, databases) without credentials

---

## 📚 Integration with Existing Skills

Autonomous-developer **orchestrates other skills**:
- **auditor** - PRD compliance checking
- **prd-test-generator** - Test creation
- **healthcare-compliance-checker** - HIPAA validation
- **vue3-component-reuse** - Frontend patterns

It's a **meta-skill** that coordinates the full development lifecycle.

---

## 🐛 Troubleshooting

### Loop stuck on same issue (infinite retry)?
**Check**: `.claude/autonomous-loop.log` for retry count
**Fix**: Lower `auto_fix.max_retries_per_issue` to exit faster

### Loop making too many commits?
**Check**: `commits.commit_frequency` setting
**Fix**: Change from "per_fix" to "per_task" or "per_phase"

### Loop stops unexpectedly?
**Check**: Exit report for exit condition
**Fix**: Adjust `loop.stop_on_breaking_changes` or `audit.blocking_threshold`

### Auto-fix making things worse?
**Check**: `auto_fix.rollback_on_regression` is true
**Fix**: Disable auto-fix for complex issues: `auto_fix.enabled: false`

---

## 📖 Example: Full Autonomous Session

**User**: "Enter autonomous mode and complete Phase 4"

**Agent**:
```
✅ Autonomous mode activated
📋 Configuration loaded from .claude/autonomous-config.yaml
🔄 Starting loop: Phase 4 (8 tasks remaining)

─────────────────────────────────────────────────
Iteration 1: Task 4.3 - Backend Highlights API
─────────────────────────────────────────────────
✅ BUILD: Implemented highlights endpoint
🔍 AUDIT: Spawning auditor subagent...
  → Auditor score: 100% (0 issues)
✅ AUDIT: PASS
🧪 TEST: Running tests...
  → 13 unit tests: PASS
  → Integration tests: Generating...
  → 5 integration tests: PASS
✅ TEST: PASS (coverage: 92%)
📦 COMMIT: Auto-committing...
  → Updated CONTEXT.md
  → Updated AUDIT.md
  → Commit: feat(highlights): implement backend highlights API
✅ COMMIT: Complete (commit abc1234)

─────────────────────────────────────────────────
Iteration 2: Task 4.4 - Frontend Search Component
─────────────────────────────────────────────────
✅ BUILD: Implemented Vue search component
🔍 AUDIT: Spawning auditor subagent...
  → Auditor score: 95% (1 minor issue: field name mismatch)
⚠️  AUDIT: Below threshold (needs fixing)
🔧 AUTO-FIX: Applying fix for field name mismatch...
  → Changed: response.total → response.pagination.totalResults
🔍 AUDIT: Re-running auditor...
  → Auditor score: 100% (0 issues)
✅ AUDIT: PASS (retry 1/3 successful)
🧪 TEST: Running tests...
  → Frontend tests: FAIL (2/9 tests failing)
⚠️  TEST: Failures detected
🔧 AUTO-DEBUG: Analyzing failures...
  → Issue: Missing await in async call
  → Applying fix...
🧪 TEST: Re-running tests...
  → Frontend tests: PASS (9/9 tests passing)
✅ TEST: PASS (retry 1/3 successful)
📦 COMMIT: Auto-committing...
  → Commit: feat(search): implement frontend search component
✅ COMMIT: Complete (commit def5678)

[... continues for remaining 6 tasks ...]

─────────────────────────────────────────────────
LOOP COMPLETE: All tasks finished
─────────────────────────────────────────────────
✅ SUCCESS: Phase 4 complete (100%)
📊 8 tasks completed, 8 commits made, 46 tests created
⏱️  Total time: 2 hours 15 minutes
🎉 No blocking issues encountered

See full report above ⬆️
```

---

**End of Autonomous Developer Skill Documentation**
