#!/bin/bash

#
# monitor-loops.sh - Monitor all autonomous worktree loops
#
# Usage:
#   ./monitor-loops.sh --status      # Show status of all loops
#   ./monitor-loops.sh --report      # Detailed report
#   ./monitor-loops.sh --stop-all    # Stop all running loops
#   ./monitor-loops.sh --resume-all  # Resume all stopped loops
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

PROJECT_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_DIR="$PROJECT_ROOT/.claude/autonomous-worktrees"

COMMAND=${1:---status}

# ============================================================================
# Helper Functions
# ============================================================================

get_worktree_status() {
    local module=$1
    local config_dir="$WORKTREE_DIR/$module"
    local status_file="$config_dir/loop-status.md"
    local pid_file="$config_dir/.loop.pid"
    local task_queue="$config_dir/TASK_QUEUE.md"

    if [ ! -f "$status_file" ]; then
        echo "NOT_INITIALIZED"
        return
    fi

    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "RUNNING"
        else
            echo "STOPPED"
        fi
    else
        echo "STOPPED"
    fi
}

get_task_stats() {
    local module=$1
    local task_queue="$WORKTREE_DIR/$module/TASK_QUEUE.md"

    if [ ! -f "$task_queue" ]; then
        echo "0/0"
        return
    fi

    completed=$(grep -c "^\- \[✅\]" "$task_queue" || echo "0")
    total=$(grep -c "^\- \[" "$task_queue" || echo "0")

    echo "$completed/$total"
}

get_active_agents() {
    local module=$1
    local status_file="$WORKTREE_DIR/$module/loop-status.md"

    if [ ! -f "$status_file" ]; then
        echo "0"
        return
    fi

    # Count agents listed in Active Agents section
    sed -n '/^## Active Agents/,/^## /p' "$status_file" | grep -c "^-" || echo "0"
}

get_last_commit_time() {
    local worktree_path=$1

    if [ ! -d "$worktree_path" ]; then
        echo "N/A"
        return
    fi

    cd "$worktree_path"
    last_commit_date=$(git log -1 --format=%cr 2>/dev/null || echo "never")
    cd - > /dev/null

    echo "$last_commit_date"
}

# ============================================================================
# Status Command
# ============================================================================

