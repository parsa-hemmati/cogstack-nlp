# Multi-Agent Workflow - Git Hooks Integration

**Version**: 1.0.0
**Created**: 2025-11-19
**Purpose**: Document how existing git hooks integrate with the new multi-agent parallel workflow

---

## Overview

The multi-agent parallel workflow enhances the existing git hooks with:
- 3 specialized agents (Developer, Auditor, Test) working simultaneously
- Structured communication via shared documents (CONTEXT.md, AUDIT.md, TESTING.md)
- Parallel execution for faster feedback (2.5x speedup)

---

## Current Hook Architecture

### Existing Hooks (Autonomous Mode)

**`.git-hooks/pre-commit`** (BLOCKING)
- Enforces CONTEXT.md + AUDIT.md dual-file updates
- Checks AUDIT.md status for blocking issues
- Validates syntax, checks for secrets, console.log statements
- **BLOCKS** commits with API changes until PRD validation passes

**`.git-hooks/post-commit`** (NON-BLOCKING)
- Spawns auditor agent to check PRD compliance
- Updates AUDIT.md with compliance score + blocking todos
- Triggers development agent to auto-fix if blocking issues found
- Logs events to `.git-hooks/autonomous.log`

**`.git-hooks/prepare-commit-msg`** (HELPER)
- Generates commit message template with required sections
- Enforces CONTEXT.md and AUDIT.md updates documentation

### New Helper Scripts (Multi-Agent Workflow)

**`.git-hooks/spawn-agents.sh`** (HELPER)
- Generates Task tool prompts for spawning 3 agents in parallel
- Usage: `./spawn-agents.sh {pre-commit|post-commit|pre-push}`
- Outputs ready-to-paste Claude Code Task(...) calls

---

## Integration Strategy

### How They Work Together

```
┌─────────────────────────────────────────────────────────────┐
│                      GIT WORKFLOW                            │
└───────────────────┬─────────────────────────────────────────┘
                    │
         ┌──────────┼──────────┐
         │          │          │
         ▼          ▼          ▼
   PRE-COMMIT   COMMIT   POST-COMMIT
         │                     │
         │                     │
    ┌────▼─────┐          ┌────▼─────┐
    │ Existing │          │ Existing │
    │ pre-     │          │ post-    │
    │ commit   │          │ commit   │
    └────┬─────┘          └────┬─────┘
         │                     │
         │                     ▼
         │              ┌─────────────┐
         │              │   Auditor   │
         │              │   Agent     │
         │              │  (Existing) │
         │              └─────────────┘
         │                     │
         │                     ▼
         │              Updates AUDIT.md
         │
         │
    ┌────▼─────────────────────────────────┐
    │ NEW: spawn-agents.sh (Optional)      │
    │ ────────────────────────────────     │
    │ For comprehensive multi-agent check: │
    │  - Developer Agent (syntax, secrets) │
    │  - Auditor Agent (HIPAA, PRD)        │
    │  - Test Agent (tests, coverage)      │
    │                                      │
    │ Usage: Manual trigger or integrate   │
    │ into existing hooks                  │
    └──────────────────────────────────────┘
```

### Workflow Modes

#### 1. **Autonomous Mode (Default - Existing)**

**Triggered by**: Existing hooks
**Agent**: Auditor only (post-commit)
**Purpose**: Fast PRD compliance checks
**Speed**: ~2-5 minutes

**Flow**:
1. Developer commits code
2. `pre-commit` validates CONTEXT.md + AUDIT.md updates
3. `post-commit` spawns auditor agent → updates AUDIT.md
4. If blocking issues found → development agent auto-fixes on next commit
5. Loop continues until ✅ CLEAR

#### 2. **Multi-Agent Mode (New - Comprehensive)**

**Triggered by**: Manual spawn-agents.sh call
**Agents**: Developer + Auditor + Test (parallel)
**Purpose**: Comprehensive validation (syntax, compliance, tests)
**Speed**: ~5-10 minutes (faster than sequential due to parallel execution)

**Flow**:
1. Developer commits code
2. `pre-commit` validates (existing checks)
3. Developer manually runs: `.git-hooks/spawn-agents.sh post-commit`
4. Copy generated Task(...) prompts
5. Paste into Claude Code session (spawns 3 agents in parallel)
6. All 3 agents report back simultaneously:
   - Auditor → AUDIT.md (compliance)
   - Test → TESTING.md (test results, coverage)
   - Developer → CONTEXT.md (technical review)

