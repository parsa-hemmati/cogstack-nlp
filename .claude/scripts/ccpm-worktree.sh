#!/bin/bash
#
# CCPM Worktree Manager
#
# Purpose: Create and manage git worktrees for modular parallel development
#
# Features:
# - Create worktrees for each module/feature
# - Each worktree has isolated task queue
# - Agents work in parallel across worktrees
# - Merge completed modules back to main
#
# Usage:
#   ./ccpm-worktree.sh create <module-name> [base-branch]
#   ./ccpm-worktree.sh list
#   ./ccpm-worktree.sh status <module-name>
#   ./ccpm-worktree.sh merge <module-name>
#   ./ccpm-worktree.sh remove <module-name>
#

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

WORKTREE_DIR="../worktrees"
PROJECT_ROOT=$(git rev-parse --show-toplevel)

# Ensure we're in git repo
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${RED}❌ ERROR: Not in a git repository${NC}"
    exit 1
fi

usage() {
    cat << EOF
${BLUE}CCPM Worktree Manager${NC}

Manage git worktrees for modular parallel development

${CYAN}Usage:${NC}
  $0 create <module-name> [base-branch]   Create worktree for module
  $0 list                                  List all worktrees
  $0 status <module-name>                  Show worktree status
  $0 merge <module-name>                   Merge completed module
  $0 remove <module-name>                  Remove worktree

${CYAN}Examples:${NC}
  # Create worktree for de-identification module
  $0 create de-identification develop

  # List all active worktrees
  $0 list

  # Check status of module
  $0 status de-identification

  # Merge completed module
  $0 merge de-identification

${CYAN}Workflow:${NC}
  1. Create worktree for new module
  2. Autonomous agents work in parallel across worktrees
  3. Each worktree has isolated TASK_QUEUE.md
  4. Merge when module complete
  5. Remove worktree

EOF
}

