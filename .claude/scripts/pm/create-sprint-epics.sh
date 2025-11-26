#!/bin/bash
# Create CCPM epics from existing sprint specifications
# Usage: bash .claude/scripts/pm/create-sprint-epics.sh [sprint-number]

SPRINTS=("1" "2" "3" "4" "5" "5.5" "6" "7" "8" "9" "9.5")

create_epic() {
    local sprint=$1
    local spec_file=""
    local plan_file=""
    local tasks_file=""
    local epic_name=""

    # Find matching files based on sprint number
    case $sprint in
        1)
            spec_file=".specify/specifications/sprint-1-patient-search-discovery.md"
            plan_file=".specify/plans/sprint-1-patient-search-discovery-plan.md"
            tasks_file=".specify/tasks/sprint-1-patient-search-discovery-tasks.md"
            epic_name="sprint-1-patient-search"
            ;;
        2)
            spec_file=".specify/specifications/sprint-2-timeline-view.md"
            plan_file=".specify/plans/sprint-2-timeline-view-plan.md"
            tasks_file=".specify/tasks/sprint-2-timeline-view-tasks.md"
            epic_name="sprint-2-timeline"
            ;;
        3)
            spec_file=".specify/specifications/sprint-3-full-text-search.md"
            plan_file=".specify/plans/sprint-3-full-text-search-plan.md"
            tasks_file=".specify/tasks/sprint-3-full-text-search-tasks.md"
            epic_name="sprint-3-search"
            ;;
        4)
            spec_file=".specify/specifications/sprint-4-ehr-deidentification.md"
            plan_file=".specify/plans/sprint-4-ehr-deidentification-plan.md"
            tasks_file=".specify/tasks/sprint-4-ehr-deidentification-tasks.md"
            epic_name="sprint-4-deidentification"
            ;;
        5)
            spec_file=".specify/specifications/sprint-5-clinical-coding.md"
            plan_file=".specify/plans/sprint-5-clinical-coding-plan.md"
            tasks_file=".specify/tasks/sprint-5-clinical-coding-tasks.md"
            epic_name="sprint-5-clinical-coding"
            ;;
        5.5)
            spec_file=".specify/specifications/sprint-5.5-event-bus.md"
            plan_file=".specify/plans/sprint-5.5-event-bus-plan.md"
            tasks_file=".specify/tasks/sprint-5.5-event-bus-tasks.md"
            epic_name="sprint-5.5-event-bus"
            ;;
        6)
            spec_file=".specify/specifications/sprint-6-clinical-decision-support.md"
            plan_file=".specify/plans/sprint-6-clinical-decision-support-plan.md"
            tasks_file=".specify/tasks/sprint-6-clinical-decision-support-tasks.md"
            epic_name="sprint-6-cds"
            ;;
        7)
            spec_file=".specify/specifications/sprint-7-automated-alerting.md"
            plan_file=".specify/plans/sprint-7-automated-alerting-plan.md"
            tasks_file=".specify/tasks/sprint-7-automated-alerting-tasks.md"
            epic_name="sprint-7-alerting"
            ;;
        8)
            spec_file=".specify/specifications/sprint-8-population-health-dashboards.md"
            plan_file=".specify/plans/sprint-8-population-health-dashboards-plan.md"
            tasks_file=".specify/tasks/sprint-8-population-health-dashboards-tasks.md"
            epic_name="sprint-8-dashboards"
            ;;
        9)
            spec_file=".specify/specifications/sprint-9-advanced-analytics.md"
            plan_file=".specify/plans/sprint-9-advanced-analytics-plan.md"
            tasks_file=".specify/tasks/sprint-9-advanced-analytics-tasks.md"
            epic_name="sprint-9-analytics"
            ;;
        9.5)
            spec_file=".specify/specifications/sprint-9.5-hardening-production.md"
            plan_file=".specify/plans/sprint-9.5-hardening-production-plan.md"
            tasks_file=".specify/tasks/sprint-9.5-hardening-production-tasks.md"
            epic_name="sprint-9.5-production"
            ;;
    esac

    echo "Creating epic: $epic_name"
    echo "  Spec: $spec_file"
    echo "  Plan: $plan_file"
    echo "  Tasks: $tasks_file"

    # Create epic directory
    mkdir -p ".claude/epics/$epic_name"

    # Copy spec as PRD reference
    if [ -f "$spec_file" ]; then
        cp "$spec_file" ".claude/prds/${epic_name}.md"
        echo "  ✓ PRD created"
    fi

    echo "  → Run: /pm:prd-parse $epic_name"
    echo "  → Then: /pm:epic-sync $epic_name"
    echo ""
}

# If sprint number provided, create only that sprint
if [ -n "$1" ]; then
    create_epic "$1"
else
    # Create all sprints
    for sprint in "${SPRINTS[@]}"; do
        create_epic "$sprint"
    done
fi

echo "Done! Next steps:"
echo "1. /pm:prd-parse <epic-name>  - Create epic from PRD"
echo "2. /pm:epic-sync <epic-name>  - Push to GitHub"
echo "3. /pm:epic-start <epic-name> - Launch parallel agents"
