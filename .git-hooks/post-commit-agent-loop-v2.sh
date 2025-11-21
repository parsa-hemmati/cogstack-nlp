#!/bin/bash
# Post-commit hook: Autonomous Agent Loop Orchestrator (Fixed)
# Version: 1.1.0 - Bug fixes for concurrent spawning

set -e

# Configuration
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"
TASK_QUEUE="$CLAUDE_DIR/TASK_QUEUE.md"
AGENT_STATUS="$CLAUDE_DIR/AGENT_STATUS.md"
CONFIG_FILE="$CLAUDE_DIR/agent-loop-config.yaml"
LOOP_LOG="$CLAUDE_DIR/logs/agent-loop.log"

mkdir -p "$CLAUDE_DIR/logs"
touch "$LOOP_LOG"

log() {
    local level=$1
    shift
    echo "[$(date -Iseconds)] [$level] $@" >> "$LOOP_LOG"
    [ "$level" = "INFO" ] && echo "[$level] $@"
}

load_config() {
    local key=$1
    local default=$2
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "$default"
        return
    fi
    local value=$(grep "^${key}:" "$CONFIG_FILE" 2>/dev/null | sed 's/^[^:]*:[[:space:]]*//' | tr -d '"' | tr -d "'" | head -1)
    echo "${value:-$default}"
}

MAX_TOTAL_AGENTS=$(load_config "max_total_agents" "6")
ENABLED=$(load_config "git_hooks.post_commit.enabled" "true")
DRY_RUN=$(load_config "debug.dry_run" "false")

log "INFO" "========================================"
log "INFO" "Post-commit hook: Agent loop starting"
log "INFO" "Commit: $(git rev-parse --short HEAD)"
log "INFO" "Config: max_agents=$MAX_TOTAL_AGENTS, dry_run=$DRY_RUN"

[ "$ENABLED" != "true" ] && { log "INFO" "Hook disabled. Exiting."; exit 0; }
[ ! -f "$TASK_QUEUE" ] && { log "WARN" "TASK_QUEUE.md not found. Exiting."; exit 0; }

get_max_instances() {
    local agent_type=$1
    load_config "agent_limits.$agent_type" "1"
}

get_timeout() {
    local agent_type=$1
    load_config "timeouts.$agent_type" "3600"
}

count_active_agents() {
    local agent_type=$1
    grep -c "Status: WORKING.*$agent_type" "$AGENT_STATUS" 2>/dev/null || echo "0"
}

count_total_active() {
    grep -c "Status: WORKING" "$AGENT_STATUS" 2>/dev/null || echo "0"
}

get_pending_tasks() {
    local agent_type=$1
    grep "^- \[ \] #[0-9]* \`\[$agent_type\]\`" "$TASK_QUEUE" 2>/dev/null || echo ""
}

claim_next_task() {
    local agent_type=$1
    local task_id=""

    (
        flock -x 200
        # Fixed: Use head -1 and tr to remove newlines
        task_id=$(grep -m 1 "^- \[ \] #[0-9]* \`\[$agent_type\]\`" "$TASK_QUEUE" 2>/dev/null | \
                  sed -E 's/.*#([0-9]+).*/\1/' | head -1 | tr -d '\n')

        if [ -n "$task_id" ]; then
            local timestamp=$(date +%H:%M:%S)
            # Fixed: Escape special characters and use simpler sed
            sed -i "/^- \[ \] #${task_id} \`\[${agent_type}\]\`/s/\[ \]/[🔄] (claimed: ${timestamp}, PID: $$)/" "$TASK_QUEUE"
            log "INFO" "Claimed task #$task_id for $agent_type"
        fi
        echo "$task_id"
    ) 200>"$TASK_QUEUE.lock"
}

should_spawn_agent() {
    local agent_type=$1
    local active_count=$(count_active_agents "$agent_type")
    local max_instances=$(get_max_instances "$agent_type")

    if [ "$active_count" -ge "$max_instances" ]; then
        log "DEBUG" "Skipping $agent_type: $active_count/$max_instances active"
        return 1
    fi

    local pending=$(get_pending_tasks "$agent_type")
    if [ -z "$pending" ]; then
        log "DEBUG" "Skipping $agent_type: No pending tasks"
        return 1
    fi

    return 0
}

get_task_context() {
    local task_id=$1
    grep -A 5 "^- \[🔄\] #$task_id" "$TASK_QUEUE" 2>/dev/null | head -6
}

