# 🚀 START CCPM: Sprint 2 - Timeline View Module

**Status**: Ready to Launch
**Target**: Parallel 3-agent autonomous execution
**Expected Duration**: 48 hours (vs 144 hours sequential)
**Speedup**: 3x

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Set Up Git Worktrees for Parallel Execution

```bash
# Navigate to project root
cd C:\Users\paurs\OneDrive\Desktop\cogstack-nlp

# Create worktrees for parallel agent execution
git worktree add ../cogstack-timeline-backend ccpm-consolidated
git worktree add ../cogstack-timeline-frontend ccpm-consolidated
git worktree add ../cogstack-timeline-integration ccpm-consolidated

# Verify worktrees created
git worktree list
```

**Expected Output**:
```
C:/Users/paurs/OneDrive/Desktop/cogstack-nlp                     d5eaab11 [ccpm-consolidated]
C:/Users/paurs/OneDrive/Desktop/cogstack-timeline-backend        d5eaab11 [ccpm-consolidated]
C:/Users/paurs/OneDrive/Desktop/cogstack-timeline-frontend       d5eaab11 [ccpm-consolidated]
C:/Users/paurs/OneDrive/Desktop/cogstack-timeline-integration    d5eaab11 [ccpm-consolidated]
```

---

### Step 2: Update Progress Tracking

```bash
# Update progress.json to track Sprint 2
cat > .claude/autonomous/progress.json << 'EOF'
{
  "sprint": "sprint-2-timeline-view",
  "started_at": "2025-11-24T04:45:00Z",
  "status": "in_progress",
  "current_phase": "phase-1-core-api",
  "missions_completed": 0,
  "missions_total": 8,
  "agents_active": {
    "developer-1": "ready",
    "developer-2": "ready",
    "developer-3": "ready"
  },
  "blockers": []
}
EOF
```

---

### Step 3: Activate Mission Queue

```bash
# Link Sprint 2 mission queue as active
cp .claude/autonomous/mission-queue-sprint-2.yaml .claude/autonomous/mission-queue-active.yaml

# Verify mission queue
head -20 .claude/autonomous/mission-queue-active.yaml
```

---

### Step 4: Start Autonomous Agents

Now you have **3 options** for running agents:

#### **Option A: Manual Sequential Execution** (You Control)

Start Claude Code sessions in each worktree and work through missions manually:

```bash
# Terminal 1: Backend Agent (developer-1)
cd ../cogstack-timeline-backend
# Open Claude Code and say: "Execute mission sprint-2-task-1.1 from mission-queue-active.yaml"

# Terminal 2: Frontend Agent (developer-2)
cd ../cogstack-timeline-frontend
# Open Claude Code and say: "Execute mission sprint-2-task-2.1 from mission-queue-active.yaml"

# Terminal 3: Integration Agent (developer-3)
cd ../cogstack-timeline-integration
# Open Claude Code and say: "Monitor missions and prepare integration tests"
```

**Benefits**:
- Full control over each step
- Can pause/resume anytime
- See agent output in real-time
- Best for learning CCPM

---

#### **Option B: Semi-Autonomous with Orchestrator** (Recommended)

Use the orchestrator.py to coordinate agents:

```bash
# Install dependencies
pip install pyyaml anthropic

# Run orchestrator
python .claude/agents/orchestrator.py \
  --mission-queue .claude/autonomous/mission-queue-active.yaml \
  --max-parallel 3 \
  --mode interactive

# Orchestrator will:
# 1. Read mission queue
# 2. Assign missions to agents
# 3. Create agent sessions in worktrees
# 4. Monitor progress
# 5. Handle coordination (after_complete notifications)
# 6. Prompt you for approval at checkpoints
```

**Benefits**:
- Agents work in parallel automatically
- Orchestrator handles coordination
- You approve major decisions
- Faster than manual but controlled

---

#### **Option C: Fully Autonomous (Advanced)**

Let agents run completely autonomously with minimal intervention:

```bash
# Run orchestrator in autonomous mode
python .claude/agents/orchestrator.py \
  --mission-queue .claude/autonomous/mission-queue-active.yaml \
  --max-parallel 3 \
  --mode autonomous \
  --auto-merge

# Orchestrator will:
# 1. Execute all missions autonomously
# 2. Merge successful completions automatically
# 3. Only stop for blockers or test failures
# 4. Generate progress reports every hour
```

**Benefits**:
- Maximum speed (true 3x parallelism)
- Minimal human intervention
- Agents handle everything

**Risks**:
- Less control
- Need to monitor for issues
- Best after testing Option B first

---

## 📊 Monitor Progress

### Real-Time Monitoring

```bash
# Watch progress (updates every 30 seconds)
watch -n 30 cat .claude/autonomous/progress.json

# Check agent status
cat .claude/AGENT_STATUS.md

# View task queue
cat .claude/TASK_QUEUE.md

# Check for blockers
ls .claude/autonomous/blockers/
```

### View Completed Missions

```bash
# List completed missions
grep -l "status: completed" .claude/autonomous/mission-queue-active.yaml

# View completion reports
ls .claude/autonomous/reports/
```

---

## 🎯 Mission Execution Flow

### Mission 1.1: Timeline Pydantic Schemas (developer-1)
**Duration**: 2 hours
**Worktree**: `../cogstack-timeline-backend`

