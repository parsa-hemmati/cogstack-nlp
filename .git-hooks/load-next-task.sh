#!/bin/bash
#
# LOAD NEXT TASK - Auto-load next task after current completes
# Triggered by: post-commit hook when AUDIT.md shows ✅ CLEAR
# Purpose: Read next task from .specify/tasks/ and create prompt for development agent
#
# Flow:
#   1. Current task complete + AUDIT.md shows ✅ CLEAR
#   2. Post-commit hook calls this script
#   3. Find next pending task
#   4. Create prompt for development agent
#   5. Development agent implements next task
#   6. Cycle repeats (build → audit → test → next)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   LOAD NEXT TASK: Finding next task from specification${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# ============================================================================
# STEP 1: Check if auto-load is enabled
# ============================================================================

AUTONOMOUS_CONFIG=".claude/autonomous-config.yaml"
AUTO_LOAD=false

if [ -f "$AUTONOMOUS_CONFIG" ]; then
    AUTO_LOAD=$(grep "auto_load_next:" "$AUTONOMOUS_CONFIG" | awk '{print $2}')
fi

if [ "$AUTO_LOAD" != "true" ]; then
    echo -e "${YELLOW}⏸️  Auto-load disabled in $AUTONOMOUS_CONFIG${NC}"
    echo -e "${YELLOW}   Skipping next task load${NC}"
    echo ""
    exit 0
fi

# ============================================================================
# STEP 2: Find task files
# ============================================================================

TASKS_DIR=".specify/tasks"

if [ ! -d "$TASKS_DIR" ]; then
    echo -e "${YELLOW}⚠️  Tasks directory not found: $TASKS_DIR${NC}"
    echo -e "${YELLOW}   No tasks to load${NC}"
    echo ""
    exit 0
fi

# Find all task files
TASK_FILES=$(find "$TASKS_DIR" -name "*.md" -type f | sort)

if [ -z "$TASK_FILES" ]; then
    echo -e "${YELLOW}⚠️  No task files found in $TASKS_DIR${NC}"
    echo ""
    exit 0
fi

echo -e "${BLUE}📁 Found task files:${NC}"
echo "$TASK_FILES" | sed 's/^/  /'
echo ""

# ============================================================================
# STEP 3: Read CONTEXT.md to find current progress
# ============================================================================

if [ ! -f "CONTEXT.md" ]; then
    echo -e "${YELLOW}⚠️  CONTEXT.md not found${NC}"
    echo -e "${YELLOW}   Cannot determine current task${NC}"
    echo ""
    exit 0
fi

# Extract current phase/task from CONTEXT.md
# Look for "Task X.Y: " pattern in recent changes
CURRENT_TASK=$(grep -E "Task [0-9]+\.[0-9]+" CONTEXT.md | head -1 | grep -oE "Task [0-9]+\.[0-9]+" || echo "")

if [ -z "$CURRENT_TASK" ]; then
    echo -e "${YELLOW}⚠️  Could not determine current task from CONTEXT.md${NC}"
    echo -e "${YELLOW}   Using first task in specification${NC}"
    echo ""
    CURRENT_TASK="Task 0.0"
fi

echo -e "${GREEN}✅ Current task: $CURRENT_TASK${NC}"
echo ""

# ============================================================================
# STEP 4: Find next pending task
# ============================================================================

# Extract task number (e.g., "Task 4.3" → "4.3")
CURRENT_NUM=$(echo "$CURRENT_TASK" | grep -oE "[0-9]+\.[0-9]+")

# Find next task file
NEXT_TASK_FILE=""

for task_file in $TASK_FILES; do
    # Extract task number from filename (e.g., "phase-4-tasks.md" or "task-4.5.md")
    TASK_NUM=$(basename "$task_file" | grep -oE "[0-9]+\.[0-9]+" || echo "")

    if [ -n "$TASK_NUM" ]; then
        # Compare task numbers (simple string comparison works for X.Y format)
        if [[ "$TASK_NUM" > "$CURRENT_NUM" ]]; then
            NEXT_TASK_FILE="$task_file"
            break
        fi
    fi
done

if [ -z "$NEXT_TASK_FILE" ]; then
    echo -e "${GREEN}🎉 No more tasks found${NC}"
    echo -e "${GREEN}   All tasks in specification complete!${NC}"
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────${NC}"
    echo -e "${BLUE}   🎊 AUTONOMOUS CYCLE COMPLETE 🎊${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────${NC}"
    echo ""

    # Log completion
    LOG_FILE=".git-hooks/autonomous.log"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [LOAD-NEXT-TASK] Status: ALL_COMPLETE" >> "$LOG_FILE"

    exit 0
fi

