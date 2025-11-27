#!/bin/bash
# =============================================================================
# Docker Test Runner - Orchestration Script
# =============================================================================
# Purpose: Manage Docker services lifecycle for E2E testing
# Usage:
#   ./scripts/docker-test-runner.sh start    # Start all services
#   ./scripts/docker-test-runner.sh stop     # Stop all services
#   ./scripts/docker-test-runner.sh status   # Check health status
#   ./scripts/docker-test-runner.sh run      # Full test cycle (start -> test -> stop)
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
ENV_FILE="${PROJECT_ROOT}/.env"
ENV_TEST_FILE="${PROJECT_ROOT}/.env.test"

# Timeouts (seconds)
MAX_WAIT_TIME=300  # 5 minutes total
POLL_INTERVAL=5    # Check every 5 seconds
SERVICE_TIMEOUT=120  # Per-service timeout

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Service Health Check Functions
# =============================================================================

check_postgres() {
    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U clinicaltools -d clinical_care_tools > /dev/null 2>&1
}

check_redis() {
    docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1
}

check_elasticsearch() {
    curl -s -f http://localhost:9200/_cluster/health > /dev/null 2>&1
}

check_medcat() {
    curl -s -f http://localhost:8001/api/info > /dev/null 2>&1
}

check_backend() {
    curl -s -f http://localhost:8000/api/health > /dev/null 2>&1
}

check_frontend() {
    curl -s -f http://localhost:8080 > /dev/null 2>&1
}

# =============================================================================
# Wait for Service Health
# =============================================================================

wait_for_service() {
    local service_name=$1
    local check_function=$2
    local timeout=${3:-$SERVICE_TIMEOUT}
    local elapsed=0

    log_info "Waiting for $service_name to be healthy..."

    while [ $elapsed -lt $timeout ]; do
        if $check_function; then
            log_success "$service_name is healthy (${elapsed}s)"
            return 0
        fi
        sleep $POLL_INTERVAL
        elapsed=$((elapsed + POLL_INTERVAL))
        echo -n "."
    done

    echo ""
    log_error "$service_name failed to become healthy within ${timeout}s"
    return 1
}

# =============================================================================
# Start Services
# =============================================================================

start_services() {
    log_info "Starting Docker services..."

    # Use test environment if available
    if [ -f "$ENV_TEST_FILE" ]; then
        log_info "Using test environment: $ENV_TEST_FILE"
        export $(grep -v '^#' "$ENV_TEST_FILE" | xargs)
    elif [ -f "$ENV_FILE" ]; then
        log_info "Using environment: $ENV_FILE"
    else
        log_error "No .env file found. Please create .env or .env.test"
        exit 1
    fi

    # Start all services in detached mode
    docker-compose -f "$COMPOSE_FILE" up -d

    log_success "Docker services started"
}

# =============================================================================
# Wait for All Services
# =============================================================================

