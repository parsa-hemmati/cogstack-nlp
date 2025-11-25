#!/bin/bash
#
# DEVELOPMENT AGENT - Auto-fix blocking issues from AUDIT.md
# Triggered by: pre-commit hook when AUDIT.md shows blocking issues
# Purpose: Read todos from AUDIT.md and spawn agent to fix them
#
# Flow:
#   1. Pre-commit hook detects AUDIT.md has blocking issues
#   2. This script runs
#   3. Extract todos from AUDIT.md
#   4. Spawn development agent with todo list
#   5. Agent fixes issues and stages files
#   6. Script exits with success (pre-commit continues)
#   7. Commit proceeds with fixes
#   8. Post-commit hook spawns auditor to verify

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   DEVELOPMENT AGENT: Auto-fixing AUDIT.md Blocking Todos${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# ============================================================================
# STEP 1: Extract blocking todos from AUDIT.md
# ============================================================================

if [ ! -f "AUDIT.md" ]; then
    echo -e "${RED}❌ ERROR: AUDIT.md not found${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Extracting blocking todos from AUDIT.md...${NC}"
echo ""

# Extract todos section
TODOS=$(sed -n '/#### Blocking Todos/,/^---$/p' AUDIT.md | grep '^- \[ \]' || echo "")

if [ -z "$TODOS" ]; then
    echo -e "${YELLOW}⚠️  No blocking todos found in AUDIT.md${NC}"
    echo -e "${YELLOW}   (AUDIT.md may show blocking status but no actionable todos)${NC}"
    echo ""
    exit 1
fi

echo -e "${YELLOW}Found blocking todos:${NC}"
echo "$TODOS"
echo ""

# Count todos
TODO_COUNT=$(echo "$TODOS" | wc -l)
echo -e "${BLUE}📊 Total blocking todos: $TODO_COUNT${NC}"
echo ""

# ============================================================================
# STEP 2: Check retry count (prevent infinite loops)
# ============================================================================

RETRY_LOG=".git-hooks/tmp/auto-fix-retries.log"
mkdir -p .git-hooks/tmp

# Get current retry count for these specific todos
TODO_HASH=$(echo "$TODOS" | md5sum | awk '{print $1}')
RETRY_COUNT=$(grep "^$TODO_HASH" "$RETRY_LOG" 2>/dev/null | wc -l || echo "0")

# Max retries from config
MAX_RETRIES=3
AUTONOMOUS_CONFIG=".claude/autonomous-config.yaml"
if [ -f "$AUTONOMOUS_CONFIG" ]; then
    MAX_RETRIES=$(grep "max_retries_per_issue:" "$AUTONOMOUS_CONFIG" | awk '{print $2}' || echo "3")
fi

echo -e "${BLUE}🔄 Retry count: $RETRY_COUNT / $MAX_RETRIES${NC}"
echo ""

if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
    echo -e "${RED}❌ MAX RETRIES EXCEEDED ($MAX_RETRIES attempts)${NC}"
    echo -e "${RED}   These issues could not be auto-fixed${NC}"
    echo ""
    echo -e "${YELLOW}Blocking todos (manual fix required):${NC}"
    echo "$TODOS"
    echo ""
    echo -e "${RED}⚠️  Manual intervention required${NC}"
    echo ""
    exit 1
fi

# Log this retry attempt
echo "$TODO_HASH $(date '+%Y-%m-%d %H:%M:%S')" >> "$RETRY_LOG"

# ============================================================================
# STEP 3: Create development agent prompt
# ============================================================================

echo -e "${BLUE}📝 Creating development agent prompt...${NC}"
echo ""

DEV_AGENT_PROMPT="# Development Agent - Auto-fix Blocking Issues

**Trigger**: Pre-commit hook detected blocking issues in AUDIT.md
**Retry**: Attempt $((RETRY_COUNT + 1)) / $MAX_RETRIES

## Your Task

You are a **development agent** triggered automatically to fix blocking issues. Your job is:

1. **Read the blocking todos** from AUDIT.md (listed below)
2. **Fix each issue** by editing code files
3. **Stage the fixes** (git add .)
4. **Update AUDIT.md** to mark todos as completed
5. **Exit** (pre-commit will continue and commit your fixes)

## Blocking Todos from AUDIT.md

\`\`\`
$TODOS
\`\`\`

## How to Fix Each Todo

For each todo:

1. **Read the file** mentioned in the todo
2. **Identify the issue** (Expected vs Actual)
3. **Apply the fix** using Edit tool
4. **Verify the fix** (read file again to confirm)
5. **Stage the file** (git add <file>)

## Example Fix

Todo:
\`\`\`
- [ ] **TODO-1**: Field name mismatch: response.total should be response.pagination.totalResults
  - **File**: backend/app/schemas/patient_search.py:45
  - **Expected**: pagination.totalResults (nested object, PRD spec)
  - **Actual**: total (flat field)
  - **Fix**: Create PaginationInfo schema with totalResults field, update response
\`\`\`

Fix Steps:
\`\`\`python
# 1. Read file
Read: backend/app/schemas/patient_search.py

# 2. Identify issue
# Line 45: total: int  # Wrong: flat field

# 3. Apply fix
Edit:
  old_string: 'total: int'
  new_string: 'pagination: PaginationInfo'

# 4. Stage file
git add backend/app/schemas/patient_search.py

# 5. Mark todo as done in AUDIT.md
Edit AUDIT.md:
  old_string: '- [ ] **TODO-1**: Field name mismatch...'
  new_string: '- [x] **TODO-1**: Field name mismatch... ✅ FIXED'
\`\`\`

## Important Rules

1. **Fix all todos** (don't skip any)
2. **Stage all changes** (git add .)
3. **Update AUDIT.md** to mark todos as completed
4. **Don't commit** (pre-commit hook will do that)
5. **Exit cleanly** (exit 0 = success, exit 1 = failure)

## Exit Behavior

After fixing all todos:

1. **If all fixed successfully**:
   - Update AUDIT.md: Change '🚨 BLOCKING' to '✅ CLEAR'
   - Mark all todos as [x] completed
   - Stage AUDIT.md
   - Exit 0

2. **If some issues can't be fixed**:
   - Update AUDIT.md: Add notes about what failed
   - Leave failed todos as [ ] uncompleted
   - Exit 1 (will retry on next commit attempt)

## Context

- **PRD Specifications**: .specify/specifications/*.md
- **Current commit status**: $(git status --short)
- **Recent commits**: $(git log --oneline -5)

Begin fixing now."

# Save prompt
PROMPT_FILE=".git-hooks/tmp/dev-agent-prompt-$(date +%s).txt"
echo "$DEV_AGENT_PROMPT" > "$PROMPT_FILE"

echo -e "${GREEN}✅ Development agent prompt saved to: $PROMPT_FILE${NC}"
echo ""

# ============================================================================
# STEP 4: Spawn development agent
# ============================================================================

echo -e "${BLUE}🚀 Spawning development agent...${NC}"
echo ""

# NOTE: In actual implementation, this would spawn Claude Code agent
# For now, we provide instructions for manual execution

echo -e "${YELLOW}⚠️  MANUAL STEP REQUIRED:${NC}"
echo ""
echo "To auto-fix blocking issues:"
echo "  1. Copy the prompt from: $PROMPT_FILE"
echo "  2. Paste into Claude Code session"
echo "  3. Agent will fix issues and stage files"
echo "  4. Retry commit (will succeed after fixes)"
echo ""
echo "Or wait for future automation (Claude Code CLI integration)"
echo ""

# Future: Integrate with Claude Code CLI/API when available
# claude-code agent spawn --prompt-file "$PROMPT_FILE" --wait
# EXIT_CODE=$?
# exit $EXIT_CODE

# For now, exit with error (requires manual fix)
echo -e "${RED}❌ Autonomous agent spawn not yet implemented${NC}"
echo -e "${RED}   Manual fix required (see prompt above)${NC}"
echo ""

# Log event
LOG_FILE=".git-hooks/autonomous.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') [DEV-AGENT] Todos: $TODO_COUNT | Retry: $((RETRY_COUNT + 1))/$MAX_RETRIES | Status: MANUAL_FIX_REQUIRED" >> "$LOG_FILE"

exit 1  # Exit with error (agent not fully autonomous yet)