cmd_status() {
    echo -e "${CYAN}🔄 Autonomous Worktree Status${NC}"
    echo "═══════════════════════════════════════════"
    echo ""

    if [ ! -d "$WORKTREE_DIR" ] || [ -z "$(ls -A "$WORKTREE_DIR" 2>/dev/null)" ]; then
        echo -e "${YELLOW}No worktrees initialized yet${NC}"
        echo ""
        echo "Create your first worktree with:"
        echo "  /pm:prd-new <module-name>"
        echo "  /pm:prd-parse <module-name>"
        echo "  /pm:epic-decompose <module-name>"
        echo "  .claude/scripts/spawn-worktree-loop.sh <module-name> <worktree-path>"
        return
    fi

    total_worktrees=0
    running_loops=0
    total_agents=0
    total_tasks_completed=0
    total_tasks=0

    for module_dir in "$WORKTREE_DIR"/*; do
        if [ ! -d "$module_dir" ]; then
            continue
        fi

        module=$(basename "$module_dir")
        total_worktrees=$((total_worktrees + 1))

        status=$(get_worktree_status "$module")
        task_stats=$(get_task_stats "$module")
        active_agents=$(get_active_agents "$module")

        # Parse task stats
        completed=$(echo "$task_stats" | cut -d'/' -f1)
        total=$(echo "$task_stats" | cut -d'/' -f2)
        total_tasks_completed=$((total_tasks_completed + completed))
        total_tasks=$((total_tasks + total))

        # Get worktree path
        worktree_path=$(grep "^\\*\\*Worktree\\*\\*:" "$module_dir/loop-status.md" 2>/dev/null | sed 's/.*: //' || echo "unknown")
        last_commit=$(get_last_commit_time "$worktree_path")

        # Get branch name
        if [ -d "$worktree_path" ]; then
            cd "$worktree_path"
            branch=$(git branch --show-current 2>/dev/null || echo "unknown")
            cd - > /dev/null
        else
            branch="unknown"
        fi

        # Status indicator
        case "$status" in
            "RUNNING")
                status_icon="✅"
                status_color="$GREEN"
                running_loops=$((running_loops + 1))
                total_agents=$((total_agents + active_agents))
                ;;
            "STOPPED")
                status_icon="⏸️"
                status_color="$YELLOW"
                ;;
            "NOT_INITIALIZED")
                status_icon="⚠️"
                status_color="$RED"
                ;;
            *)
                status_icon="❓"
                status_color="$NC"
                ;;
        esac

        # Progress percentage
        if [ "$total" -gt 0 ]; then
            progress=$((completed * 100 / total))
        else
            progress=0
        fi

        echo -e "${BLUE}📦 $module${NC} ($worktree_path)"
        echo "   Branch: $branch"
        echo -e "   Status: $status_icon ${status_color}$status${NC}"
        if [ "$status" = "RUNNING" ]; then
            echo "   Agents: $active_agents active"
        fi
        echo "   Tasks: $task_stats complete ($progress%)"
        echo "   Last commit: $last_commit"
        echo ""
    done

    echo "───────────────────────────────────────────"
    echo -e "${MAGENTA}💡 Summary${NC}"
    echo "   Total Worktrees: $total_worktrees"
    echo "   Running Loops: $running_loops"
    echo "   Active Agents: $total_agents"
    echo "   Tasks: $total_tasks_completed/$total_tasks complete"
    if [ "$total_tasks" -gt 0 ]; then
        overall_progress=$((total_tasks_completed * 100 / total_tasks))
        echo "   Overall Progress: $overall_progress%"
    fi
    echo ""
}

# ============================================================================
# Report Command
# ============================================================================

cmd_report() {
    echo -e "${CYAN}📊 Detailed Autonomous Loop Report${NC}"
    echo "═══════════════════════════════════════════"
    echo ""

    if [ ! -d "$WORKTREE_DIR" ] || [ -z "$(ls -A "$WORKTREE_DIR" 2>/dev/null)" ]; then
        echo -e "${YELLOW}No worktrees initialized${NC}"
        return
    fi

    for module_dir in "$WORKTREE_DIR"/*; do
        if [ ! -d "$module_dir" ]; then
            continue
        fi

        module=$(basename "$module_dir")

        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE}📦 Module: $module${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        status_file="$module_dir/loop-status.md"
        task_queue="$module_dir/TASK_QUEUE.md"

        if [ ! -f "$status_file" ]; then
            echo "   Not initialized"
            echo ""
            continue
        fi

        # Display loop status
        echo -e "${YELLOW}Loop Status:${NC}"
        cat "$status_file"
        echo ""

        # Display task queue summary
        echo -e "${YELLOW}Task Queue Summary:${NC}"
        echo ""
        pending=$(grep -c "^\- \[ \]" "$task_queue" 2>/dev/null || echo "0")
        in_progress=$(grep -c "^\- \[🔄\]" "$task_queue" 2>/dev/null || echo "0")
        completed=$(grep -c "^\- \[✅\]" "$task_queue" 2>/dev/null || echo "0")
        failed=$(grep -c "^\- \[❌\]" "$task_queue" 2>/dev/null || echo "0")
        blocked=$(grep -c "^\- \[⏸️\]" "$task_queue" 2>/dev/null || echo "0")

        echo "   Pending: $pending"
        echo "   In Progress: $in_progress"
        echo "   Completed: $completed"
        echo "   Failed: $failed"
        echo "   Blocked: $blocked"
        echo ""

        # Display next pending tasks
        if [ "$pending" -gt 0 ]; then
            echo -e "${YELLOW}Next Pending Tasks:${NC}"
            grep "^\- \[ \]" "$task_queue" 2>/dev/null | head -3
            if [ "$pending" -gt 3 ]; then
                echo "   ... and $((pending - 3)) more"
            fi
            echo ""
        fi

        # Display recent commits
        worktree_path=$(grep "^\\*\\*Worktree\\*\\*:" "$status_file" 2>/dev/null | sed 's/.*: //' || echo "unknown")
        if [ -d "$worktree_path" ]; then
            echo -e "${YELLOW}Recent Commits (last 5):${NC}"
            cd "$worktree_path"
            git log --oneline -5 2>/dev/null || echo "   No commits yet"
            cd - > /dev/null
            echo ""
        fi
    done
}

# ============================================================================
# Stop All Command
# ============================================================================

cmd_stop_all() {
    echo -e "${RED}⏹️  Stopping All Autonomous Loops${NC}"
    echo "═══════════════════════════════════════════"
    echo ""

    if [ ! -d "$WORKTREE_DIR" ] || [ -z "$(ls -A "$WORKTREE_DIR" 2>/dev/null)" ]; then
        echo -e "${YELLOW}No worktrees found${NC}"
        return
    fi

    stopped=0

    for module_dir in "$WORKTREE_DIR"/*; do
        if [ ! -d "$module_dir" ]; then
            continue
        fi

        module=$(basename "$module_dir")
        pid_file="$module_dir/.loop.pid"

        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "Stopping $module (PID $pid)..."
                kill -TERM "$pid"
                stopped=$((stopped + 1))
            fi
        fi
    done

    echo ""
    echo -e "${GREEN}✅ Stopped $stopped loop(s)${NC}"
}

# ============================================================================
# Resume All Command
# ============================================================================

cmd_resume_all() {
    echo -e "${GREEN}▶️  Resuming All Autonomous Loops${NC}"
    echo "═══════════════════════════════════════════"
    echo ""

    if [ ! -d "$WORKTREE_DIR" ] || [ -z "$(ls -A "$WORKTREE_DIR" 2>/dev/null)" ]; then
        echo -e "${YELLOW}No worktrees found${NC}"
        return
    fi

    resumed=0

    for module_dir in "$WORKTREE_DIR"/*; do
        if [ ! -d "$module_dir" ]; then
            continue
        fi

        module=$(basename "$module_dir")
        status=$(get_worktree_status "$module")

        if [ "$status" = "STOPPED" ] || [ "$status" = "NOT_INITIALIZED" ]; then
            worktree_path=$(grep "^\\*\\*Worktree\\*\\*:" "$module_dir/loop-status.md" 2>/dev/null | sed 's/.*: //' || echo "")

            if [ -d "$worktree_path" ]; then
                echo "Starting loop for $module..."
                cd "$worktree_path"
                "$PROJECT_ROOT/.claude/scripts/worktree-loop-runner.sh" "$module" &
                cd - > /dev/null
                resumed=$((resumed + 1))
            fi
        fi
    done

    echo ""
    echo -e "${GREEN}✅ Resumed $resumed loop(s)${NC}"
}

# ============================================================================
# Main
# ============================================================================

case "$COMMAND" in
    --status)
        cmd_status
        ;;
    --report)
        cmd_report
        ;;
    --stop-all)
        cmd_stop_all
        ;;
    --resume-all)
        cmd_resume_all
        ;;
    --help)
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  --status      Show status of all worktrees (default)"
        echo "  --report      Detailed report with task queues and commits"
        echo "  --stop-all    Stop all running autonomous loops"
        echo "  --resume-all  Resume all stopped loops"
        echo "  --help        Show this help message"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Run '$0 --help' for usage"
        exit 1
        ;;
esac
