# CCPM + Autonomous Loop Quick Start Guide

**Goal**: Start multiple parallel worktrees, each running its own never-ending autonomous agent loop

---

## What You Get

After following this guide, you'll have:

✅ **3 parallel git worktrees** (search, timeline, de-identification)
✅ **Each worktree running autonomous loop** (never stops)
✅ **Agents working simultaneously** (developer, auditor, tester, documentation)
✅ **Automatic task delegation** (agents create tasks for each other)
✅ **Real-time monitoring** (track progress across all worktrees)

---

## Prerequisites

- CCPM installed ✅ (already done)
- Git worktree support ✅
- Claude Code access ✅

---

## Step 1: View Current Epic (Search Module)

The search-module epic is already created as a demonstration.

```bash
# View the epic and tasks
cat .claude/ccpm/epics/search-module/epic.md

# List all tasks
ls -la .claude/ccpm/epics/search-module/
# Should show: 019.md, 020.md, 022.md, 023.md, 025.md, epic.md
```

**Tasks**:
- #019: Create useSearch composable
- #020: Create SearchBar component
- #021: Create SearchResults (DONE ✅)
- #022: Integration tests
- #023: Documentation
- #024: XSS fix (DONE ✅)
- #025: Security re-audit

---

## Step 2: Create Worktree for Search Module

```bash
# Create git worktree (isolated branch for parallel work)
git worktree add ../epic-search-module -b epic/search-module

# Verify worktree created
git worktree list
# Should show:
# /home/user/cogstack-nlp                       <current branch>
# /home/user/epic-search-module                 epic/search-module
```

---

## Step 3: Initialize Autonomous Loop in Worktree

```bash
# Initialize the autonomous loop for this worktree
.claude/scripts/spawn-worktree-loop.sh search-module ../epic-search-module
```

**What this does**:
- Creates `.claude/autonomous-worktrees/search-module/` directory
- Converts epic tasks to `TASK_QUEUE.md` format
- Creates worktree-specific agent config
- Creates `loop-status.md` tracker
- Sets up loop runner script

**Output**:
```
🚀 Initializing Autonomous Loop for Worktree
==========================================
Module: search-module
Worktree: ../epic-search-module
Epic: /home/user/cogstack-nlp/.claude/ccpm/epics/search-module

📁 Creating worktree configuration...
📋 Converting epic tasks to task queue...
✅ Created task queue with 6 tasks
⚙️ Creating agent configuration...
✅ Agent configuration created
📊 Creating loop status tracker...
✅ Loop status tracker created
🔄 Creating loop runner script...
✅ Loop runner script created

✅ Worktree Autonomous Loop Initialized!
==========================================

📦 Module: search-module
📂 Worktree: ../epic-search-module
📋 Task Queue: .claude/autonomous-worktrees/search-module/TASK_QUEUE.md
📊 Status: .claude/autonomous-worktrees/search-module/loop-status.md

🎯 Next Steps:

1. Enter the worktree:
   cd ../epic-search-module

2. Start the autonomous loop:
   .claude/scripts/worktree-loop-runner.sh search-module &

3. Monitor status:
   tail -f .claude/autonomous-worktrees/search-module/loop-status.md
```

---

## Step 4: View Task Queue

```bash
# View tasks for this worktree
cat .claude/autonomous-worktrees/search-module/TASK_QUEUE.md
```

**Example**:
```markdown
# Task Queue: search-module Module

## Tasks

- [ ] #019 [developer] Create useSearch Composable
- [ ] #020 [developer] Create SearchBar Component
- [✅] #021 [developer] Create SearchResults Component
- [ ] #022 [tester] Integration Tests for Search Module
- [ ] #023 [documentation] Document Search Module
- [✅] #024 [developer] FIX CRITICAL XSS vulnerability
- [ ] #025 [auditor] Re-review XSS Fix Verification

**Total Tasks**: 7
```

---

## Step 5: Start Autonomous Loop

```bash
# Enter the worktree
cd ../epic-search-module

# Start the loop in background
.claude/scripts/worktree-loop-runner.sh search-module &
# Loop PID: 12345

# Return to main repo
cd -
```

**What the loop does** (every 30 seconds):
1. Check TASK_QUEUE.md for pending tasks
2. If pending task found → prepare agent prompt
3. Agent prompt waits for pickup (CCWeb limitation)
4. When agent completes → commit triggers more agents
5. Loop continues indefinitely

---

## Step 6: Monitor All Worktrees

```bash
# View status of all worktrees
.claude/scripts/monitor-loops.sh --status
```

**Example Output**:
```
🔄 Autonomous Worktree Status
═══════════════════════════════════════════

📦 search-module (../epic-search-module)
   Branch: epic/search-module
   Status: ✅ RUNNING
   Agents: 2 active (developer, auditor)
   Tasks: 2/7 complete (29%)
   Last commit: 5 minutes ago

───────────────────────────────────────────
💡 Summary
   Total Worktrees: 1
   Running Loops: 1
   Active Agents: 2
   Tasks: 2/7 complete
   Overall Progress: 29%
```

---

## Step 7: Create More Parallel Worktrees (Optional)

### Timeline Module

