#!/bin/bash
# Monitor Autonomous Loop - Real-time Dashboard
# Usage: bash monitor-loop.sh [refresh_interval]
# Example: bash monitor-loop.sh 5

# Configuration
REFRESH_INTERVAL=${1:-5}  # Default 5 seconds
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
TASK_QUEUE="$PROJECT_ROOT/.claude/TASK_QUEUE.md"
AGENT_STATUS="$PROJECT_ROOT/.claude/AGENT_STATUS.md"
LOOP_LOG="$PROJECT_ROOT/.claude/logs/agent-loop.log"

# Check if files exist
if [ ! -f "$TASK_QUEUE" ]; then
    echo "❌ ERROR: TASK_QUEUE.md not found"
    echo "Initialize autonomous loop first"
    exit 1
fi

# Function to display dashboard
display_dashboard() {
    clear

    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  AUTONOMOUS DEVELOPMENT LOOP - LIVE DASHBOARD             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # Task Queue Status
    echo "📊 Task Queue Status:"
    local pending=$(grep -c "^- \[ \]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local in_progress=$(grep -c "^- \[🔄\]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local completed=$(grep -c "^- \[✅\]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local failed=$(grep -c "^- \[❌\]" "$TASK_QUEUE" 2>/dev/null || echo "0")

    echo "  📋 Pending:     $pending"
    echo "  🔄 In Progress: $in_progress"
    echo "  ✅ Completed:   $completed"
    echo "  ❌ Failed:      $failed"
    echo ""

    # Active Agents
    echo "👥 Active Agents:"
    if grep -q "Status: WORKING" "$AGENT_STATUS" 2>/dev/null; then
        grep "Status: WORKING" "$AGENT_STATUS" | sed 's/- /  🟢 /' | head -10
    else
        echo "  (No active agents)"
    fi
    echo ""

    # Recent Activity
    echo "📝 Recent Activity (last 5 commits):"
    git log --oneline --format="  %h - %s" -5 2>/dev/null || echo "  (No commits yet)"
    echo ""

    # Loop Log Tail
    echo "📄 Recent Log Entries (last 5):"
    if [ -f "$LOOP_LOG" ]; then
        tail -5 "$LOOP_LOG" | sed 's/^/  /'
    else
        echo "  (No log entries yet)"
    fi
    echo ""

    # System Info
    echo "⏱️  Last Update: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "🔄 Refresh: Every ${REFRESH_INTERVAL}s (Ctrl+C to exit)"
}

# Main loop
echo "Starting autonomous loop monitor..."
echo "Refresh interval: ${REFRESH_INTERVAL}s"
echo "Press Ctrl+C to exit"
echo ""

while true; do
    display_dashboard
    sleep "$REFRESH_INTERVAL"
done
