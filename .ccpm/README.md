# CCPM Multi-Agent Workflow - Pilot Setup

**Version**: 1.0.0
**Status**: Pilot Phase
**Target**: Task 2.4 - Boolean Query Parsing

---

## Overview

This directory contains configuration for **CCPM (Claude Code Project Manager)** - a multi-agent orchestration system that enables parallel development with 8 specialized agents.

**Pilot Configuration**:
- **3 agents**: Developer, Auditor, Tester
- **1 task**: Task 2.4 - Boolean Query Parsing
- **Goal**: Validate workflow, measure time savings, test coordination

---

## Prerequisites

### Install CCPM

```bash
# Option 1: npm (recommended)
npm install -g @automazeio/ccpm

# Option 2: From source
git clone https://github.com/automazeio/ccpm
cd ccpm
npm install
npm link
```

### Verify Installation

```bash
ccpm --version
# Expected: ccpm/1.x.x

ccpm help
# Shows available commands
```

---

## Configuration Files

```
.ccpm/
├── ccpm.yaml          # Main configuration (8 agents, workflows)
├── README.md          # This file
└── pilot-results.md   # Pilot metrics (created after run)
```

**Key Config Sections**:
1. **Agents** (lines 20-215): 8 agent definitions
2. **Workflows** (lines 217-320): 3 workflows (feature, sprint, pilot)
3. **Coordination** (lines 322-380): Communication, conflicts, priorities
4. **Git Integration** (lines 382-440): Pre-commit, post-commit, pre-push hooks
5. **Monitoring** (lines 442-500): Dashboard, metrics, alerts

---

## Pilot Execution

### Step 1: Validate Configuration

```bash
# From project root
cd /var/lib/docker/codespacemount/workspace/cogstack-nlp

# Validate ccpm.yaml syntax
ccpm validate .ccpm/ccpm.yaml

# Expected output:
# ✓ Configuration valid
# ✓ 8 agents defined
# ✓ 3 workflows configured
# ✓ No syntax errors
```

### Step 2: Dry Run (Simulation)

```bash
# Simulate pilot workflow without actually running agents
ccpm run --workflow pilot --dry-run

# Expected output:
# ┌─────────────────────────────────────────┐
# │ CCPM Pilot Workflow (DRY RUN)           │
# ├─────────────────────────────────────────┤
# │ Stage 1: Task Assignment                │
# │   → task-definer: Read Task 2.4 spec    │
# │                                         │
# │ Stage 2: Parallel Development           │
# │   → developer (1 instance): Task 2.4    │
# │   → auditor (concurrent): Quick audit   │
# │                                         │
# │ Stage 3: Validation                     │
# │   → tester: Run test suite              │
# │   → debugger (conditional): Fix fails   │
# │                                         │
# │ Success Criteria:                       │
# │   ✓ Task complete                       │
# │   ✓ Tests passing                       │
# │   ✓ Audit warnings ≤ 2                  │
# └─────────────────────────────────────────┘
```

### Step 3: Run Pilot (Live)

```bash
# Run pilot with 3 agents
ccpm run --workflow pilot \
  --agents developer,auditor,tester \
  --output .ccpm/pilot-results.md \
  --dashboard

# Flags:
#   --workflow pilot       Use pilot workflow (limited agents)
#   --agents ...          Specify which agents to use
#   --output FILE         Save results to file
#   --dashboard           Start web dashboard (port 8080)
```

**What Happens**:
1. **Task Definer**: Reads `.specify/tasks/sprint-3-full-text-search-tasks.md`, extracts Task 2.4
2. **Developer**: Implements Task 2.4 (Boolean Query Parsing)
   - Writes tests first (TDD)
   - Implements `_build_boolean_query()` method
   - Updates CONTEXT.md with changes
3. **Auditor** (concurrent): Reviews code for HIPAA/GDPR compliance
   - Quick audit mode (fast validation)
   - Updates AUDIT.md with findings
4. **Tester**: Runs test suite
   - Executes pytest for backend tests
   - Reports results to TESTING.md
5. **Debugger** (conditional): Only runs if tests fail
   - Max 3 retry attempts
   - Escalates to user if can't fix

### Step 4: Monitor Dashboard

Open http://localhost:8080/ccpm-dashboard in your browser

```
╔═══════════════════════════════════════════════════════════╗
║  CogStack NLP - Pilot: Task 2.4                          ║
╠═══════════════════════════════════════════════════════════╣
║  Status: In Progress                                      ║
║  Active Agents: 2/3 (Developer, Auditor)                 ║
║  Progress: 45%                                            ║
║  Elapsed: 1h 15m                                          ║
║  ETA: 1h 45m                                              ║
╚═══════════════════════════════════════════════════════════╝

TIMELINE:
[14:00] Pilot started
[14:05] Task Definer: Task 2.4 loaded (acceptance criteria: 7 items)
[14:10] Developer: Writing tests (4/7 tests complete)
[14:12] Auditor: Quick audit started
[14:20] Developer: Tests complete, implementing _build_boolean_query()
[14:25] Auditor: No HIPAA violations detected ✓
[14:35] Developer: Implementation 80% complete
[14:45] Developer: Committed code, updating CONTEXT.md
[14:50] Auditor: Comprehensive audit started
[14:55] Tester: Running pytest... [Current]
```

