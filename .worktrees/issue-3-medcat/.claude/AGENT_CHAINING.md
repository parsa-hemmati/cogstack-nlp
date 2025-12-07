# Agent Chaining & Autonomous Loop System

**Version**: 1.0.0
**Status**: ✅ Implemented
**Purpose**: Documentation for the unstoppable autonomous agent workflow

---

## 🎯 Overview

This system creates **continuous autonomous development loops** where agents automatically spawn each other based on completion events, creating an unstoppable workflow that continues until all tasks are complete.

### Key Features

1. **Pre-Commit Hooks**: Spawn minimum 4 agents before every commit (validation)
2. **Post-Commit Hooks**: Spawn 3 agents after every commit (validation + continuation)
3. **Orchestrator Agent**: Meta-agent that coordinates all other agents
4. **Agent Chaining**: Agents automatically spawn dependent agents
5. **Wave-Based Execution**: Parallel tasks → validation → fixes → next wave
6. **Safety Limits**: Prevents infinite loops and runaway processes

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Commit Workflow                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  git commit                                                  │
│       ↓                                                      │
│  ┌────────────────────────────────────────────┐            │
│  │  Pre-Commit Hook (BLOCKING)                 │            │
│  │  - Spawn 2 developer agents (parallel)      │            │
│  │  - Spawn 1 documentation agent              │            │
│  │  - Spawn 1 orchestrator agent               │            │
│  │  ✓ All must approve to proceed              │            │
│  └────────────────────────────────────────────┘            │
│       ↓                                                      │
│  Commit succeeds                                            │
│       ↓                                                      │
│  ┌────────────────────────────────────────────┐            │
│  │  Post-Commit Hook (NON-BLOCKING)            │            │
│  │  - Spawn 1 auditor agent (background)       │            │
│  │  - Spawn 1 tester agent (background)        │            │
│  │  - Spawn 1 orchestrator agent (background)  │            │
│  │  → Updates AUDIT.md, TESTING.md             │            │
│  └────────────────────────────────────────────┘            │
│       ↓                                                      │
│  Orchestrator reads task queues                             │
│       ↓                                                      │
│  Spawns next wave of agents (3-6 parallel)                  │
│       ↓                                                      │
│  Loop continues...                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Agent Types & Capabilities

| Agent Type | Description | Tools | Can Spawn | Blocking? |
|------------|-------------|-------|-----------|-----------|
| **developer** | Implements features | Read, Write, Edit, Bash, Grep, Glob | tester, documentation, debugger | ❌ No |
| **tester** | Runs tests, validates quality | Read, Bash, Grep, Glob, Write | debugger, documentation | ✅ Yes (blocks deploy) |
| **auditor** | HIPAA/GDPR compliance checker | Read, Grep, Glob | developer, debugger | ✅ Yes (blocks commit) |
| **debugger** | Fixes bugs and errors | Read, Write, Edit, Bash, Grep, Glob | tester | ❌ No |
| **documentation** | Creates/updates docs | Read, Write, Grep, Glob | - | ❌ No |
| **architecture-designer** | Designs technical architecture | Read, Grep, Glob, Write | developer, task-definer | ❌ No |
| **task-definer** | Breaks down epics into tasks | Read, Grep, Glob, Write | developer | ❌ No |
| **orchestrator** | Meta-agent coordinator | Read, Grep, Glob, Task | All agents | ❌ No |

---

## 🔄 Agent Chaining Rules

These rules define **automatic agent spawning** based on completion events:

### Rule 1: Developer Completes → Spawn Tester + Documentation

```yaml
developer_completes:
  spawn: [tester, documentation]
  reason: "New code needs tests and documentation"
```

**Example**:
```
Developer Agent completes Task #004 (Batch API)
  → Automatically spawns:
     - Tester Agent (run integration tests)
     - Documentation Agent (update API docs)
```

### Rule 2: Tester Finds Failures → Spawn Debugger

```yaml
tester_finds_failures:
  spawn: [debugger]
  reason: "Tests failed, need debugging"
```

**Example**:
```
Tester Agent finds 3 failing integration tests
  → Automatically spawns:
     - Debugger Agent (fix failing tests)
```

### Rule 3: Debugger Fixes Code → Re-run Tester

```yaml
debugger_fixes_code:
  spawn: [tester]
  reason: "Re-run tests after fixes"
```

**Example**:
```
Debugger Agent fixes 3 integration tests
  → Automatically spawns:
     - Tester Agent (re-run full suite)
```

### Rule 4: Auditor Finds Issues → Spawn Developer + Debugger (BLOCKING)

```yaml
auditor_finds_issues:
  spawn: [developer, debugger]
  reason: "Compliance issues need fixing"
  blocking: true
```

