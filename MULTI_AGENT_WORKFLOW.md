# Multi-Agent Parallel Workflow - Design Document

**Version**: 1.0.0
**Created**: 2025-11-19
**Status**: Implementation Ready

---

## 🎯 Executive Summary

This document describes the **redesigned multi-agent parallel workflow** for continuous development, testing, and auditing. Instead of a single sequential agent, **3 specialized agents work simultaneously**, communicating via shared documents (CONTEXT.md, AUDIT.md, TESTING.md) and coordinating through Git hooks.

**Key Benefits**:
- ⚡ **3x faster feedback** through parallel execution
- 🛡️ **Continuous compliance validation** (HIPAA/GDPR/PRD)
- 🧪 **Automated quality assurance** (tests run on every commit)
- 📊 **Shared knowledge** across all agents
- 🤖 **Safer autonomous mode** (multiple validation layers)

---

## 🏗️ Architecture

### Agent Specialization

```
┌─────────────────────────────────────────────────────────────┐
│                     GIT COMMIT TRIGGER                       │
└───────────────────┬─────────────────────────────────────────┘
                    │
       ┌────────────┼────────────┐
       │            │            │
       ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Developer│  │ Auditor  │  │   Test   │
│  Agent   │  │  Agent   │  │  Agent   │
└─────┬────┘  └────┬─────┘  └────┬─────┘
      │            │             │
      │    ┌───────┴──────┐      │
      │    │              │      │
      ▼    ▼              ▼      ▼
   CONTEXT.md          AUDIT.md  TESTING.md
      ▲    ▲              ▲      ▲
      │    │              │      │
      └────┼──────────────┼──────┘
           │              │
      Read & Respond to Findings
```

### Agent Roles

#### 1. Developer Agent (Primary Builder)
- **Role**: Implements features, writes production code
- **Skills**: spec-kit-enforcer, infrastructure-expert, vue3-component-reuse, modular-app-architect
- **Tools**: Full access (Read, Write, Edit, Bash, Grep, Glob, Task)
- **Writes To**: CONTEXT.md (technical changes, agent communication)
- **Reads From**: AUDIT.md (compliance feedback), TESTING.md (test results)

#### 2. Auditor Agent (Compliance Checker)
- **Role**: HIPAA/GDPR validation, PRD alignment checking, drift detection
- **Skills**: healthcare-compliance-checker, prd-compliance-checker, medcat-meta-annotations, fhir-r4-mapper
- **Tools**: Read-only (Read, Grep, Glob - NO Write/Edit for safety)
- **Writes To**: AUDIT.md (compliance findings), CONTEXT.md (agent communication)
- **Reads From**: CONTEXT.md (what was built), code files, PRD specifications

#### 3. Test Agent (Quality Assurance)
- **Role**: Test generation, execution, coverage tracking, performance benchmarking
- **Skills**: prd-test-generator, autonomous-developer (TDD loops)
- **Tools**: Read, Bash (run tests), Grep, Glob, Write (update TESTING.md)
- **Writes To**: TESTING.md (test results), CONTEXT.md (agent communication)
- **Reads From**: CONTEXT.md (what to test), AUDIT.md (compliance requirements), PRD specs, test files

---

## 📋 Shared Document Protocol

### CONTEXT.md (Technical Memory)
**Primary Owner**: Developer Agent

**Sections**:
- Recent Changes (Developer writes)
- Architecture Decision Records (Developer writes)
- Implementation Status (Developer writes)
- **NEW**: Agent Communication (All agents write)

**Agent Communication Format**:
```markdown
### [Agent Name] [ISO 8601 Timestamp]
**Status**: [Working/Blocked/Complete]
**Progress**: [Percentage or description]
**Findings**: [Summary or link to detailed findings]
**Blockers**: [List or "None"]
**Requests**: [Requests to other agents or "None"]
```

### AUDIT.md (Compliance Memory)
**Primary Owner**: Auditor Agent

**Sections**:
- Current Compliance Status (Auditor writes)
- Compliance Review (Auditor writes)
- Previous Commits (Auditor writes)
- **NEW**: Auditor Findings (Auditor writes detailed findings)

