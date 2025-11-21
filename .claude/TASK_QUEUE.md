# Autonomous Development Task Queue

**Last Updated**: 2025-11-21T00:00:00Z
**Active Agents**: 0
**Pending Tasks**: 0
**Completed Tasks**: 0
**Failed Tasks**: 0

---

## 🔴 High Priority (P0 - Critical)

<!-- Blocker issues, HIPAA violations, security problems -->
<!-- Format: - [ ] #ID `[agent-type]` Task description **@creator** (created: HH:MM:SS) -->

---

## 🟡 Normal Priority (P1 - Important)

<!-- Features, bug fixes, improvements -->

---

## 🟢 Low Priority (P2 - Nice to Have)

<!-- Documentation, refactoring, optimization -->

---

## ✅ Completed (Last 20)

<!-- Tasks marked as complete - sorted by completion time (newest first) -->

---

## ❌ Failed / Blocked (Retry Count)

<!-- Tasks that failed or are blocked - requires user review -->

---

## 📋 Task Format

```markdown
- [ ] #ID `[agent-type]` Task description **@creator** (created: HH:MM:SS)
  - **Context**: Why this task exists
  - **Files**: List of files to modify
  - **Depends**: Task IDs this depends on (if any)
  - **Acceptance**: How to verify completion
```

## 📊 Task States

- `[ ]` - Pending (unclaimed)
- `[🔄]` - In Progress (claimed by agent, PID in description)
- `[✅]` - Completed (finished successfully)
- `[❌]` - Failed (exceeded retries or escalated)
- `[⏸️]` - Blocked (waiting on dependency or user decision)

## 🔢 Task ID Assignment

Task IDs are auto-incremented integers starting from 1. Next available ID: **1**

To add a task manually:
```bash
bash .claude/scripts/add-task.sh "agent-type" "Task description" "P1"
```

## 📝 Notes

- Tasks are claimed atomically using file locks to prevent race conditions
- post-commit hook spawns agents for unclaimed tasks (up to 6 concurrent)
- Agents update this file when completing or failing tasks
- See AGENT_STATUS.md for real-time agent status
- See COORDINATION.md for agent messages
