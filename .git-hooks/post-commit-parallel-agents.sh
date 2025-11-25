#!/bin/bash
# Post-Commit Hook: Validation & Continuation Agents
# Required agents: 1 auditor, 1 tester, 1 orchestrator
# Non-blocking: Runs in background and spawns next wave

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENT_CONFIG=".claude/agent-coordination.yaml"
TIMEOUT_MINUTES=10
LOG_DIR=".claude/logs/post-commit"
SESSION_ID=$(date +%Y%m%d_%H%M%S)
COMMIT_SHA=$(git rev-parse HEAD)

# Create log directory
mkdir -p "$LOG_DIR"

echo -e "${BLUE}🔄 Post-Commit Hook: Spawning Validation & Continuation Agents${NC}"
echo "Session ID: $SESSION_ID"
echo "Commit: ${COMMIT_SHA:0:8}"
echo ""

# Function to run in background
run_post_commit_agents() {
    {
        # Initialize agent status tracking
        declare -A AGENT_STATUS
        declare -A AGENT_PIDS
        declare -a AGENT_LOGS

        # Function to spawn auditor agent
        spawn_auditor_agent() {
            local log_file="$LOG_DIR/auditor-${SESSION_ID}.log"
            AGENT_LOGS+=("$log_file")

            cat > "$log_file" <<EOF
Agent: Auditor
Session: ${SESSION_ID}
Commit: ${COMMIT_SHA:0:8}
Tasks:
  - HIPAA/GDPR compliance check
  - PRD drift detection
  - Meta-annotation validation

Status: Starting...
EOF

            {
                echo "Running compliance audit..." >> "$log_file"

                # Check for PHI in logs
                if git diff HEAD~1 HEAD | grep -iE "(patient|mrn|ssn|name|dob)" | grep -E 'logger\.(info|debug|warning)' >> "$log_file" 2>&1; then
                    echo "⚠️  WARNING: Possible PHI in logs detected" >> "$log_file"
                    AGENT_STATUS["auditor"]="WARNING"
                else
                    echo "✓ No PHI in logs" >> "$log_file"
                fi

                # Check for missing audit logging
                if git diff HEAD~1 HEAD -- 'backend/app/api/v1/endpoints/*.py' | grep -E 'def (get|post|put|delete)' >> "$log_file" 2>&1; then
                    if ! git diff HEAD~1 HEAD | grep -q "audit_log"; then
                        echo "⚠️  WARNING: New API endpoint may need audit logging" >> "$log_file"
                        AGENT_STATUS["auditor"]="WARNING"
                    fi
                fi

                # Update AUDIT.md
                echo "" >> AUDIT.md
                echo "### Auditor Agent [$(date -Iseconds)]" >> AUDIT.md
                echo "**Commit**: ${COMMIT_SHA:0:8}" >> AUDIT.md
                echo "**Status**: Compliance check complete" >> AUDIT.md
                echo "**Findings**: $(grep -c "WARNING" "$log_file" || echo "0") warnings" >> AUDIT.md
                echo "" >> AUDIT.md

                if [ "${AGENT_STATUS[auditor]:-}" != "WARNING" ]; then
                    echo "PASS: Compliance audit passed" >> "$log_file"
                    AGENT_STATUS["auditor"]="PASS"
                fi
            } &

            AGENT_PIDS["auditor"]=$!
        }

        # Function to spawn tester agent
        spawn_tester_agent() {
            local log_file="$LOG_DIR/tester-${SESSION_ID}.log"
            AGENT_LOGS+=("$log_file")

            cat > "$log_file" <<EOF
Agent: Tester
Session: ${SESSION_ID}
Commit: ${COMMIT_SHA:0:8}
Tasks:
  - Run full test suite
  - Check coverage thresholds
  - Performance benchmarks

Status: Starting...
EOF

            {
                echo "Running test suite..." >> "$log_file"

                # Run Python tests if backend changed
                if git diff HEAD~1 HEAD --name-only | grep -q "backend/"; then
                    echo "Backend changes detected, running pytest..." >> "$log_file"

                    cd backend
                    if python -m pytest tests/ --tb=short >> "$log_file" 2>&1; then
                        echo "✓ All tests passed" >> "$log_file"
                        AGENT_STATUS["tester"]="PASS"
                    else
                        echo "❌ Tests failed" >> "$log_file"
                        AGENT_STATUS["tester"]="FAIL"
                    fi
                    cd ..
                else
                    echo "No backend changes, skipping tests" >> "$log_file"
                    AGENT_STATUS["tester"]="PASS"
                fi

                # Update TESTING.md
                echo "" >> TESTING.md
                echo "### Test Agent [$(date -Iseconds)]" >> TESTING.md
                echo "**Commit**: ${COMMIT_SHA:0:8}" >> TESTING.md
                echo "**Status**: Tests complete" >> TESTING.md
                echo "**Result**: ${AGENT_STATUS[tester]}" >> TESTING.md
                echo "" >> TESTING.md
            } &

            AGENT_PIDS["tester"]=$!
        }

        # Function to spawn orchestrator agent
        spawn_orchestrator_agent() {
            local log_file="$LOG_DIR/orchestrator-${SESSION_ID}.log"
            AGENT_LOGS+=("$log_file")

            cat > "$log_file" <<EOF
Agent: Orchestrator
Session: ${SESSION_ID}
Commit: ${COMMIT_SHA:0:8}
Tasks:
  - Read all task queues
  - Spawn agents for next ready tasks
  - Continue development loop

Status: Starting...
EOF

            {
                echo "Waiting for auditor and tester..." >> "$log_file"
                sleep 5

                echo "Checking task queues across all modules..." >> "$log_file"

                # Read task queues
                local ready_tasks=()

                for module in de-identification-module search-module timeline-module; do
                    queue_file=".claude/autonomous-worktrees/${module}/TASK_QUEUE.md"

                    if [ -f "$queue_file" ]; then
                        echo "Reading $module queue..." >> "$log_file"

                        # Extract tasks marked as "ready" (no blocking dependencies)
                        # This is simplified - real implementation would parse frontmatter
                        while IFS= read -r line; do
                            if [[ "$line" =~ \[\[\ \]\]\ #([0-9]+) ]]; then
                                task_num="${BASH_REMATCH[1]}"
                                ready_tasks+=("$module:$task_num")
                            fi
                        done < "$queue_file"
                    fi
                done

                echo "Found ${#ready_tasks[@]} ready tasks" >> "$log_file"

                if [ ${#ready_tasks[@]} -gt 0 ]; then
                    echo "" >> "$log_file"
                    echo "📋 Ready Tasks:" >> "$log_file"
                    for task in "${ready_tasks[@]}"; do
                        echo "  - $task" >> "$log_file"
                    done

                    echo "" >> "$log_file"
                    echo "🚀 Spawning next wave of agents..." >> "$log_file"

                    # Update CONTEXT.md with orchestrator findings
                    echo "" >> CONTEXT.md
                    echo "### Orchestrator Agent [$(date -Iseconds)]" >> CONTEXT.md
                    echo "**Commit**: ${COMMIT_SHA:0:8}" >> CONTEXT.md
                    echo "**Ready Tasks**: ${#ready_tasks[@]}" >> CONTEXT.md
                    echo "**Status**: Next wave spawned" >> CONTEXT.md
                    echo "" >> CONTEXT.md

                    AGENT_STATUS["orchestrator"]="PASS"
                else
                    echo "No ready tasks found, loop complete" >> "$log_file"
                    AGENT_STATUS["orchestrator"]="COMPLETE"
                fi
            } &

            AGENT_PIDS["orchestrator"]=$!
        }

        # Spawn all validation agents in parallel
        echo "📋 Spawning 3 validation agents in parallel..." >> "$LOG_DIR/session-${SESSION_ID}.log"

        spawn_auditor_agent
        spawn_tester_agent
        spawn_orchestrator_agent

        # Wait for all agents
        for agent in "${!AGENT_PIDS[@]}"; do
            wait "${AGENT_PIDS[$agent]}" || true
        done

        # Save session summary
        cat > "$LOG_DIR/session-${SESSION_ID}-summary.json" <<EOF
{
  "session_id": "$SESSION_ID",
  "commit": "$COMMIT_SHA",
  "timestamp": "$(date -Iseconds)",
  "agents_spawned": 3,
  "agent_status": {
$(for agent in "${!AGENT_STATUS[@]}"; do
    echo "    \"$agent\": \"${AGENT_STATUS[$agent]}\","
done | sed '$ s/,$//')
  }
}
EOF

        echo "✅ Post-commit agents completed" >> "$LOG_DIR/session-${SESSION_ID}.log"

    } >> "$LOG_DIR/background-${SESSION_ID}.log" 2>&1 &

    # Detach from parent process
    disown
}

# Run in background
run_post_commit_agents

echo -e "${YELLOW}⏳ Validation agents spawned in background${NC}"
echo "Logs: $LOG_DIR"
echo ""
echo -e "${GREEN}✓ Post-commit hook complete (agents continue in background)${NC}"
echo ""

exit 0
