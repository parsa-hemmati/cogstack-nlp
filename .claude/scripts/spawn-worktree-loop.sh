#!/bin/bash

#
# spawn-worktree-loop.sh - Initialize and start autonomous loop in a git worktree
#
# Usage: ./spawn-worktree-loop.sh <module_name> <worktree_path>
# Example: ./spawn-worktree-loop.sh search-module ../epic-search-module
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MODULE_NAME=$1
WORKTREE_PATH=$2

if [ -z "$MODULE_NAME" ] || [ -z "$WORKTREE_PATH" ]; then
    echo -e "${RED}Usage: $0 <module_name> <worktree_path>${NC}"
    echo "Example: $0 search-module ../epic-search-module"
    exit 1
fi

PROJECT_ROOT=$(git rev-parse --show-toplevel)
EPIC_DIR="$PROJECT_ROOT/.claude/ccpm/epics/$MODULE_NAME"
WORKTREE_CONFIG_DIR="$PROJECT_ROOT/.claude/autonomous-worktrees/$MODULE_NAME"

echo -e "${BLUE}🚀 Initializing Autonomous Loop for Worktree${NC}"
echo "=========================================="
echo "Module: $MODULE_NAME"
echo "Worktree: $WORKTREE_PATH"
echo "Epic: $EPIC_DIR"
echo ""

# ============================================================================
# 1. Validate Inputs
# ============================================================================

if [ ! -d "$WORKTREE_PATH" ]; then
    echo -e "${RED}❌ Worktree not found: $WORKTREE_PATH${NC}"
    echo "Create it with: git worktree add $WORKTREE_PATH -b epic/$MODULE_NAME"
    exit 1
fi

if [ ! -d "$EPIC_DIR" ]; then
    echo -e "${RED}❌ Epic not found: $EPIC_DIR${NC}"
    echo "Create it with:"
    echo "  /pm:prd-new $MODULE_NAME"
    echo "  /pm:prd-parse $MODULE_NAME"
    echo "  /pm:epic-decompose $MODULE_NAME"
    exit 1
fi

# ============================================================================
# 2. Create Worktree Configuration Directory
# ============================================================================

echo -e "${YELLOW}📁 Creating worktree configuration...${NC}"
mkdir -p "$WORKTREE_CONFIG_DIR"

# ============================================================================
# 3. Convert Epic Tasks to TASK_QUEUE.md
# ============================================================================

echo -e "${YELLOW}📋 Converting epic tasks to task queue...${NC}"

TASK_QUEUE="$WORKTREE_CONFIG_DIR/TASK_QUEUE.md"

cat > "$TASK_QUEUE" << EOF
# Task Queue: $MODULE_NAME Module

**Module**: $MODULE_NAME
**Worktree**: $WORKTREE_PATH
**Epic**: $EPIC_DIR
**Created**: $(date +%Y-%m-%dT%H:%M:%S%z)
**Status**: INITIALIZED

---

## Task States