### TESTING.md (Quality Memory)
**Primary Owner**: Test Agent

**Sections**:
- Current Test Status (Test Agent writes)
- Coverage Metrics (Test Agent writes)
- Failed Tests (Test Agent writes)
- Performance Benchmarks (Test Agent writes)
- **NEW**: Test Agent Findings (Test Agent writes recommendations)

---

## 🔗 Git Hook Integration

### pre-commit (All 3 Agents - BLOCKING)

**Trigger**: On every `git commit`
**Execution**: **PARALLEL** (all 3 agents run simultaneously)
**Blocking**: **YES** (commit only proceeds if all agents approve)
**Timeout**: 5 minutes

**Agent Responsibilities**:

1. **Developer Agent**:
   - Validates code syntax
   - Checks for hardcoded secrets
   - Verifies CONTEXT.md updated

2. **Auditor Agent**:
   - Quick HIPAA check (no PHI in logs)
   - Quick PRD alignment (breaking changes?)

3. **Test Agent**:
   - Runs modified test files
   - Smoke tests critical paths

**Success Criteria**: All 3 agents report "PASS"

**Output**:
```bash
🔀 Running parallel agent checks...
  ✓ Developer Agent: Syntax valid, CONTEXT.md updated
  ✓ Auditor Agent: No HIPAA violations, no breaking changes
  ✓ Test Agent: Modified tests passing
✅ All agents approve - commit proceeding
```

### post-commit (Auditor + Test Agents - NON-BLOCKING)

**Trigger**: After successful commit
**Execution**: **PARALLEL** (both agents run simultaneously)
**Blocking**: **NO** (background work)
**Timeout**: 10 minutes

**Agent Responsibilities**:

1. **Auditor Agent**:
   - Full HIPAA/GDPR audit
   - Full PRD compliance check
   - Updates AUDIT.md with findings

2. **Test Agent**:
   - Runs full test suite
   - Updates coverage metrics
   - Updates TESTING.md with results

**Success Criteria**: Both agents complete (warnings allowed)

**Output**: Updates to AUDIT.md and TESTING.md (visible in next `git status`)

### pre-push (All 3 Agents - BLOCKING)

**Trigger**: Before `git push` to remote
**Execution**: **PARALLEL** (all 3 agents run simultaneously)
**Blocking**: **YES** (push only proceeds if all agents approve with 0 blocking issues)
**Timeout**: 15 minutes

**Agent Responsibilities**:

1. **Developer Agent**:
   - Verifies all commits have CONTEXT.md updates
   - Checks for TODO/FIXME comments

2. **Auditor Agent**:
   - Final compliance validation
   - Verifies 0 blocking issues in AUDIT.md

3. **Test Agent**:
   - Runs full suite + performance benchmarks
   - Verifies coverage ≥85%
   - Verifies all tests passing

**Success Criteria**: All 3 agents report "PASS" with 0 blocking issues

---

## 🔄 Communication Flow

### Example: Implementing a New Feature

**Step 1: Developer Agent implements Task 5.4.1**
```markdown
## Agent Communication

### Developer Agent [2025-11-19T14:30:00Z]
**Status**: Task 5.4.1 complete - Filter UI component
**Progress**: 100%
**Findings**: None
**Blockers**: None
**Requests**: Auditor review, Test run full suite
```

**Step 2: Developer commits**
```bash
git add .
git commit -m "feat(timeline): Task 5.4.1 - Filter UI component"
```

**Step 3: pre-commit hook spawns 3 agents (PARALLEL)**
- All 3 agents run simultaneously
- Each agent checks its responsibilities
- Commit proceeds only if all approve

**Step 4: post-commit hook spawns Auditor + Test (BACKGROUND)**
- Both agents run full validation in background
- Results written to AUDIT.md and TESTING.md

