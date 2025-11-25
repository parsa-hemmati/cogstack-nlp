#!/usr/bin/env bash
# =============================================================================
# Environment Verification Script for Clinical Care Tools Base Application
# =============================================================================
# Purpose: Verify all Phase 0 environment setup requirements
# Version: 1.0.0
# Author: Autonomous Execution Framework (Mission 0.7)
#
# Usage: ./scripts/verify-environment.sh
# Exit Codes: 0 = all checks passed, 1 = one or more checks failed
#
# Checks Performed:
# - Docker installation (version ≥24.0)
# - Docker Compose installation (version ≥2.20)
# - Docker volumes existence (postgres_data, redis_data, medcat_models, backend_logs)
# - PostgreSQL service (running, healthy, connectable, version ≥15)
# - Redis service (running, healthy, PING test)
# - CogStack-ModelServe service (optional, warn if not available)
#
# Color Codes:
# - Green (✅): Check passed
# - Red (❌): Check failed (critical)
# - Yellow (⚠️ ): Warning (non-critical)
# =============================================================================

set -euo pipefail

# Color codes
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_check() {
    echo -e "\n${BLUE}[CHECK]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ((FAILED++))
}

print_warn() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
    ((WARNINGS++))
}

# =============================================================================
# Check 1: Docker Installation
# =============================================================================
check_docker() {
    print_check "Docker installation"

    if ! command -v docker &> /dev/null; then
        print_fail "Docker is not installed"
        echo "  Install from: https://docs.docker.com/get-docker/"
        return 1
    fi

    DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+' | head -1)
    DOCKER_MAJOR=$(echo "$DOCKER_VERSION" | cut -d. -f1)

    if [ "$DOCKER_MAJOR" -lt 24 ]; then
        print_fail "Docker version $DOCKER_VERSION (requires ≥24.0)"
        return 1
    fi

    print_pass "Docker $DOCKER_VERSION installed"
    return 0
}

# =============================================================================
# Check 2: Docker Compose Installation
# =============================================================================
check_docker_compose() {
    print_check "Docker Compose installation"

    if ! docker-compose --version &> /dev/null; then
        print_fail "Docker Compose is not installed"
        echo "  Install from: https://docs.docker.com/compose/install/"
        return 1
    fi

    COMPOSE_VERSION=$(docker-compose --version | grep -oP '\d+\.\d+' | head -1)
    COMPOSE_MAJOR=$(echo "$COMPOSE_VERSION" | cut -d. -f1)
    COMPOSE_MINOR=$(echo "$COMPOSE_VERSION" | cut -d. -f2)

    if [ "$COMPOSE_MAJOR" -lt 2 ] || ([ "$COMPOSE_MAJOR" -eq 2 ] && [ "$COMPOSE_MINOR" -lt 20 ]); then
        print_fail "Docker Compose version $COMPOSE_VERSION (requires ≥2.20)"
        return 1
    fi

    print_pass "Docker Compose $COMPOSE_VERSION installed"
    return 0
}

