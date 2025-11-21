# Autonomous Agent Loop - Quick Reference

**Version**: 1.6.0
**Status**: ✅ Production-Ready (All bugs fixed, 6/6 agents validated)

---

## 📚 What Is This?

A **self-sustaining development loop** where Claude Code subagents work continuously without human intervention. Agents collaborate by:

1. Reading tasks from `TASK_QUEUE.md`
2. Completing work autonomously
3. Creating new tasks for other agents
4. Committing their work (triggers next agent via git hook)
5. Loop continues until all tasks complete

**Key Innovation**: Git commits are **synchronization points** - each commit automatically spawns the next agent.

---

## 🚀 Quick Start

### 1. Initialize (First Time Only)

```bash
# Run initialization script
bash .claude/scripts/init-loop.sh
```

This will:
- Create necessary directories (logs, metrics)
- Link git hooks (post-commit, pre-commit)
- Verify state files exist
- Make scripts executable

### 2. Add Your First Task

```bash
# Add a task using the helper script
bash .claude/scripts/add-task.sh "developer" "Implement Sprint 5 Task 5.4.1 - Filter UI" "P1"
```

**Arguments**:
- Agent type: `developer`, `auditor`, `tester`, `debugger`, `documentation`, `task-definer`, `architecture-designer`, `test-generator`
- Task description: Brief description of what to do
- Priority: `P0` (critical), `P1` (important), `P2` (nice-to-have)

### 3. Start the Loop

```bash
# Commit the task to trigger the loop
git add .claude/TASK_QUEUE.md
git commit -m "chore: add task #1 to autonomous loop"

# The post-commit hook will automatically:
# - Detect the pending task
# - Spawn the appropriate agent (developer in this case)
# - Agent will work autonomously
```

### 4. Monitor Progress (Optional)

```bash
# Real-time dashboard (updates every 5 seconds)
bash .claude/scripts/monitor-loop.sh

# Or check logs
tail -f .claude/logs/agent-loop.log

# Or view task queue
cat .claude/TASK_QUEUE.md
```

---

## 📁 File Structure

```
.claude/
├── AUTONOMOUS_LOOP_DESIGN.md       # Complete design documentation
├── AUTONOMOUS_LOOP_README.md       # This file (quick reference)
├── agent-loop-config.yaml          # Configuration
├── TASK_QUEUE.md                   # Central task board
├── AGENT_STATUS.md                 # Agent heartbeats
├── COORDINATION.md                 # Agent messages
├── scripts/
│   ├── init-loop.sh                # Initialization script
│   ├── add-task.sh                 # Add tasks easily
│   ├── monitor-loop.sh             # Real-time dashboard
│   └── agent-wrapper.sh            # Agent execution wrapper
└── logs/
    ├── agent-loop.log              # Main loop log
    └── agent-<type>-<id>.log       # Individual agent logs

.git-hooks/
├── post-commit-agent-loop.sh       # Main orchestrator (spawns agents)
└── pre-commit-task-check.sh        # Validates task completion
```

---

## 🎯 How It Works

### Agent Lifecycle

```
1. [IDLE]
   └─> post-commit hook detects pending task

2. [CLAIMING]
   └─> Agent atomically claims task (mark [🔄])

3. [WORKING]
   └─> Agent executes task, updates heartbeat every 30s

4. [COMPLETING]
   └─> Agent marks task [✅]
   └─> Creates new tasks for other agents
   └─> Updates COORDINATION.md with messages

5. [COMMITTING]
   └─> Agent commits changes
   └─> post-commit hook triggers
   └─> Next agent spawned
   └─> LOOP CONTINUES
```

### Task States

- `[ ]` - **Pending**: Unclaimed, waiting for agent
- `[🔄]` - **In Progress**: Claimed by agent, currently working
- `[✅]` - **Completed**: Finished successfully
- `[❌]` - **Failed**: Exceeded retries or crashed
- `[⏸️]` - **Blocked**: Waiting on dependency or user decision

### Completion Detection

Loop automatically terminates when:
- ✅ No pending tasks (`[ ]`)
- ✅ No in-progress tasks (`[🔄]`)
- ✅ All agents IDLE

Then generates completion report:
```
╔════════════════════════════════════════════════════════════╗
║  AUTONOMOUS DEVELOPMENT LOOP - COMPLETION REPORT          ║
╚════════════════════════════════════════════════════════════╝

✅ Total Tasks Completed: 15
❌ Failed Tasks: 0
📊 Success Rate: 100%
⏱️  Duration: 2h 15m
```

---

## ⚙️ Configuration

Edit `.claude/agent-loop-config.yaml` to customize:

```yaml
# Max concurrent agents
max_total_agents: 6

# Per-agent limits
agent_limits:
  developer: 3      # Max 3 developers in parallel
  auditor: 1        # Only 1 auditor (sequential compliance)
  tester: 1         # Only 1 tester (resource-intensive)
  debugger: 2       # Max 2 debuggers

# Agent timeouts (seconds)
timeouts:
  developer: 3600   # 60 minutes
  auditor: 900      # 15 minutes
  tester: 1800      # 30 minutes

# Retry limits (before user escalation)
retry_limits:
  debugger: 3       # Max 3 attempts
  developer: 2      # Max 2 attempts
```

---

## 📊 Monitoring & Logs

### Real-time Dashboard

```bash
bash .claude/scripts/monitor-loop.sh 5
```

Shows:
- Task queue status (pending, in-progress, completed, failed)
- Active agents (with PIDs and progress)
- Recent commits
- Recent log entries

### Log Files

```bash
# Main loop log
tail -f .claude/logs/agent-loop.log

# Individual agent logs
tail -f .claude/logs/agent-developer-1.log
```

### Task Queue

```bash
# View current tasks
cat .claude/TASK_QUEUE.md

# Count pending tasks
grep -c "^- \[ \]" .claude/TASK_QUEUE.md
```

### Agent Status

```bash
# View agent statuses
cat .claude/AGENT_STATUS.md

# Count active agents
grep -c "Status: WORKING" .claude/AGENT_STATUS.md
```

---

## 🛠️ Common Operations

### Add a Task Manually

```bash
bash .claude/scripts/add-task.sh "developer" "Implement feature X" "P1"
git add .claude/TASK_QUEUE.md
git commit -m "chore: add task"
```

### Add a Task from Another Agent

Edit `TASK_QUEUE.md` directly:

```markdown
## 🟡 Normal Priority (P1)
- [ ] #15 `[auditor]` Review Filter UI for compliance **@developer** (created: 14:30:00)
```

Then commit to trigger loop.

### Stop the Loop

The loop stops automatically when all tasks complete. To force stop:

```bash
# Remove all pending tasks from TASK_QUEUE.md
# Or kill active agent processes (not recommended)
```

### Restart the Loop

```bash
# Add new tasks
bash .claude/scripts/add-task.sh "developer" "New task" "P1"

# Commit to trigger
git add .claude/TASK_QUEUE.md
git commit -m "chore: restart loop"
```

### Disable the Loop Temporarily

Edit `.claude/agent-loop-config.yaml`:

```yaml
git_hooks:
  post_commit:
    enabled: false  # Disable loop
```

Or use `--no-verify` to skip hooks:

```bash
git commit --no-verify -m "Manual commit"
```

---

## 🚨 Troubleshooting

### Loop Not Starting

**Symptoms**: Tasks remain pending, no agents spawned

**Solutions**:
1. Check if hooks are linked: `ls -la .git/hooks/post-commit`
2. Check if hooks are executable: `ls -l .git/hooks/post-commit`
3. Check loop log: `tail .claude/logs/agent-loop.log`
4. Verify config: `cat .claude/agent-loop-config.yaml | grep enabled`

### Agent Timeout

**Symptoms**: Task marked `[❌]` with "timeout" message

**Solutions**:
1. Increase timeout in config: `timeouts.agent-type`
2. Check agent log: `cat .claude/logs/agent-<type>-<id>.log`
3. Retry manually: Create new task for same work

### Deadlock Detected

**Symptoms**: "DEADLOCK" message in log, no progress

**Solutions**:
1. Check task dependencies in TASK_QUEUE.md
2. Resolve circular dependencies
3. Force-spawn agent: Add task and commit

### Agent Crash

**Symptoms**: Task marked `[❌]` with "crashed" message

**Solutions**:
1. Check agent log: `cat .claude/logs/agent-<type>-<id>.log`
2. Check error details in log
3. Fix issue and retry task

---

## 📈 Best Practices

### Task Description

✅ **Good**:
```markdown
- [ ] #10 `[developer]` Implement Task 5.4.1 - Filter UI component (frontend/src/components/FilterPanel.vue)
```

❌ **Bad**:
```markdown
- [ ] #10 `[developer]` Do the thing
```

### Task Granularity

✅ **Good**: Tasks that take 1-2 hours
❌ **Bad**: Tasks that take >4 hours (break into subtasks)

### Task Dependencies

✅ **Good**: Create dependent tasks after prerequisite completes
❌ **Bad**: Create circular dependencies

### Agent Selection

✅ **Good**: Assign to agent that matches the work
❌ **Bad**: Assign developer task to auditor

---

## 🎓 Example Workflows

### Simple Feature Implementation