---

## Expected Results

### Success Criteria

✅ **Task Complete**: `_build_boolean_query()` method implemented
✅ **Tests Passing**: 100% (all Task 2.4 tests pass)
✅ **Audit Pass**: 0 blocking issues, ≤2 warnings
✅ **No Merge Conflicts**: Clean commit history
✅ **Time Saved**: ≥30% vs single agent (target: 1.5h vs 2h)

### Metrics Tracked

**Time Comparison**:
- **Single Agent** (historical): ~2 hours
- **CCPM Pilot** (3 agents): Target 1.5 hours (25% savings)

**Quality Metrics**:
- Test coverage: ≥90%
- Code review: Automated (Auditor)
- Compliance: Continuous validation

**Agent Performance**:
- Developer: Task implementation time
- Auditor: Issues detected (want: early detection)
- Tester: Time to validate
- Coordination: Blocking events, deadlocks (want: 0)

### Output Files

After pilot completion:

```
.ccpm/pilot-results.md    # Comprehensive metrics report
CONTEXT.md                # Updated with Task 2.4 entry
AUDIT.md                  # Updated with compliance review
TESTING.md                # Updated with test results
backend/app/search/       # Updated query_builder.py
backend/tests/            # New test_boolean_query.py
```

---

## Troubleshooting

### Issue: CCPM not found

```bash
# Check installation
which ccpm
npm list -g @automazeio/ccpm

# Reinstall
npm install -g @automazeio/ccpm
```

### Issue: Configuration validation fails

```bash
# Check YAML syntax
yamllint .ccpm/ccpm.yaml

# Common issues:
# - Indentation (use 2 spaces, not tabs)
# - Missing colons
# - Invalid agent names
```

### Issue: Dashboard not loading

```bash
# Check port availability
lsof -i :8080

# Try different port
ccpm run --workflow pilot --dashboard --port 8081
```

### Issue: Agent timeout

```bash
# Increase timeout in ccpm.yaml (line 42):
timeout: 60min  # Was: 30min

# Or pass via CLI:
ccpm run --workflow pilot --timeout 60
```

### Issue: File locking conflicts

```bash
# Check active locks
ccpm status --locks

# Clear stale locks
ccpm clean --locks
```

---

## Next Steps After Pilot

### Analyze Results

```bash
# View pilot report
cat .ccpm/pilot-results.md

# Key metrics to check:
# - Time saved (target: ≥25%)
# - Quality (coverage, bugs caught)
# - Compliance (violations detected)
# - Coordination (blocking events)
```

### Scale to Full Workflow

If pilot successful (all criteria met):

```bash
# Scale to 8 agents for Sprint 3 Phase 3
ccpm run --workflow feature-development \
  --agents all \
  --feature "Sprint 3 Phase 3: Frontend Search UI"

# Expected results:
# - 3 developers building in parallel
# - Tests/audit/docs happen concurrently
# - 3x faster than single agent
# - Continuous compliance validation
```

### Enable Git Hooks

```bash
# Install CCPM git hooks
ccpm install-hooks

# This adds:
# .git/hooks/pre-commit    → Auditor (quick) + Tester (modified)
# .git/hooks/post-commit   → Auditor (full) + Documentation
# .git/hooks/pre-push      → Auditor (comprehensive) + Tester (full)
```

---

## Configuration Reference

### Agent Models

- **Sonnet**: Complex tasks (architecture, developer, auditor, debugger)
- **Haiku**: Simple/formulaic tasks (test-generator, tester, documentation)

**Cost per task**:
- Sonnet: ~$0.50-1.00
- Haiku: ~$0.10-0.20
- **Pilot total**: ~$2-3 (3 agents, 1 task)

### Workflows

1. **pilot**: Limited (3 agents, 1 task) - For testing
2. **feature-development**: Full (8 agents, 1 feature) - Single feature
3. **sprint-execution**: Maximum (8 agents, 3 features) - Entire sprint

### Concurrency Limits

- Max concurrent agents: 8
- Max instances per agent: 3 (developer)
- Rate limit: 50 requests/minute

---

## Support

**Issues**: https://github.com/automazeio/ccpm/issues
**Docs**: https://ccpm.automaze.io/docs
**Project**: See CONTEXT.md "Development Workflow" section

---

## Changelog

### v1.0.0 (2025-11-20)
- Initial pilot configuration
- 8 agents defined (3 active for pilot)
- 3 workflows configured
- Git hook integration
- Dashboard monitoring
