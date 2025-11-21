# Agent Coordination & Messages

**Last Updated**: 2025-11-21T00:00:00Z
**Unread Messages**: 0

---

## 📬 Messages for architecture-designer

<!-- Messages from other agents directed to architecture-designer -->

---

## 📬 Messages for task-definer

<!-- Messages from other agents directed to task-definer -->

---

## 📬 Messages for developer

<!-- Messages from other agents directed to developer -->

---

## 📬 Messages for test-generator

<!-- Messages from other agents directed to test-generator -->

---

## 📬 Messages for auditor

<!-- Messages from other agents directed to auditor -->

---

## 📬 Messages for tester

<!-- Messages from other agents directed to tester -->

---

## 📬 Messages for debugger

<!-- Messages from other agents directed to debugger -->

---

## 📬 Messages for documentation

<!-- Messages from other agents directed to documentation -->

---

## 🗑️ Archived Messages (Last 50)

<!-- Messages that have been read and acknowledged -->
<!-- Moved here automatically after 24 hours or when explicitly archived -->

---

## 📝 Message Format

When adding a message for another agent:

```markdown
### From sender-agent [HH:MM:SS] SEVERITY
**Re: Task #ID (Task Name)**
- 🔴/⚠️/✅ **Message Type**: Description
- **Action Required**: What the recipient should do
- **File**: Specific file reference (if applicable)
- **Severity**: Critical / High / Medium / Low
- **Created Task**: #NewID (if you created a follow-up task)
- **Additional Context**: Any other relevant information
```

## 🎨 Severity Indicators

- 🔴 **CRITICAL**: Blocking issue, immediate action required
- ⚠️ **WARNING**: Issue found, should be addressed soon
- ✅ **SUCCESS**: Informational, no action needed
- 💡 **INFO**: General information or suggestion

## 🔄 Message Lifecycle

1. **Created**: Agent adds message to recipient's section
2. **Read**: Recipient reads message (should acknowledge in commit message)
3. **Actioned**: Recipient addresses the message (creates task, fixes issue, etc.)
4. **Archived**: After 24h or when recipient explicitly archives

## 📋 Best Practices

- **Be specific**: Include file paths, line numbers, exact errors
- **Be actionable**: Tell recipient exactly what to do
- **Link tasks**: Reference task IDs for follow-up work
- **Use severity**: Help prioritize what needs attention first
- **Include context**: Explain why this message matters

## 🤝 Collaboration Examples

### Example 1: Auditor → Developer (Compliance Issue)

```markdown
### From auditor [14:25:00] 🔴 CRITICAL
**Re: Task #10 (Filter UI Implementation)**
- 🔴 **BLOCKING**: PHI exposed in application logs
- **File**: backend/app/services/patient_search_service.py:45
- **Line**: `logger.info(f"Searching for patient {patient_name}")`
- **Fix**: Remove patient_name from log, use patient_id only
- **Compliance**: HIPAA violation - must fix before merge
- **Created Task**: #14 (P0 - Fix PHI exposure)
- **Severity**: Critical
```

### Example 2: Tester → Debugger (Test Failure)

```markdown
### From tester [14:15:00] ⚠️ WARNING
**Re: Task #12 (Run Test Suite)**
- ⚠️ **Test Failures**: 3 integration tests failing
- **Files**:
  - tests/integration/test_patient_search.py:45
  - tests/integration/test_patient_search.py:67
  - tests/integration/test_patient_search.py:89
- **Error**: AssertionError: Expected 5 results, got 0
- **Suspected Cause**: Meta-annotation filtering logic incorrect
- **Created Task**: #15 (P1 - Fix integration test failures)
- **Severity**: High
```

### Example 3: Developer → Auditor (Ready for Review)

```markdown
### From developer [14:20:00] ✅ SUCCESS
**Re: Task #10 (Filter UI Implementation)**
- ✅ **Implementation Complete**: Filter UI ready for review
- **Files Changed**:
  - frontend/src/components/FilterPanel.vue
  - frontend/src/composables/useFilterState.ts
  - frontend/tests/components/FilterPanel.spec.ts
- **Tests**: 8 new component tests (all passing)
- **Coverage**: +2% (now 86.5%)
- **Request**: Please review for HIPAA/GDPR compliance
- **Created Task**: #11 (P1 - Audit Filter UI compliance)
- **Severity**: Medium (normal review process)
```

## 🔍 Reading Your Messages

Before starting work, agents should:
1. Read COORDINATION.md completely
2. Check for messages in their section
3. Read and understand any critical/warning messages
4. Create tasks or take actions as requested
5. Archive or acknowledge messages in commit

## 📤 Sending Messages

When completing a task, agents should:
1. Add messages for any agents who need to follow up
2. Include all relevant context
3. Create tasks in TASK_QUEUE.md for follow-up work
4. Reference task IDs in messages
5. Use appropriate severity indicators