wait_for_all_services() {
    log_info "Waiting for all services to be healthy..."
    local start_time=$(date +%s)
    local failed_services=()

    # Wait for each service in dependency order
    # PostgreSQL (fast startup)
    if ! wait_for_service "PostgreSQL" check_postgres 60; then
        failed_services+=("postgres")
    fi

    # Redis (fast startup)
    if ! wait_for_service "Redis" check_redis 30; then
        failed_services+=("redis")
    fi

    # Elasticsearch (slow startup - needs index creation)
    if ! wait_for_service "Elasticsearch" check_elasticsearch 120; then
        failed_services+=("elasticsearch")
    fi

    # MedCAT Service (slowest - model loading)
    if ! wait_for_service "MedCAT Service" check_medcat 180; then
        failed_services+=("medcat-service")
    fi

    # Backend API (depends on postgres, redis, medcat)
    if ! wait_for_service "Backend API" check_backend 90; then
        failed_services+=("backend")
    fi

    # Frontend (depends on backend)
    if ! wait_for_service "Frontend" check_frontend 60; then
        failed_services+=("frontend")
    fi

    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))

    if [ ${#failed_services[@]} -eq 0 ]; then
        log_success "All services healthy in ${total_time}s"
        return 0
    else
        log_error "Failed services: ${failed_services[*]}"
        return 1
    fi
}

# =============================================================================
# Stop Services
# =============================================================================

stop_services() {
    log_info "Stopping Docker services..."
    docker-compose -f "$COMPOSE_FILE" down
    log_success "Docker services stopped"
}

# =============================================================================
# Check Status
# =============================================================================

check_status() {
    log_info "Checking service health status..."
    echo ""

    local services=("postgres:check_postgres" "redis:check_redis" "elasticsearch:check_elasticsearch" "medcat-service:check_medcat" "backend:check_backend" "frontend:check_frontend")

    for service_check in "${services[@]}"; do
        local service_name="${service_check%%:*}"
        local check_func="${service_check##*:}"

        if $check_func 2>/dev/null; then
            echo -e "  ${GREEN}[HEALTHY]${NC} $service_name"
        else
            echo -e "  ${RED}[UNHEALTHY]${NC} $service_name"
        fi
    done

    echo ""
}

# =============================================================================
# Run Playwright Tests
# =============================================================================

run_playwright_tests() {
    log_info "Running Playwright E2E tests..."

    cd "${PROJECT_ROOT}/frontend"

    # Install playwright browsers if needed
    npx playwright install chromium --with-deps 2>/dev/null || true

    # Run tests
    npm run test:e2e -- --reporter=json --output-file=playwright-results.json
    local exit_code=$?

    cd "$PROJECT_ROOT"

    if [ $exit_code -eq 0 ]; then
        log_success "Playwright tests passed"
    else
        log_error "Playwright tests failed with exit code $exit_code"
    fi

    return $exit_code
}

# =============================================================================
# Run browser-use AI Tests
# =============================================================================

run_browseruse_tests() {
    log_info "Running browser-use AI exploratory tests..."

    cd "${PROJECT_ROOT}/backend"

    # Run AI tests with pytest
    python -m pytest tests/e2e_browser/ -v --tb=short 2>&1 || true
    local exit_code=$?

    cd "$PROJECT_ROOT"

    if [ $exit_code -eq 0 ]; then
        log_success "browser-use AI tests passed"
    else
        log_warning "browser-use AI tests had issues (exit code $exit_code)"
    fi

    return $exit_code
}

# =============================================================================
# Full Test Run
# =============================================================================

run_full_test_cycle() {
    log_info "=== Starting Full E2E Test Cycle ==="
    local start_time=$(date +%s)
    local exit_code=0

    # Start services
    start_services

    # Wait for health
    if ! wait_for_all_services; then
        log_error "Services failed to start. Aborting tests."
        stop_services
        exit 1
    fi

    # Run Playwright tests
    if ! run_playwright_tests; then
        exit_code=1
    fi

    # Run browser-use tests (if available)
    if [ -d "${PROJECT_ROOT}/backend/tests/e2e_browser" ]; then
        if ! run_browseruse_tests; then
            # Don't fail on AI test issues (they're exploratory)
            log_warning "AI tests had issues but continuing..."
        fi
    else
        log_warning "No browser-use tests found in backend/tests/e2e_browser/"
    fi

    # Stop services
    stop_services

    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))

    echo ""
    log_info "=== Test Cycle Complete ==="
    log_info "Total time: ${total_time}s"

    if [ $exit_code -eq 0 ]; then
        log_success "All tests passed!"
    else
        log_error "Some tests failed"
    fi

    return $exit_code
}

# =============================================================================
# Main Entry Point
# =============================================================================

case "${1:-}" in
    start)
        start_services
        wait_for_all_services
        ;;
    stop)
        stop_services
        ;;
    status)
        check_status
        ;;
    run)
        run_full_test_cycle
        ;;
    playwright)
        run_playwright_tests
        ;;
    browseruse)
        run_browseruse_tests
        ;;
    *)
        echo "Usage: $0 {start|stop|status|run|playwright|browseruse}"
        echo ""
        echo "Commands:"
        echo "  start      - Start all Docker services and wait for health"
        echo "  stop       - Stop all Docker services"
        echo "  status     - Check health status of all services"
        echo "  run        - Full test cycle: start -> test -> stop"
        echo "  playwright - Run Playwright E2E tests only"
        echo "  browseruse - Run browser-use AI tests only"
        exit 1
        ;;
esac
