#!/bin/bash
# Post-commit hook: Autonomous Agent Loop Orchestrator
# Version: 1.0.0
#
# This hook spawns Claude Code agents automatically after each commit
# based on pending tasks in TASK_QUEUE.md
#
# Usage: Automatically triggered by git post-commit hook

set -e

# Configuration
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"
TASK_QUEUE="$CLAUDE_DIR/TASK_QUEUE.md"
AGENT_STATUS="$CLAUDE_DIR/AGENT_STATUS.md"
COORDINATION="$CLAUDE_DIR/COORDINATION.md"
CONFIG_FILE="$CLAUDE_DIR/agent-loop-config.yaml"
LOOP_LOG="$CLAUDE_DIR/logs/agent-loop.log"
METRICS_DIR="$CLAUDE_DIR/metrics"

# Create directories if they don't exist
mkdir -p "$CLAUDE_DIR/logs" "$METRICS_DIR"

# Initialize log file
touch "$LOOP_LOG"

# Utility functions
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date -Iseconds)
    echo "[$timestamp] [$level] $message" >> "$LOOP_LOG"

    # Also echo to stdout for INFO level in non-background mode
    if [ "$level" = "INFO" ] && [ "${AGENT_LOOP_BACKGROUND:-0}" -eq 0 ]; then
        echo "[$level] $message"
    fi
}

# Load configuration from YAML (simple parser)
load_config() {
    local key=$1
    local default=$2

    if [ ! -f "$CONFIG_FILE" ]; then
        echo "$default"
        return
    fi

    # Simple YAML parser (handles key: value format)
    local value=$(grep "^${key}:" "$CONFIG_FILE" | sed 's/^[^:]*:[[:space:]]*//' | tr -d '"' | tr -d "'")

    if [ -z "$value" ]; then
        echo "$default"
    else
        echo "$value"
    fi
}

# Configuration values
MAX_TOTAL_AGENTS=$(load_config "max_total_agents" "6")
HEARTBEAT_INTERVAL=$(load_config "heartbeat_interval" "30")
ENABLED=$(load_config "git_hooks.post_commit.enabled" "true")
DRY_RUN=$(load_config "debug.dry_run" "false")

log "INFO" "========================================"
log "INFO" "Post-commit hook: Agent loop starting"
log "INFO" "Commit: $(git rev-parse --short HEAD)"
log "INFO" "Author: $(git log -1 --format='%an')"
log "INFO" "Config: max_agents=$MAX_TOTAL_AGENTS, dry_run=$DRY_RUN"

# Check if hook is enabled
if [ "$ENABLED" != "true" ]; then
    log "INFO" "Post-commit hook disabled in config. Exiting."
    exit 0
fi

# Check if shared state files exist
if [ ! -f "$TASK_QUEUE" ]; then
    log "WARN" "TASK_QUEUE.md not found. Autonomous loop not initialized. Exiting."
    exit 0
fi

# Function: Update agent status
update_agent_status() {
    local agent=$1
    local status=$2
    local task_id=$3
    local pid=$4

    local timestamp=$(date +%H:%M:%S)

    # Use flock for concurrency safety
    (
        flock -x 200

        # Update the agent's status section
        # This is a simplified version - full implementation would use proper markdown parsing
        sed -i "/^### $agent/,/^---/{
            s/Status: .*/Status: $status (Task #$task_id)/;
            s/Last Heartbeat: .*/Last Heartbeat: $timestamp/;
        }" "$AGENT_STATUS" 2>/dev/null || true

    ) 200>"$AGENT_STATUS.lock"

    log "DEBUG" "Updated status for $agent: $status (Task #$task_id, PID: $pid)"
}

# Function: Get max instances for agent type
get_max_instances() {
    local agent_type=$1
    load_config "agent_limits.$agent_type" "1"
}