- \`[ ]\` - Pending (not started)
- \`[🔄]\` - In Progress (agent working)
- \`[✅]\` - Completed (done)
- \`[❌]\` - Failed (needs retry)
- \`[⏸️]\` - Blocked (waiting on dependency)

---

## Tasks

EOF

# Parse epic task files and convert to task queue format
task_count=0
for task_file in "$EPIC_DIR"/*.md; do
    if [ -f "$task_file" ] && [ "$(basename "$task_file")" != "epic.md" ]; then
        task_num=$(basename "$task_file" .md)

        # Read task title from file
        task_title=$(grep -m 1 "^# " "$task_file" | sed 's/^# //')

        # Read status from frontmatter if exists
        status=$(grep "^status:" "$task_file" | awk '{print $2}' || echo "open")

        # Convert CCPM status to our format
        case "$status" in
            "open")
                task_status="[ ]"
                ;;
            "in-progress")
                task_status="[🔄]"
                ;;
            "completed")
                task_status="[✅]"
                ;;
            *)
                task_status="[ ]"
                ;;
        esac

        # Determine agent type based on task content
        agent_type="developer"  # Default
        if echo "$task_title" | grep -qi "test\|spec"; then
            agent_type="tester"
        elif echo "$task_title" | grep -qi "doc\|guide"; then
            agent_type="documentation"
        elif echo "$task_title" | grep -qi "audit\|compliance\|security"; then
            agent_type="auditor"
        fi

        # Add to task queue
        echo "- [$task_status] #$task_num [$agent_type] $task_title" >> "$TASK_QUEUE"
        task_count=$((task_count + 1))
    fi
done

echo "" >> "$TASK_QUEUE"
echo "---" >> "$TASK_QUEUE"
echo "" >> "$TASK_QUEUE"
echo "**Total Tasks**: $task_count" >> "$TASK_QUEUE"

echo -e "${GREEN}✅ Created task queue with $task_count tasks${NC}"

# ============================================================================
# 4. Create Worktree-Specific Agent Config
# ============================================================================

echo -e "${YELLOW}⚙️ Creating agent configuration...${NC}"

AGENT_CONFIG="$WORKTREE_CONFIG_DIR/agent-config.yaml"

cat > "$AGENT_CONFIG" << 'EOF'
# Agent Configuration for Worktree
# This config is used by agents working in this worktree

agents:
  developer:
    model: sonnet
    max_concurrent: 2
    timeout: 2hours
    skills:
      - infrastructure-expert
      - vue3-component-reuse
      - medcat-architecture

  auditor:
    model: sonnet
    max_concurrent: 1
    timeout: 1hour
    skills:
      - healthcare-compliance-checker
      - prd-compliance-checker

  tester:
    model: haiku
    max_concurrent: 2
    timeout: 1hour
    skills:
      - prd-test-generator

  documentation:
    model: haiku
    max_concurrent: 1
    timeout: 30min
    skills:
      - documentation

coordination:
  delegation_rules:
    - developer → auditor + tester + documentation
    - auditor (if issues) → developer
    - tester (if failures) → debugger
    - documentation (needs examples) → developer

  task_queue: TASK_QUEUE.md
  status_file: loop-status.md
  lock_dir: .locks/
EOF

echo -e "${GREEN}✅ Agent configuration created${NC}"

# ============================================================================
# 5. Create Loop Status File
# ============================================================================

echo -e "${YELLOW}📊 Creating loop status tracker...${NC}"

LOOP_STATUS="$WORKTREE_CONFIG_DIR/loop-status.md"

cat > "$LOOP_STATUS" << EOF
# Autonomous Loop Status: $MODULE_NAME

**Module**: $MODULE_NAME
**Worktree**: $WORKTREE_PATH
**Started**: $(date +%Y-%m-%dT%H:%M:%S%z)
**Status**: INITIALIZED
**PID**: (not started)

---

## Active Agents

(none)

---

## Recent Activity

(no activity yet)

---

## Statistics

- **Tasks Completed**: 0/$task_count
- **Total Commits**: 0
- **Agents Spawned**: 0
- **Delegation Events**: 0

---

## Control

To start the loop:
\`\`\`bash
cd $WORKTREE_PATH
.claude/scripts/worktree-loop-runner.sh $MODULE_NAME &
\`\`\`

To stop the loop:
\`\`\`bash
kill -TERM \$(cat $WORKTREE_CONFIG_DIR/.loop.pid)
\`\`\`

To view status:
\`\`\`bash
cat $LOOP_STATUS
\`\`\`
EOF

echo -e "${GREEN}✅ Loop status tracker created${NC}"

# ============================================================================
# 6. Create Worktree Loop Runner Script
# ============================================================================

echo -e "${YELLOW}🔄 Creating loop runner script...${NC}"

LOOP_RUNNER="$PROJECT_ROOT/.claude/scripts/worktree-loop-runner.sh"

if [ ! -f "$LOOP_RUNNER" ]; then
    cat > "$LOOP_RUNNER" << 'LOOP_RUNNER_EOF'
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
LOOP_RUNNER_EOF

    chmod +x "$LOOP_RUNNER"
    echo -e "${GREEN}✅ Loop runner script created${NC}"
else
    echo -e "${GREEN}✅ Loop runner script already exists${NC}"
fi

# ============================================================================
# 7. Create Lock Directory
# ============================================================================

mkdir -p "$WORKTREE_CONFIG_DIR/.locks"

# ============================================================================
# 8. Summary and Next Steps
# ============================================================================

echo ""
echo -e "${GREEN}✅ Worktree Autonomous Loop Initialized!${NC}"
echo "=========================================="
echo ""
echo "📦 Module: $MODULE_NAME"
echo "📂 Worktree: $WORKTREE_PATH"
echo "📋 Task Queue: $WORKTREE_CONFIG_DIR/TASK_QUEUE.md"
echo "📊 Status: $WORKTREE_CONFIG_DIR/loop-status.md"
echo ""
echo -e "${YELLOW}🎯 Next Steps:${NC}"
echo ""
echo "1. Enter the worktree:"
echo "   cd $WORKTREE_PATH"
echo ""
echo "2. Start the autonomous loop:"
echo "   .claude/scripts/worktree-loop-runner.sh $MODULE_NAME &"
echo ""
echo "3. Monitor status:"
echo "   tail -f $WORKTREE_CONFIG_DIR/loop-status.md"
echo ""
echo "4. From another terminal, view task queue:"
echo "   cat $WORKTREE_CONFIG_DIR/TASK_QUEUE.md"
echo ""
echo "5. Open Claude Code in this worktree to pick up agent tasks"
echo ""
echo -e "${BLUE}💡 The loop will:${NC}"
echo "   • Check for pending tasks every 30 seconds"
echo "   • Prepare agent prompts for task pickup"
echo "   • Continue indefinitely until all tasks complete"
echo "   • Coordinate with other worktrees via main repo"
echo ""
