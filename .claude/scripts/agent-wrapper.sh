#!/bin/bash
# Agent Wrapper Script
# Spawns and monitors Claude Code agents with proper environment
#
# Usage: agent-wrapper.sh <agent-type> <task-id> <timeout> <prompt-file>
# Example: agent-wrapper.sh "developer" "10" "3600" "/tmp/prompt.txt"

set -e

# Arguments
AGENT_TYPE=$1
TASK_ID=$2
TIMEOUT=$3
PROMPT_FILE=$4

# Validate arguments
if [ -z "$AGENT_TYPE" ] || [ -z "$TASK_ID" ] || [ -z "$TIMEOUT" ] || [ -z "$PROMPT_FILE" ]; then
    echo "Usage: agent-wrapper.sh <agent-type> <task-id> <timeout> <prompt-file>"
    exit 1
fi

# Configuration
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"
AGENT_STATUS="$CLAUDE_DIR/AGENT_STATUS.md"
TASK_QUEUE="$CLAUDE_DIR/TASK_QUEUE.md"
AGENT_LOG="$CLAUDE_DIR/logs/agent-${AGENT_TYPE}-${TASK_ID}.log"
PID_FILE="$CLAUDE_DIR/logs/agent-${AGENT_TYPE}-${TASK_ID}.pid"

# Store own PID
echo $$ > "$PID_FILE"

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date -Iseconds)
    echo "[$timestamp] [$level] $message" >> "$AGENT_LOG"
}

log "INFO" "========================================"
log "INFO" "Agent wrapper starting"
log "INFO" "Agent Type: $AGENT_TYPE"
log "INFO" "Task ID: $TASK_ID"
log "INFO" "Timeout: $TIMEOUT seconds"
log "INFO" "PID: $$"
log "INFO" "========================================"

# Update agent status to WORKING
update_agent_status() {
    local status=$1
    local progress=$2

    local timestamp=$(date +%H:%M:%S)

    # Simple status update (simplified - full implementation would be more robust)
    (
        flock -x 200
        # This is a placeholder - full implementation would properly update AGENT_STATUS.md
        log "DEBUG" "Status update: $status ($progress)"
    ) 200>"$AGENT_STATUS.lock"
}

# Timeout monitoring (background process)
(
    sleep "$TIMEOUT"

    # Check if agent still running
    if ps -p $$ > /dev/null 2>&1; then
        log "ERROR" "⚠️ TIMEOUT: Agent exceeded $TIMEOUT seconds"

        # Kill agent
        kill -9 $$ 2>/dev/null || true

        # Mark task as failed
        (
            flock -x 200
            sed -i "s/^- \[🔄\] #$TASK_ID/- [❌] #$TASK_ID (timeout: ${TIMEOUT}s)/" "$TASK_QUEUE"
        ) 200>"$TASK_QUEUE.lock"

        log "ERROR" "Agent killed due to timeout"
    fi
) &

TIMEOUT_PID=$!
log "INFO" "Timeout monitor spawned (PID: $TIMEOUT_PID)"

# Error handler
handle_error() {
    local exit_code=$?

    if [ $exit_code -ne 0 ]; then
        log "ERROR" "🔴 CRASH: Agent exited with code $exit_code"

        # Mark task as failed
        (
            flock -x 200
            sed -i "s/^- \[🔄\] #$TASK_ID/- [❌] #$TASK_ID (crashed: exit $exit_code)/" "$TASK_QUEUE"
        ) 200>"$TASK_QUEUE.lock"

        # Update agent status to FAILED
        update_agent_status "FAILED" "crashed"

        # Kill timeout monitor
        kill $TIMEOUT_PID 2>/dev/null || true
    fi
}

trap 'handle_error' EXIT

# Set environment variables for agent
export CLAUDE_AGENT_TYPE="$AGENT_TYPE"
export CLAUDE_TASK_ID="$TASK_ID"
export CLAUDE_PROJECT_ROOT="$PROJECT_ROOT"
export CLAUDE_LOG_FILE="$AGENT_LOG"

# Update status to WORKING
update_agent_status "WORKING" "0%"

log "INFO" "Starting agent execution..."
log "INFO" "Prompt file: $PROMPT_FILE"

# ============================================================================
# ACTUAL AGENT EXECUTION
# ============================================================================
# This is where the actual Claude Code agent would be invoked
# For now, this is a placeholder that simulates agent work

log "INFO" "Reading prompt..."
PROMPT=$(cat "$PROMPT_FILE")

log "INFO" "Prompt length: ${#PROMPT} characters"

# TODO: Replace this section with actual Claude Code agent invocation
# Example (when integrated with Claude Code):
#   claude-code agent \
#     --type "$AGENT_TYPE" \
#     --task-id "$TASK_ID" \
#     --prompt-file "$PROMPT_FILE" \
#     --log-file "$AGENT_LOG" \
#     --project-root "$PROJECT_ROOT"

# SIMULATION (Remove in production):
log "INFO" "SIMULATION: Agent would execute here"
log "INFO" "SIMULATION: Reading task from TASK_QUEUE.md"
log "INFO" "SIMULATION: Reading messages from COORDINATION.md"
log "INFO" "SIMULATION: Executing task..."

# Simulate work with progress updates
for i in {1..5}; do
    progress=$((i * 20))
    update_agent_status "WORKING" "${progress}%"
    log "INFO" "SIMULATION: Progress ${progress}%"
    sleep 2
done

log "INFO" "SIMULATION: Task complete"

# Simulate updating shared files
log "INFO" "SIMULATION: Updating TASK_QUEUE.md (marking task complete)"
log "INFO" "SIMULATION: Updating AGENT_STATUS.md (status = IDLE)"
log "INFO" "SIMULATION: Updating COORDINATION.md (adding messages)"
log "INFO" "SIMULATION: Creating follow-up tasks"

# END SIMULATION
# ============================================================================

log "INFO" "Agent execution complete"

# Kill timeout monitor (agent completed successfully)
kill $TIMEOUT_PID 2>/dev/null || true

# Update status to IDLE
update_agent_status "IDLE" "100%"

log "INFO" "========================================"
log "INFO" "Agent wrapper complete"
log "INFO" "========================================"

# Remove PID file
rm -f "$PID_FILE"

exit 0
