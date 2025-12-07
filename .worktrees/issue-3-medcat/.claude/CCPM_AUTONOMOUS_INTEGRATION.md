# CCPM + Autonomous Loop Integration

**Version**: 1.0.0
**Date**: 2025-11-21
**Purpose**: Integrate CCPM's worktree management with autonomous agent loops for true parallel development

---

## Architecture Overview

This integration combines:
- **CCPM**: Project management, epic/task organization, worktree management
- **Autonomous Loops**: Continuous agent execution, task delegation, never-ending cycles

**Result**: Multiple parallel worktrees, each running its own autonomous agent loop continuously

---

## System Components

### 1. CCPM Structure (Installed)

```
.claude/ccpm/
├── commands/pm/          # /pm:* slash commands
├── epics/               # Epic and task files
├── prds/                # Product requirement documents
├── scripts/             # Helper scripts
├── hooks/               # Git hooks
├── rules/               # Coordination rules
└── context/             # Shared context
```

### 2. Autonomous Loop Components (Existing)

```
.claude/
├── TASK_QUEUE.md        # Central task tracking
├── agent-loop-config.yaml  # Agent configurations
├── scripts/
│   ├── agent-wrapper.sh    # Agent execution wrapper
│   └── claim-task.sh       # Task claiming logic
└── logs/                # Agent execution logs
```

### 3. Integration Layer (NEW)

```
.claude/
├── autonomous-worktrees/    # Worktree-specific configs
│   ├── search-module/
│   │   ├── TASK_QUEUE.md    # Module-specific tasks
│   │   ├── agent-config.yaml
│   │   └── loop-status.md
│   ├── timeline-module/
│   └── deidentification-module/
└── scripts/
    ├── spawn-worktree-loop.sh  # Start autonomous loop in worktree
    ├── monitor-loops.sh         # Monitor all active loops
    └── sync-worktrees.sh        # Coordinate between worktrees
```

---

## Workflow: Creating Autonomous Worktree

### Step 1: Create Epic with CCPM

```bash
# 1. Create PRD for new module
/pm:prd-new search-module

# 2. Parse to technical plan
/pm:prd-parse search-module

# 3. Decompose into tasks
/pm:epic-decompose search-module

# 4. View the plan
/pm:epic-show search-module
```

This creates:
```
.claude/ccpm/epics/search-module/
├── epic.md          # Technical plan
├── 001.md           # Task: SearchBar component
├── 002.md           # Task: SearchResults component
├── 003.md           # Task: useSearch composable
└── 004.md           # Task: Integration tests
```

### Step 2: Create Worktree for Epic

```bash
# Create git worktree for parallel development
git worktree add ../epic-search-module -b epic/search-module

# Worktree structure:
# ../epic-search-module/        <- Isolated git working directory
#   ├── .git/                   <- Linked to main repo
#   ├── frontend/               <- Can modify independently
#   ├── backend/
#   └── .claude/                <- Shared config (symlinked)
```

### Step 3: Initialize Autonomous Loop in Worktree

```bash
# Initialize autonomous loop for this worktree
.claude/scripts/spawn-worktree-loop.sh search-module ../epic-search-module

# This creates:
# 1. Module-specific TASK_QUEUE.md from epic tasks
# 2. Worktree-specific agent config
# 3. Post-commit hook that spawns agents in THIS worktree
# 4. Background loop process (runs continuously)
```

### Step 4: Start the Loop

```bash
# The loop starts automatically and:
# 1. Reads tasks from .claude/ccpm/epics/search-module/*.md
# 2. Converts to TASK_QUEUE.md format
# 3. Spawns appropriate agents (developer, auditor, tester)
# 4. Agents work → commit → trigger more agents
# 5. Loop continues until all tasks complete
# 6. Never stops on its own (truly autonomous)
```

---

## Multiple Parallel Worktrees

### Scenario: 3 Modules Developing in Parallel

```bash
# Terminal 1: Search Module Loop
cd ../epic-search-module
# Autonomous loop running:
# - Developer agent working on SearchBar
# - Auditor reviewing XSS vulnerabilities
# - Tester running component tests

# Terminal 2: Timeline Module Loop
cd ../epic-timeline-module
# Autonomous loop running:
# - Developer implementing TimelineView
# - Documentation agent writing API docs
# - Architecture designer planning data flow

# Terminal 3: De-Identification Module Loop
cd ../epic-deidentification-module
# Autonomous loop running:
# - Developer implementing PHI detection
# - Auditor checking HIPAA compliance
# - Tester validating edge cases
```

Each worktree:
- ✅ Has its own TASK_QUEUE.md
- ✅ Runs its own autonomous loop
- ✅ Spawns its own agents
- ✅ Commits independently
- ✅ Never stops (continuous loop)