**Example**:
```
Auditor Agent finds PHI in application logs (HIPAA violation)
  → BLOCKS commit
  → Automatically spawns:
     - Developer Agent (remove PHI from logs)
     - Debugger Agent (verify fix works)
```

### Rule 5: All Tests Pass → Spawn Orchestrator

```yaml
all_tests_pass:
  spawn: [orchestrator]
  reason: "Ready for next task wave"
```

**Example**:
```
Tester Agent reports 100% tests passing
  → Automatically spawns:
     - Orchestrator Agent (read task queues, spawn next wave)
```

---

## 🌊 Wave-Based Execution Strategy

The orchestrator uses a **4-phase wave strategy** for continuous execution:

### Phase 1: Parallel Tasks

```yaml
phase: "parallel_tasks"
description: "Spawn all tasks that can run in parallel"
agents: ["developer", "developer", "developer"]
wait_for_completion: true
```

**What happens**:
- Orchestrator reads task queues from all 3 modules
- Identifies tasks with no blocking dependencies
- Spawns up to 3 developer agents in parallel
- Waits for all to complete before moving to next phase

**Example**:
```
Ready tasks: Timeline #001, Timeline #002, Search #019
  → Spawn 3 developer agents simultaneously
  → All work in parallel git worktrees
  → Wait for completion
```

### Phase 2: Validation

```yaml
phase: "validation"
description: "Validate completed work"
agents: ["auditor", "tester"]
wait_for_completion: true
```

**What happens**:
- Spawns auditor agent (HIPAA/GDPR compliance check)
- Spawns tester agent (run full test suite)
- Both run in parallel
- Waits for both to complete

**Example**:
```
Phase 1 complete (3 tasks implemented)
  → Spawn auditor agent (checks Timeline #001, #002, Search #019)
  → Spawn tester agent (runs all tests)
  → Wait for validation results
```

### Phase 3: Fix Issues (Conditional)

```yaml
phase: "fix_issues"
description: "Fix any issues found by validation"
condition: "Issues detected by auditor or tester"
agents: ["debugger"]
wait_for_completion: true
```

**What happens**:
- Only runs if Phase 2 found issues
- Spawns debugger agent to fix issues
- Waits for fixes to complete
- Loops back to Phase 2 (re-validation)

**Example**:
```
Auditor found 2 warnings, Tester found 3 failing tests
  → Spawn debugger agent
  → Debugger fixes all issues
  → Loop back to Phase 2 (re-validate)
```

### Phase 4: Next Wave

```yaml
phase: "next_wave"
description: "Spawn next wave of agents"
agents: ["orchestrator"]
wait_for_completion: false  # Non-blocking, continues loop
```

**What happens**:
- Spawns orchestrator agent recursively
- Orchestrator reads updated task queues
- Identifies newly ready tasks (dependencies now met)
- Loops back to Phase 1 with new tasks

**Example**:
```
All validation passed
  → Spawn orchestrator agent
  → Orchestrator finds Timeline #003 now ready (depends on #001, #002)
  → Loop back to Phase 1 with new task
```

---

## 🛡️ Safety Limits

Prevents runaway loops and infinite processes:

```yaml
safety:
  max_consecutive_failures: 5  # Stop if 5 agents fail in a row
  max_loop_iterations: 100      # Safety limit for infinite loop
  agent_timeout_minutes: 30     # Kill agent if runs longer than 30m
  commit_rate_limit: 50         # Max commits per hour
```

### Termination Conditions

The loop stops when ANY of these conditions are met:

1. **All tasks complete**: All 21 tasks across 3 modules are done
2. **No pending tasks**: No tasks ready to start
3. **Loop timeout**: 100 iterations exceeded
4. **User manually stops**: User runs `./claude/agents/run-orchestrator.sh stop`

---

## 🚀 Usage

### Starting the Orchestrator

```bash
# Start orchestrator in background
./.claude/agents/run-orchestrator.sh start

# Check status
./.claude/agents/run-orchestrator.sh status

# View logs
./.claude/agents/run-orchestrator.sh logs

# Stop orchestrator
./.claude/agents/run-orchestrator.sh stop
```

### Automatic Triggering via Git Hooks

The orchestrator is **automatically triggered** by:

1. **Every commit**: Post-commit hook spawns orchestrator
2. **After validation**: Orchestrator spawns itself recursively
3. **After fixes**: Debugger completion triggers re-validation

**You don't need to manually start the orchestrator** - it's automatically activated by git hooks!

### Manual Triggering

For testing or debugging:

```bash
# Run orchestrator once (not continuous)
python3 .claude/agents/orchestrator.py

# Run with custom config
python3 .claude/agents/orchestrator.py --config .claude/agent-coordination-test.yaml
```

---

## 📊 Monitoring

### Real-Time Status

The orchestrator updates 3 shared documents:

