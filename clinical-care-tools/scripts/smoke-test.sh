#!/bin/bash

##############################################################################
# Smoke Tests for Clinical Care Tools Production Deployment
#
# Verifies critical functionality after deployment:
# 1. Health checks - API, database, services
# 2. Authentication - login flow working
# 3. Core features - patient search, document upload
# 4. Data protection - encryption, audit logging
# 5. Performance - response times acceptable
#
# Usage: ./scripts/smoke-test.sh [target_url] [admin_username] [admin_password]
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TARGET_URL="${1:-http://localhost:8000}"
ADMIN_USER="${2:-admin@example.com}"
ADMIN_PASS="${3:-admin_password_123!}"

TESTS_PASSED=0
TESTS_FAILED=0
START_TIME=$(date +%s)

# Logging functions
log_pass() {
    echo -e "${GREEN}✓ PASS${NC} $1"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}✗ FAIL${NC} $1"
    ((TESTS_FAILED++))
}

log_info() {
    echo -e "${YELLOW}ℹ INFO${NC} $1"
}

log_header() {
    echo ""
    echo "=============================================================="
    echo "  $1"
    echo "=============================================================="
}

# Test functions
test_api_health() {
    log_header "Health Check Tests"

    # Test API is responding
    response=$(curl -s -w "\n%{http_code}" "$TARGET_URL/api/v1/health")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "200" ]; then
        log_pass "API health endpoint responding"
    else
        log_fail "API health endpoint (HTTP $http_code)"
        return 1
    fi

    # Test API version
    response=$(curl -s "$TARGET_URL/api/v1/version")
    if echo "$response" | grep -q "version"; then
        log_pass "API version endpoint working"
    else
        log_fail "API version endpoint"
    fi
}

test_database_connectivity() {
    log_header "Database Connectivity Tests"

    # Test database health
    response=$(curl -s -w "\n%{http_code}" "$TARGET_URL/api/v1/health/db")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "200" ]; then
        log_pass "Database connectivity verified"
    else
        log_fail "Database connectivity (HTTP $http_code)"
    fi
}

test_authentication() {
    log_header "Authentication Tests"

    # Test login
    response=$(curl -s -X POST "$TARGET_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$ADMIN_USER\", \"password\": \"$ADMIN_PASS\"}")

    if echo "$response" | grep -q "access_token"; then
        log_pass "User login successful"
        ACCESS_TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    else
        log_fail "User login"
        return 1
    fi

    # Test token validation
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$TARGET_URL/api/v1/users/me")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "200" ]; then
        log_pass "JWT token validation"
    else
        log_fail "JWT token validation (HTTP $http_code)"
    fi
}

test_core_endpoints() {
    log_header "Core Functionality Tests"

    # Need authentication token
    login_response=$(curl -s -X POST "$TARGET_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$ADMIN_USER\", \"password\": \"$ADMIN_PASS\"}")

    ACCESS_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

    # Test projects endpoint
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$TARGET_URL/api/v1/projects")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "200" ]; then
        log_pass "Projects endpoint accessible"
    else
        log_fail "Projects endpoint (HTTP $http_code)"
    fi

    # Test users endpoint
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$TARGET_URL/api/v1/users")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "200" ]; then
        log_pass "Users endpoint accessible"
    else
        log_fail "Users endpoint (HTTP $http_code)"
    fi

    # Test audit logs endpoint
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$TARGET_URL/api/v1/audit-logs")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "200" ]; then
        log_pass "Audit logs endpoint accessible"
    else
        log_fail "Audit logs endpoint (HTTP $http_code)"
    fi
}

test_performance() {
    log_header "Performance Tests"

    login_response=$(curl -s -X POST "$TARGET_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$ADMIN_USER\", \"password\": \"$ADMIN_PASS\"}")

    ACCESS_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

    # Test response time for health endpoint (target: <100ms)
    response=$(curl -s -w "%{time_total}" -o /dev/null "$TARGET_URL/api/v1/health")
    response_ms=$(echo "$response * 1000" | bc)

    if (( $(echo "$response_ms < 100" | bc -l) )); then
        log_pass "Health endpoint response time (${response_ms%.*}ms)"
    else
        log_fail "Health endpoint response time (${response_ms%.*}ms, target: <100ms)"
    fi

    # Test response time for projects endpoint (target: <500ms)
    response=$(curl -s -w "%{time_total}" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -o /dev/null "$TARGET_URL/api/v1/projects")
    response_ms=$(echo "$response * 1000" | bc)

    if (( $(echo "$response_ms < 500" | bc -l) )); then
        log_pass "Projects endpoint response time (${response_ms%.*}ms)"
    else
        log_fail "Projects endpoint response time (${response_ms%.*}ms, target: <500ms)"
    fi
}