**Agent Instructions** (if running manually):
```
Execute Mission: sprint-2-task-1.1

Read: .claude/autonomous/mission-queue-active.yaml (mission sprint-2-task-1.1)
Follow: RIPER cycle (Research → Innovate → Plan → Execute → Review)
Output: backend/app/schemas/timeline.py + tests
Success: 12 tests passing, ≥90% coverage
```

---

### Mission 2.1: Frontend Timeline Component (developer-2) - RUNS IN PARALLEL!
**Duration**: 3 hours
**Worktree**: `../cogstack-timeline-frontend`

**Agent Instructions** (if running manually):
```
Execute Mission: sprint-2-task-2.1

Read: .claude/autonomous/mission-queue-active.yaml (mission sprint-2-task-2.1)
Dependency: Wait for sprint-2-task-1.1 (schemas) to complete
Follow: RIPER cycle
Output: frontend/src/components/Timeline/TimelineView.vue + tests
Success: Components render, tests passing, ≥85% coverage
```

---

## 🔒 Safety Mechanisms

### Auditor Agent Validation

The auditor agent automatically reviews every commit for:
- ✅ HIPAA compliance (PHI handling, audit logging)
- ✅ GDPR compliance (data minimization, consent)
- ✅ Test coverage (≥85%)
- ✅ Code quality (no hardcoded secrets, SQL injection prevention)

**Auditor blocks merges** if violations detected!

### File Locking

Agents use file locks to prevent write conflicts:
```
backend/app/schemas/timeline.py.lock (developer-1 writing)
frontend/src/components/Timeline.vue.lock (developer-2 writing)
```

---

## 🚨 Handling Blockers

If an agent encounters a blocker:

1. **Agent creates blocker file**:
   ```bash
   .claude/autonomous/blockers/blocker-003-<description>.md
   ```

2. **Agent updates mission status**:
   ```yaml
   status: blocked
   blocker_reason: "Frontend directory doesn't exist"
   ```

3. **You resolve blocker**:
   ```bash
   # Read blocker description
   cat .claude/autonomous/blockers/blocker-003-*.md

   # Resolve (e.g., create directory)
   mkdir -p frontend/src/components/Timeline

   # Mark blocker resolved
   mv .claude/autonomous/blockers/blocker-003-*.md \
      .claude/autonomous/blockers/resolved/
   ```

4. **Agent resumes**:
   Mission status changes back to `ready`

---

## 📈 Expected Results

### After 10 Hours (Phase 1 Complete):
- ✅ Timeline API implemented (backend)
- ✅ Timeline UI started (frontend)
- ✅ 20+ tests passing
- ✅ ≥85% test coverage

### After 20 Hours (Phase 2 Complete):
- ✅ Timeline UI complete
- ✅ D3.js visualization working
- ✅ Frontend tests passing
- ✅ Ready for integration

### After 48 Hours (Sprint 2 Complete):
- ✅ Full timeline feature working end-to-end
- ✅ Integration tests passing
- ✅ Performance: Timeline loads <500ms
- ✅ All acceptance criteria met
- ✅ Ready for production deployment

---

## 🎓 Learning Mode

If this is your first time with CCPM autonomous execution:

### Day 1: Learn with Option A (Manual)
- Work through Mission 1.1 manually with Claude Code
- Understand RIPER cycle
- See TDD in action
- Learn mission structure

### Day 2: Scale with Option B (Semi-Autonomous)
- Let orchestrator handle coordination
- See parallel execution in action
- Approve major decisions
- Monitor progress

### Week 2: Automate with Option C (Fully Autonomous)
- Let agents handle entire sprints
- Focus on reviewing completed work
- Handle blockers only
- Maximum productivity

---

## 📚 Reference Documentation

- **Mission Queue**: `.claude/autonomous/mission-queue-sprint-2.yaml`
- **CCPM Config**: `.ccpm/ccpm.yaml`
- **Agent Definitions**: `.claude/agents/`
- **Sprint 2 Tasks**: `.specify/tasks/sprint-2-timeline-view-tasks.md`
- **Sprint 2 Plan**: `.specify/plans/sprint-2-timeline-view-plan.md`
- **Sprint 2 Spec**: `.specify/specifications/sprint-2-timeline-view.md`

---

## 🚀 Ready to Start?

### Recommended: Start with Option A (Manual Sequential)

```bash
# 1. Set up worktrees
git worktree add ../cogstack-timeline-backend ccpm-consolidated

# 2. Navigate to backend worktree
cd ../cogstack-timeline-backend

# 3. Start Claude Code session (in terminal)
# Then say: "Execute mission sprint-2-task-1.1 from .claude/autonomous/mission-queue-sprint-2.yaml"

# 4. Claude Code will:
#    - Read the mission
#    - Follow RIPER cycle
#    - Implement Task 1.1 (Timeline Schemas)
#    - Write tests
#    - Verify success criteria
#    - Update progress.json
```

### Or: Jump to Option B (Semi-Autonomous Orchestrator)

```bash
# Coming soon: orchestrator.py will coordinate everything automatically
# For now, use Option A and manually coordinate
```

---

**Next Steps**:
1. Choose your option (A, B, or C)
2. Follow the instructions above
3. Watch the agents work!
4. Review completed missions
5. Merge successful work

🎉 **Welcome to CCPM Autonomous Development!**
