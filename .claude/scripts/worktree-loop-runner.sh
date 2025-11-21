#!/bin/bash

#
# worktree-loop-runner.sh - Autonomous loop that runs in a worktree
#
# Usage: cd <worktree> && .claude/scripts/worktree-loop-runner.sh <module_name> &
#

set -e

MODULE_NAME=$1

if [ -z "$MODULE_NAME" ]; then
    echo "Usage: $0 <module_name>"
    exit 1
fi

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$PROJECT_ROOT" ]; then
    # We're in a worktree, find main repo
    MAIN_WORKTREE=$(git rev-parse --path-format=absolute --git-common-dir | sed 's|/.git/worktrees/.*|/.git|' | sed 's|/.git||')
    PROJECT_ROOT="$MAIN_WORKTREE"
fi

WORKTREE_CONFIG_DIR="$PROJECT_ROOT/.claude/autonomous-worktrees/$MODULE_NAME"
TASK_QUEUE="$WORKTREE_CONFIG_DIR/TASK_QUEUE.md"
LOOP_STATUS="$WORKTREE_CONFIG_DIR/loop-status.md"
PID_FILE="$WORKTREE_CONFIG_DIR/.loop.pid"

# Save PID
echo $$ > "$PID_FILE"

# Update status
sed -i "s/^\\*\\*Status\\*\\*:.*/\\*\\*Status\\*\\*: RUNNING/" "$LOOP_STATUS"
sed -i "s/^\\*\\*PID\\*\\*:.*/\\*\\*PID\\*\\*: $$/" "$LOOP_STATUS"

echo "[$(date +%Y-%m-%dT%H:%M:%S)] Loop started with PID $$"

# Trap to handle shutdown
cleanup() {
    echo "[$(date +%Y-%m-%dT%H:%M:%S)] Loop stopping..."
    sed -i "s/^\\*\\*Status\\*\\*:.*/\\*\\*Status\\*\\*: STOPPED/" "$LOOP_STATUS"
    rm -f "$PID_FILE"
    exit 0
}
trap cleanup SIGTERM SIGINT

# Main loop
iteration=0
while true; do
    iteration=$((iteration + 1))

    # Check for pending tasks
    pending=$(grep -c "^\- \[ \]" "$TASK_QUEUE" || echo "0")

    if [ "$pending" -gt 0 ]; then
        echo "[$(date +%Y-%m-%dT%H:%M:%S)] Found $pending pending task(s)"

        # Get first pending task
        task_line=$(grep "^\- \[ \]" "$TASK_QUEUE" | head -1)
        task_id=$(echo "$task_line" | grep -oP '#\d+' | sed 's/#//')
        agent_type=$(echo "$task_line" | grep -oP '\[\w+\]' | tr -d '[]')

        echo "[$(date +%Y-%m-%dT%H:%M:%S)] Preparing to spawn $agent_type for task #$task_id"

        # Prepare agent prompt (for manual pickup or future API spawning)
        "$PROJECT_ROOT/.claude/scripts/agent-wrapper.sh" \
            --task-id "$task_id" \
            --agent-type "$agent_type" \
            --worktree "$(pwd)"

        # In CCWeb: Agent prompt is prepared, waiting for pickup
        # In future: CCWeb API would spawn agent here

        # For now, log the waiting state
        echo "[$(date +%Y-%m-%dT%H:%M:%S)] Agent prompt prepared for task #$task_id, waiting for pickup..."

    else
        echo "[$(date +%Y-%m-%dT%H:%M:%S)] No pending tasks (iteration $iteration)"

        # Check if new tasks available from epic
        "$PROJECT_ROOT/.claude/scripts/sync-epic-to-queue.sh" "$MODULE_NAME"
    fi

    # Loop delay (prevent CPU spinning)
    sleep 30
done
