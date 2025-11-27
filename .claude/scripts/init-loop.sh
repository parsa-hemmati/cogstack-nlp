#!/bin/bash
# Initialize Autonomous Agent Loop
# Sets up git hooks, creates directories, and initializes state files

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  AUTONOMOUS AGENT LOOP - INITIALIZATION                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Get project root
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "📂 Project root: $PROJECT_ROOT"
echo ""

# Step 1: Create directories
echo "1️⃣  Creating directories..."
mkdir -p "$CLAUDE_DIR/logs"
mkdir -p "$CLAUDE_DIR/metrics"
mkdir -p "$CLAUDE_DIR/scripts"
echo "   ✅ Directories created"
echo ""

# Step 2: Link git hooks
echo "2️⃣  Linking git hooks..."

# Create symlinks to custom hooks
if [ ! -f "$GIT_HOOKS_DIR/post-commit" ]; then
    ln -s "../../.git-hooks/post-commit-agent-loop.sh" "$GIT_HOOKS_DIR/post-commit"
    echo "   ✅ post-commit hook linked"
else
    echo "   ⚠️  post-commit hook already exists, skipping"
fi

if [ ! -f "$GIT_HOOKS_DIR/pre-commit" ]; then
    ln -s "../../.git-hooks/pre-commit-task-check.sh" "$GIT_HOOKS_DIR/pre-commit"
    echo "   ✅ pre-commit hook linked"
else
    echo "   ⚠️  pre-commit hook already exists, skipping"
fi

# Make hooks executable
chmod +x "$PROJECT_ROOT/.git-hooks/post-commit-agent-loop.sh"
chmod +x "$PROJECT_ROOT/.git-hooks/pre-commit-task-check.sh"
echo "   ✅ Hooks made executable"
echo ""

# Step 3: Make scripts executable
echo "3️⃣  Making scripts executable..."
chmod +x "$CLAUDE_DIR/scripts/add-task.sh"
chmod +x "$CLAUDE_DIR/scripts/monitor-loop.sh"
chmod +x "$CLAUDE_DIR/scripts/agent-wrapper.sh"
chmod +x "$CLAUDE_DIR/scripts/init-loop.sh"
echo "   ✅ Scripts made executable"
echo ""

# Step 4: Verify state files exist
echo "4️⃣  Verifying state files..."

FILES_TO_CHECK=(
    "$CLAUDE_DIR/TASK_QUEUE.md"
    "$CLAUDE_DIR/AGENT_STATUS.md"
    "$CLAUDE_DIR/COORDINATION.md"
    "$CLAUDE_DIR/agent-loop-config.yaml"
)

all_exist=true
for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $(basename "$file") exists"
    else
        echo "   ❌ $(basename "$file") missing"
        all_exist=false
    fi
done

if [ "$all_exist" = false ]; then
    echo ""
    echo "⚠️  Some state files are missing. They should have been created during setup."
    echo "Please ensure the following files exist:"
    for file in "${FILES_TO_CHECK[@]}"; do
        echo "  - $file"
    done
    exit 1
fi
echo ""

# Step 5: Create initial log file
echo "5️⃣  Initializing log file..."
if [ ! -f "$CLAUDE_DIR/logs/agent-loop.log" ]; then
    echo "[$(date -Iseconds)] [INFO] Autonomous agent loop initialized" > "$CLAUDE_DIR/logs/agent-loop.log"
    echo "   ✅ Log file created"
else
    echo "   ⚠️  Log file already exists"
fi
echo ""

# Step 6: Create lock files
echo "6️⃣  Creating lock files..."
touch "$CLAUDE_DIR/TASK_QUEUE.md.lock"
touch "$CLAUDE_DIR/AGENT_STATUS.md.lock"
echo "   ✅ Lock files created"
echo ""

# Step 7: Test git hooks
echo "7️⃣  Testing git hooks..."
if [ -x "$GIT_HOOKS_DIR/post-commit" ]; then
    echo "   ✅ post-commit hook is executable"
else
    echo "   ❌ post-commit hook is not executable"
    exit 1
fi

if [ -x "$GIT_HOOKS_DIR/pre-commit" ]; then
    echo "   ✅ pre-commit hook is executable"
else
    echo "   ❌ pre-commit hook is not executable"
    exit 1
fi
echo ""

# Done!
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  INITIALIZATION COMPLETE ✅                                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📚 Quick Start Guide:"
echo ""
echo "1. Add your first task:"
echo "   bash .claude/scripts/add-task.sh \"developer\" \"Your task description\" \"P1\""
echo ""
echo "2. Commit to trigger the loop:"
echo "   git add .claude/TASK_QUEUE.md"
echo "   git commit -m \"chore: add first task\""
echo ""
echo "3. Monitor the loop (optional):"
echo "   bash .claude/scripts/monitor-loop.sh"
echo ""
echo "📝 Documentation:"
echo "   - Design: .claude/AUTONOMOUS_LOOP_DESIGN.md"
echo "   - Config: .claude/agent-loop-config.yaml"
echo "   - Logs: .claude/logs/agent-loop.log"
echo ""
echo "🎉 Ready for autonomous development!"