**Step 5: Developer reads agent findings**
```bash
# Check AUDIT.md
## Auditor Findings
- ⚠️  Warning: New endpoint missing RBAC check
- ✅ No PHI exposure detected

# Check TESTING.md
## Test Agent Findings
- ✅ All tests passing (143/143)
- 💡 Recommendation: Add edge case test
```

**Step 6: Developer responds to findings**
```markdown
### Developer Agent [2025-11-19T15:00:00Z]
**Status**: Addressing Auditor findings from Task 5.4.1
**Progress**: 50%
**Findings**: Fixed RBAC issue, added edge case test
**Blockers**: None
**Requests**: Auditor re-review, Test re-run
```

**Step 7: Developer commits fix (cycle repeats)**

---

## 🤖 Autonomous Mode Integration

### Autonomous Continuation Criteria

**Continue autonomously when**:
- ✅ All agents approve in pre-commit
- ✅ No blocking issues in AUDIT.md
- ✅ All tests passing in TESTING.md
- ✅ No "Requests" pending in Agent Communication

### Autonomous Pause Criteria

**Pause for user review when**:
- ❌ Auditor finds blocking HIPAA/GDPR violation
- ❌ Test coverage drops below 80%
- ❌ PRD drift detected with breaking changes
- ❌ Any agent reports a blocker

### Conflict Resolution

**Agent Priority Order**:
1. **Auditor** (compliance is non-negotiable)
2. **Test** (quality gates must pass)
3. **Developer** (implementation decisions)

**Escalation**:
- If Auditor blocks → Developer **must** fix
- If Test fails → Developer **must** fix or skip with justification
- If agents disagree → Escalate to user via CONTEXT.md

---

## ⚙️ Configuration

### Agent Manifest
**File**: `.claude/agents.yaml`
**Contents**:
- Agent definitions (name, role, skills, tools)
- Workflow coordination (triggers, parallel execution)
- Communication protocol (update frequency, message format)
- Conflict resolution (priority order, escalation rules)

### Git Hooks
**Scripts**:
- `.git-hooks/pre-commit-parallel.sh` (spawn 3 agents, validate, block if fail)
- `.git-hooks/post-commit-parallel.sh` (spawn 2 agents, background work)
- `.git-hooks/pre-push-parallel.sh` (spawn 3 agents, final validation)

### Shared Documents
**Files**:
- `CONTEXT.md` (Technical memory + Agent Communication)
- `AUDIT.md` (Compliance memory + Auditor Findings)
- `TESTING.md` (Quality memory + Test Agent Findings)

---

## 📊 Benefits

### 1. Parallel Efficiency
- **Before**: Sequential agent → ~5 min per commit
- **After**: Parallel agents → ~2 min per commit (3 agents run simultaneously)
- **Speedup**: 2.5x faster feedback loop

### 2. Continuous Validation
- **Compliance**: Every commit checked for HIPAA/GDPR violations
- **Quality**: Every commit runs tests and checks coverage
- **PRD Alignment**: Every commit validated against specifications
- **Result**: Issues caught in pre-commit, not in production

### 3. Early Detection
- **Pre-commit**: Blocks commits with critical issues
- **Post-commit**: Provides full audit in background
- **Pre-push**: Final gate before code reaches main branch
- **Result**: Fast feedback, thorough validation

### 4. Shared Memory
- **CONTEXT.md**: All agents see technical changes
- **AUDIT.md**: All agents see compliance requirements
- **TESTING.md**: All agents see quality status
- **Result**: No knowledge loss between agents or sessions

### 5. Specialization
- **Developer**: Focuses on implementation
- **Auditor**: Focuses on compliance (read-only for safety)
- **Test**: Focuses on quality
- **Result**: Each agent excels in its domain

### 6. Autonomous Safety
- **Multiple validators**: 3 agents check different aspects
- **Blocking gates**: Commits blocked if agents disagree
- **Audit trail**: Every decision documented in shared docs
- **Result**: Safer autonomous operation

---

## 🚀 Implementation Status

### Completed
- ✅ Multi-agent architecture design
- ✅ Agent manifest (`.claude/agents.yaml`)
- ✅ Shared document templates (CONTEXT.md, AUDIT.md, TESTING.md)
- ✅ CLAUDE.md integration (v1.7.0)
- ✅ Agent Communication section in CONTEXT.md