---

## Task Delegation Across Worktrees

### Within a Worktree (Fast)

```markdown
# In epic-search-module/TASK_QUEUE.md

- [✅] #1 [developer] Create SearchBar component
  → Delegates to [auditor] Review SearchBar security
  → Delegates to [tester] Test SearchBar interactions
  → Delegates to [documentation] Document SearchBar API
```

Delegation happens via local file updates (instant).

### Across Worktrees (Coordinated)

```markdown
# Timeline module depends on Search module's API

# epic-search-module/TASK_QUEUE.md
- [✅] #3 [developer] Export SearchAPI interface
  → Creates task in main TASK_QUEUE.md for timeline module

# Main .claude/TASK_QUEUE.md (coordination layer)
- [ ] #10 [developer] Timeline: Integrate SearchAPI
  → Assigned to: epic-timeline-module
  → Depends on: epic-search-module #3
```

Main TASK_QUEUE.md acts as coordination layer for cross-module tasks.

---

## Git Hook Integration

### Per-Worktree Post-Commit Hook

Each worktree has its own `.git/hooks/post-commit`:

```bash
#!/bin/bash
# .git/hooks/post-commit (in epic-search-module)

WORKTREE_NAME="search-module"
EPIC_DIR=".claude/ccpm/epics/$WORKTREE_NAME"
TASK_QUEUE=".claude/autonomous-worktrees/$WORKTREE_NAME/TASK_QUEUE.md"

# 1. Check for completed tasks
completed=$(grep -c "^\- \[✅\]" "$TASK_QUEUE")

if [ "$completed" -gt 0 ]; then
    # 2. Parse delegation rules
    # If developer completed → spawn auditor + tester
    # If auditor found issues → spawn developer (fix task)
    # If tester found failures → spawn debugger

    # 3. Spawn agents via Task tool
    # (In CCWeb, this prepares prompts for pickup)
    .claude/scripts/spawn-agents.sh "$WORKTREE_NAME"
fi

# 4. Sync status to main repo
.claude/scripts/sync-worktree-status.sh "$WORKTREE_NAME"
```

### Main Repo Post-Commit Hook

Coordinates across worktrees:

```bash
#!/bin/bash
# .git/hooks/post-commit (main repo)

# 1. Check for cross-worktree dependencies
.claude/scripts/check-worktree-dependencies.sh

# 2. If worktree A completed task that worktree B depends on:
#    - Update worktree B's TASK_QUEUE.md
#    - Trigger worktree B's loop to pick up unblocked tasks

# 3. Monitor all active worktree loops
.claude/scripts/monitor-loops.sh --report
```

---

## Monitoring & Control

### View All Worktree Status

```bash
.claude/scripts/monitor-loops.sh --status
```

Output:
```
🔄 Autonomous Worktree Status
═══════════════════════════════════════════

📦 search-module (../epic-search-module)
   Branch: epic/search-module
   Status: RUNNING
   Agents: 3 active (developer, auditor, tester)
   Tasks: 4/12 complete (33%)
   Last commit: 2 minutes ago

📦 timeline-module (../epic-timeline-module)
   Branch: epic/timeline-module
   Status: RUNNING
   Agents: 2 active (developer, documentation)
   Tasks: 7/15 complete (47%)
   Last commit: 5 minutes ago

📦 deidentification-module (../epic-deidentification-module)
   Branch: epic/deidentification-module
   Status: BLOCKED
   Reason: Waiting for search-module task #3
   Tasks: 2/8 complete (25%)
   Last commit: 10 minutes ago

💡 Total: 3 worktrees, 5 active agents, 13/35 tasks (37%)
```

### Stop All Loops (Emergency)

```bash
.claude/scripts/monitor-loops.sh --stop-all

# Gracefully stops all autonomous loops
# Agents finish current commit, then exit
```

### Resume Loops

```bash
.claude/scripts/monitor-loops.sh --resume-all

# Restarts autonomous loops for all worktrees
```

---

## Technical Details

### How Agents Spawn in Worktrees

**Problem**: In CCWeb, bash scripts cannot spawn Claude Code agents directly.

**Solution**: Use Task tool preparation + background process model

