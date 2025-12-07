# Agent Status Dashboard

**Total Agents**: 8
**Active**: 0
**Idle**: 8
**Waiting**: 0
**Failed**: 0
**Last Check**: 2025-11-21T00:00:00Z

---

## 🟢 Active Agents

<!-- Agents currently working on tasks -->
<!-- Auto-populated by agents during execution -->

---

## 🔵 Idle Agents (Available for Work)

### architecture-designer
- **Status**: IDLE
- **Last Completed**: None
- **Pending Assignments**: None
- **Last Heartbeat**: N/A
- **Total Tasks Completed**: 0
- **Success Rate**: N/A

### task-definer
- **Status**: IDLE
- **Last Completed**: None
- **Pending Assignments**: None
- **Last Heartbeat**: N/A
- **Total Tasks Completed**: 0
- **Success Rate**: N/A

### developer
- **Status**: IDLE
- **Last Completed**: None
- **Pending Assignments**: None
- **Last Heartbeat**: N/A
- **Total Tasks Completed**: 0
- **Success Rate**: N/A

### test-generator
- **Status**: IDLE
- **Last Completed**: None
- **Pending Assignments**: None
- **Last Heartbeat**: N/A
- **Total Tasks Completed**: 0
- **Success Rate**: N/A

### auditor
- **Status**: IDLE
- **Last Completed**: None
- **Pending Assignments**: None
- **Last Heartbeat**: N/A
- **Total Tasks Completed**: 0
- **Success Rate**: N/A

### tester
- **Status**: IDLE
- **Last Completed**: None
- **Pending Assignments**: None
- **Last Heartbeat**: N/A
- **Total Tasks Completed**: 0
- **Success Rate**: N/A

### debugger
- **Status**: IDLE
- **Last Completed**: None
- **Pending Assignments**: None
- **Last Heartbeat**: N/A
- **Total Tasks Completed**: 0
- **Success Rate**: N/A

### documentation
- **Status**: IDLE
- **Last Completed**: None
- **Pending Assignments**: None
- **Last Heartbeat**: N/A
- **Total Tasks Completed**: 0
- **Success Rate**: N/A

---

## ⏸️ Waiting / Blocked Agents

<!-- Agents waiting for dependencies or blocked -->

---

## 🔴 Failed / Crashed Agents

<!-- Agents that crashed or exceeded timeout -->

---

## 🔴 Critical Alerts

<!-- Auto-generated alerts for attention-needed situations -->

---

## 📊 Agent Metrics (Last 24h)

| Agent | Tasks Completed | Avg Duration | Success Rate | Errors | Timeouts |
|-------|-----------------|--------------|--------------|--------|----------|
| architecture-designer | 0 | N/A | N/A | 0 | 0 |
| task-definer | 0 | N/A | N/A | 0 | 0 |
| developer | 0 | N/A | N/A | 0 | 0 |
| test-generator | 0 | N/A | N/A | 0 | 0 |
| auditor | 0 | N/A | N/A | 0 | 0 |
| tester | 0 | N/A | N/A | 0 | 0 |
| debugger | 0 | N/A | N/A | 0 | 0 |
| documentation | 0 | N/A | N/A | 0 | 0 |

---

## 📝 Status Update Format

When claiming a task, agents should update their section:

```markdown
### agent-name [PID: 12345]
- **Status**: WORKING (Task #10)
- **Started**: HH:MM:SS
- **Progress**: 20% (reading specification)
- **Last Heartbeat**: HH:MM:SS (30s ago)
- **Next Action**: Write tests for component
- **ETA**: HH:MM:SS
```

When completing a task:

```markdown
### agent-name
- **Status**: IDLE
- **Last Completed**: Task #10 (Filter UI implementation, 45m, ✅)
- **Last Heartbeat**: HH:MM:SS
- **Total Tasks Completed**: 1
- **Success Rate**: 100%
```

## 🔔 Heartbeat Monitoring

Agents should update their "Last Heartbeat" field every 30 seconds during execution. If heartbeat not updated for >2 minutes, agent is considered crashed/frozen.

## 🎯 Claiming Tasks

To claim a task from TASK_QUEUE.md:
1. Use flock to acquire lock on TASK_QUEUE.md
2. Find first unclaimed task for your agent type
3. Atomically update task status to [🔄]
4. Release lock
5. Update your status in this file to WORKING
