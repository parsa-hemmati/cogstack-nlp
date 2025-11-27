#!/bin/bash
# Pre-commit hook: Task Completion Validator
# Version: 1.0.0
#
# Ensures agent has completed assigned tasks before allowing commit
#
# Usage: Automatically triggered by git pre-commit hook

set -e

# Configuration
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"
TASK_QUEUE="$CLAUDE_DIR/TASK_QUEUE.md"
AGENT_STATUS="$CLAUDE_DIR/AGENT_STATUS.md"
CONFIG_FILE="$CLAUDE_DIR/agent-loop-config.yaml"

# Determine which agent is committing
# This can be set by the agent wrapper script or detected from environment
CURRENT_AGENT=${CLAUDE_AGENT_TYPE:-"user"}

# Load configuration
load_config() {
    local key=$1
    local default=$2

    if [ ! -f "$CONFIG_FILE" ]; then
        echo "$default"
        return
    fi

    local value=$(grep "^${key}:" "$CONFIG_FILE" | sed 's/^[^:]*:[[:space:]]*//' | tr -d '"' | tr -d "'")

    if [ -z "$value" ]; then
        echo "$default"
    else
        echo "$value"
    fi
}

ENABLED=$(load_config "git_hooks.pre_commit.enabled" "true")
STRICT_MODE=$(load_config "git_hooks.pre_commit.strict_mode" "true")

# Check if hook is enabled
if [ "$ENABLED" != "true" ]; then
    exit 0
fi

# If committing user (not agent), allow
if [ "$CURRENT_AGENT" = "user" ]; then
    # Optional: Check if TASK_QUEUE.md is being modified
    if git diff --cached --name-only | grep -q "TASK_QUEUE.md"; then
        echo "✅ Pre-commit: User modifying TASK_QUEUE.md (allowed)"
    fi
    exit 0
fi

echo "Pre-commit check: Validating task completion for agent '$CURRENT_AGENT'..."

# Check if TASK_QUEUE exists
if [ ! -f "$TASK_QUEUE" ]; then
    echo "⚠️  WARNING: TASK_QUEUE.md not found. Allowing commit."
    exit 0
fi

# Check if agent has in-progress tasks
in_progress_tasks=$(grep -c "^- \[🔄\].*\`\[$CURRENT_AGENT\]\`" "$TASK_QUEUE" 2>/dev/null || echo "0")

if [ "$in_progress_tasks" -gt 0 ]; then
    if [ "$STRICT_MODE" = "true" ]; then
        echo "❌ ERROR: Agent '$CURRENT_AGENT' has $in_progress_tasks in-progress task(s)"
        echo ""
        echo "Incomplete tasks:"
        grep "^- \[🔄\].*\`\[$CURRENT_AGENT\]\`" "$TASK_QUEUE"
        echo ""
        echo "Please:"
        echo "  1. Mark task as complete: Change [🔄] → [✅] in TASK_QUEUE.md"
        echo "  2. OR mark as failed: Change [🔄] → [❌] and add reason"
        echo "  3. Update AGENT_STATUS.md with your current status"
        echo "  4. Try commit again"
        echo ""
        echo "To bypass this check (not recommended):"
        echo "  git commit --no-verify"
        exit 1
    else
        echo "⚠️  WARNING: Agent '$CURRENT_AGENT' has $in_progress_tasks in-progress task(s)"
        echo "Strict mode disabled, allowing commit."
    fi
fi

# Check if TASK_QUEUE.md is being updated
if ! git diff --cached --name-only | grep -q "TASK_QUEUE.md"; then
    echo "⚠️  WARNING: TASK_QUEUE.md not updated in this commit."
    echo "Did you forget to mark your task complete?"
    echo ""
    echo "Press Enter to continue anyway, or Ctrl+C to abort..."
    read -r
fi

# Check if AGENT_STATUS.md is being updated
if ! git diff --cached --name-only | grep -q "AGENT_STATUS.md"; then
    echo "⚠️  WARNING: AGENT_STATUS.md not updated in this commit."
    echo "Did you forget to update your agent status?"
    echo ""
    echo "Press Enter to continue anyway, or Ctrl+C to abort..."
    read -r
fi

echo "✅ Pre-commit check passed for agent '$CURRENT_AGENT'"
exit 0
