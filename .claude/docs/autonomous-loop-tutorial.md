# Autonomous Loop Tutorial: Step-by-Step Guide

**Version**: 1.6.0
**Audience**: Developers new to the autonomous loop system
**Prerequisites**: Basic git and bash knowledge
**Duration**: 30-45 minutes

---

## 📚 Table of Contents

1. [Introduction](#introduction)
2. [Setup](#setup)
3. [Your First Task](#your-first-task)
4. [Understanding the Loop](#understanding-the-loop)
5. [Real-World Examples](#real-world-examples)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## 1. Introduction

### What is the Autonomous Loop?

The autonomous loop is a **self-sustaining development system** where Claude Code subagents work continuously without human intervention until all tasks are complete.

**Key concept**: Each git commit triggers the next agent, creating a continuous development cycle.

```
You → Add task → Commit → Hook spawns agent → Agent works → Agent commits →
Hook spawns next agent → ... → All tasks complete
```

### Why Use It?

- **Zero waiting**: Agents work 24/7 without human intervention
- **Parallel efficiency**: Up to 6 agents work simultaneously
- **Self-organizing**: Agents create tasks for each other
- **Git-native**: No external services or databases needed

---

## 2. Setup

### Step 1: Initialize the Loop

```bash
# Navigate to your project
cd /path/to/your/project

# Run initialization script
bash .claude/scripts/init-loop.sh
```

**What this does**:
- Creates log directories
- Links git hooks (post-commit, pre-commit)
- Verifies state files exist
- Makes scripts executable

### Step 2: Verify Setup

```bash
# Run test script
bash .claude/scripts/test-loop.sh
```

**Expected output**:
```
========================================
TEST SUMMARY
========================================
Total tests run: 25
Passed: 25
Success rate: 100%

✓ ALL TESTS PASSED
Autonomous loop validation successful!
```

---

## 3. Your First Task

### Example 1: Simple Feature Implementation

**Scenario**: You want to add a new utility function to your codebase.

#### Step 1: Add the Task

```bash
bash .claude/scripts/add-task.sh "developer" "Add string utility function for title case conversion" "P1"
```

**Output**:
```
✅ Task #25 added to queue
Agent: developer
Description: Add string utility function for title case conversion
Priority: P1
```

#### Step 2: Commit to Trigger the Loop

```bash
git add .claude/TASK_QUEUE.md
git commit -m "chore: add task #25 - title case utility"
```

**What happens automatically**:
1. Post-commit hook detects new task
2. Hook spawns developer agent
3. Agent reads task #25
4. Agent implements function with tests
5. Agent commits code
6. Hook detects completion → loop terminates (no more tasks)

#### Step 3: Monitor Progress (Optional)

```bash
# Watch logs in real-time
tail -f .claude/logs/agent-loop.log

# Or use dashboard (updates every 5s)
bash .claude/scripts/monitor-loop.sh
```

---

## 4. Understanding the Loop

### The Agent Lifecycle

```
1. IDLE
   └─> Task added to TASK_QUEUE.md

2. CLAIMING
   └─> Post-commit hook detects task
   └─> Hook atomically claims task (marks [🔄])

3. WORKING
   └─> Agent executes task
   └─> Agent updates heartbeat every 30s
   └─> Agent creates follow-up tasks if needed

4. COMPLETING
   └─> Agent marks task [✅]
   └─> Agent updates CONTEXT.md
   └─> Agent commits changes

5. TRIGGERING NEXT
   └─> Post-commit hook fires
   └─> Hook spawns next agents (up to 6 concurrent)
   └─> Loop continues...
```

### Task States

| State | Symbol | Meaning |
|-------|--------|---------|
| Pending | `[ ]` | Waiting for agent to claim |
| In Progress | `[🔄]` | Agent currently working |
| Completed | `[✅]` | Successfully finished |
| Failed | `[❌]` | Exceeded retries or crashed |
| Blocked | `[⏸️]` | Waiting on dependency or user |

---

## 5. Real-World Examples

### Example 2: Feature with Dependencies

**Scenario**: Implementing a new API endpoint that requires tests and documentation.

#### Step 1: Add Main Task

```bash
bash .claude/scripts/add-task.sh "developer" "Implement POST /api/v1/users endpoint" "P1"
```

#### Step 2: Agent Creates Follow-Up Tasks

The developer agent will automatically create:
- Task #27 `[auditor]` Review users endpoint for HIPAA compliance
- Task #28 `[tester]` Run integration tests for users endpoint
- Task #29 `[documentation]` Document users endpoint in API docs

#### Step 3: Watch the Chain Reaction

```
Commit (task #26) → Developer works (45 min) → Creates tasks #27-29 → Commits
                    ↓
Post-commit hook → Spawns auditor, tester, documentation (parallel)
                    ↓
Agents work simultaneously → All complete → Commit
                    ↓
Loop terminates (all tasks done)
```

---

### Example 3: Sprint Development

**Scenario**: You have a complete sprint with 12 tasks across multiple features.

#### Step 1: Add All Tasks at Once

```bash
# Task 1: Architecture
bash .claude/scripts/add-task.sh "architecture-designer" "Create technical plan for Sprint 5" "P1"

# Then commit
git add .claude/TASK_QUEUE.md
git commit -m "chore: start Sprint 5 autonomous development"
```

#### Step 2: Architecture Agent Creates Task Breakdown

The architecture-designer will:
1. Read specification
2. Design system architecture
3. Create task for task-definer agent

#### Step 3: Task-Definer Creates 12 Implementation Tasks

```markdown
- [ ] #2 `[developer]` Implement filter UI component
- [ ] #3 `[developer]` Add filter API endpoint
- [ ] #4 `[developer]` Create filter service layer
- [ ] #5 `[test-generator]` Generate tests for filter feature
- [ ] #6 `[auditor]` Review filter implementation
- [ ] #7 `[tester]` Run full test suite
- ... (6 more tasks)
```

#### Step 4: Agents Work Concurrently

```
Time: 0:00
├─ developer (task #2) ─────────> 60 min ──> Complete
├─ developer (task #3) ───────> 45 min ──> Complete
└─ developer (task #4) ─────────> 75 min ──> Complete

Time: 1:15
├─ test-generator (task #5) ──> 20 min ──> Complete
├─ auditor (task #6) ───────> 15 min ──> Complete  (finds issue, creates task #13)
└─ tester (task #7) ─────────> 30 min ──> Complete

Time: 1:45
└─ debugger (task #13) ──────> 10 min ──> Complete  (fixes auditor issue)

Total: ~2 hours for 12 tasks (vs 6 hours sequential)
```

---

### Example 4: Handling Failures

**Scenario**: An agent fails due to missing dependency.

#### What Happens

```bash
# Agent tries to import missing library
ImportError: No module named 'missing_lib'

# Agent marks task as [❌]
# Agent creates escalation task
```

**In TASK_QUEUE.md**:
```markdown
- [❌] #15 `[developer]` Implement feature X (failed: missing dependency)

- [ ] #16 `[user]` Install missing_lib before retrying task #15 **@developer**
  - **Context**: Feature X requires missing_lib
  - **Action**: Run: pip install missing_lib
  - **Next**: Recreate task #15 after installation
```

**You fix it**:
```bash
pip install missing_lib
bash .claude/scripts/add-task.sh "developer" "Implement feature X (retry)" "P0"
git commit -m "chore: retry task #15 with dependency installed"
# Loop resumes!
```

---

## 6. Troubleshooting

### Issue 1: Loop Not Starting

**Symptoms**: Tasks remain pending, no agents spawned

**Solutions**:
1. Check hook is linked: `ls -la .git/hooks/post-commit`
2. Check hook is executable: `chmod +x .git-hooks/post-commit-agent-loop.sh`
3. Check config: `grep enabled .claude/agent-loop-config.yaml`
4. Check logs: `tail .claude/logs/agent-loop.log`

---

### Issue 2: Agent Timeout

**Symptoms**: Task marked `[❌]` with "timeout" message

**Solutions**:
1. Increase timeout in `.claude/agent-loop-config.yaml`:
   ```yaml
   timeouts:
     developer: 7200  # 2 hours instead of 1 hour
   ```
2. Check agent log: `cat .claude/logs/agent-developer-15.log`
3. Retry task with simpler scope

---

### Issue 3: Interleaved Log Output

**Symptoms**: Logs show garbled output like "Spawning developer for task #[INFO] Claimed task #22"

**Status**: Fixed in v1.6.0! If you see this, you're on an older version.

**Solution**: Update to v1.6.0:
```bash
git pull origin main
bash .claude/scripts/init-loop.sh
```

---

## 7. Best Practices

### DO ✅

**1. Write Clear Task Descriptions**

Good:
```bash
bash .claude/scripts/add-task.sh "developer" "Implement Task 5.4.1 - Filter UI component with meta-annotation support (frontend/src/components/FilterPanel.vue)" "P1"
```

Bad:
```bash
bash .claude/scripts/add-task.sh "developer" "Do the filter thing" "P1"
```

**2. Break Large Tasks into Smaller Ones**

Good: 12 tasks × 1-2 hours = manageable

Bad: 1 task × 24 hours = high risk of failure

**3. Monitor Logs During First Run**

```bash
# Keep this open for your first loop
tail -f .claude/logs/agent-loop.log
```

**4. Use Priorities Effectively**

- `P0` (critical): Blocker bugs, security issues
- `P1` (important): Feature work, normal development
- `P2` (nice-to-have): Documentation, refactoring

**5. Let Agents Create Tasks**

Don't micro-manage! Agents know what follow-up work is needed.

---

### DON'T ❌

**1. Don't Modify Tasks While Agents Work**

Wait for task to complete before editing TASK_QUEUE.md

**2. Don't Skip Initialization**

Always run `init-loop.sh` in new environments

**3. Don't Ignore Failures**

If agent fails, investigate why before retrying

**4. Don't Commit with `--no-verify` in Loop**

This skips hooks and breaks the loop!

**5. Don't Expect Instant Results**

Agents need time to work. First task typically takes 30-60 minutes.

---

## 8. Advanced Usage

### Custom Agent Limits

Edit `.claude/agent-loop-config.yaml`:

```yaml
max_total_agents: 6

agent_limits:
  developer: 4        # Allow 4 developers in parallel
  auditor: 1          # Keep sequential for compliance
  tester: 2           # Allow 2 testers
  debugger: 3         # Allow 3 debuggers
```

### Custom Timeouts

```yaml
timeouts:
  developer: 3600     # 1 hour
  architecture-designer: 7200  # 2 hours (needs more time)
  tester: 1800        # 30 minutes
```

### Disable Loop Temporarily

```yaml
git_hooks:
  post_commit:
    enabled: false  # Loop won't run
```

Or use `--no-verify`:
```bash
git commit --no-verify -m "Manual commit without triggering loop"
```

---

## 9. Real Session Example

Let's walk through a complete session from start to finish.

### Initial State

```bash
$ cat .claude/TASK_QUEUE.md
# No pending tasks
```

### Add First Task

```bash
$ bash .claude/scripts/add-task.sh "developer" "Add user search feature" "P1"
✅ Task #1 added to queue

$ git add .claude/TASK_QUEUE.md
$ git commit -m "chore: add task #1"
[INFO] Post-commit hook: Agent loop starting
[INFO] Claimed task #1 for developer
[INFO] Spawning developer for task #1...
[INFO] Agent developer spawned (PID: 12345, task #1)
```

### 45 Minutes Later...

```bash
$ tail .claude/logs/agent-developer-1.log
[INFO] Reading TASK_QUEUE.md
[INFO] Task #1: Add user search feature
[INFO] Creating tests...
[INFO] Tests created: test_user_search.py
[INFO] Implementing feature...
[INFO] Feature complete
[INFO] Creating follow-up tasks...
[INFO] Committing changes...

$ cat .claude/TASK_QUEUE.md
- [✅] #1 `[developer]` Add user search feature
- [ ] #2 `[auditor]` Review user search for HIPAA compliance
- [ ] #3 `[tester]` Run integration tests for user search
- [ ] #4 `[documentation]` Document user search API
```

### Hook Spawns Next 3 Agents

```bash
[INFO] Post-commit hook: Agent loop starting
[INFO] Spawning auditor for task #2...
[INFO] Spawning tester for task #3...
[INFO] Spawning documentation for task #4...
[INFO] Post-commit complete. Spawned: 3, Total active: 3
```

### 20 Minutes Later: All Complete

```bash
$ cat .claude/TASK_QUEUE.md
- [✅] #1 `[developer]` Add user search feature
- [✅] #2 `[auditor]` Review user search for HIPAA compliance
- [✅] #3 `[tester]` Run integration tests for user search
- [✅] #4 `[documentation]` Document user search API

$ tail .claude/logs/agent-loop.log
[INFO] ✅ AUTONOMOUS LOOP COMPLETE!

╔════════════════════════════════════════════════════════════╗
║  AUTONOMOUS DEVELOPMENT LOOP - COMPLETION REPORT          ║
╚════════════════════════════════════════════════════════════╝

📊 TASK SUMMARY
  ✅ Tasks Completed: 4
  ❌ Tasks Failed:    0
  📈 Success Rate:    100%
  🎯 Total Tasks:     4

⏱️  SESSION TIMING
  🚀 Started:  2025-11-21T14:00:00+00:00
  🏁 Ended:    2025-11-21T15:05:00+00:00
  📝 Commits:  5
  🤖 Spawns:   4

👥 AGENT METRICS
  developer:      1 tasks
  auditor:        1 tasks
  tester:         1 tasks
  debugger:       0 tasks
  documentation:  1 tasks

All agents IDLE. Loop terminated successfully.
```

**Total time**: 1 hour 5 minutes for complete feature including tests, compliance review, and documentation!

---

## 10. Next Steps

**You've completed the tutorial! 🎉**

**What to do next**:

1. **Try it yourself**: Add a simple task and watch the loop work
2. **Read the design doc**: `.claude/AUTONOMOUS_LOOP_DESIGN.md` (1,250 lines)
3. **Customize config**: Edit `.claude/agent-loop-config.yaml` for your needs
4. **Join the workflow**: Start using it for real development

**Questions?**
- Check `.claude/AUTONOMOUS_LOOP_README.md` (quick reference)
- Read CONTEXT.md ADR-012 (technical details)
- Review agent definitions in `.claude/agents/*.md`

**Happy autonomous development! 🚀**
