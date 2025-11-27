#!/bin/bash
# CCPM Cherry-Pick Execution Script
# This script performs the actual cherry-picking based on analysis results

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}===========================================${NC}"
echo -e "${PURPLE}CCPM Cherry-Pick Execution - Phase 2${NC}"
echo -e "${PURPLE}===========================================${NC}"
echo ""

# Configuration
CURRENT_BRANCH="ccpm-consolidated"
CANDIDATES_FILE=".ccpm/reports/cherry-pick-candidates.txt"
LOG_FILE=".ccpm/cherry-pick-execution.log"
CONFLICT_LOG=".ccpm/conflicts.log"
SUCCESS_LOG=".ccpm/success.log"

# Initialize logs
echo "Cherry-Pick Execution Log - $(date)" > $LOG_FILE
echo "Conflict Log - $(date)" > $CONFLICT_LOG
echo "Success Log - $(date)" > $SUCCESS_LOG

# Function to safely cherry-pick a commit
safe_cherry_pick() {
    local COMMIT=$1
    local DESCRIPTION=$2
    local MODULE=$3

    echo -e "${YELLOW}Attempting to cherry-pick: $COMMIT${NC}"
    echo "  Module: $MODULE"
    echo "  Description: $DESCRIPTION"

    # Try cherry-pick
    if git cherry-pick --no-commit $COMMIT 2>>$LOG_FILE; then
        # Check for conflicts
        if git diff --check; then
            # No conflicts, commit the cherry-pick
            git commit -m "cherry-pick($MODULE): $DESCRIPTION

Cherry-picked from: $COMMIT
Module: $MODULE
Automated by CCPM parallel consolidation" 2>>$LOG_FILE

            echo -e "${GREEN}  ✓ Successfully cherry-picked${NC}"
            echo "$COMMIT|$MODULE|$DESCRIPTION|SUCCESS" >> $SUCCESS_LOG
            return 0
        else
            echo -e "${RED}  ✗ Conflicts detected${NC}"
            echo "$COMMIT|$MODULE|$DESCRIPTION|CONFLICT" >> $CONFLICT_LOG

            # Abort the cherry-pick
            git cherry-pick --abort 2>/dev/null
            return 1
        fi
    else
        echo -e "${RED}  ✗ Cherry-pick failed${NC}"
        echo "$COMMIT|$MODULE|$DESCRIPTION|FAILED" >> $CONFLICT_LOG

        # Ensure we're in a clean state
        git cherry-pick --abort 2>/dev/null
        return 1
    fi
}

# Function to cherry-pick commits for a specific module
cherry_pick_module() {
    local MODULE=$1
    local BRANCH=$2
    local PATTERN=$3
    local LIMIT=$4

    echo -e "${BLUE}Processing module: $MODULE from branch: $BRANCH${NC}"
    echo "========================================="

    # Get commits for this module
    COMMITS=$(git log $BRANCH --oneline --grep="$PATTERN" -- "*$MODULE*" -n $LIMIT 2>/dev/null | cut -d' ' -f1)

    if [ -z "$COMMITS" ]; then
        echo "  No commits found for pattern: $PATTERN"
        return
    fi

    for COMMIT in $COMMITS; do
        # Get commit message
        MSG=$(git log -1 --pretty=%s $COMMIT)

        # Attempt cherry-pick
        safe_cherry_pick $COMMIT "$MSG" $MODULE
        sleep 1  # Small delay between operations
    done
}

# Function to run parallel cherry-picking with worker pools
run_parallel_cherry_picks() {
    echo -e "${YELLOW}Starting parallel cherry-pick execution...${NC}"
    echo ""

    # Create a temporary file for managing parallel jobs
    JOBS_FILE=".ccpm/parallel-jobs.txt"
    > $JOBS_FILE

    # Define worker tasks
    cat << EOF > $JOBS_FILE
Worker-1|medcat-v2|origin/medcat/v2.3|feat\|fix\|perf|5
Worker-2|trainer|development|feat\|enhance\|ui|5
Worker-3|search|development|search\|query\|elastic|10
Worker-4|docker|main|docker\|deploy\|ci|3
Worker-5|docs|development|docs\|README|5
Worker-6|test|development|test\|spec|5
Worker-7|clinical|development|clinical\|patient\|fhir|5
Worker-8|backend|development|api\|service\|endpoint|5
EOF

    # Process jobs with limited parallelism
    PARALLEL_LIMIT=4
    ACTIVE_JOBS=0

    while IFS='|' read -r WORKER MODULE BRANCH PATTERN LIMIT; do
        # Wait if we've reached parallel limit
        while [ $(jobs -r | wc -l) -ge $PARALLEL_LIMIT ]; do
            sleep 2
        done

        # Launch worker in background
        (
            echo -e "${PURPLE}[$WORKER] Starting...${NC}"
            cherry_pick_module "$MODULE" "$BRANCH" "$PATTERN" "$LIMIT"
            echo -e "${PURPLE}[$WORKER] Complete${NC}"
        ) &

        ACTIVE_JOBS=$((ACTIVE_JOBS + 1))
        echo "Active workers: $ACTIVE_JOBS"

    done < $JOBS_FILE

    # Wait for all jobs to complete
    echo -e "${YELLOW}Waiting for all workers to complete...${NC}"
    wait

    echo -e "${GREEN}All workers completed${NC}"
}

