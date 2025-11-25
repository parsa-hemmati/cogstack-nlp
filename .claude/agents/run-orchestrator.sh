#!/bin/bash
# Wrapper script for running the orchestrator agent

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ORCHESTRATOR_SCRIPT=".claude/agents/orchestrator.py"
LOG_DIR=".claude/logs/orchestrator"
PID_FILE="$LOG_DIR/orchestrator.pid"

mkdir -p "$LOG_DIR"

# Function to check if orchestrator is already running
is_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start orchestrator
start_orchestrator() {
    if is_running; then
        echo -e "${YELLOW}⚠️  Orchestrator already running (PID: $(cat $PID_FILE))${NC}"
        exit 1
    fi

    echo -e "${BLUE}🚀 Starting Orchestrator Agent${NC}"
    echo ""

    # Run orchestrator in background
    nohup python3 "$ORCHESTRATOR_SCRIPT" > "$LOG_DIR/orchestrator-$(date +%Y%m%d_%H%M%S).log" 2>&1 &

    pid=$!
    echo "$pid" > "$PID_FILE"

    echo -e "${GREEN}✓ Orchestrator started (PID: $pid)${NC}"
    echo "Logs: $LOG_DIR"
    echo ""
    echo "To stop: $0 stop"
    echo "To view logs: $0 logs"
}

# Function to stop orchestrator
stop_orchestrator() {
    if ! is_running; then
        echo -e "${YELLOW}⚠️  Orchestrator not running${NC}"
        exit 1
    fi

    pid=$(cat "$PID_FILE")
    echo -e "${BLUE}🛑 Stopping Orchestrator Agent (PID: $pid)${NC}"

    kill "$pid"
    rm -f "$PID_FILE"

    echo -e "${GREEN}✓ Orchestrator stopped${NC}"
}

# Function to view orchestrator status
status_orchestrator() {
    if is_running; then
        pid=$(cat "$PID_FILE")
        echo -e "${GREEN}✓ Orchestrator running (PID: $pid)${NC}"

        # Show recent log entries
        echo ""
        echo "Recent activity:"
        tail -n 10 "$LOG_DIR"/*.log 2>/dev/null | head -n 10 || echo "No logs found"
    else
        echo -e "${YELLOW}⊘ Orchestrator not running${NC}"
    fi
}

# Function to view logs
view_logs() {
    echo -e "${BLUE}📋 Orchestrator Logs${NC}"
    echo ""

    if [ -d "$LOG_DIR" ]; then
        latest_log=$(ls -t "$LOG_DIR"/*.log 2>/dev/null | head -n 1)

        if [ -n "$latest_log" ]; then
            echo "Latest log: $latest_log"
            echo ""
            tail -f "$latest_log"
        else
            echo "No logs found"
        fi
    else
        echo "Log directory not found"
    fi
}

# Main command handler
case "${1:-}" in
    start)
        start_orchestrator
        ;;
    stop)
        stop_orchestrator
        ;;
    restart)
        stop_orchestrator
        start_orchestrator
        ;;
    status)
        status_orchestrator
        ;;
    logs)
        view_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the orchestrator agent"
        echo "  stop     - Stop the orchestrator agent"
        echo "  restart  - Restart the orchestrator agent"
        echo "  status   - Check orchestrator status"
        echo "  logs     - View orchestrator logs"
        exit 1
        ;;
esac