# Function: Get timeout for agent type
get_timeout() {
    local agent_type=$1
    load_config "timeouts.$agent_type" "3600"
}

# Function: Count active agents of specific type
count_active_agents() {
    local agent_type=$1

    if [ ! -f "$AGENT_STATUS" ]; then
        echo "0"
        return
    fi

    # Count how many instances of this agent type are WORKING
    local count=$(grep -c "^### $agent_type.*PID:" "$AGENT_STATUS" 2>/dev/null || echo "0")
    echo "$count"
}

# Function: Count total active agents
count_total_active_agents() {
    if [ ! -f "$AGENT_STATUS" ]; then
        echo "0"
        return
    fi

    # Count all WORKING agents
    local count=$(grep -c "Status: WORKING" "$AGENT_STATUS" 2>/dev/null || echo "0")
    echo "$count"
}

# Function: Get pending tasks for agent type
get_pending_tasks() {
    local agent_type=$1

    if [ ! -f "$TASK_QUEUE" ]; then
        echo ""
        return
    fi

    # Find all unclaimed tasks for this agent type
    # Format: - [ ] #ID `[agent-type]` ...
    grep "^- \[ \] #[0-9]* \`\[$agent_type\]\`" "$TASK_QUEUE" 2>/dev/null || echo ""
}

# Function: Get task priority
get_task_priority() {
    local task_line=$1

    # Check which section the task is in
    # This is simplified - full implementation would parse markdown properly
    echo "P1"  # Default to P1
}

# Function: Claim next task atomically
claim_next_task() {
    local agent_type=$1

    local task_id=""

    # Use flock to prevent race conditions
    (
        flock -x 200

        # Find first unclaimed task for this agent type
        task_id=$(grep -m 1 "^- \[ \] #[0-9]* \`\[$agent_type\]\`" "$TASK_QUEUE" 2>/dev/null | sed -E 's/.*#([0-9]*).*/\1/')

        if [ -n "$task_id" ]; then
            # Mark task as in progress
            local timestamp=$(date +%H:%M:%S)
            local pid=$$

            sed -i "s/^- \[ \] #$task_id \`\[$agent_type\]\`/- [🔄] #$task_id \`[$agent_type]\` (claimed: $timestamp, PID: $pid)/" "$TASK_QUEUE"

            log "INFO" "Claimed task #$task_id for $agent_type"
        fi

        echo "$task_id"

    ) 200>"$TASK_QUEUE.lock"
}

# Function: Check if should spawn agent
should_spawn_agent() {
    local agent_type=$1

    # Check if agent already has max instances
    local active_count=$(count_active_agents "$agent_type")
    local max_instances=$(get_max_instances "$agent_type")

    if [ "$active_count" -ge "$max_instances" ]; then
        log "DEBUG" "Skipping $agent_type: $active_count/$max_instances instances active"
        return 1
    fi

    # Check if tasks exist for this agent
    local pending=$(get_pending_tasks "$agent_type")

    if [ -z "$pending" ]; then
        log "DEBUG" "Skipping $agent_type: No pending tasks"
        return 1
    fi

    return 0
}

# Function: Extract task context
get_task_context() {
    local task_id=$1

    # Extract full task details from TASK_QUEUE.md
    # This is simplified - full implementation would parse markdown properly
    local context=$(sed -n "/^- \[🔄\] #$task_id/,/^$/p" "$TASK_QUEUE")

    echo "$context"
}

