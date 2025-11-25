#!/bin/bash
# Add Task Script
# Usage: bash add-task.sh "agent-type" "Task description" "priority"
# Example: bash add-task.sh "developer" "Implement Filter UI" "P1"

set -e

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: bash add-task.sh \"agent-type\" \"Task description\" [priority]"
    echo ""
    echo "Arguments:"
    echo "  agent-type: developer, auditor, tester, debugger, etc."
    echo "  description: Brief task description"
    echo "  priority: P0 (critical), P1 (important), P2 (nice-to-have) [default: P1]"
    echo ""
    echo "Example:"
    echo "  bash add-task.sh \"developer\" \"Implement Filter UI component\" \"P1\""
    exit 1
fi

AGENT_TYPE=$1
DESCRIPTION=$2
PRIORITY=${3:-"P1"}

# Configuration
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
TASK_QUEUE="$PROJECT_ROOT/.claude/TASK_QUEUE.md"

# Validate agent type
VALID_AGENTS="developer auditor tester debugger documentation task-definer architecture-designer test-generator user"

if ! echo "$VALID_AGENTS" | grep -wq "$AGENT_TYPE"; then
    echo "❌ ERROR: Invalid agent type '$AGENT_TYPE'"
    echo "Valid types: $VALID_AGENTS"
    exit 1
fi

# Validate priority
if ! echo "$PRIORITY" | grep -Eq "^P[0-2]$"; then
    echo "❌ ERROR: Invalid priority '$PRIORITY'"
    echo "Valid priorities: P0, P1, P2"
    exit 1
fi

# Check if TASK_QUEUE exists
if [ ! -f "$TASK_QUEUE" ]; then
    echo "❌ ERROR: TASK_QUEUE.md not found at $TASK_QUEUE"
    echo "Initialize autonomous loop first"
    exit 1
fi

# Get next task ID
get_next_task_id() {
    # Find highest existing task ID
    local max_id=$(grep -oP "^- \[[^\]]*\] #\K[0-9]+" "$TASK_QUEUE" 2>/dev/null | sort -n | tail -1)

    if [ -z "$max_id" ]; then
        echo "1"
    else
        echo "$((max_id + 1))"
    fi
}

# Add task atomically
add_task() {
    local agent=$1
    local desc=$2
    local priority=$3

    # Use flock for atomic operation
    (
        flock -x 200

        local task_id=$(get_next_task_id)
        local timestamp=$(date +%H:%M:%S)
        local creator=${CLAUDE_AGENT_TYPE:-"user"}

        # Format task line
        local task_line="- [ ] #$task_id \`[$agent]\` $desc **@$creator** (created: $timestamp)"

        # Find correct section based on priority
        local section_marker
        case "$priority" in
            P0) section_marker="## 🔴 High Priority" ;;
            P1) section_marker="## 🟡 Normal Priority" ;;
            P2) section_marker="## 🟢 Low Priority" ;;
        esac

        # Insert task after section marker
        sed -i "/^$section_marker/a\\
$task_line" "$TASK_QUEUE"

        # Update task count in header
        local pending_count=$(grep -c "^- \[ \]" "$TASK_QUEUE")
        sed -i "s/^\*\*Pending Tasks\*\*: [0-9]*/\*\*Pending Tasks\*\*: $pending_count/" "$TASK_QUEUE"

        # Update timestamp
        sed -i "s/^\*\*Last Updated\*\*: .*/\*\*Last Updated\*\*: $(date -Iseconds)/" "$TASK_QUEUE"

        echo "$task_id"

    ) 200>"$TASK_QUEUE.lock"
}

echo "Adding task to TASK_QUEUE.md..."

TASK_ID=$(add_task "$AGENT_TYPE" "$DESCRIPTION" "$PRIORITY")

echo "✅ Task #$TASK_ID created successfully"
echo ""
echo "Details:"
echo "  ID: #$TASK_ID"
echo "  Agent: $AGENT_TYPE"
echo "  Description: $DESCRIPTION"
echo "  Priority: $PRIORITY"
echo "  Creator: ${CLAUDE_AGENT_TYPE:-user}"
echo ""
echo "To trigger autonomous loop, commit any file:"
echo "  git add .claude/TASK_QUEUE.md"
echo "  git commit -m \"chore: add task #$TASK_ID\""

exit 0
