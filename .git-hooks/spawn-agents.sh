#!/bin/bash
#
# Multi-Agent Spawn Helper
# Generates Task tool prompts for spawning the 3 specialized agents
#
# Usage:
#   ./spawn-agents.sh pre-commit    # Generate pre-commit agent prompts
#   ./spawn-agents.sh post-commit   # Generate post-commit agent prompts
#   ./spawn-agents.sh pre-push      # Generate pre-push agent prompts
#

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TRIGGER=${1:-pre-commit}

echo -e "${BLUE}🤖 Multi-Agent Workflow - $TRIGGER${NC}"
echo ""

# Get the last commit info
LAST_COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "No commits yet")
LAST_COMMIT_MSG=$(git log -1 --pretty=%B 2>/dev/null || echo "No commits yet")
CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null || git diff --cached --name-only)

echo -e "${YELLOW}Trigger: $TRIGGER${NC}"
echo -e "${YELLOW}Last Commit: $LAST_COMMIT_SHA${NC}"
echo ""

case $TRIGGER in
  pre-commit)
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}PRE-COMMIT: Quick Validation (All 3 Agents in Parallel)${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Spawn these 3 agents in a single message with multiple Task tool calls:"
    echo ""

    echo -e "${BLUE}1. Developer Agent (Quick Check)${NC}"
    cat <<'EOF'
Task({
  subagent_type: "general-purpose",
  model: "haiku",
  description: "Developer quick validation",
  prompt: `You are the Developer Agent performing pre-commit validation.

**Context**: Pre-commit hook triggered

**Your responsibilities:**
1. Validate Python/TypeScript syntax on staged files
2. Check for hardcoded secrets (API keys, passwords)
3. Verify CONTEXT.md was updated with meaningful changes
4. Quick smoke test (if applicable)

**Files to check:**
${CHANGED_FILES}

**Report format:**
### Developer Agent [$(date -Iseconds)]
**Status**: [Complete]
**Findings**: [List any issues]
**Blockers**: [None or list]
**Verdict**: [PASS/FAIL]

If FAIL, list specific issues that must be fixed before commit.`
})
EOF
    echo ""

    echo -e "${BLUE}2. Auditor Agent (Quick Check)${NC}"
    cat <<'EOF'
Task({
  subagent_type: "general-purpose",
  model: "haiku",
  description: "Auditor quick validation",
  prompt: `You are the Auditor Agent performing pre-commit compliance check.

**Context**: Pre-commit hook triggered

**Your responsibilities:**
1. Quick HIPAA check: No PHI in application logs
2. Quick PRD alignment: Any breaking changes?
3. Check if AUDIT.md status is CLEAR

**Files to check:**
${CHANGED_FILES}

**Report format:**
### Auditor Agent [$(date -Iseconds)]
**Status**: [Complete]
**Findings**: [List any issues]
**Blockers**: [None or list]
**Verdict**: [PASS/FAIL]

If FAIL, this is BLOCKING - commit must not proceed.`
})
EOF
    echo ""

    echo -e "${BLUE}3. Test Agent (Quick Check)${NC}"
    cat <<'EOF'
Task({
  subagent_type: "general-purpose",
  model: "haiku",
  description: "Test quick validation",
  prompt: `You are the Test Agent performing pre-commit test validation.

**Context**: Pre-commit hook triggered

**Your responsibilities:**
1. Run tests for modified files only
2. Quick smoke test on critical paths
3. Verify no test files were broken

**Files to check:**
${CHANGED_FILES}

**Report format:**
### Test Agent [$(date -Iseconds)]
**Status**: [Complete]
**Findings**: [Test results]
**Blockers**: [None or list]
**Verdict**: [PASS/FAIL]

If FAIL, list which tests failed and why.`
})
EOF
    echo ""
    echo -e "${YELLOW}⏱  Timeout: 5 minutes${NC}"
    echo -e "${RED}🚫 BLOCKING: Commit proceeds only if ALL 3 agents report PASS${NC}"
    ;;

  post-commit)
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}POST-COMMIT: Full Validation (Auditor + Test in Parallel)${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Spawn these 2 agents in a single message with multiple Task tool calls:"
    echo ""

    echo -e "${BLUE}1. Auditor Agent (Full Audit)${NC}"
    cat <<EOF
Task({
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Auditor full compliance audit",
  prompt: \`You are the Auditor Agent performing post-commit full audit.

**Context**: Commit completed - ${LAST_COMMIT_SHA:0:8}
**Commit Message**: ${LAST_COMMIT_MSG}

**Your responsibilities:**
1. Full HIPAA/GDPR compliance audit
2. Full PRD alignment check against Sprint specifications
3. Check for API drift (field names, types, structure)
4. Update AUDIT.md with detailed findings

**Files changed:**
${CHANGED_FILES}

**Actions:**
1. Read all changed files
2. Check against relevant PRD (.specify/sprints/*.md)
3. Run healthcare-compliance-checker skill (activate automatically)
4. Run prd-compliance-checker skill (activate automatically)
5. Update AUDIT.md with:
   - Feature compliance scores
   - Drift detection results
   - Any blocking issues found
   - Compliance trends

**Report format:**
Write findings to AUDIT.md following the established format.

Then write to CONTEXT.md Agent Communication section:

### Auditor Agent [$(date -Iseconds)]
**Status**: [Complete]
**Progress**: 100%
**Findings**: See AUDIT.md - [X blocking issues / 0 blocking issues]
**Blockers**: [List or "None"]
**Requests**: [Requests to Developer Agent or "None"]

**Warnings**: Non-blocking, but results written to AUDIT.md for next commit.\`
})
EOF
    echo ""

    echo -e "${BLUE}2. Test Agent (Full Suite)${NC}"
    cat <<EOF
Task({
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Test full test suite",
  prompt: \`You are the Test Agent performing post-commit full test suite.

**Context**: Commit completed - ${LAST_COMMIT_SHA:0:8}
**Commit Message**: ${LAST_COMMIT_MSG}

**Your responsibilities:**
1. Run full backend test suite (pytest)
2. Run full frontend test suite (vitest)
3. Update coverage metrics
4. Update TESTING.md with results and recommendations

**Files changed:**
${CHANGED_FILES}

**Actions:**
1. Run: cd backend && pytest --cov=app --cov-report=term
2. Run: cd frontend && npm run test:coverage
3. Analyze results
4. Update TESTING.md with:
   - Current test status
   - Coverage metrics (overall, by module)
   - Failed tests (if any)
   - Performance benchmarks (if applicable)
   - Recommendations for improvement

**Report format:**
Write results to TESTING.md following the established format.

Then write to CONTEXT.md Agent Communication section:

### Test Agent [$(date -Iseconds)]
**Status**: [Complete]
**Progress**: 100%
**Findings**: [X tests passing/failing, Y% coverage]
**Blockers**: [List or "None"]
**Requests**: [Requests to Developer Agent or "None"]

**Warnings**: Non-blocking, but results written to TESTING.md for next commit.\`
})
EOF
    echo ""
    echo -e "${YELLOW}⏱  Timeout: 10 minutes${NC}"
    echo -e "${GREEN}✅ NON-BLOCKING: Results written to AUDIT.md and TESTING.md${NC}"
    ;;

  pre-push)
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}PRE-PUSH: Final Validation (All 3 Agents in Parallel)${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Spawn these 3 agents in a single message with multiple Task tool calls:"
    echo ""

    echo -e "${BLUE}1. Developer Agent (Final Check)${NC}"
    cat <<'EOF'
Task({
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Developer final validation",
  prompt: `You are the Developer Agent performing pre-push validation.

**Context**: About to push to remote

**Your responsibilities:**
1. Verify all commits have CONTEXT.md updates
2. Check for TODO/FIXME comments in code (not documentation)
3. Verify no debug code (console.log, breakpoints)
4. Check commit message quality

**Report format:**
### Developer Agent [$(date -Iseconds)]
**Status**: [Complete]
**Findings**: [List any issues]
**Blockers**: [None or list]
**Verdict**: [PASS/FAIL]

If FAIL, list specific issues that must be fixed before push.`
})
EOF
    echo ""

    echo -e "${BLUE}2. Auditor Agent (Final Validation)${NC}"
    cat <<'EOF'
Task({
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Auditor final validation",
  prompt: `You are the Auditor Agent performing pre-push compliance validation.

**Context**: About to push to remote

**Your responsibilities:**
1. Final compliance validation (HIPAA/GDPR)
2. Verify AUDIT.md shows 0 blocking issues
3. Check all commits are PRD-compliant

**Report format:**
### Auditor Agent [$(date -Iseconds)]
**Status**: [Complete]
**Findings**: [List any issues]
**Blockers**: [None or list]
**Verdict**: [PASS/FAIL]

Read AUDIT.md and verify "✅ CLEAR" status with 0 blocking issues.

If FAIL, this is BLOCKING - push must not proceed.`
})
EOF
    echo ""

    echo -e "${BLUE}3. Test Agent (Final Validation)${NC}"
    cat <<'EOF'
Task({
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Test final validation",
  prompt: `You are the Test Agent performing pre-push test validation.

**Context**: About to push to remote

**Your responsibilities:**
1. Run full test suite with performance benchmarks
2. Verify coverage ≥85%
3. Verify all tests passing
4. Check TESTING.md for any blockers

**Report format:**
### Test Agent [$(date -Iseconds)]
**Status**: [Complete]
**Findings**: [Test results, coverage]
**Blockers**: [None or list]
**Verdict**: [PASS/FAIL]

If coverage <85% or tests failing, this is BLOCKING - push must not proceed.`
})
EOF
    echo ""
    echo -e "${YELLOW}⏱  Timeout: 15 minutes${NC}"
    echo -e "${RED}🚫 BLOCKING: Push proceeds only if ALL 3 agents report PASS${NC}"
    ;;

  *)
    echo -e "${RED}Unknown trigger: $TRIGGER${NC}"
    echo "Usage: $0 {pre-commit|post-commit|pre-push}"
    exit 1
    ;;
esac

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📝 How to use:${NC}"
echo "1. Copy the Task(...) prompts above"
echo "2. Paste into your Claude Code session"
echo "3. Send as a SINGLE MESSAGE with all Task calls"
echo "4. Wait for all agents to report back"
echo "5. Check verdicts (all must be PASS for blocking triggers)"
echo ""
echo -e "${YELLOW}📚 Documentation:${NC}"
echo "- Full workflow: MULTI_AGENT_WORKFLOW.md"
echo "- Agent manifest: .claude/agents.yaml"
echo "- CLAUDE.md section: Multi-Agent Parallel Workflow"
echo ""