# Function: Spawn agent
spawn_agent() {
    local agent_type=$1
    local task_id=$2

    if [ "$DRY_RUN" = "true" ]; then
        log "INFO" "[DRY RUN] Would spawn $agent_type for task #$task_id"
        return 0
    fi

    log "INFO" "Spawning $agent_type for task #$task_id..."

    # Extract task details
    local task_context=$(get_task_context "$task_id")

    # Get timeout for this agent type
    local timeout=$(get_timeout "$agent_type")

    # Create agent prompt
    local agent_prompt="You are the $agent_type agent in a continuous autonomous development loop.

**Your Task**: #$task_id from TASK_QUEUE.md

$task_context

**Instructions**:
1. Read .claude/TASK_QUEUE.md completely to understand task #$task_id
2. Read .claude/COORDINATION.md for any messages directed to you
3. Read your agent definition: .claude/agents/$agent_type.md
4. Execute the task following your agent definition
5. Update your progress in .claude/AGENT_STATUS.md (heartbeat every 30s)
6. When complete:
   - Update TASK_QUEUE.md (move #$task_id from [🔄] → [✅])
   - Add new tasks for other agents if needed (use proper format)
   - Update COORDINATION.md with messages for other agents
   - Update CONTEXT.md with technical changes (if applicable)
   - Commit your work with proper commit message
7. The post-commit hook will spawn the next agent automatically

**Critical Rules**:
- DO NOT wait for user acknowledgment
- DO mark task as complete when done
- DO create tasks for other agents if their work is needed
- DO update all shared files (TASK_QUEUE, AGENT_STATUS, COORDINATION, CONTEXT if needed)
- DO commit immediately when task complete
- DO NOT ask the user questions unless you have a blocker requiring a decision

**Autonomous Mode**: You are working independently. No status reporting to user unless you encounter a blocker that requires user decision.

**Timeout**: You have $timeout seconds to complete this task. After timeout, you will be killed and task marked as failed.

Begin working on task #$task_id now."

    # Create temporary file with agent prompt
    local prompt_file="$CLAUDE_DIR/logs/agent-${agent_type}-${task_id}.prompt"
    echo "$agent_prompt" > "$prompt_file"

    # Spawn agent in background using agent wrapper
    local agent_script="$CLAUDE_DIR/scripts/agent-wrapper.sh"

    # If wrapper doesn't exist, use simple spawning
    if [ ! -f "$agent_script" ]; then
        log "WARN" "Agent wrapper not found, using simple spawn"

        # Simple spawning (not recommended for production)
        (
            # This is a placeholder - actual implementation would invoke Claude Code agent
            # For now, just log that agent would be spawned
            log "INFO" "Agent $agent_type (task #$task_id) would execute here"

            # Update agent status to WORKING
            update_agent_status "$agent_type" "WORKING" "$task_id" "$$"

            # Simulate work (remove this in production)
            sleep 5

            # Update agent status to IDLE
            update_agent_status "$agent_type" "IDLE" "$task_id" "$$"

            log "INFO" "Agent $agent_type completed task #$task_id (simulated)"

        ) &

        local agent_pid=$!

        log "INFO" "Agent $agent_type spawned (PID: $agent_pid, task #$task_id)"

        # Store PID for monitoring
        echo "$agent_pid" > "$CLAUDE_DIR/logs/agent-${agent_type}-${task_id}.pid"

        return 0
    fi

    # Use agent wrapper (recommended)
    bash "$agent_script" "$agent_type" "$task_id" "$timeout" "$prompt_file" &

    local agent_pid=$!

    log "INFO" "Agent $agent_type spawned (PID: $agent_pid, task #$task_id)"

    # Store PID for monitoring
    echo "$agent_pid" > "$CLAUDE_DIR/logs/agent-${agent_type}-${task_id}.pid"
}

# Function: Check for completion
check_completion() {
    local pending_count=$(grep -c "^- \[ \]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local in_progress_count=$(grep -c "^- \[🔄\]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local completed_count=$(grep -c "^- \[✅\]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local failed_count=$(grep -c "^- \[❌\]" "$TASK_QUEUE" 2>/dev/null || echo "0")

    if [ "$pending_count" -eq 0 ] && [ "$in_progress_count" -eq 0 ]; then
        log "INFO" "✅ AUTONOMOUS LOOP COMPLETE: All tasks finished!"

        # Calculate success rate
        local total=$((completed_count + failed_count))
        local success_rate=0

        if [ "$total" -gt 0 ]; then
            success_rate=$((100 * completed_count / total))
        fi

        # Generate completion report
        local report="
╔════════════════════════════════════════════════════════════╗
║  AUTONOMOUS DEVELOPMENT LOOP - COMPLETION REPORT          ║
╚════════════════════════════════════════════════════════════╝

✅ Total Tasks Completed: $completed_count
❌ Failed Tasks: $failed_count
📊 Success Rate: ${success_rate}%
⏱️  Session Start: $(head -1 "$LOOP_LOG" | cut -d']' -f1 | tr -d '[')
⏱️  Session End: $(date -Iseconds)

All agents are now IDLE. Development loop has terminated.

To resume autonomous development:
1. Add new tasks to .claude/TASK_QUEUE.md
2. Commit any file (triggers post-commit hook)
3. Loop will resume automatically

For details, see:
- Task history: .claude/TASK_QUEUE.md
- Agent metrics: .claude/AGENT_STATUS.md
- Loop log: .claude/logs/agent-loop.log
"

        echo "$report" | tee -a "$LOOP_LOG"

        return 0
    fi

    return 1
}

# Function: Check for deadlock
check_deadlock() {
    local pending_count=$(grep -c "^- \[ \]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local in_progress_count=$(grep -c "^- \[🔄\]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local active_agents=$(count_total_active_agents)

    # Deadlock: pending tasks exist but no agents working and no in-progress tasks
    if [ "$pending_count" -gt 0 ] && [ "$in_progress_count" -eq 0 ] && [ "$active_agents" -eq 0 ]; then
        log "WARN" "⚠️ DEADLOCK DETECTED: $pending_count tasks pending but no agents working"

        # Try to break deadlock by spawning agent for first pending task
        local first_task=$(grep -m 1 "^- \[ \]" "$TASK_QUEUE")
        local agent_type=$(echo "$first_task" | sed -E 's/.*`\[([a-z-]+)\]`.*/\1/')
        local task_id=$(echo "$first_task" | sed -E 's/.*#([0-9]*).*/\1/')

        log "INFO" "Breaking deadlock: Spawning $agent_type for task #$task_id"

        # Claim and spawn
        local claimed_id=$(claim_next_task "$agent_type")

        if [ -n "$claimed_id" ]; then
            spawn_agent "$agent_type" "$claimed_id"
            return 0
        else
            log "ERROR" "Failed to claim task #$task_id for deadlock recovery"
            return 1
        fi
    fi

    return 1
}

# Main orchestration logic

log "INFO" "Checking task queue status..."

# Check for completion first
if check_completion; then
    exit 0
fi

# Check for deadlock
if check_deadlock; then
    exit 0
fi

# Get current active agent count
active_agents=$(count_total_active_agents)

log "INFO" "Active agents: $active_agents / $MAX_TOTAL_AGENTS"

# Spawn agents for pending tasks (up to max concurrent limit)
for agent_type in developer auditor tester debugger documentation task-definer architecture-designer test-generator; do

    # Break if max concurrent agents reached
    if [ "$active_agents" -ge "$MAX_TOTAL_AGENTS" ]; then
        log "INFO" "Max concurrent agents ($MAX_TOTAL_AGENTS) reached. Deferring remaining tasks."
        break
    fi

    # Check if should spawn this agent type
    if should_spawn_agent "$agent_type"; then
        # Claim next task for this agent
        task_id=$(claim_next_task "$agent_type")

        if [ -n "$task_id" ]; then
            spawn_agent "$agent_type" "$task_id"
            active_agents=$((active_agents + 1))

            # Small delay between spawns to avoid thundering herd
            sleep 1
        fi
    fi
done

log "INFO" "Post-commit hook complete. $active_agents agents working."
log "INFO" "========================================"

exit 0