echo -e "${GREEN}✅ Next task file: $NEXT_TASK_FILE${NC}"
echo ""

# ============================================================================
# STEP 5: Read next task specification
# ============================================================================

NEXT_TASK_CONTENT=$(cat "$NEXT_TASK_FILE")

echo -e "${BLUE}📖 Next task preview:${NC}"
head -20 "$NEXT_TASK_FILE" | sed 's/^/  /'
echo "  ..."
echo ""

# ============================================================================
# STEP 6: Create development agent prompt
# ============================================================================

echo -e "${BLUE}📝 Creating development agent prompt for next task...${NC}"
echo ""

DEV_AGENT_PROMPT="# Development Agent - Next Task

**Trigger**: Previous task complete, AUDIT.md shows ✅ CLEAR
**Current Task**: $CURRENT_TASK (COMPLETED)
**Next Task**: $(basename "$NEXT_TASK_FILE" .md)

## Your Task

Implement the next task from the specification.

## Task Specification

File: $NEXT_TASK_FILE

\`\`\`markdown
$NEXT_TASK_CONTENT
\`\`\`

## Workflow

Follow the standard development workflow:

1. **READ** the task specification completely
2. **PLAN** implementation steps (use TodoWrite if complex)
3. **IMPLEMENT** the task:
   - Write code following patterns from existing codebase
   - Follow PRD specifications exactly
   - Use existing components/services where possible
4. **TEST** the implementation:
   - Write unit tests
   - Write integration tests (if API changes)
   - Write security tests (if PHI-related)
5. **UPDATE** documentation:
   - Update CONTEXT.md with \"Recent Changes\" entry
   - Stage CONTEXT.md for commit
   - AUDIT.md will be updated by auditor post-commit
6. **COMMIT** with comprehensive message:
   - Format: <type>(<scope>): <short summary>
   - Include: Changes, Rationale, Tests, CONTEXT.md Updates
   - Stage all changes: git add .
   - Commit: git commit -m \"...\"

## Post-Commit Flow

After you commit:
1. **Post-commit hook** will spawn auditor agent
2. **Auditor** will check PRD compliance and update AUDIT.md
3. **If AUDIT.md shows blocking issues**:
   - Pre-commit hook will trigger development agent to auto-fix
   - Development agent will fix and re-commit
   - Post-commit hook will re-run auditor
   - Cycle repeats until AUDIT.md shows ✅ CLEAR
4. **Once AUDIT.md shows ✅ CLEAR**:
   - This script will load next task
   - You'll be prompted to implement next task
   - Cycle continues

## Important Notes

- **Follow Spec-Kit workflow**: Spec → Plan → Tasks → Code
- **Update CONTEXT.md**: MANDATORY before commit
- **Don't update AUDIT.md manually**: Auditor updates it automatically
- **Test thoroughly**: All tests must pass before commit
- **HIPAA compliance**: Use healthcare-compliance-checker skill if PHI-related

## Context

- **Current Phase**: Phase 4 (Patient Search)
- **Recent Commits**: $(git log --oneline -3)
- **Branch**: $(git branch --show-current)
- **PRD Specifications**: .specify/specifications/*.md

Begin implementing next task now."

# Save prompt
PROMPT_FILE=".git-hooks/tmp/next-task-prompt-$(date +%s).txt"
mkdir -p .git-hooks/tmp
echo "$DEV_AGENT_PROMPT" > "$PROMPT_FILE"

echo -e "${GREEN}✅ Next task prompt saved to: $PROMPT_FILE${NC}"
echo ""

# ============================================================================
# STEP 7: Present to user or spawn agent
# ============================================================================

echo -e "${YELLOW}⚠️  MANUAL STEP REQUIRED:${NC}"
echo ""
echo "Next task is ready to implement:"
echo "  Task: $(basename "$NEXT_TASK_FILE" .md)"
echo "  Prompt: $PROMPT_FILE"
echo ""
echo "To continue autonomous development:"
echo "  1. Copy prompt from: $PROMPT_FILE"
echo "  2. Paste into Claude Code session"
echo "  3. Agent will implement task"
echo "  4. Cycle continues automatically"
echo ""
echo "Or pause autonomous mode:"
echo "  1. Edit .claude/autonomous-config.yaml"
echo "  2. Set: tasks.auto_load_next: false"
echo ""

# Future: Auto-spawn agent
# claude-code agent spawn --prompt-file "$PROMPT_FILE" --background

# Log event
LOG_FILE=".git-hooks/autonomous.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') [LOAD-NEXT-TASK] Next: $(basename "$NEXT_TASK_FILE" .md) | Prompt: $PROMPT_FILE" >> "$LOG_FILE"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

exit 0