```bash
# 1. Add task
bash .claude/scripts/add-task.sh "developer" "Implement Filter UI" "P1"
git add .claude/TASK_QUEUE.md && git commit -m "chore: add task #1"

# 2. Developer works (45 min)
# 3. Developer creates follow-up tasks:
#    - #2 [auditor] Review Filter UI
#    - #3 [tester] Run test suite
#    - #4 [documentation] Document FilterPanel
# 4. Developer commits

# 5. post-commit spawns 3 agents concurrently
# 6. Agents work in parallel
# 7. Auditor finds issue, creates #5 [developer] Fix RBAC
# 8. Auditor commits

# 9. post-commit spawns developer for #5
# 10. Developer fixes, commits
# 11. All tasks complete, loop terminates
```

### Sprint Development

```bash
# 1. Create technical plan
bash .claude/scripts/add-task.sh "architecture-designer" "Create Sprint 5 plan" "P1"
git commit -m "chore: start Sprint 5"

# 2. Architecture-designer creates plan, creates task for task-definer
# 3. Task-definer breaks into 12 tasks
# 4. Developers pick up tasks (3 parallel)
# 5. Loop continues for days until all 12 tasks complete
# 6. Completion report generated
```

---

## 📋 Version History & Bug Fixes

### v1.6.0 (2025-11-21) - Production Ready ✅

**Status**: All critical bugs fixed, 6/6 agents validated, production-ready

**Bug Fixes (v1.2.0 → v1.6.0)**:

1. **v1.2.0 (commit a7a3b47)** - Fixed grep count and task ID bugs
   - **Bug**: `grep -c` returning "0\n0" instead of "0"
   - **Fix**: Changed to `|| true` with `${count:-0}` fallback
   - **Bug**: Task IDs captured with trailing newlines
   - **Fix**: Added `head -1 | tr -d '\n'` pipeline

2. **v1.3.0 (commit 2bf2a47)** - Fixed early exit bug
   - **Bug**: Only 1 agent spawned per commit (expected up to 6)
   - **Fix**: Removed `&& exit 0` after `check_deadlock`, allowing main loop to run

3. **v1.4.0 (commit 6b93d3a)** - Fixed task counting bug
   - **Bug**: Counted 7 tasks instead of 6 (including documentation templates)
   - **Fix**: Changed regex from `^- \[ \]` to `^- \[ \] #[0-9]` (requires numeric ID)

4. **v1.5.0 (commit 8159584)** - Fixed deadlock false positives
   - **Bug**: Normal startup counted as deadlock
   - **Fix**: Only trigger deadlock on crashed agents: `in_progress > 0 && active == 0`

5. **v1.6.0 (commit f773887)** - **CRITICAL FIX** - Fixed set -e compatibility
   - **Bug**: Script stopped at "Checking task queue..." with no further output (BLOCKING)
   - **Fix**: Added `|| true` to prevent `set -e` from exiting on `check_deadlock` return 1
   - **Impact**: Without this fix, ZERO agents spawned (loop completely non-functional)

**Validation Results**:
- ✅ Commit f773887: 4 agents spawned concurrently (developer, tester, debugger, documentation)
- ✅ Commit 189b286: +1 agent spawned (5 total active)
- ✅ Commit d1662cb: +1 agent spawned (6/6 maximum concurrent reached)
- ✅ Commit 2d58981: 4 real development tasks auto-spawned (production validation)
- ✅ Success rate: 100% (all spawned agents executed successfully)

**Production Status**:
- ✅ All 6 critical bugs fixed
- ✅ Concurrent spawning validated (6/6 agents working simultaneously)
- ✅ Real development started (transitioned from simulation to actual work)
- ✅ Currently running with active agents (tasks #19-24)

**See**: CONTEXT.md ADR-012 for complete technical details

---

## 📚 Further Reading

- **Complete Design**: `.claude/AUTONOMOUS_LOOP_DESIGN.md` (1,250 lines)
- **Configuration**: `.claude/agent-loop-config.yaml`
- **Agent Definitions**: `.claude/agents/*.md`
- **CCPM Architecture**: `CONTEXT.md` (search "CCPM Multi-Agent")

---

## 💡 Tips

- **Start small**: Test with 1-2 tasks before full sprint
- **Monitor logs**: Keep `tail -f .claude/logs/agent-loop.log` open
- **Use dashboard**: `monitor-loop.sh` provides live status
- **Check heartbeats**: Agents should update every 30s
- **Review completion**: Check TASK_QUEUE.md for quality
- **Tune timeouts**: Adjust based on task complexity

---

**Ready to begin autonomous development? Run `bash .claude/scripts/init-loop.sh` to start!** 🚀