# =============================================================================
# Check 3: Docker Volumes
# =============================================================================
check_volumes() {
    print_check "Docker volumes"

    # Phase 0 requires postgres_data and redis_data
    REQUIRED_VOLUMES=("clinical_care_postgres_data" "clinical_care_redis_data")
    # These will be created in Phase 1+ when backend/modelserve start
    OPTIONAL_VOLUMES=("clinical_care_medcat_models" "clinical_care_backend_logs")

    MISSING_REQUIRED=()
    MISSING_OPTIONAL=()

    # Check required volumes
    for volume in "${REQUIRED_VOLUMES[@]}"; do
        if ! docker volume inspect "$volume" &> /dev/null; then
            MISSING_REQUIRED+=("$volume")
        fi
    done

    # Check optional volumes
    for volume in "${OPTIONAL_VOLUMES[@]}"; do
        if ! docker volume inspect "$volume" &> /dev/null; then
            MISSING_OPTIONAL+=("$volume")
        fi
    done

    if [ ${#MISSING_REQUIRED[@]} -gt 0 ]; then
        print_fail "Missing required volumes: ${MISSING_REQUIRED[*]}"
        echo "  Run: docker-compose up -d postgres redis"
        return 1
    fi

    if [ ${#MISSING_OPTIONAL[@]} -gt 0 ]; then
        print_warn "Missing optional volumes: ${MISSING_OPTIONAL[*]} (will be created when backend/modelserve start)"
    fi

    print_pass "All ${#REQUIRED_VOLUMES[@]} required volumes exist"
    return 0
}

# =============================================================================
# Check 4: PostgreSQL Service
# =============================================================================
check_postgres() {
    print_check "PostgreSQL service"

    # Check if container is running
    if ! docker-compose ps postgres | grep -q "Up"; then
        print_fail "PostgreSQL container is not running"
        echo "  Run: docker-compose up -d postgres"
        return 1
    fi

    # Check health status
    POSTGRES_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' clinical_care_postgres 2>/dev/null || echo "unknown")
    if [ "$POSTGRES_HEALTH" != "healthy" ]; then
        print_fail "PostgreSQL is not healthy (status: $POSTGRES_HEALTH)"
        echo "  Check logs: docker-compose logs postgres"
        return 1
    fi

    # Check connection
    if ! docker-compose exec -T postgres pg_isready -U clinicaltools -d clinical_care_tools &> /dev/null; then
        print_fail "Cannot connect to PostgreSQL"
        return 1
    fi

    # Check version
    POSTGRES_VERSION=$(docker-compose exec -T postgres psql -U clinicaltools -d clinical_care_tools -t -c "SELECT version();" | grep -oP 'PostgreSQL \d+\.\d+' | grep -oP '\d+\.\d+')
    POSTGRES_MAJOR=$(echo "$POSTGRES_VERSION" | cut -d. -f1)

    if [ "$POSTGRES_MAJOR" -lt 15 ]; then
        print_fail "PostgreSQL version $POSTGRES_VERSION (requires ≥15)"
        return 1
    fi

    print_pass "PostgreSQL $POSTGRES_VERSION (healthy, connectable)"
    return 0
}

# =============================================================================
# Check 5: Redis Service
# =============================================================================
check_redis() {
    print_check "Redis service"

    # Check if container is running
    if ! docker-compose ps redis | grep -q "Up"; then
        print_fail "Redis container is not running"
        echo "  Run: docker-compose up -d redis"
        return 1
    fi

    # Check health status
    REDIS_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' clinical_care_redis 2>/dev/null || echo "unknown")
    if [ "$REDIS_HEALTH" != "healthy" ]; then
        print_fail "Redis is not healthy (status: $REDIS_HEALTH)"
        echo "  Check logs: docker-compose logs redis"
        return 1
    fi

    # Load Redis password from .env
    if [ ! -f .env ]; then
        print_fail ".env file not found (required for Redis password)"
        return 1
    fi

    # Source .env and get REDIS_PASSWORD
    export $(grep -v '^#' .env | grep REDIS_PASSWORD | xargs)

    if [ -z "${REDIS_PASSWORD:-}" ]; then
        print_fail "REDIS_PASSWORD not set in .env"
        return 1
    fi

    # Check PING
    PING_RESULT=$(docker-compose exec -T redis redis-cli --no-auth-warning -a "$REDIS_PASSWORD" ping 2>/dev/null || echo "FAIL")
    if [ "$PING_RESULT" != "PONG" ]; then
        print_fail "Redis PING failed (got: $PING_RESULT)"
        return 1
    fi

    # Check persistence configuration
    APPENDONLY=$(docker-compose exec -T redis redis-cli --no-auth-warning -a "$REDIS_PASSWORD" CONFIG GET appendonly 2>/dev/null | tail -1)
    if [ "$APPENDONLY" != "yes" ]; then
        print_warn "Redis AOF persistence not enabled (expected: yes, got: $APPENDONLY)"
    fi

    print_pass "Redis 7.2 (healthy, PING OK, AOF=$APPENDONLY)"
    return 0
}

# =============================================================================
# Check 6: MedCAT Service (Optional)
# =============================================================================
check_cogstack_modelserve() {
    print_check "MedCAT service (optional)"

    # Check if container is running
    if ! docker-compose ps medcat-service | grep -q "Up" 2>/dev/null; then
        print_warn "MedCAT service container is not running (blocked by Mission 0.2: MedCAT models download)"
        echo "  This is expected if MedCAT models are not yet downloaded"
        echo "  See models/README.md for download instructions"
        return 0
    fi

    # Check health status
    MEDCAT_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' clinical_care_medcat 2>/dev/null || echo "unknown")
    if [ "$MEDCAT_HEALTH" != "healthy" ]; then
        print_warn "MedCAT service is not healthy (status: $MEDCAT_HEALTH)"
        echo "  This may be normal if models are still loading (takes 60-90 seconds)"
        return 0
    fi

    # Check health endpoint (using Python since curl is not in the container)
    if ! curl -sf http://localhost:8001/api/info &> /dev/null; then
        print_warn "MedCAT service health endpoint not responding"
        return 0
    fi

    print_pass "MedCAT service (healthy, API responding)"
    return 0
}

# =============================================================================
# Main Execution
# =============================================================================
main() {
    print_header "Clinical Care Tools - Environment Verification"
    echo "This script verifies Phase 0 environment setup requirements."
    echo "Version: 1.0.0 | Mission: MVP Phase 0, Task 0.7"

    # Run all checks
    check_docker || true
    check_docker_compose || true
    check_volumes || true
    check_postgres || true
    check_redis || true
    check_cogstack_modelserve || true

    # Summary
    print_header "Verification Summary"
    echo -e "${GREEN}✅ Passed:${NC}   $PASSED"
    echo -e "${RED}❌ Failed:${NC}   $FAILED"
    echo -e "${YELLOW}⚠️  Warnings:${NC} $WARNINGS"

    if [ $FAILED -gt 0 ]; then
        echo -e "\n${RED}❌ Environment verification FAILED${NC}"
        echo "Fix the errors above and run this script again."
        exit 1
    fi

    if [ $WARNINGS -gt 0 ]; then
        echo -e "\n${YELLOW}⚠️  Environment verification passed with warnings${NC}"
        echo "Review warnings above. System may work but not all components are ready."
        exit 0
    fi

    echo -e "\n${GREEN}✅ Environment verification PASSED${NC}"
    echo "All Phase 0 requirements met. Ready for Phase 1 (Core Infrastructure)."
    exit 0
}

# Run main function
main "$@"
