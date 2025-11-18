# 🤖 Starting Autonomous Development Mode

Quick guide to activate fully autonomous build → audit → test → debug → commit loop.

---

## 🚀 Quick Start (3 ways)

### Option 1: Say It to Claude Code
```
"Enter autonomous mode and complete Phase 4"
"Continuous development - don't stop until done"
"Auto-build everything autonomously"
```

### Option 2: Edit Configuration First
1. Open `.claude/autonomous-config.yaml`
2. Verify settings (especially `loop.enabled: true`)
3. Say: "Start autonomous loop"

### Option 3: Future (Slash Command)
```
/autonomous start
/autonomous stop
/autonomous status
```

---

## ⚙️ Configuration Checklist

Before starting autonomous mode, **review these key settings** in `.claude/autonomous-config.yaml`:

### 🔄 Loop Behavior
```yaml
loop:
  enabled: true                    # ✅ Must be true
  max_iterations: 100              # Safety limit (adjust if needed)
  stop_on_success: false           # false = continue to next task
  stop_on_blocking: true           # true = stop if can't auto-fix
  stop_on_breaking_changes: true   # true = require user decision
```

### 🔧 Auto-Fix Settings
```yaml
auto_fix:
  enabled: true                    # ✅ Enable automatic fixing
  max_retries_per_issue: 3         # Prevent infinite loops
  fix_auditor_issues: true         # Fix PRD compliance drift
  fix_test_failures: true          # Fix failing tests
  fix_breaking_changes: false      # ⚠️ Require user decision
```

### 📦 Commit Settings
```yaml
commits:
  auto_commit: true                # ✅ Auto-commit without asking
  commit_frequency: "per_task"     # When to commit
  auto_push: false                 # ⚠️ false = local only (safer)
```

### 🎯 Task Management
```yaml
tasks:
  auto_load_next: true             # ✅ Continue to next task
  source_priority:
    - "specification"              # Tasks from .specify/tasks/
    - "test_report"                # Missing tests
    - "technical_debt"             # CONTEXT.md debt items
```

---

## 📋 What Happens in Autonomous Mode?

```
FOR EACH TASK:
  ┌─────────────────────────────────────────┐
  │ 1. BUILD:   Implement task              │
  │ 2. AUDIT:   Check PRD compliance        │
  │ 3. FIX:     Auto-fix if issues (3x max) │
  │ 4. TEST:    Generate + run tests        │
  │ 5. DEBUG:   Auto-fix failures (3x max)  │
  │ 6. COMMIT:  Auto-commit with docs       │
  │ 7. NEXT:    Load next task OR exit      │
  └─────────────────────────────────────────┘
         │
         └─► REPEAT until done/blocked
```

