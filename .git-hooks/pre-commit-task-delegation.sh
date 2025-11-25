#!/bin/bash
#
# Pre-commit hook to enforce task delegation between agents
#
# Purpose: Create a never-ending autonomous loop where agents create tasks for each other
#
# Rules:
# 1. Developer completes task → MUST create auditor + tester tasks
# 2. Auditor finds issues → MUST create developer task to fix
# 3. Tester finds failures → MUST create developer task to debug
# 4. Documentation updates → MUST create developer task for code examples
#
# To install:
#   ln -sf ../../.git-hooks/pre-commit-task-delegation.sh .git/hooks/pre-commit-task-delegation
#

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TASK_QUEUE=".claude/TASK_QUEUE.md"

echo -e "${BLUE}🔄 Checking task delegation...${NC}"

# Skip if no TASK_QUEUE exists
if [ ! -f "$TASK_QUEUE" ]; then
    echo -e "${YELLOW}⚠️  TASK_QUEUE.md not found - skipping delegation check${NC}"
    exit 0
fi

# Check if TASK_QUEUE.md was modified in this commit
task_queue_modified=$(git diff --cached --name-only | grep "^.claude/TASK_QUEUE.md$" || true)

if [ -z "$task_queue_modified" ]; then
    echo -e "${YELLOW}⚠️  TASK_QUEUE.md not modified - no delegation to check${NC}"
    exit 0
fi

# Get the diff to see what changed
task_diff=$(git diff --cached .claude/TASK_QUEUE.md)

# Count completed tasks (marked with ✅ in this commit)
completed_count=$(echo "$task_diff" | grep "^+.*\[✅\]" | wc -l || echo "0")

# Count new pending tasks (added with [ ] in this commit)
new_tasks_count=$(echo "$task_diff" | grep "^+.*\[ \]" | wc -l || echo "0")

echo ""
echo "📊 Task Delegation Summary:"
echo "  ✅ Tasks completed: $completed_count"
echo "  📝 New tasks created: $new_tasks_count"
echo ""

# If tasks were completed, check if delegation happened
if [ "$completed_count" -gt 0 ]; then
    # Extract agent types from completed tasks
    completed_agents=$(echo "$task_diff" | grep "^+.*\[✅\]" | grep -oP '\[\K[^\]]+(?=\])' | sort -u || true)

    # Check delegation rules
    delegation_ok=true

    # Rule 1: Developer completes task → must create auditor OR tester tasks
    if echo "$completed_agents" | grep -q "developer"; then
        if [ "$new_tasks_count" -eq 0 ]; then
            echo -e "${RED}❌ DELEGATION REQUIRED: Developer completed task(s) but created NO follow-up tasks!${NC}"
            echo ""
            echo "Developer must create tasks for:"
            echo "  • [auditor] - Review changes for HIPAA/GDPR compliance"
            echo "  • [tester] - Run tests and validate coverage"
            echo "  • [documentation] - Update docs (if API/schema changed)"
            echo ""
            delegation_ok=false
        else
            # Check if at least one auditor or tester task was created
            new_task_agents=$(echo "$task_diff" | grep "^+.*\[ \]" | grep -oP '\[\K[^\]]+(?=\])' | sort -u || true)

            if ! echo "$new_task_agents" | grep -qE "(auditor|tester)"; then
                echo -e "${YELLOW}⚠️  WARNING: Developer completed task but didn't create auditor/tester tasks${NC}"
                echo ""
                echo "Consider creating:"
                echo "  • [auditor] - Review changes for compliance"
                echo "  • [tester] - Validate test coverage"
                echo ""
                echo -n "Continue anyway? [y/N] "
                read -r response
                if [[ ! "$response" =~ ^[Yy]$ ]]; then
                    echo -e "${RED}❌ Commit aborted${NC}"
                    exit 1
                fi
            fi
        fi
    fi

    # Rule 2: Auditor finds issues → must create developer task
    if echo "$completed_agents" | grep -q "auditor"; then
        # Check if auditor created developer tasks for fixes
        new_developer_tasks=$(echo "$task_diff" | grep "^+.*\[ \].*\[developer\]" | wc -l || echo "0")

        if [ "$new_developer_tasks" -eq 0 ]; then
            echo -e "${YELLOW}⚠️  INFO: Auditor completed review without creating developer fix tasks${NC}"
            echo "This is OK if no issues were found."
            echo ""
        fi
    fi

    # Rule 3: Tester finds failures → must create developer task
    if echo "$completed_agents" | grep -q "tester"; then
        # Check if tester created developer tasks for fixes
        new_developer_tasks=$(echo "$task_diff" | grep "^+.*\[ \].*\[developer\]" | wc -l || echo "0")

        if [ "$new_developer_tasks" -eq 0 ]; then
            echo -e "${YELLOW}⚠️  INFO: Tester completed testing without creating developer fix tasks${NC}"
            echo "This is OK if all tests passed."
            echo ""
        fi
    fi

    if [ "$delegation_ok" = false ]; then
        echo ""
        echo -e "${RED}❌ BLOCKING: Task delegation rules violated!${NC}"
        echo ""
        echo "To fix:"
        echo "  1. Add tasks to TASK_QUEUE.md using:"
        echo "     bash .claude/scripts/add-task.sh \"agent-type\" \"Task description\" \"P1\""
        echo ""
        echo "  2. Stage the updated TASK_QUEUE.md:"
        echo "     git add .claude/TASK_QUEUE.md"
        echo ""
        echo "  3. Retry commit"
        echo ""
        exit 1
    fi
fi

# Success
echo -e "${GREEN}✅ Task delegation check passed!${NC}"
echo ""

# Show the autonomous loop in action
if [ "$new_tasks_count" -gt 0 ]; then
    echo -e "${BLUE}🔄 Autonomous Loop Active:${NC}"
    echo "  → $completed_count task(s) completed"
    echo "  → $new_tasks_count new task(s) created"
    echo "  → Post-commit hook will spawn agents for pending tasks"
    echo ""
fi

exit 0