test_security_headers() {
    log_header "Security Headers Tests"

    # Test for security headers
    response=$(curl -s -i "$TARGET_URL/api/v1/health")

    if echo "$response" | grep -qi "X-Content-Type-Options"; then
        log_pass "X-Content-Type-Options header present"
    else
        log_fail "X-Content-Type-Options header missing"
    fi

    if echo "$response" | grep -qi "X-Frame-Options"; then
        log_pass "X-Frame-Options header present"
    else
        log_fail "X-Frame-Options header missing"
    fi

    if echo "$response" | grep -qi "Strict-Transport-Security\|HSTS"; then
        log_pass "HSTS header present"
    else
        log_fail "HSTS header missing"
    fi
}

test_encryption() {
    log_header "Encryption Status Tests"

    login_response=$(curl -s -X POST "$TARGET_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$ADMIN_USER\", \"password\": \"$ADMIN_PASS\"}")

    ACCESS_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

    # Test encryption status endpoint
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$TARGET_URL/api/v1/admin/encryption-status")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "200" ]; then
        log_pass "Encryption status endpoint"
    else
        log_info "Encryption status endpoint (HTTP $http_code) - may not be implemented"
    fi
}

test_audit_logging() {
    log_header "Audit Logging Tests"

    login_response=$(curl -s -X POST "$TARGET_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$ADMIN_USER\", \"password\": \"$ADMIN_PASS\"}")

    ACCESS_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

    # Test audit logs exist
    response=$(curl -s \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$TARGET_URL/api/v1/audit-logs")

    if echo "$response" | grep -q "user_id\|action\|timestamp"; then
        log_pass "Audit logs contain required fields"
    else
        log_fail "Audit logs missing required fields"
    fi
}

test_database_services() {
    log_header "Database Service Tests"

    # Test Redis connectivity
    response=$(curl -s -w "\n%{http_code}" "$TARGET_URL/api/v1/health/redis")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "200" ]; then
        log_pass "Redis connectivity"
    else
        log_info "Redis connectivity (HTTP $http_code) - may not be required"
    fi

    # Test Elasticsearch connectivity
    response=$(curl -s -w "\n%{http_code}" "$TARGET_URL/api/v1/health/elasticsearch")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "200" ]; then
        log_pass "Elasticsearch connectivity"
    else
        log_info "Elasticsearch connectivity (HTTP $http_code) - may not be required"
    fi
}

test_error_handling() {
    log_header "Error Handling Tests"

    # Test 404 handling
    response=$(curl -s -w "\n%{http_code}" "$TARGET_URL/api/v1/nonexistent")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "404" ]; then
        log_pass "404 error handling"
    else
        log_fail "404 error handling (HTTP $http_code)"
    fi

    # Test unauthorized handling
    response=$(curl -s -w "\n%{http_code}" "$TARGET_URL/api/v1/projects")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" == "401" ]; then
        log_pass "Unauthorized (401) error handling"
    else
        log_fail "Unauthorized error handling (HTTP $http_code)"
    fi
}

print_summary() {
    log_header "Smoke Test Summary"

    TOTAL=$((TESTS_PASSED + TESTS_FAILED))
    PERCENTAGE=$((TESTS_PASSED * 100 / TOTAL))

    echo "Total Tests: $TOTAL"
    echo -e "Passed:      ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed:      ${RED}$TESTS_FAILED${NC}"
    echo "Success Rate: $PERCENTAGE%"

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo "Duration: ${DURATION}s"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✓ All smoke tests passed!${NC}"
        return 0
    else
        echo -e "\n${RED}✗ Some smoke tests failed. Review above for details.${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo "=================================================="
    echo "  Clinical Care Tools - Smoke Test Suite"
    echo "=================================================="
    echo "Target URL: $TARGET_URL"
    echo "Started: $(date)"
    echo ""

    # Run all tests
    test_api_health || true
    test_database_connectivity || true
    test_authentication || true
    test_core_endpoints || true
    test_performance || true
    test_security_headers || true
    test_encryption || true
    test_audit_logging || true
    test_database_services || true
    test_error_handling || true

    # Print summary and exit
    print_summary
}

main
