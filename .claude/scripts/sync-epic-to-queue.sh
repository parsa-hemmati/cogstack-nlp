#!/bin/bash

#
# sync-epic-to-queue.sh - Synchronize CCPM epic tasks to worktree TASK_QUEUE.md
#
# Usage: ./sync-epic-to-queue.sh <module_name>
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

EPIC_DIR="$PROJECT_ROOT/.claude/ccpm/epics/$MODULE_NAME"
WORKTREE_CONFIG_DIR="$PROJECT_ROOT/.claude/autonomous-worktrees/$MODULE_NAME"
TASK_QUEUE="$WORKTREE_CONFIG_DIR/TASK_QUEUE.md"

if [ ! -d "$EPIC_DIR" ]; then
    echo "Epic not found: $EPIC_DIR"
    exit 1
fi

if [ ! -f "$TASK_QUEUE" ]; then
    echo "Task queue not found: $TASK_QUEUE"
    exit 1
fi

# Temporary file
TMP_QUEUE=$(mktemp)

# Copy header from existing queue
sed -n '1,/^## Tasks$/p' "$TASK_QUEUE" > "$TMP_QUEUE"
echo "" >> "$TMP_QUEUE"

# Get existing tasks from queue (to preserve status)
declare -A existing_tasks

while IFS= read -r line; do
    if [[ "$line" =~ ^\-\ \[(.)\]\ \#([0-9]+) ]]; then
        status="${BASH_REMATCH[1]}"
        task_num="${BASH_REMATCH[2]}"
        existing_tasks[$task_num]="$status"
    fi
done < "$TASK_QUEUE"

# Parse epic task files
for task_file in "$EPIC_DIR"/*.md; do
    if [ -f "$task_file" ] && [ "$(basename "$task_file")" != "epic.md" ]; then
        task_num=$(basename "$task_file" .md)

        # Read task title
        task_title=$(grep -m 1 "^# " "$task_file" | sed 's/^# //' || echo "Untitled Task")

        # Check if task already exists in queue (preserve status)
        if [ -n "${existing_tasks[$task_num]}" ]; then
            task_status="${existing_tasks[$task_num]}"
        else
            # New task - check status from epic file
            status=$(grep "^status:" "$task_file" | awk '{print $2}' || echo "open")
            case "$status" in
                "open")
                    task_status=" "
                    ;;
                "in-progress")
                    task_status="🔄"
                    ;;
                "completed")
                    task_status="✅"
                    ;;
                *)
                    task_status=" "
                    ;;
            esac
        fi

        # Determine agent type
        agent_type="developer"
        if echo "$task_title" | grep -qi "test\|spec"; then
            agent_type="tester"
        elif echo "$task_title" | grep -qi "doc\|guide"; then
            agent_type="documentation"
        elif echo "$task_title" | grep -qi "audit\|compliance\|security"; then
            agent_type="auditor"
        fi

        # Add to queue
        echo "- [$task_status] #$task_num [$agent_type] $task_title" >> "$TMP_QUEUE"
    fi
done

# Add footer
echo "" >> "$TMP_QUEUE"
echo "---" >> "$TMP_QUEUE"
echo "" >> "$TMP_QUEUE"

total=$(grep -c "^\- \[" "$TMP_QUEUE" || echo "0")
echo "**Total Tasks**: $total" >> "$TMP_QUEUE"
echo "**Last Synced**: $(date +%Y-%m-%dT%H:%M:%S%z)" >> "$TMP_QUEUE"

# Replace queue file
mv "$TMP_QUEUE" "$TASK_QUEUE"

echo "Synced $total tasks from epic to queue"
