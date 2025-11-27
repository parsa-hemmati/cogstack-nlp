#!/bin/bash
# Test Script: Autonomous Loop Validation
# Version: 1.0.0
# Purpose: Validate all autonomous loop functions work correctly

set -e

# Colors for output
RED='\033[0:31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"
TASK_QUEUE="$CLAUDE_DIR/TASK_QUEUE.md"
AGENT_STATUS="$CLAUDE_DIR/AGENT_STATUS.md"
HOOK_SCRIPT="$PROJECT_ROOT/.git-hooks/post-commit-agent-loop.sh"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
    ((TESTS_RUN++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
    ((TESTS_RUN++))
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

test_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# Test 1: File existence
test_header "TEST 1: Required Files Exist"

if [ -f "$TASK_QUEUE" ]; then
    pass "TASK_QUEUE.md exists"
else
    fail "TASK_QUEUE.md missing"
fi

if [ -f "$AGENT_STATUS" ]; then
    pass "AGENT_STATUS.md exists"
else
    fail "AGENT_STATUS.md missing"
fi

if [ -f "$HOOK_SCRIPT" ]; then
    pass "post-commit-agent-loop.sh exists"
else
    fail "post-commit-agent-loop.sh missing"
fi

if [ -x "$HOOK_SCRIPT" ]; then
    pass "post-commit hook is executable"
else
    fail "post-commit hook not executable"
fi

# Test 2: Hook functions
test_header "TEST 2: Hook Functions"

# Source the hook script functions (skip execution)
source "$HOOK_SCRIPT" 2>/dev/null || {
    fail "Cannot source hook script"
    exit 1
}

# Test count functions
if type count_active_agents &>/dev/null; then
    pass "count_active_agents() function exists"
else
    fail "count_active_agents() function missing"
fi

if type count_total_active &>/dev/null; then
    pass "count_total_active() function exists"
else
    fail "count_total_active() function missing"
fi

if type check_completion &>/dev/null; then
    pass "check_completion() function exists"
else
    fail "check_completion() function missing"
fi

if type check_deadlock &>/dev/null; then
    pass "check_deadlock() function exists"
else
    fail "check_deadlock() function missing"
fi

if type claim_next_task &>/dev/null; then
    pass "claim_next_task() function exists"
else
    fail "claim_next_task() function missing"
fi

if type spawn_agent &>/dev/null; then
    pass "spawn_agent() function exists"
else
    fail "spawn_agent() function missing"
fi

# Test 3: Task queue format
test_header "TEST 3: Task Queue Format"

pending_count=$(grep -c "^- \[ \] #[0-9]" "$TASK_QUEUE" 2>/dev/null || true)
in_progress_count=$(grep -c "^- \[🔄\]" "$TASK_QUEUE" 2>/dev/null || true)
completed_count=$(grep -c "^- \[✅\]" "$TASK_QUEUE" 2>/dev/null || true)

info "Pending tasks: $pending_count"
info "In-progress tasks: $in_progress_count"
info "Completed tasks: $completed_count"

if [ -n "$pending_count" ]; then
    pass "Can count pending tasks"
else
    fail "Cannot count pending tasks"
fi

if [ -n "$completed_count" ]; then
    pass "Can count completed tasks"
else
    fail "Cannot count completed tasks"
fi

# Test 4: Task ID extraction
test_header "TEST 4: Task ID Extraction"

first_task=$(grep -m 1 "^- \[" "$TASK_QUEUE" 2>/dev/null || echo "")
if [ -n "$first_task" ]; then
    task_id=$(echo "$first_task" | sed -E 's/.*#([0-9]+).*/\1/' | head -1 | tr -d '\n')

    if [[ "$task_id" =~ ^[0-9]+$ ]]; then
        pass "Task ID extraction works (extracted: #$task_id)"

        # Check for newlines
        if echo "$task_id" | grep -q $'\n'; then
            fail "Task ID contains newlines"
        else
            pass "Task ID has no newlines"
        fi
    else
        fail "Task ID extraction returned invalid value: '$task_id'"
    fi
else
    info "No tasks found to test extraction"
fi

# Test 5: Agent type extraction
test_header "TEST 5: Agent Type Extraction"

if [ -n "$first_task" ]; then
    agent_type=$(echo "$first_task" | sed -E 's/.*`\[([a-z-]+)\]`.*/\1/' | head -1 | tr -d '\n')

    if [[ "$agent_type" =~ ^[a-z-]+$ ]]; then
        pass "Agent type extraction works (extracted: $agent_type)"
    else
        fail "Agent type extraction returned invalid value: '$agent_type'"
    fi
fi

# Test 6: Configuration loading
test_header "TEST 6: Configuration Loading"

config_file="$CLAUDE_DIR/agent-loop-config.yaml"
if [ -f "$config_file" ]; then
    pass "Configuration file exists"

    max_agents=$(grep "^max_total_agents:" "$config_file" | sed 's/^[^:]*:[[:space:]]*//')
    if [ -n "$max_agents" ] && [ "$max_agents" -gt 0 ]; then
        pass "Can read max_total_agents: $max_agents"
    else
        fail "Cannot read max_total_agents from config"
    fi
else
    fail "Configuration file missing"
fi

# Test 7: Log directory
test_header "TEST 7: Log Directory"

log_dir="$CLAUDE_DIR/logs"
if [ -d "$log_dir" ]; then
    pass "Log directory exists"

    if [ -w "$log_dir" ]; then
        pass "Log directory is writable"
    else
        fail "Log directory not writable"
    fi
else
    fail "Log directory missing"
fi

# Test 8: Lock files
test_header "TEST 8: Lock File Mechanism"

lock_file="$TASK_QUEUE.lock"
if touch "$lock_file" 2>/dev/null; then
    pass "Can create lock files"
    rm -f "$lock_file"
else
    fail "Cannot create lock files"
fi

# Test 9: Git hook integration
test_header "TEST 9: Git Hook Integration"

git_hook=".git/hooks/post-commit"
if [ -L "$git_hook" ] || [ -f "$git_hook" ]; then
    pass "Git post-commit hook exists"

    if [ -x "$git_hook" ]; then
        pass "Git hook is executable"
    else
        fail "Git hook not executable"
    fi
else
    info "Git hook not linked (run init-loop.sh)"
fi

# Test 10: Agent definitions
test_header "TEST 10: Agent Definitions"

agents_dir="$CLAUDE_DIR/agents"
if [ -d "$agents_dir" ]; then
    pass "Agents directory exists"

    agent_count=$(ls "$agents_dir"/*.md 2>/dev/null | wc -l)
    if [ "$agent_count" -gt 0 ]; then
        pass "Found $agent_count agent definitions"
    else
        fail "No agent definitions found"
    fi
else
    fail "Agents directory missing"
fi

# Summary
test_header "TEST SUMMARY"

echo "Total tests run: $TESTS_RUN"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ "$TESTS_FAILED" -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
fi

success_rate=$((100 * TESTS_PASSED / TESTS_RUN))
echo "Success rate: ${success_rate}%"

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "\n${GREEN}✓ ALL TESTS PASSED${NC}"
    echo "Autonomous loop validation successful!"
    exit 0
else
    echo -e "\n${RED}✗ SOME TESTS FAILED${NC}"
    echo "Please fix the issues above before using the autonomous loop."
    exit 1
fi
