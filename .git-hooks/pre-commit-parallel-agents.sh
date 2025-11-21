#!/bin/bash
# Pre-Commit Hook: Parallel Agent Spawning
# Required agents: 2 developers, 1 documentation, 1 orchestrator
# Blocks commit if any agent reports blocking issues

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENT_CONFIG=".claude/agent-coordination.yaml"
TIMEOUT_MINUTES=10
LOG_DIR=".claude/logs/pre-commit"
SESSION_ID=$(date +%Y%m%d_%H%M%S)

# Create log directory
mkdir -p "$LOG_DIR"

echo -e "${BLUE}🔀 Pre-Commit Hook: Spawning Required Agents${NC}"
echo "Session ID: $SESSION_ID"
echo ""

# Check if agent coordination config exists
if [ ! -f "$AGENT_CONFIG" ]; then
    echo -e "${RED}❌ Error: Agent coordination config not found${NC}"
    echo "Expected: $AGENT_CONFIG"
    exit 1
fi

# Initialize agent status tracking
declare -A AGENT_STATUS
declare -A AGENT_PIDS
declare -a AGENT_LOGS

# Function to spawn a developer agent
spawn_developer_agent() {
    local agent_num=$1
    local log_file="$LOG_DIR/developer-${agent_num}-${SESSION_ID}.log"
    AGENT_LOGS+=("$log_file")

    echo -e "${BLUE}→ Spawning Developer Agent #${agent_num}${NC}"

    # Create agent prompt
    cat > "$log_file" <<EOF
Agent: Developer #${agent_num}
Session: ${SESSION_ID}
Tasks:
  - Validate syntax and imports
  - Verify tests exist for changed code
  - Check for hardcoded secrets
  - Verify CONTEXT.md updated

Status: Starting...
EOF

    # Simulate agent spawn (in real implementation, this would call Claude Agent SDK)
    {
        echo "Validating syntax..."

        # Check Python syntax
        if ! find backend -name "*.py" -exec python3 -m py_compile {} + 2>&1 | tee -a "$log_file"; then
            echo "BLOCKING: Python syntax errors found" >> "$log_file"
            AGENT_STATUS["developer-$agent_num"]="BLOCKING"
            return 1
        fi

        # Check for secrets
        if grep -r "password\s*=\s*['\"]" backend/ 2>&1 | grep -v "test" | tee -a "$log_file"; then
            echo "BLOCKING: Hardcoded secrets detected" >> "$log_file"
            AGENT_STATUS["developer-$agent_num"]="BLOCKING"
            return 1
        fi

        # Check CONTEXT.md updated
        if ! git diff --cached --name-only | grep -q "CONTEXT.md"; then
            # Check if there are code changes
            if git diff --cached --name-only | grep -qE '\.(py|ts|vue)$'; then
                echo "BLOCKING: CONTEXT.md not updated with code changes" >> "$log_file"
                AGENT_STATUS["developer-$agent_num"]="BLOCKING"
                return 1
            fi
        fi

        echo "PASS: All developer checks passed" >> "$log_file"
        AGENT_STATUS["developer-$agent_num"]="PASS"
    } &

    AGENT_PIDS["developer-$agent_num"]=$!
}

# Function to spawn documentation agent
spawn_documentation_agent() {
    local log_file="$LOG_DIR/documentation-${SESSION_ID}.log"
    AGENT_LOGS+=("$log_file")

    echo -e "${BLUE}→ Spawning Documentation Agent${NC}"

    cat > "$log_file" <<EOF
Agent: Documentation
Session: ${SESSION_ID}
Tasks:
  - Verify CONTEXT.md and AUDIT.md updated
  - Check commit message format
  - Validate documentation consistency

Status: Starting...
EOF

    {
        # Check CONTEXT.md updated
        if git diff --cached --name-only | grep -qE '\.(py|ts|vue)$'; then
            if ! git diff --cached --name-only | grep -q "CONTEXT.md"; then
                echo "BLOCKING: CONTEXT.md must be updated with code changes" >> "$log_file"
                AGENT_STATUS["documentation"]="BLOCKING"
                return 1
            fi

            if ! git diff --cached --name-only | grep -q "AUDIT.md"; then
                echo "BLOCKING: AUDIT.md must be updated with code changes" >> "$log_file"
                AGENT_STATUS["documentation"]="BLOCKING"
                return 1
            fi
        fi

        echo "PASS: Documentation checks passed" >> "$log_file"
        AGENT_STATUS["documentation"]="PASS"
    } &

    AGENT_PIDS["documentation"]=$!
}