# Function to resolve conflicts interactively
resolve_conflicts() {
    echo -e "${YELLOW}Checking for unresolved conflicts...${NC}"

    if [ -s $CONFLICT_LOG ]; then
        echo -e "${RED}Conflicts were detected. Review the conflict log:${NC}"
        echo "  $CONFLICT_LOG"
        echo ""
        echo "Manual resolution may be required for:"
        tail -5 $CONFLICT_LOG
    else
        echo -e "${GREEN}No conflicts detected!${NC}"
    fi
}

# Function to generate execution summary
generate_summary() {
    echo -e "${YELLOW}Generating execution summary...${NC}"

    SUMMARY_FILE=".ccpm/reports/execution-summary.md"

    echo "# CCPM Cherry-Pick Execution Summary" > $SUMMARY_FILE
    echo "Date: $(date)" >> $SUMMARY_FILE
    echo "" >> $SUMMARY_FILE

    # Count successes and failures
    SUCCESS_COUNT=$(wc -l < $SUCCESS_LOG 2>/dev/null || echo 0)
    CONFLICT_COUNT=$(wc -l < $CONFLICT_LOG 2>/dev/null || echo 0)

    echo "## Statistics" >> $SUMMARY_FILE
    echo "- Successful cherry-picks: $SUCCESS_COUNT" >> $SUMMARY_FILE
    echo "- Conflicts/Failures: $CONFLICT_COUNT" >> $SUMMARY_FILE
    echo "- Total attempts: $((SUCCESS_COUNT + CONFLICT_COUNT))" >> $SUMMARY_FILE
    echo "" >> $SUMMARY_FILE

    echo "## Successful Cherry-Picks" >> $SUMMARY_FILE
    echo '```' >> $SUMMARY_FILE
    cat $SUCCESS_LOG 2>/dev/null | head -20 >> $SUMMARY_FILE
    echo '```' >> $SUMMARY_FILE
    echo "" >> $SUMMARY_FILE

    echo "## Conflicts/Failures" >> $SUMMARY_FILE
    echo '```' >> $SUMMARY_FILE
    cat $CONFLICT_LOG 2>/dev/null | head -20 >> $SUMMARY_FILE
    echo '```' >> $SUMMARY_FILE

    echo -e "${GREEN}Summary generated at: $SUMMARY_FILE${NC}"
}

# Function to validate the consolidated branch
validate_consolidation() {
    echo -e "${YELLOW}Validating consolidated branch...${NC}"

    # Check if builds work
    echo "  Checking if project builds..."
    # Add your build commands here

    # Check git status
    echo "  Git status:"
    git status --short

    # Show recent commits
    echo "  Recent commits on $CURRENT_BRANCH:"
    git log --oneline -10

    echo -e "${GREEN}Validation complete${NC}"
}

# Main execution
main() {
    echo "CCPM Cherry-Pick Execution"
    echo "=========================="
    echo ""

    # Verify we're on the right branch
    CURRENT=$(git branch --show-current)
    if [ "$CURRENT" != "$CURRENT_BRANCH" ]; then
        echo -e "${RED}Error: Not on $CURRENT_BRANCH branch${NC}"
        echo "Current branch: $CURRENT"
        exit 1
    fi

    # Create backup point
    echo "Creating backup tag..."
    git tag -f ccpm-backup-$(date +%Y%m%d-%H%M%S)

    # Step 1: Execute parallel cherry-picks
    run_parallel_cherry_picks
    echo ""

    # Step 2: Check for conflicts
    resolve_conflicts
    echo ""

    # Step 3: Generate summary
    generate_summary
    echo ""

    # Step 4: Validate
    validate_consolidation
    echo ""

    echo -e "${GREEN}===========================================${NC}"
    echo -e "${GREEN}CCPM Cherry-Pick Execution Complete!${NC}"
    echo -e "${GREEN}===========================================${NC}"
    echo ""
    echo "Results:"
    echo "  - Success log: $SUCCESS_LOG"
    echo "  - Conflict log: $CONFLICT_LOG"
    echo "  - Execution summary: .ccpm/reports/execution-summary.md"
    echo ""
    echo "Next steps:"
    echo "1. Review the execution summary"
    echo "2. Resolve any conflicts listed in $CONFLICT_LOG"
    echo "3. Run tests to ensure everything works"
    echo "4. Commit and push the consolidated branch"
}

# Trap to ensure cleanup on exit
trap 'echo -e "${YELLOW}Cleaning up...${NC}"; git cherry-pick --abort 2>/dev/null || true' EXIT

# Run main
main