1. **CONTEXT.md**: Technical changes and agent communication
2. **AUDIT.md**: Compliance status and findings
3. **TESTING.md**: Test results and coverage

**Check orchestrator status**:

```bash
# View CONTEXT.md for latest orchestrator update
tail -n 50 CONTEXT.md | grep -A 20 "Orchestrator Agent"

# Check logs
tail -f .claude/logs/orchestrator/*.log
```

### Session Summaries

After each session, the orchestrator saves a summary:

```bash
cat .claude/logs/orchestrator/session-20251121_183000-summary.json
```

Example:
```json
{
  "session_id": "20251121_183000",
  "iterations": 15,
  "completed_tasks": 12,
  "modules": {
    "de-identification-module": {
      "completed": 6,
      "total": 8,
      "progress": 75.0
    },
    "timeline-module": {
      "completed": 4,
      "total": 8,
      "progress": 50.0
    },
    "search-module": {
      "completed": 2,
      "total": 5,
      "progress": 40.0
    }
  }
}
```

---

## 🔧 Configuration

### Main Configuration File

**Location**: `.claude/agent-coordination.yaml`

**Key Sections**:

```yaml
# Agent types and their capabilities
agent_types:
  developer:
    description: "Implements features, writes code"
    tools: [Read, Write, Edit, Bash, Grep, Glob]
    can_spawn: [tester, documentation, debugger]

# Pre-commit hook (BLOCKING)
pre_commit:
  required_agents:
    - type: developer
      count: 2  # Spawn 2 in parallel
    - type: documentation
      count: 1
    - type: orchestrator
      count: 1

# Post-commit hook (NON-BLOCKING)
post_commit:
  required_agents:
    - type: auditor
      count: 1
    - type: tester
      count: 1
    - type: orchestrator
      count: 1

# Continuous loop strategy
continuous_loop:
  enabled: true
  wave_strategy:
    - phase: "parallel_tasks"
      agents: ["developer", "developer", "developer"]
    - phase: "validation"
      agents: ["auditor", "tester"]
    - phase: "fix_issues"
      condition: "Issues detected"
      agents: ["debugger"]
    - phase: "next_wave"
      agents: ["orchestrator"]

# Agent chaining rules
chaining_rules:
  developer_completes:
    spawn: [tester, documentation]
  tester_finds_failures:
    spawn: [debugger]
  debugger_fixes_code:
    spawn: [tester]
  auditor_finds_issues:
    spawn: [developer, debugger]
    blocking: true
  all_tests_pass:
    spawn: [orchestrator]
```

### Module-Specific Configuration

```yaml
modules:
  de-identification-module:
    priority: P0
    task_count: 8
    completed: 6
    worktree: "../epic-deidentification-module"

  search-module:
    priority: P0
    task_count: 5
    completed: 4
    worktree: "../epic-search-module"

  timeline-module:
    priority: P1
    task_count: 8
    completed: 2
    worktree: "../epic-timeline-module"
```

---

## 🧪 Testing

### Test the Pre-Commit Hook

```bash
# Make a small change
echo "# Test" >> README.md

# Update CONTEXT.md (required)
echo "Test change" >> CONTEXT.md

# Update AUDIT.md (required)
echo "Test audit" >> AUDIT.md

# Commit (triggers pre-commit hook)
git add .
git commit -m "test: verify pre-commit hook"

# Expected output:
# 🔀 Pre-Commit Hook: Spawning Required Agents
# → Spawning Developer Agent #1
# → Spawning Developer Agent #2
# → Spawning Documentation Agent
# → Spawning Orchestrator Agent
# ⏳ Waiting for agents to complete...
# ✅ All agents approve - commit proceeding
```

### Test the Post-Commit Hook

```bash
# After commit succeeds:
# ✓ Post-commit agents spawned in background
# Logs: .claude/logs/post-commit

# Check background agents
tail -f .claude/logs/post-commit/*.log

# Check AUDIT.md updated
tail -n 20 AUDIT.md

# Check TESTING.md updated
tail -n 20 TESTING.md
```

### Test the Orchestrator

```bash
# Start orchestrator manually
./.claude/agents/run-orchestrator.sh start

# Check status
./.claude/agents/run-orchestrator.sh status

# View logs in real-time
./.claude/agents/run-orchestrator.sh logs

# Expected output:
# 🚀 Orchestrator Agent Starting
# Session ID: 20251121_183000
# 📋 Loading modules and task queues...
#    Modules: 3
#    Total tasks: 21
#    Completed: 12
#
# 🔄 Iteration 1
# 📊 Status:
#    Ready tasks: 3
#    Running agents: 0
#    Completed: 12
#
# 📋 Phase: parallel_tasks
#    Agents: developer, developer, developer
#    → Spawned developer agent for de-identification-module:007
#    → Spawned developer agent for timeline-module:003
#    → Spawned developer agent for timeline-module:004
#    ✓ Spawned 3 agents
```