---

## When to Use Each Mode

### Use Autonomous Mode When:
- ✅ Working on small changes (<500 lines)
- ✅ Fast iteration required
- ✅ PRD compliance is primary concern
- ✅ Tests are already passing

### Use Multi-Agent Mode When:
- ✅ Completing a major phase or feature
- ✅ Before creating a pull request
- ✅ After significant refactoring
- ✅ Want comprehensive validation (syntax + compliance + tests)
- ✅ Need full test suite run with coverage metrics

---

## Usage Examples

### Example 1: Quick Iteration (Autonomous Mode)

```bash
# Make changes
git add .
git commit -m "feat: quick fix"
# → pre-commit validates
# → post-commit spawns auditor automatically
# → AUDIT.md updated in background
# → Continue working
```

### Example 2: Phase Completion (Multi-Agent Mode)

```bash
# Complete Phase 5.4
git add .
git commit -m "feat: Phase 5.4 complete"
# → pre-commit validates
# → post-commit spawns auditor (existing)

# Now manually trigger comprehensive validation
.git-hooks/spawn-agents.sh post-commit

# Output shows Task(...) prompts for 3 agents
# Copy and paste into Claude Code session

# Agents run in parallel:
# - Auditor: Full HIPAA/GDPR + PRD audit → AUDIT.md
# - Test: Full test suite + coverage → TESTING.md
# - Developer: Technical review → CONTEXT.md

# Check results in 5-10 minutes
cat AUDIT.md   # Compliance scores
cat TESTING.md # Test results, coverage
```

### Example 3: Pre-Push Validation (Multi-Agent Mode)

```bash
# Before pushing to remote
.git-hooks/spawn-agents.sh pre-push

# Copy generated prompts
# Paste into Claude Code
# Wait for all 3 agents to report PASS
# Then push:
git push
```

---

## Configuration

### Enable/Disable Autonomous Mode

**File**: `.claude/autonomous-config.yaml`

```yaml
enabled: true  # Set to false to disable autonomous post-commit auditor

auto_fix:
  enabled: true  # Development agent auto-fixes blocking issues
```

### Agent Communication

**All agents write status updates to**: `CONTEXT.md` → `## 💬 Agent Communication`

**Format**:
```markdown
### [Agent Name] [ISO 8601 Timestamp]
**Status**: [Working/Blocked/Complete]
**Progress**: [Percentage or description]
**Findings**: [Summary or link to detailed findings]
**Blockers**: [List or "None"]
**Requests**: [Requests to other agents or "None"]
```

---

## Troubleshooting

### Issue: Autonomous mode not triggering

**Solution**:
1. Check `.claude/autonomous-config.yaml` exists
2. Verify `enabled: true`
3. Check `.git-hooks/autonomous.log` for errors

### Issue: Multi-agent prompts not working

**Solution**:
1. Ensure `.git-hooks/spawn-agents.sh` is executable: `chmod +x .git-hooks/spawn-agents.sh`
2. Copy the ENTIRE output (all Task(...) blocks)
3. Paste as a SINGLE message in Claude Code

### Issue: Agents not writing to shared documents

**Solution**:
1. Check agents have write permissions to CONTEXT.md, AUDIT.md, TESTING.md
2. Verify agent prompts include "Update [DOCUMENT].md" instructions
3. Check git status to see if files were modified

---

## Future Enhancements

**Planned**:
1. ✅ Automatic parallel agent spawning (when Claude Code CLI/API available)
2. ✅ Agent health monitoring (timeout detection, failure alerts)
3. ✅ Workflow visualization (agent communication graph)
4. ✅ 4th agent: Documentation Agent (auto-generate docs from code)

**Current Status**: Manual trigger via spawn-agents.sh (future: fully automated)

---

## References

- **Full Design**: [MULTI_AGENT_WORKFLOW.md](../../MULTI_AGENT_WORKFLOW.md)
- **Agent Manifest**: [.claude/agents.yaml](../.claude/agents.yaml)
- **CLAUDE.md Section**: Multi-Agent Parallel Workflow (v1.7.0+)
- **Existing Hook Docs**: [.git-hooks/README.md](./README.md)

---

**Questions?** See MULTI_AGENT_WORKFLOW.md or ask the team lead.