create_worktree() {
    local module_name=$1
    local base_branch=${2:-develop}

    echo -e "${BLUE}🌳 Creating worktree for module: $module_name${NC}"
    echo ""

    # Validate module name
    if [ -z "$module_name" ]; then
        echo -e "${RED}❌ ERROR: Module name required${NC}"
        usage
        exit 1
    fi

    # Create branch name
    local branch_name="feature/$module_name"
    local worktree_path="$PROJECT_ROOT/$WORKTREE_DIR/$module_name"

    # Check if worktree already exists
    if [ -d "$worktree_path" ]; then
        echo -e "${RED}❌ ERROR: Worktree already exists at $worktree_path${NC}"
        exit 1
    fi

    # Create worktree directory
    mkdir -p "$PROJECT_ROOT/$WORKTREE_DIR"

    # Create worktree
    echo -e "${CYAN}Creating worktree at: $worktree_path${NC}"
    git worktree add -b "$branch_name" "$worktree_path" "$base_branch"

    # Initialize module-specific task queue
    local module_task_queue="$worktree_path/.claude/TASK_QUEUE.md"

    echo ""
    echo -e "${CYAN}Initializing module task queue...${NC}"

    cat > "$module_task_queue" << EOF
# Task Queue: $module_name Module

**Module**: $module_name
**Created**: $(date +%Y-%m-%dT%H:%M:%S%z)
**Base Branch**: $base_branch
**Worktree**: $worktree_path

---

## 🔴 High Priority (P0 - Critical)

<!-- Add critical tasks here -->

---

## 🟡 Normal Priority (P1 - Important)

<!-- Add important tasks here -->

---

## 🟢 Low Priority (P2 - Nice to Have)

<!-- Add nice-to-have tasks here -->

---

## Task Status Legend

- \`[ ]\` - Pending (not yet claimed)
- \`[🔄]\` - In Progress (claimed by agent)
- \`[✅]\` - Completed (done)
- \`[❌]\` - Failed (error occurred)
- \`[⏸️]\` - Blocked (waiting on dependency)

## 🔢 Task ID Assignment

Task IDs are auto-incremented integers starting from 1. Next available ID: **1**

To add a task:
\`\`\`bash
cd $worktree_path
bash .claude/scripts/add-task.sh "agent-type" "Task description" "P1"
\`\`\`

---

## Module Development Workflow

1. **Add tasks** to this queue for the module
2. **Commit** to trigger autonomous loop
3. **Agents spawn** and work on tasks
4. **Review** AGENT_STATUS.md for progress
5. **Merge** when all tasks complete

EOF

    # Create module README
    cat > "$worktree_path/MODULE_README.md" << EOF
# $module_name Module

**Status**: 🚧 In Development
**Worktree**: $worktree_path
**Branch**: $branch_name
**Base**: $base_branch

## Overview

<!-- Describe module purpose and features -->

## Development

### Task Queue

See [\`.claude/TASK_QUEUE.md\`](.claude/TASK_QUEUE.md) for current tasks.

### Adding Tasks

\`\`\`bash
bash .claude/scripts/add-task.sh "developer" "Implement X feature" "P1"
git add .claude/TASK_QUEUE.md
git commit -m "chore: add task for X feature"
# Post-commit hook spawns agents automatically
\`\`\`

### Checking Progress

\`\`\`bash
# View task queue
cat .claude/TASK_QUEUE.md

# View agent status
cat .claude/AGENT_STATUS.md

# View loop log
tail -f .claude/logs/agent-loop.log
\`\`\`

### Autonomous Loop

The autonomous loop runs in this worktree independently:
- Post-commit hook triggers on every commit
- Up to 6 agents spawn concurrently
- Agents work on tasks in TASK_QUEUE.md
- Completion report generated when all tasks done

## Architecture

<!-- Document module architecture -->

## Integration Points

<!-- List integration points with main application -->

## Testing

<!-- Document testing strategy -->

## Completion Criteria

- [ ] All tasks in TASK_QUEUE.md complete
- [ ] All tests passing (≥85% coverage)
- [ ] HIPAA/GDPR compliance validated
- [ ] Documentation complete
- [ ] Integration tests with main app passing

## Merge Checklist

Before merging to \`$base_branch\`:
- [ ] All completion criteria met
- [ ] Code review completed
- [ ] No merge conflicts
- [ ] CI/CD pipeline passing
- [ ] CONTEXT.md and AUDIT.md updated

EOF

    echo ""
    echo -e "${GREEN}✅ Worktree created successfully!${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "  1. cd $worktree_path"
    echo "  2. Add tasks:"
    echo "     bash .claude/scripts/add-task.sh \"developer\" \"Implement feature\" \"P1\""
    echo "  3. Commit to trigger autonomous loop:"
    echo "     git add .claude/TASK_QUEUE.md && git commit -m \"chore: add tasks\""
    echo ""
    echo -e "${BLUE}Worktree path: $worktree_path${NC}"
    echo -e "${BLUE}Branch: $branch_name${NC}"
    echo ""
}

list_worktrees() {
    echo -e "${BLUE}🌳 Active Worktrees${NC}"
    echo ""

    git worktree list --porcelain | awk '
        /^worktree/ { path = $2 }
        /^branch/ { branch = $2 }
        /^$/ {
            if (path && branch) {
                print "📁 " path
                print "   Branch: " branch
                print ""
            }
            path = ""
            branch = ""
        }
    '
}

worktree_status() {
    local module_name=$1
    local worktree_path="$PROJECT_ROOT/$WORKTREE_DIR/$module_name"

    if [ ! -d "$worktree_path" ]; then
        echo -e "${RED}❌ ERROR: Worktree not found: $module_name${NC}"
        exit 1
    fi

    echo -e "${BLUE}📊 Worktree Status: $module_name${NC}"
    echo ""

    cd "$worktree_path"

    # Git status
    echo -e "${CYAN}Git Status:${NC}"
    git status --short
    echo ""

    # Task queue summary
    if [ -f ".claude/TASK_QUEUE.md" ]; then
        echo -e "${CYAN}Task Queue Summary:${NC}"
        local pending=$(grep -c "^\- \[ \]" .claude/TASK_QUEUE.md || echo "0")
        local in_progress=$(grep -c "^\- \[🔄\]" .claude/TASK_QUEUE.md || echo "0")
        local completed=$(grep -c "^\- \[✅\]" .claude/TASK_QUEUE.md || echo "0")
        local failed=$(grep -c "^\- \[❌\]" .claude/TASK_QUEUE.md || echo "0")

        echo "  Pending: $pending"
        echo "  In Progress: $in_progress"
        echo "  Completed: $completed"
        echo "  Failed: $failed"
        echo ""
    fi

    # Agent status
    if [ -f ".claude/AGENT_STATUS.md" ]; then
        echo -e "${CYAN}Active Agents:${NC}"
        grep -E "^\*\*Status\*\*: (WORKING|CLAIMING|COMMITTING)" .claude/AGENT_STATUS.md | wc -l || echo "0"
        echo ""
    fi

    # Recent commits
    echo -e "${CYAN}Recent Commits (last 5):${NC}"
    git log --oneline -5
    echo ""
}

merge_worktree() {
    local module_name=$1
    local worktree_path="$PROJECT_ROOT/$WORKTREE_DIR/$module_name"

    if [ ! -d "$worktree_path" ]; then
        echo -e "${RED}❌ ERROR: Worktree not found: $module_name${NC}"
        exit 1
    fi

    echo -e "${BLUE}🔀 Merging worktree: $module_name${NC}"
    echo ""

    # Get branch name
    cd "$worktree_path"
    local branch_name=$(git rev-parse --abbrev-ref HEAD)

    # Check if all tasks complete
    if [ -f ".claude/TASK_QUEUE.md" ]; then
        local pending=$(grep -c "^\- \[ \]" .claude/TASK_QUEUE.md || echo "0")
        local in_progress=$(grep -c "^\- \[🔄\]" .claude/TASK_QUEUE.md || echo "0")

        if [ "$pending" -gt 0 ] || [ "$in_progress" -gt 0 ]; then
            echo -e "${YELLOW}⚠️  WARNING: Tasks still pending/in-progress!${NC}"
            echo "  Pending: $pending"
            echo "  In Progress: $in_progress"
            echo ""
            echo -n "Merge anyway? [y/N] "
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                echo -e "${RED}❌ Merge aborted${NC}"
                exit 1
            fi
        fi
    fi

    # Switch to main repo
    cd "$PROJECT_ROOT"

    # Get base branch (default to develop)
    local base_branch="develop"

    echo -e "${CYAN}Switching to $base_branch...${NC}"
    git checkout "$base_branch"

    echo -e "${CYAN}Pulling latest changes...${NC}"
    git pull origin "$base_branch"

    echo -e "${CYAN}Merging $branch_name...${NC}"
    git merge --no-ff "$branch_name" -m "feat($module_name): merge module from worktree

Module: $module_name
Worktree: $worktree_path
Branch: $branch_name

This merge includes all work completed in the $module_name module worktree."

    echo ""
    echo -e "${GREEN}✅ Merge successful!${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "  1. Review merged code"
    echo "  2. Run full test suite"
    echo "  3. Push to remote: git push origin $base_branch"
    echo "  4. Remove worktree: $0 remove $module_name"
    echo ""
}

remove_worktree() {
    local module_name=$1
    local worktree_path="$PROJECT_ROOT/$WORKTREE_DIR/$module_name"

    if [ ! -d "$worktree_path" ]; then
        echo -e "${RED}❌ ERROR: Worktree not found: $module_name${NC}"
        exit 1
    fi

    echo -e "${BLUE}🗑️  Removing worktree: $module_name${NC}"
    echo ""

    # Check if merged
    cd "$worktree_path"
    local branch_name=$(git rev-parse --abbrev-ref HEAD)

    cd "$PROJECT_ROOT"

    echo -e "${YELLOW}⚠️  WARNING: This will remove the worktree and delete all local changes!${NC}"
    echo "Worktree: $worktree_path"
    echo "Branch: $branch_name"
    echo ""
    echo -n "Continue? [y/N] "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Aborted${NC}"
        exit 1
    fi

    # Remove worktree
    git worktree remove "$worktree_path"

    # Delete branch (optional)
    echo ""
    echo -n "Delete branch $branch_name? [y/N] "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git branch -d "$branch_name" || git branch -D "$branch_name"
        echo -e "${GREEN}✅ Branch deleted${NC}"
    fi

    echo ""
    echo -e "${GREEN}✅ Worktree removed!${NC}"
    echo ""
}

# Main command router
case "${1:-}" in
    create)
        create_worktree "$2" "$3"
        ;;
    list)
        list_worktrees
        ;;
    status)
        worktree_status "$2"
        ;;
    merge)
        merge_worktree "$2"
        ;;
    remove)
        remove_worktree "$2"
        ;;
    *)
        usage
        exit 1
        ;;
esac