**Exit Conditions** (when loop stops):
- ✅ **SUCCESS**: All tasks complete, tests pass, 100% PRD compliant
- 🚫 **BLOCKED**: Max retries exceeded (can't auto-fix)
- ⚠️ **PAUSE**: Breaking changes (need user decision)
- ❌ **ERROR**: External dependency missing

---

## 📊 Monitoring Progress

### Periodic Reports (every 5 iterations)
Shows:
- Current task
- Tasks completed/remaining
- Auditor score
- Test results
- Issues auto-fixed
- Time elapsed/remaining

### Exit Report (when complete)
Shows:
- Total tasks completed
- Total commits made
- Total tests created
- Issues encountered/fixed
- Time breakdown
- Quality metrics
- Next steps

### Log File
```bash
# View real-time progress
tail -f .claude/autonomous-loop.log
```

---

## 🛡️ Safety Features

### 1. Retry Limits
- Max 3 attempts to fix each unique issue
- After 3 failures → BLOCKED, exit loop, report to user

### 2. Iteration Limit
- Max 100 iterations (prevent infinite loops)
- Configurable via `loop.max_iterations`

### 3. Rollback on Regression
- If fix makes things worse → automatic rollback
- Uses git stash for safety

### 4. Breaking Change Detection
- Architectural changes → PAUSE, ask user
- Examples: Endpoint path changes, schema restructuring

### 5. File/Line Limits
- Max 10 files per iteration (default)
- Max 2000 lines per iteration (default)
- Exceeding → Ask confirmation

---

## ⚠️ Important Notes

### Before Starting Autonomous Mode

✅ **DO THIS**:
1. Ensure specifications exist (`.specify/specifications/*.md`)
2. Ensure tasks defined (`.specify/tasks/*.md`)
3. Review configuration (`.claude/autonomous-config.yaml`)
4. Commit current work (clean git state)
5. Create feature branch if needed

❌ **DON'T DO THIS**:
1. Start without specifications (loop will fail)
2. Enable `auto_push: true` on main branch (risky!)
3. Set `max_retries_per_issue` too high (infinite loops)
4. Disable safety features (`rollback_on_regression: false`)

### During Autonomous Mode

✅ **SAFE TO DO**:
- Monitor `.claude/autonomous-loop.log`
- Review commits as they're made
- Interrupt with Ctrl+C if needed (graceful exit)

❌ **AVOID**:
- Manually editing files while loop runs (conflicts!)
- Deleting `.claude/autonomous-config.yaml` (loop crashes)
- Force-stopping (use Ctrl+C for graceful exit)

### After Autonomous Mode

✅ **RECOMMENDED**:
1. Review all commits made
2. Run tests in Docker environment
3. Create pull request for review
4. Deploy to staging for QA
5. Update project documentation

---

## 🐛 Troubleshooting

### Problem: Loop exits immediately with "No tasks found"
**Solution**: Create tasks in `.specify/tasks/*.md` first

### Problem: Loop stuck on same issue (retrying forever)
**Solution**: Check `.claude/autonomous-loop.log`, lower `max_retries_per_issue`

### Problem: Too many commits being made
**Solution**: Change `commit_frequency` from "per_fix" to "per_task"

### Problem: Loop stops with PAUSE (breaking changes)
**Solution**: Review auditor report, decide if change is acceptable, adjust code or PRD

### Problem: Tests fail but loop doesn't auto-fix
**Solution**: Check `testing.auto_fix_failures: true` is set

---

## 📚 Example Session

```
You: "Enter autonomous mode and complete Phase 4"

Claude:
✅ Autonomous mode activated
📋 Loaded config from .claude/autonomous-config.yaml
🔄 Starting loop: Phase 4 (8 tasks)

─────────────────────────────────────────────────
Iteration 1: Task 4.3 - Backend Highlights API
─────────────────────────────────────────────────
✅ BUILD: Complete
🔍 AUDIT: 100% compliant
🧪 TEST: 18 tests passing
📦 COMMIT: feat(highlights): implement backend API

─────────────────────────────────────────────────
Iteration 2: Task 4.4 - Frontend Search Component
─────────────────────────────────────────────────
✅ BUILD: Complete
🔍 AUDIT: 95% compliant (1 issue)
🔧 AUTO-FIX: Field name mismatch → FIXED
🔍 AUDIT: 100% compliant
🧪 TEST: 2/9 failing
🔧 AUTO-DEBUG: Missing await → FIXED
🧪 TEST: 9/9 passing
📦 COMMIT: feat(search): implement frontend component

[... 6 more iterations ...]

─────────────────────────────────────────────────
LOOP COMPLETE
─────────────────────────────────────────────────
✅ SUCCESS: Phase 4 complete
📊 8 tasks, 8 commits, 46 tests
⏱️  2h 15m total time
```

---

## 🎯 Customization Examples

### Conservative Mode (Manual Review)
```yaml
loop:
  stop_on_success: true          # Stop after each task
commits:
  auto_commit: false             # Don't auto-commit
auto_fix:
  max_retries_per_issue: 1       # One attempt only
```

### Aggressive Mode (Full Automation)
```yaml
loop:
  stop_on_success: false         # Keep going
  max_iterations: 500            # High limit
commits:
  auto_commit: true              # Auto-commit
  commit_frequency: "per_phase"  # Batch commits
auto_fix:
  max_retries_per_issue: 5       # More attempts
```

### Testing Focus (Generate All Tests)
```yaml
tasks:
  source_priority:
    - "test_report"              # Missing tests first
    - "specification"            # Then spec tasks
testing:
  auto_generate_missing: true    # Always create tests
  required_line_coverage: 90     # High bar
```

---

## 📞 Getting Help

**Documentation**:
- Configuration: `.claude/autonomous-config.yaml` (inline comments)
- Skill details: `.claude/skills/autonomous-developer/SKILL.md`
- General guide: `CLAUDE.md`

**Troubleshooting**:
- Check log: `.claude/autonomous-loop.log`
- Review commits: `git log --oneline`
- Check status: Review periodic reports

**Stopping the Loop**:
- Graceful: Press Ctrl+C (will finish current iteration then exit)
- Force: Ctrl+C twice (may leave incomplete work)

---

## ✅ Checklist Before Starting

```
[ ] Specifications exist (.specify/specifications/*.md)
[ ] Tasks defined (.specify/tasks/*.md)
[ ] Configuration reviewed (.claude/autonomous-config.yaml)
[ ] Git state clean (no uncommitted changes)
[ ] On feature branch (not main)
[ ] auto_push: false (safety first)
[ ] max_iterations reasonable (100 default)
[ ] max_retries_per_issue reasonable (3 default)
```

**Once checklist complete, say**:
```
"Enter autonomous mode"
```

---

**Happy autonomous developing!** 🚀