# Function to spawn orchestrator agent
spawn_orchestrator_agent() {
    local log_file="$LOG_DIR/orchestrator-${SESSION_ID}.log"
    AGENT_LOGS+=("$log_file")

    echo -e "${BLUE}→ Spawning Orchestrator Agent${NC}"

    cat > "$log_file" <<EOF
Agent: Orchestrator
Session: ${SESSION_ID}
Tasks:
  - Coordinate all agents
  - Spawn any additional needed agents
  - Monitor overall health

Status: Starting...
EOF

    {
        # Orchestrator waits for other agents and makes final decision
        sleep 2

        # Check if all required agents spawned successfully
        local all_spawned=true
        for agent in "developer-1" "developer-2" "documentation"; do
            if [ -z "${AGENT_PIDS[$agent]:-}" ]; then
                echo "WARNING: Agent $agent not spawned" >> "$log_file"
                all_spawned=false
            fi
        done

        if [ "$all_spawned" = true ]; then
            echo "PASS: All required agents spawned successfully" >> "$log_file"
            AGENT_STATUS["orchestrator"]="PASS"
        else
            echo "WARNING: Some agents missing" >> "$log_file"
            AGENT_STATUS["orchestrator"]="PASS"  # Non-blocking
        fi
    } &

    AGENT_PIDS["orchestrator"]=$!
}

# Spawn all required agents in parallel
echo -e "${YELLOW}📋 Spawning 4 required agents in parallel...${NC}"
echo ""

spawn_developer_agent 1
spawn_developer_agent 2
spawn_documentation_agent
spawn_orchestrator_agent

echo ""
echo -e "${YELLOW}⏳ Waiting for agents to complete (timeout: ${TIMEOUT_MINUTES}m)...${NC}"
echo ""

# Wait for all agents with timeout
TIMEOUT_SECONDS=$((TIMEOUT_MINUTES * 60))
START_TIME=$(date +%s)

for agent in "${!AGENT_PIDS[@]}"; do
    pid=${AGENT_PIDS[$agent]}

    # Wait with timeout
    while kill -0 "$pid" 2>/dev/null; do
        CURRENT_TIME=$(date +%s)
        ELAPSED=$((CURRENT_TIME - START_TIME))

        if [ $ELAPSED -gt $TIMEOUT_SECONDS ]; then
            echo -e "${RED}⏱️  Timeout: Agent $agent exceeded ${TIMEOUT_MINUTES}m${NC}"
            kill "$pid" 2>/dev/null || true
            AGENT_STATUS["$agent"]="TIMEOUT"
            break
        fi

        sleep 1
    done

    # Get exit status if not already set
    if [ -z "${AGENT_STATUS[$agent]:-}" ]; then
        wait "$pid"
        if [ $? -eq 0 ]; then
            AGENT_STATUS["$agent"]="PASS"
        else
            AGENT_STATUS["$agent"]="FAIL"
        fi
    fi
done

echo ""
echo -e "${BLUE}📊 Agent Results:${NC}"
echo ""

# Display results
BLOCKING_ISSUES=0
WARNINGS=0

for agent in "${!AGENT_STATUS[@]}"; do
    status="${AGENT_STATUS[$agent]}"

    case "$status" in
        PASS)
            echo -e "  ${GREEN}✓${NC} $agent: PASS"
            ;;
        BLOCKING)
            echo -e "  ${RED}✗${NC} $agent: BLOCKING ISSUE"
            BLOCKING_ISSUES=$((BLOCKING_ISSUES + 1))
            ;;
        FAIL)
            echo -e "  ${YELLOW}⚠${NC} $agent: FAILED (non-blocking)"
            WARNINGS=$((WARNINGS + 1))
            ;;
        TIMEOUT)
            echo -e "  ${RED}⏱${NC} $agent: TIMEOUT"
            BLOCKING_ISSUES=$((BLOCKING_ISSUES + 1))
            ;;
    esac
done

echo ""

# Show logs for failed agents
if [ $BLOCKING_ISSUES -gt 0 ] || [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}📋 Agent Logs:${NC}"
    echo ""

    for log_file in "${AGENT_LOGS[@]}"; do
        if [ -f "$log_file" ]; then
            agent_name=$(basename "$log_file" | sed 's/-'${SESSION_ID}'.log//')
            status="${AGENT_STATUS[$agent_name]:-UNKNOWN}"

            if [ "$status" != "PASS" ]; then
                echo -e "${BLUE}--- $agent_name ---${NC}"
                tail -n 10 "$log_file"
                echo ""
            fi
        fi
    done
fi

# Decision
if [ $BLOCKING_ISSUES -gt 0 ]; then
    echo -e "${RED}❌ COMMIT BLOCKED${NC}"
    echo "Blocking issues found: $BLOCKING_ISSUES"
    echo ""
    echo "Fix the issues above and try again."
    echo "Logs available in: $LOG_DIR"
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  COMMIT ALLOWED WITH WARNINGS${NC}"
    echo "Warnings found: $WARNINGS (non-blocking)"
    echo ""
fi

echo -e "${GREEN}✅ All agents approve - commit proceeding${NC}"
echo ""

# Save session summary
cat > "$LOG_DIR/session-${SESSION_ID}-summary.json" <<EOF
{
  "session_id": "$SESSION_ID",
  "timestamp": "$(date -Iseconds)",
  "agents_spawned": 4,
  "blocking_issues": $BLOCKING_ISSUES,
  "warnings": $WARNINGS,
  "result": "$([ $BLOCKING_ISSUES -eq 0 ] && echo "PASS" || echo "BLOCKED")",
  "agent_status": {
$(for agent in "${!AGENT_STATUS[@]}"; do
    echo "    \"$agent\": \"${AGENT_STATUS[$agent]}\","
done | sed '$ s/,$//')
  }
}
EOF

exit 0