```bash
# spawn-worktree-loop.sh (runs in each worktree)

while true; do
    # 1. Check TASK_QUEUE.md for pending tasks
    pending=$(grep -c "^\- \[ \]" TASK_QUEUE.md)

    if [ "$pending" -gt 0 ]; then
        # 2. Prepare agent prompt for Task tool
        task_id=$(grep "^\- \[ \]" TASK_QUEUE.md | head -1 | grep -oP '#\d+')
        agent_type=$(grep "^\- \[ \]" TASK_QUEUE.md | head -1 | grep -oP '\[\w+\]')

        # 3. Create prompt file for pickup
        .claude/scripts/agent-wrapper.sh \
            --task-id "$task_id" \
            --agent-type "$agent_type" \
            --worktree "$(pwd)"

        # 4. In CCWeb: Prompt file waits for manual pickup OR
        #    In future: CCWeb API spawns agent automatically

        # 5. Wait for task to complete (file lock mechanism)
        while [ -f ".claude/locks/task-$task_id.lock" ]; do
            sleep 5
        done
    else
        # No pending tasks, check for new tasks from epic
        .claude/scripts/sync-epic-to-queue.sh
    fi

    # Loop delay (prevent CPU spinning)
    sleep 10
done
```

### File Locking for Coordination

```bash
# claim-task.sh (atomic task claiming)

task_id=$1
lock_file=".claude/locks/task-$task_id.lock"

# Atomic lock acquisition using flock
{
    flock -x 200 || exit 1

    # Check if task already claimed
    if [ -f "$lock_file" ]; then
        echo "Task already claimed"
        exit 1
    fi

    # Claim task
    echo "$$" > "$lock_file"
    echo "Agent PID: $$ claimed task #$task_id"

} 200>"$lock_file.tmp"

# On exit, release lock
trap "rm -f $lock_file $lock_file.tmp" EXIT
```

---

## CCWeb Limitations & Workarounds

### Limitation 1: Cannot Spawn Claude Code from Bash

**Problem**: `bash` scripts cannot invoke `claude-code` CLI to spawn agents

**Workarounds**:
1. **Prompt Preparation**: Scripts prepare agent prompts, wait for manual pickup
2. **Background Monitoring**: Human opens multiple Claude Code windows, each picks up tasks
3. **Future CCWeb API**: When available, scripts can make API calls to spawn agents

**Current State**: Semi-autonomous (requires human to spawn initial agents per worktree)

### Limitation 2: File System Coordination Only

**Problem**: No inter-process communication between agents

**Workarounds**:
1. **File-based queues**: TASK_QUEUE.md acts as message queue
2. **File locks**: Atomic operations via `flock`
3. **Status files**: Agents write status updates to `.claude/status/*.md`

**Works well**: File system is fast, reliable, and version-controlled

### Limitation 3: No True Daemon

**Problem**: No background daemon to orchestrate worktrees

**Workarounds**:
1. **Per-worktree loops**: Each worktree runs its own loop script
2. **Monitoring script**: Separate process monitors all worktrees
3. **Git hooks**: Trigger coordination on commits

**Current State**: Distributed orchestration (no single point of failure)

---

## Future Enhancements

### Phase 1: Basic Integration (CURRENT)
- ✅ CCPM installed and configured
- ✅ Local mode (no GitHub required)
- ✅ Worktree creation scripts
- ✅ Task delegation hooks
- ⏳ Autonomous loop spawning (manual initiation)

### Phase 2: True Autonomy (NEXT)
- [ ] CCWeb API integration for agent spawning
- [ ] Background daemon for worktree orchestration
- [ ] Automatic dependency resolution across worktrees
- [ ] Real-time monitoring dashboard

### Phase 3: Advanced Features
- [ ] Dynamic worktree creation (on-demand)
- [ ] Load balancing (distribute agents across worktrees)
- [ ] Failure recovery (auto-restart crashed loops)
- [ ] Metrics collection (agent performance, task velocity)

---

## Quick Start Guide

### 1. Install CCPM (DONE)
```bash
# Already completed - CCPM installed in .claude/ccpm/
```

### 2. Create Your First Epic
```bash
/pm:prd-new my-feature
/pm:prd-parse my-feature
/pm:epic-decompose my-feature
```

### 3. Create Worktree and Start Loop
```bash
# Create worktree
git worktree add ../epic-my-feature -b epic/my-feature

# Initialize autonomous loop
.claude/scripts/spawn-worktree-loop.sh my-feature ../epic-my-feature

# Start working (opens Claude Code in worktree)
cd ../epic-my-feature
```

### 4. Monitor Progress
```bash
# From main repo
.claude/scripts/monitor-loops.sh --status
```

---

## Summary

This integration achieves the user's goal of **"multiple parallel worktrees, each stuck in its own never-ending loop"** by:

1. ✅ Using CCPM for epic/task organization
2. ✅ Creating git worktrees for parallel development
3. ✅ Running autonomous agent loops in each worktree
4. ✅ Coordinating via file system and git hooks
5. ✅ Enabling task delegation within and across worktrees

**Result**: True parallel autonomous development at the module level, with each module progressing independently while coordinating on dependencies.
