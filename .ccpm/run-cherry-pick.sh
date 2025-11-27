#!/bin/bash
# CCPM Parallel Cherry-Pick Execution Script
# This script coordinates multiple workers to cherry-pick best implementations

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CCPM Parallel Cherry-Pick Consolidation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
CCPM_CONFIG=".ccpm/ccpm-cherry-pick.yaml"
WORKERS=8
PARALLEL_LIMIT=4
CURRENT_BRANCH="ccpm-consolidated"
ANALYSIS_DIR=".ccpm/analysis"
REPORTS_DIR=".ccpm/reports"

# Create necessary directories
mkdir -p $ANALYSIS_DIR
mkdir -p $REPORTS_DIR

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    # Check if we're on the correct branch
    CURRENT=$(git branch --show-current)
    if [ "$CURRENT" != "$CURRENT_BRANCH" ]; then
        echo -e "${RED}Error: Not on $CURRENT_BRANCH branch${NC}"
        echo "Please checkout $CURRENT_BRANCH first"
        exit 1
    fi

    # Fetch all remotes
    echo "Fetching all remotes..."
    git fetch --all --prune

    echo -e "${GREEN}Prerequisites checked successfully${NC}"
}

# Function to analyze branches for a specific module
analyze_module() {
    local WORKER_ID=$1
    local MODULE=$2
    local BRANCHES=$3
    local OUTPUT_FILE=$4

    echo -e "${BLUE}[$WORKER_ID] Analyzing module: $MODULE${NC}"
    echo "# Analysis Report for $MODULE" > $OUTPUT_FILE
    echo "## Branches Analyzed" >> $OUTPUT_FILE
    echo "" >> $OUTPUT_FILE

    for BRANCH in $BRANCHES; do
        echo "  Checking branch: $BRANCH"
        echo "### Branch: $BRANCH" >> $OUTPUT_FILE

        # Check if module exists in branch
        git ls-tree -r $BRANCH --name-only | grep -E "$MODULE" | head -10 >> $OUTPUT_FILE 2>/dev/null || echo "No matches found" >> $OUTPUT_FILE

        # Get recent commits for this module
        echo "#### Recent Commits:" >> $OUTPUT_FILE
        git log --oneline $BRANCH -- "*$MODULE*" -10 2>/dev/null >> $OUTPUT_FILE || echo "No commits found" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    done

    echo -e "${GREEN}[$WORKER_ID] Analysis complete${NC}"
}

# Function to run parallel workers
run_parallel_analysis() {
    echo -e "${YELLOW}Starting parallel analysis with $WORKERS workers...${NC}"
    echo ""

    # Worker 1: MedCAT Core
    (
        analyze_module "Worker-1" "medcat-v2" \
            "origin/medcat/v2.3 origin/medcat/v2.2 origin/medcat/v2.1 development main" \
            "$ANALYSIS_DIR/medcat-core-analysis.md"
    ) &

    # Worker 2: UI/Frontend
    (
        analyze_module "Worker-2" "trainer" \
            "myfork/development development origin/trainer-remove-medcat-utils main" \
            "$ANALYSIS_DIR/ui-frontend-analysis.md"
    ) &

    # Worker 3: Search & NLP
    (
        analyze_module "Worker-3" "search" \
            "development myfork/development main" \
            "$ANALYSIS_DIR/search-nlp-analysis.md"
    ) &

    # Worker 4: Infrastructure
    (
        analyze_module "Worker-4" "docker\|scripts\|deploy" \
            "myfork/autonomous/mvp-execution development main" \
            "$ANALYSIS_DIR/infrastructure-analysis.md"
    ) &

    # Limit parallel processes
    while [ $(jobs -r | wc -l) -ge $PARALLEL_LIMIT ]; do
        sleep 1
    done

    # Worker 5: Documentation
    (
        analyze_module "Worker-5" "docs\|README\|CONTEXT" \
            "development myfork/development main" \
            "$ANALYSIS_DIR/documentation-analysis.md"
    ) &

    # Worker 6: Testing
    (
        analyze_module "Worker-6" "test" \
            "development myfork/development main" \
            "$ANALYSIS_DIR/testing-quality-analysis.md"
    ) &

    # Worker 7: Clinical Features
    (
        analyze_module "Worker-7" "clinical\|patient\|fhir" \
            "development myfork/development main" \
            "$ANALYSIS_DIR/clinical-features-analysis.md"
    ) &

    # Worker 8: API & Backend
    (
        analyze_module "Worker-8" "backend\|api" \
            "development myfork/development main" \
            "$ANALYSIS_DIR/api-backend-analysis.md"
    ) &

    # Wait for all workers to complete
    echo -e "${YELLOW}Waiting for all workers to complete...${NC}"
    wait

    echo -e "${GREEN}All workers completed analysis${NC}"
}

