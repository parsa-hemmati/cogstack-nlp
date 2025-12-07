#!/bin/bash
# =============================================================================
# E2E Test Runner - All Modules
# =============================================================================
# Purpose: Run Playwright E2E tests across all project modules
# Usage:
#   ./scripts/e2e-test-all.sh              # Test all modules
#   ./scripts/e2e-test-all.sh medcat-trainer  # Test specific module
#   ./scripts/e2e-test-all.sh --list       # List available modules
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TESTS_DIR="${PROJECT_ROOT}/tests/e2e"
RESULTS_DIR="${PROJECT_ROOT}/tests/e2e/results"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Module configurations
declare -A MODULES
MODULES["medcat-trainer"]="medcat-trainer|8001|MedCAT Trainer"
MODULES["medcat-demo-app"]="medcat-demo-app|8000|MedCAT Demo App"
MODULES["anoncat-demo-app"]="anoncat-demo-app|8000|AnonCAT Demo App"
MODULES["medcat-service"]="medcat-service/docker|5000|MedCAT Service API"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# List available modules
list_modules() {
    echo ""
    log_info "Available modules for E2E testing:"
    echo ""
    for module in "${!MODULES[@]}"; do
        IFS='|' read -r path port name <<< "${MODULES[$module]}"
        echo "  - $module (Port: $port) - $name"
    done
    echo ""
    echo "Usage: $0 [module-name]"
    echo "       $0 --all"
    echo ""
}

# Start a module's Docker services
start_module() {
    local module=$1
    IFS='|' read -r path port name <<< "${MODULES[$module]}"

    log_info "Starting $name..."

    local compose_dir="${PROJECT_ROOT}/${path}"

    if [ ! -d "$compose_dir" ]; then
        log_error "Module directory not found: $compose_dir"
        return 1
    fi

    cd "$compose_dir"
    docker-compose up -d
    cd "$PROJECT_ROOT"

    # Wait for service to be healthy
    log_info "Waiting for $name to be healthy on port $port..."
    local timeout=120
    local elapsed=0

    while [ $elapsed -lt $timeout ]; do
        if curl -s -f "http://localhost:${port}" > /dev/null 2>&1; then
            log_success "$name is healthy"
            return 0
        fi
        sleep 5
        elapsed=$((elapsed + 5))
        echo -n "."
    done

    echo ""
    log_error "$name failed to become healthy within ${timeout}s"
    return 1
}

# Stop a module's Docker services
stop_module() {
    local module=$1
    IFS='|' read -r path port name <<< "${MODULES[$module]}"

    log_info "Stopping $name..."

    local compose_dir="${PROJECT_ROOT}/${path}"

    if [ -d "$compose_dir" ]; then
        cd "$compose_dir"
        docker-compose down 2>/dev/null || true
        cd "$PROJECT_ROOT"
    fi

    log_success "$name stopped"
}

# Run Playwright tests for a module
run_tests() {
    local module=$1
    IFS='|' read -r path port name <<< "${MODULES[$module]}"

    log_info "Running E2E tests for $name..."

    # Set base URL for tests
    export BASE_URL="http://localhost:${port}"

    # Create results directory
    mkdir -p "${RESULTS_DIR}/${module}"

    # Run Playwright tests
    cd "$TESTS_DIR"

    local test_file="${module}.spec.ts"
    if [ ! -f "$test_file" ]; then
        test_file="generic.spec.ts"
        log_warning "No specific test file for $module, using generic tests"
    fi

    npx playwright test "$test_file" \
        --reporter=json \
        --output="${RESULTS_DIR}/${module}" \
        > "${RESULTS_DIR}/${module}/results.json" 2>&1 || true

    # Also run with list reporter for console output
    npx playwright test "$test_file" --reporter=list 2>&1 | tee "${RESULTS_DIR}/${module}/console.log"

    local exit_code=${PIPESTATUS[0]}

    cd "$PROJECT_ROOT"

    return $exit_code
}

# Test a single module
test_module() {
    local module=$1
    local exit_code=0

    echo ""
    echo "============================================================"
    log_info "Testing module: $module"
    echo "============================================================"

    # Start services
    if ! start_module "$module"; then
        log_error "Failed to start $module"
        return 1
    fi

    # Run tests
    if ! run_tests "$module"; then
        log_warning "Some tests failed for $module"
        exit_code=1
    fi

    # Stop services
    stop_module "$module"

    return $exit_code
}

# Test all modules
test_all_modules() {
    local failed_modules=()
    local passed_modules=()

    for module in "${!MODULES[@]}"; do
        if test_module "$module"; then
            passed_modules+=("$module")
        else
            failed_modules+=("$module")
        fi
    done

    # Summary
    echo ""
    echo "============================================================"
    log_info "E2E TEST SUMMARY"
    echo "============================================================"

    if [ ${#passed_modules[@]} -gt 0 ]; then
        log_success "Passed modules: ${passed_modules[*]}"
    fi

    if [ ${#failed_modules[@]} -gt 0 ]; then
        log_error "Failed modules: ${failed_modules[*]}"
        return 1
    fi

    log_success "All modules passed!"
    return 0
}

# Generate test report
generate_report() {
    log_info "Generating consolidated test report..."

    local report_file="${RESULTS_DIR}/summary.md"

    cat > "$report_file" << EOF
# E2E Test Report

**Generated**: $(date -Iseconds)
**Project**: CogStack NLP

## Module Results

EOF

    for module in "${!MODULES[@]}"; do
        IFS='|' read -r path port name <<< "${MODULES[$module]}"
        local console_log="${RESULTS_DIR}/${module}/console.log"

        echo "### $name" >> "$report_file"
        echo "" >> "$report_file"

        if [ -f "$console_log" ]; then
            # Extract pass/fail summary
            local passed=$(grep -c "✓" "$console_log" 2>/dev/null || echo "0")
            local failed=$(grep -c "✘" "$console_log" 2>/dev/null || echo "0")

            echo "- **Passed**: $passed" >> "$report_file"
            echo "- **Failed**: $failed" >> "$report_file"
            echo "" >> "$report_file"
        else
            echo "- No results available" >> "$report_file"
            echo "" >> "$report_file"
        fi
    done

    log_success "Report generated: $report_file"
}

# Main
case "${1:-}" in
    --list|-l)
        list_modules
        ;;
    --all|-a)
        test_all_modules
        generate_report
        ;;
    --help|-h)
        echo "Usage: $0 [options] [module-name]"
        echo ""
        echo "Options:"
        echo "  --list, -l     List available modules"
        echo "  --all, -a      Test all modules"
        echo "  --help, -h     Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 medcat-trainer    Test medcat-trainer module"
        echo "  $0 --all             Test all modules"
        ;;
    "")
        # Default: test medcat-trainer
        test_module "medcat-trainer"
        ;;
    *)
        if [ -n "${MODULES[$1]:-}" ]; then
            test_module "$1"
        else
            log_error "Unknown module: $1"
            list_modules
            exit 1
        fi
        ;;
esac