### Pending
- ⏳ Git hook scripts (`.git-hooks/pre-commit-parallel.sh`, etc.)
- ⏳ Agent spawning mechanism (actual parallel execution)
- ⏳ Testing with real commits

### Future Enhancements
- 📅 Performance metrics dashboard (agent response times)
- 📅 Agent health monitoring (timeout detection, failure alerts)
- 📅 Workflow visualization (agent communication graph)
- 📅 4th agent: Documentation Agent (auto-generate docs from code)

---

## 📖 Usage Guide

### For Developers (Developer Agent)

**Every commit**:
1. Implement feature/fix
2. Update CONTEXT.md (Recent Changes)
3. Write Agent Communication status
4. Commit (hooks run automatically)
5. Read AUDIT.md and TESTING.md for findings
6. Address blocking issues
7. Repeat

**Key principle**: Treat AUDIT.md and TESTING.md as your code reviewers.

### For Auditors (Auditor Agent)

**Every commit**:
1. Read CONTEXT.md (what was built)
2. Run HIPAA/GDPR checks
3. Run PRD alignment checks
4. Write findings to AUDIT.md
5. Write status to CONTEXT.md Agent Communication
6. Block if critical issues found

**Key principle**: Compliance is non-negotiable. Block commits without hesitation.

### For Testers (Test Agent)

**Every commit**:
1. Read CONTEXT.md (what to test)
2. Run test suite (modified files in pre-commit, full suite in post-commit)
3. Check coverage and benchmarks
4. Write results to TESTING.md
5. Write recommendations to CONTEXT.md Agent Communication
6. Block if tests fail or coverage drops

**Key principle**: Quality gates enforce minimum standards.

---

## 🔍 Monitoring

### Agent Health Metrics

**Track**:
- Response time per agent (target: <2 min for pre-commit)
- Success rate per agent (target: >95%)
- Blocker rate per agent (% of commits blocked)

**Alerts**:
- Agent timeout (>5 min for pre-commit)
- Agent failure (exit code ≠ 0)
- Agent deadlock (agents waiting on each other)

### Workflow Health Metrics

**Track**:
- Time to merge (commit → push)
- Blocker resolution time (issue found → fixed)
- Agent agreement rate (% of commits where all agents approve)

**KPIs**:
- Autonomous completion rate: >90%
- Compliance pass rate: 100%
- Test pass rate: >95%

---

## 💡 Best Practices

### For All Agents

1. **Be specific**: Reference file paths, line numbers, commit SHAs
2. **Be timely**: Update status within 30 seconds to 3 minutes
3. **Be clear**: Use "BLOCKING" prefix for critical issues
4. **Be collaborative**: Request reviews explicitly in Agent Communication

### For Conflict Resolution

1. **Auditor wins**: Compliance issues are non-negotiable
2. **Test validates**: Quality gates must pass
3. **Developer decides**: Implementation choices (if compliant and tested)
4. **Escalate to user**: When agents genuinely disagree

### For Autonomous Mode

1. **Check all 3 documents**: CONTEXT.md, AUDIT.md, TESTING.md
2. **Address all blockers**: Don't continue with pending issues
3. **Update Agent Communication**: Keep other agents informed
4. **Respect agent priority**: Auditor > Test > Developer

---

## 📚 References

- **CLAUDE.md**: Full AI assistant guide (v1.7.0+)
- **CONTEXT.md**: Technical memory and Agent Communication
- **AUDIT.md**: Compliance audit trail
- **TESTING.md**: Quality assurance results
- **.claude/agents.yaml**: Agent manifest and configuration
- **Skills Guide**: How skills integrate with agents (from Anthropic docs)

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-19 | Initial multi-agent workflow design |

---

**Questions?** See CLAUDE.md section "Multi-Agent Parallel Workflow" or ask the team lead.

**Ready to implement?** Start with git hook scripts, then test with small commits.