# Function to identify cherry-pick candidates
identify_candidates() {
    echo -e "${YELLOW}Identifying cherry-pick candidates...${NC}"

    # Create consolidated candidate list
    CANDIDATES_FILE="$REPORTS_DIR/cherry-pick-candidates.txt"
    echo "# Cherry-Pick Candidates" > $CANDIDATES_FILE
    echo "Generated: $(date)" >> $CANDIDATES_FILE
    echo "" >> $CANDIDATES_FILE

    # Example: Find commits with high value keywords
    echo "## High-Value Commits" >> $CANDIDATES_FILE
    git log --all --grep="feat\|fix\|perf\|security" --oneline --since="30 days ago" | head -50 >> $CANDIDATES_FILE

    echo -e "${GREEN}Candidates identified and saved to $CANDIDATES_FILE${NC}"
}

# Function to create consolidation plan
create_consolidation_plan() {
    echo -e "${YELLOW}Creating consolidation plan...${NC}"

    PLAN_FILE="$REPORTS_DIR/consolidation-plan.md"
    echo "# Consolidation Plan for $CURRENT_BRANCH" > $PLAN_FILE
    echo "Generated: $(date)" >> $PLAN_FILE
    echo "" >> $PLAN_FILE
    echo "## Summary" >> $PLAN_FILE
    echo "- Target Branch: $CURRENT_BRANCH" >> $PLAN_FILE
    echo "- Workers: $WORKERS" >> $PLAN_FILE
    echo "- Modules Analyzed: 8" >> $PLAN_FILE
    echo "" >> $PLAN_FILE
    echo "## Merge Sequence" >> $PLAN_FILE
    echo "1. Documentation updates (no conflicts expected)" >> $PLAN_FILE
    echo "2. Test additions (minimal conflicts)" >> $PLAN_FILE
    echo "3. Infrastructure changes" >> $PLAN_FILE
    echo "4. Backend services" >> $PLAN_FILE
    echo "5. Frontend components" >> $PLAN_FILE
    echo "6. Clinical features" >> $PLAN_FILE
    echo "7. MedCAT core updates" >> $PLAN_FILE
    echo "" >> $PLAN_FILE

    echo -e "${GREEN}Consolidation plan created${NC}"
}

# Function to generate final report
generate_report() {
    echo -e "${YELLOW}Generating final report...${NC}"

    REPORT_FILE="$REPORTS_DIR/final-report.md"
    echo "# CCPM Cherry-Pick Consolidation Report" > $REPORT_FILE
    echo "## Execution Summary" >> $REPORT_FILE
    echo "- Date: $(date)" >> $REPORT_FILE
    echo "- Branch: $CURRENT_BRANCH" >> $REPORT_FILE
    echo "- Workers Used: $WORKERS" >> $REPORT_FILE
    echo "" >> $REPORT_FILE
    echo "## Analysis Results" >> $REPORT_FILE
    echo "" >> $REPORT_FILE

    # Append all analysis files
    for analysis in $ANALYSIS_DIR/*.md; do
        echo "### $(basename $analysis .md)" >> $REPORT_FILE
        head -20 $analysis >> $REPORT_FILE
        echo "..." >> $REPORT_FILE
        echo "" >> $REPORT_FILE
    done

    echo -e "${GREEN}Report generated at $REPORT_FILE${NC}"
}

# Main execution
main() {
    echo "Starting CCPM Parallel Cherry-Pick Process"
    echo "==========================================="
    echo ""

    # Step 1: Check prerequisites
    check_prerequisites
    echo ""

    # Step 2: Run parallel analysis
    run_parallel_analysis
    echo ""

    # Step 3: Identify candidates
    identify_candidates
    echo ""

    # Step 4: Create consolidation plan
    create_consolidation_plan
    echo ""

    # Step 5: Generate report
    generate_report
    echo ""

    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}CCPM Cherry-Pick Analysis Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Next Steps:"
    echo "1. Review analysis reports in: $ANALYSIS_DIR/"
    echo "2. Review consolidation plan: $REPORTS_DIR/consolidation-plan.md"
    echo "3. Review candidates list: $REPORTS_DIR/cherry-pick-candidates.txt"
    echo "4. Execute cherry-picks using: git cherry-pick <commit-sha>"
    echo ""
    echo "To execute the actual cherry-picks, run:"
    echo "  .ccpm/execute-cherry-picks.sh"
}

# Run main function
main