spawn_agent() {
    local agent_type=$1
    local task_id=$2

    [ "$DRY_RUN" = "true" ] && { log "INFO" "[DRY RUN] Would spawn $agent_type for #$task_id"; return 0; }

    log "INFO" "Spawning $agent_type for task #$task_id..."

    local task_context=$(get_task_context "$task_id")
    local timeout=$(get_timeout "$agent_type")

    local agent_prompt="You are the $agent_type agent in a continuous autonomous development loop.

**Your Task**: #$task_id from TASK_QUEUE.md

$task_context

**Instructions**:
1. Read .claude/TASK_QUEUE.md to understand task #$task_id
2. Read .claude/COORDINATION.md for messages directed to you
3. Read your agent definition: .claude/agents/$agent_type.md
4. Execute the task following TDD approach
5. Update .claude/AGENT_STATUS.md every 30s (heartbeat)
6. When complete:
   - Mark task [✅] in TASK_QUEUE.md
   - Create follow-up tasks if needed
   - Update COORDINATION.md with messages
   - Update CONTEXT.md if applicable
   - Commit with proper message
7. Post-commit hook spawns next agents automatically

**Critical Rules**:
- Work independently (no user questions unless blocked)
- Mark task complete when done
- Create tasks for other agents as needed
- Update all shared files
- Commit immediately when complete

**Timeout**: $timeout seconds

Begin task #$task_id now."

    local prompt_file="$CLAUDE_DIR/logs/agent-${agent_type}-${task_id}.prompt"
    echo "$agent_prompt" > "$prompt_file"

    local agent_script="$CLAUDE_DIR/scripts/agent-wrapper.sh"
    if [ ! -f "$agent_script" ]; then
        log "ERROR" "Agent wrapper not found at $agent_script"
        return 1
    fi

    bash "$agent_script" "$agent_type" "$task_id" "$timeout" "$prompt_file" >> "$LOOP_LOG" 2>&1 &
    local agent_pid=$!

    log "INFO" "Agent $agent_type spawned (PID: $agent_pid, task #$task_id)"
    echo "$agent_pid" > "$CLAUDE_DIR/logs/agent-${agent_type}-${task_id}.pid"
}

check_completion() {
    local pending=$(grep -c "^- \[ \]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local in_progress=$(grep -c "^- \[🔄\]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local completed=$(grep -c "^- \[✅\]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local failed=$(grep -c "^- \[❌\]" "$TASK_QUEUE" 2>/dev/null || echo "0")

    if [ "$pending" -eq 0 ] && [ "$in_progress" -eq 0 ]; then
        log "INFO" "✅ AUTONOMOUS LOOP COMPLETE!"

        local total=$((completed + failed))
        local success_rate=0
        [ "$total" -gt 0 ] && success_rate=$((100 * completed / total))

        cat << EOF | tee -a "$LOOP_LOG"

╔════════════════════════════════════════════════════════════╗
║  AUTONOMOUS DEVELOPMENT LOOP - COMPLETION REPORT          ║
╚════════════════════════════════════════════════════════════╝

✅ Tasks Completed: $completed
❌ Tasks Failed: $failed
📊 Success Rate: ${success_rate}%
⏱️  Session: $(head -1 "$LOOP_LOG" | cut -d']' -f1 | tr -d '[') to $(date -Iseconds)

All agents IDLE. Loop terminated.

To resume:
1. Add tasks to .claude/TASK_QUEUE.md
2. Commit to trigger loop

EOF
        return 0
    fi
    return 1
}

check_deadlock() {
    local pending=$(grep -c "^- \[ \]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local in_progress=$(grep -c "^- \[🔄\]" "$TASK_QUEUE" 2>/dev/null || echo "0")
    local active=$(count_total_active)

    if [ "$pending" -gt 0 ] && [ "$in_progress" -eq 0 ] && [ "$active" -eq 0 ]; then
        log "WARN" "⚠️ DEADLOCK: $pending tasks pending, no agents working"

        local first_task=$(grep -m 1 "^- \[ \]" "$TASK_QUEUE")
        local agent_type=$(echo "$first_task" | sed -E 's/.*`\[([a-z-]+)\]`.*/\1/' | head -1 | tr -d '\n')
        local task_id=$(claim_next_task "$agent_type")

        if [ -n "$task_id" ]; then
            log "INFO" "Breaking deadlock: spawning $agent_type for #$task_id"
            spawn_agent "$agent_type" "$task_id"
            return 0
        fi
    fi
    return 1
}

# Main orchestration
log "INFO" "Checking task queue..."

check_completion && exit 0
check_deadlock && exit 0

# Fixed: Get clean count
active_agents=$(count_total_active)
log "INFO" "Active agents: $active_agents / $MAX_TOTAL_AGENTS"

# Spawn agents up to max concurrent limit
spawned=0
for agent_type in developer auditor tester debugger documentation task-definer architecture-designer test-generator; do

    # Break if max reached
    [ "$active_agents" -ge "$MAX_TOTAL_AGENTS" ] && {
        log "INFO" "Max agents ($MAX_TOTAL_AGENTS) reached. Deferring."
        break
    }

    # Spawn multiple instances if agent type allows
    local max_instances=$(get_max_instances "$agent_type")
    local current_count=$(count_active_agents "$agent_type")
    local can_spawn=$((max_instances - current_count))

    # Spawn up to max instances for this agent type
    for ((i=0; i<can_spawn; i++)); do
        [ "$active_agents" -ge "$MAX_TOTAL_AGENTS" ] && break

        if should_spawn_agent "$agent_type"; then
            task_id=$(claim_next_task "$agent_type")

            if [ -n "$task_id" ]; then
                spawn_agent "$agent_type" "$task_id"
                active_agents=$((active_agents + 1))
                spawned=$((spawned + 1))
                sleep 0.5  # Small delay between spawns
            else
                break  # No more tasks for this agent type
            fi
        else
            break
        fi
    done
done

log "INFO" "Post-commit complete. Spawned: $spawned, Total active: $active_agents"
log "INFO" "========================================"

exit 0