```bash
# 1. Create epic (using CCPM commands)
# Note: In CCWeb, you'll need to do this manually or via slash commands

# 2. Create worktree
git worktree add ../epic-timeline-module -b epic/timeline-module

# 3. Initialize loop
.claude/scripts/spawn-worktree-loop.sh timeline-module ../epic-timeline-module

# 4. Start loop
cd ../epic-timeline-module
.claude/scripts/worktree-loop-runner.sh timeline-module &
cd -
```

### De-Identification Module

```bash
# Same pattern:
git worktree add ../epic-deidentification-module -b epic/deidentification-module
.claude/scripts/spawn-worktree-loop.sh deidentification-module ../epic-deidentification-module
cd ../epic-deidentification-module
.claude/scripts/worktree-loop-runner.sh deidentification-module &
cd -
```

Now you have **3 parallel worktrees**, each with its own autonomous loop!

---

## Step 8: Detailed Monitoring

```bash
# Detailed report with task queues and commits
.claude/scripts/monitor-loops.sh --report
```

**Output includes**:
- Loop status per worktree
- Task queue breakdown (pending, in-progress, completed)
- Next pending tasks
- Recent commits (last 5)
- Agent activity

---

## Controlling the Loops

### Stop All Loops

```bash
.claude/scripts/monitor-loops.sh --stop-all
```

Gracefully stops all autonomous loops. Agents finish current commit, then exit.

### Resume All Loops

```bash
.claude/scripts/monitor-loops.sh --resume-all
```

Restarts autonomous loops for all stopped worktrees.

### Stop Single Loop

```bash
# Find PID
cat .claude/autonomous-worktrees/search-module/.loop.pid
# PID: 12345

# Stop loop
kill -TERM 12345
```

---

## How Agents Coordinate

### Within a Worktree (Fast)

```
Developer completes Task #019
    ↓
Commits changes
    ↓
Post-commit hook detects completion
    ↓
Hook spawns: Auditor (review), Tester (validate), Documentation (document)
    ↓
3 agents work in parallel
    ↓
Each agent commits when done → triggers more agents
    ↓
Loop continues until all tasks complete
```

### Across Worktrees (Coordinated)

```
Timeline module needs SearchAPI from Search module
    ↓
Search module completes Task #019 (useSearch composable)
    ↓
Search module creates cross-worktree task in main TASK_QUEUE.md
    ↓
Main repo coordinator detects unblocked task
    ↓
Timeline worktree picks up task
    ↓
Timeline continues development
```

---

## CCWeb Limitations

**Current State**: Semi-autonomous
- ✅ Loops run continuously
- ✅ Agent prompts prepared automatically
- ❌ Agents need manual spawn (CCWeb can't spawn Claude Code from bash)

**Workaround**:
1. Loop prepares agent prompt
2. Prompt logged to `.claude/logs/agent-{PID}.log`
3. Human (you) opens Claude Code in worktree
4. Agent picks up prepared prompt and executes
5. Agent commits → triggers next agents

**Future**: When CCWeb API available, loops will be fully autonomous (no human intervention)

---

## Troubleshooting

### Worktree not found

**Issue**: `spawn-worktree-loop.sh` says worktree not found

**Fix**:
```bash
# Create worktree first
git worktree add <path> -b <branch-name>

# Then initialize loop
.claude/scripts/spawn-worktree-loop.sh <module> <path>
```

### Loop not running

**Issue**: `monitor-loops.sh` shows "STOPPED"

**Fix**:
```bash
# Check if process exists
ps aux | grep worktree-loop-runner

# If not running, start it
cd <worktree-path>
.claude/scripts/worktree-loop-runner.sh <module> &
```

### Tasks not syncing

**Issue**: Epic tasks not appearing in TASK_QUEUE.md

**Fix**:
```bash
# Manually sync
.claude/scripts/sync-epic-to-queue.sh <module>

# Check epic directory exists
ls .claude/ccpm/epics/<module>/
```

---

## Next Steps

1. **Create your own epic**:
   ```bash
   # Using CCPM commands (when available)
   /pm:prd-new my-feature
   /pm:prd-parse my-feature
   /pm:epic-decompose my-feature
   ```

2. **Initialize worktree**:
   ```bash
   git worktree add ../epic-my-feature -b epic/my-feature
   .claude/scripts/spawn-worktree-loop.sh my-feature ../epic-my-feature
   ```

3. **Start loop**:
   ```bash
   cd ../epic-my-feature
   .claude/scripts/worktree-loop-runner.sh my-feature &
   ```

4. **Monitor progress**:
   ```bash
   .claude/scripts/monitor-loops.sh --status
   ```

---

## Summary

You now have **multiple parallel worktrees, each stuck in its own never-ending loop**! 🎉

**What's autonomous**:
- ✅ Continuous task checking (every 30 seconds)
- ✅ Automatic agent prompt preparation
- ✅ Task delegation (agents create tasks for each other)
- ✅ Coordinated development across worktrees

**What requires manual intervention** (CCWeb limitation):
- Spawning Claude Code agents (prompts are prepared, you execute them)

**When fully autonomous** (future CCWeb API):
- Agents spawn automatically
- No human intervention required
- True 24/7 continuous development

---

For detailed architecture, see [CCPM_AUTONOMOUS_INTEGRATION.md](.claude/CCPM_AUTONOMOUS_INTEGRATION.md)