### Test Agent Chaining

1. **Trigger developer completion**:
   - Complete a task and commit
   - Verify tester + documentation agents spawned

2. **Trigger tester failure**:
   - Introduce a failing test
   - Commit and verify debugger agent spawned

3. **Trigger auditor blocking**:
   - Add PHI to application logs
   - Commit and verify it's BLOCKED
   - Verify developer + debugger agents spawned

---

## 🐛 Troubleshooting

### Orchestrator Not Spawning Agents

**Check logs**:
```bash
cat .claude/logs/orchestrator/*.log | grep "ERROR"
```

**Common issues**:
1. Task dependencies not met → Wait for dependent tasks to complete
2. Max parallel agents reached → Wait for running agents to finish
3. All tasks already completed → Loop terminated successfully

### Pre-Commit Hook Blocking Commits

**Check hook logs**:
```bash
cat .claude/logs/pre-commit/*.log | grep "BLOCKING"
```

**Common issues**:
1. CONTEXT.md not updated → Add CONTEXT.md to commit
2. AUDIT.md not updated → Add AUDIT.md to commit
3. Python syntax errors → Fix syntax errors
4. Hardcoded secrets → Remove secrets, use environment variables

### Agents Stuck or Timeout

**Check agent status**:
```bash
ps aux | grep "python.*orchestrator"
ps aux | grep "claude.*agent"
```

**Kill stuck agents**:
```bash
# Stop orchestrator
./.claude/agents/run-orchestrator.sh stop

# Kill specific agent
kill <PID>

# Restart orchestrator
./.claude/agents/run-orchestrator.sh start
```

### Loop Running Too Long

**Check iteration count**:
```bash
grep "Iteration" .claude/logs/orchestrator/*.log | tail -n 1
```

**If > 100 iterations**: Safety limit will stop loop automatically

**Manual stop**:
```bash
./.claude/agents/run-orchestrator.sh stop
```

---

## 📈 Performance Metrics

### Current Status (2025-11-21)

- **Total tasks**: 21
- **Completed**: 12 (57%)
- **Modules**:
  - De-identification: 6/8 (75%)
  - Timeline: 2/8 (25%)
  - Search: 4/5 (80%)

### Expected Throughput

- **Parallel agents**: 3-6 agents running simultaneously
- **Average task time**: 1-2 hours per task
- **Total time estimate**: ~40 hours total (with parallelization)
- **Calendar time**: ~2-3 weeks (with validation and fixes)

### Agent Spawn Rate

- **Pre-commit**: 4 agents per commit (2 developers, 1 documentation, 1 orchestrator)
- **Post-commit**: 3 agents per commit (1 auditor, 1 tester, 1 orchestrator)
- **Wave execution**: 3-6 agents per wave (parallel tasks)
- **Total spawns**: ~50-100 agents across entire project

---

## 🎓 Best Practices

### For Developers

1. **Always update CONTEXT.md and AUDIT.md** before committing
2. **Run validation script** before committing large changes
3. **Monitor orchestrator logs** to see agent activity
4. **Let the loop run** - don't manually intervene unless necessary

### For the Orchestrator

1. **Trust the chaining rules** - agents will spawn automatically
2. **Monitor safety limits** - loop will stop if issues detected
3. **Check logs regularly** - identify stuck agents early
4. **Review session summaries** - track overall progress

### For Auditor/Tester Agents

1. **Document all findings** in AUDIT.md and TESTING.md
2. **Use blocking sparingly** - only for critical issues
3. **Provide clear fix suggestions** - help debugger agents
4. **Update compliance scores** - track trends over time

---

## 📚 Related Documentation

- **Configuration**: `.claude/agent-coordination.yaml`
- **Pre-Commit Hook**: `.git-hooks/pre-commit-parallel-agents.sh`
- **Post-Commit Hook**: `.git-hooks/post-commit-parallel-agents.sh`
- **Orchestrator Agent**: `.claude/agents/orchestrator.py`
- **Wrapper Script**: `.claude/agents/run-orchestrator.sh`
- **CONTEXT.md**: Technical memory and agent communication
- **AUDIT.md**: Compliance status and auditor findings
- **TESTING.md**: Test results and tester findings

---

## 🆘 Support

**Questions or issues?**

1. Check this documentation first
2. Review agent logs (`.claude/logs/`)
3. Check CONTEXT.md for recent changes
4. Open a discussion issue with:
   - Session ID
   - Error messages from logs
   - Expected vs actual behavior

---

**Version**: 1.0.0
**Last Updated**: 2025-11-21
**Status**: ✅ Fully Implemented and Tested
