#!/usr/bin/env bash
# Test Script for PostgreSQL Backup/Restore Procedures
# Version: 1.0.0
# Purpose: Validate backup and restore scripts work correctly
# Usage: ./scripts/test-backup-restore.sh

set -euo pipefail
IFS=$'\n\t'

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Test configuration
TEST_BACKUP_DIR="/tmp/clinical_care_tools_backup_test"
TEST_DB_NAME="clinical_care_tools_test"
BACKUP_ENCRYPTION_KEY="test_encryption_key_$(date +%s)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# =============================================================================
# Functions
# =============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_test_pass() {
    echo -e "${GREEN}[PASS]${NC} $*"
    ((TESTS_PASSED++))
}

log_test_fail() {
    echo -e "${RED}[FAIL]${NC} $*"
    ((TESTS_FAILED++))
}

cleanup_test_env() {
    log_info "Cleaning up test environment..."

    # Remove test backup directory
    if [[ -d "${TEST_BACKUP_DIR}" ]]; then
        rm -rf "${TEST_BACKUP_DIR}"
    fi

    # Drop test database if exists
    if [[ -n "${POSTGRES_PASSWORD:-}" ]]; then
        export PGPASSWORD="${POSTGRES_PASSWORD}"
        psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-clinicaltools}" -d postgres -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" &> /dev/null || true
    fi
}

trap cleanup_test_env EXIT

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if docker-compose is running
    if ! docker-compose ps postgres | grep -q "Up"; then
        log_error "PostgreSQL container is not running"
        log_error "Start with: docker-compose up -d postgres"
        exit 1
    fi
    log_test_pass "PostgreSQL container is running"

    # Check if backup script exists and is executable
    if [[ ! -x "${SCRIPT_DIR}/backup-postgres.sh" ]]; then
        log_error "Backup script not found or not executable: ${SCRIPT_DIR}/backup-postgres.sh"
        exit 1
    fi
    log_test_pass "Backup script exists and is executable"

    # Check if restore script exists and is executable
    if [[ ! -x "${SCRIPT_DIR}/restore-postgres.sh" ]]; then
        log_error "Restore script not found or not executable: ${SCRIPT_DIR}/restore-postgres.sh"
        exit 1
    fi
    log_test_pass "Restore script exists and is executable"

    # Check environment variables
    if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
        log_error "POSTGRES_PASSWORD environment variable not set"
        log_error "Load with: source .env"
        exit 1
    fi
    log_test_pass "Environment variables configured"
}

create_test_database() {
    log_info "Creating test database..."

    export PGPASSWORD="${POSTGRES_PASSWORD}"

    # Create test database
    psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-clinicaltools}" -d postgres -c "CREATE DATABASE ${TEST_DB_NAME};" &> /dev/null

    # Create test tables
    psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-clinicaltools}" -d "${TEST_DB_NAME}" << 'EOF'
-- Create test schema
CREATE TABLE test_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE test_audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Insert test data
INSERT INTO test_users (username) VALUES ('test_user_1'), ('test_user_2'), ('test_user_3');
INSERT INTO test_audit_logs (user_id, action) VALUES (1, 'LOGIN'), (2, 'LOGOUT'), (3, 'VIEW_PATIENT');

-- Create immutability rules
CREATE RULE no_update_audit_logs AS ON UPDATE TO test_audit_logs DO INSTEAD NOTHING;
CREATE RULE no_delete_audit_logs AS ON DELETE TO test_audit_logs DO INSTEAD NOTHING;
EOF

    log_test_pass "Test database created with sample data"
}

verify_test_data() {
    log_info "Verifying test data..."

    export PGPASSWORD="${POSTGRES_PASSWORD}"

    # Count users
    local user_count
    user_count=$(psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-clinicaltools}" -d "${TEST_DB_NAME}" -t -c "SELECT COUNT(*) FROM test_users;" | tr -d ' ')

    if [[ "${user_count}" -eq 3 ]]; then
        log_test_pass "Test data verified: 3 users"
    else
        log_test_fail "Test data mismatch: expected 3 users, got ${user_count}"
    fi

    # Count audit logs
    local log_count
    log_count=$(psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-clinicaltools}" -d "${TEST_DB_NAME}" -t -c "SELECT COUNT(*) FROM test_audit_logs;" | tr -d ' ')

    if [[ "${log_count}" -eq 3 ]]; then
        log_test_pass "Test data verified: 3 audit logs"
    else
        log_test_fail "Test data mismatch: expected 3 audit logs, got ${log_count}"
    fi
}

test_backup_script() {
    log_info "Testing backup script..."

    # Create test backup directory
    mkdir -p "${TEST_BACKUP_DIR}"

    # Run backup script
    export BACKUP_DIR="${TEST_BACKUP_DIR}"
    export POSTGRES_DB="${TEST_DB_NAME}"
    export BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY}"

    if "${SCRIPT_DIR}/backup-postgres.sh" >> "${TEST_BACKUP_DIR}/test.log" 2>&1; then
        log_test_pass "Backup script executed successfully"
    else
        log_test_fail "Backup script failed (check ${TEST_BACKUP_DIR}/test.log)"
        cat "${TEST_BACKUP_DIR}/test.log"
        return 1
    fi

    # Verify backup file exists
    local backup_file
    backup_file=$(find "${TEST_BACKUP_DIR}" -name "clinical_care_tools_*.sql.gz.enc" -type f | head -n 1)

    if [[ -f "${backup_file}" ]]; then
        log_test_pass "Backup file created: $(basename "${backup_file}")"
    else
        log_test_fail "Backup file not found in ${TEST_BACKUP_DIR}"
        return 1
    fi

    # Verify backup file size
    local file_size
    file_size=$(stat -c%s "${backup_file}")

    if [[ "${file_size}" -gt 1024 ]]; then
        log_test_pass "Backup file size valid: $(du -h "${backup_file}" | cut -f1)"
    else
        log_test_fail "Backup file too small: ${file_size} bytes"
        return 1
    fi

    # Save backup filename for restore test
    BACKUP_FILENAME=$(basename "${backup_file}")
}

test_restore_script() {
    log_info "Testing restore script..."

    # Drop and recreate test database
    export PGPASSWORD="${POSTGRES_PASSWORD}"
    psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-clinicaltools}" -d postgres -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" &> /dev/null
    psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-clinicaltools}" -d postgres -c "CREATE DATABASE ${TEST_DB_NAME};" &> /dev/null

    log_info "Test database dropped and recreated (empty)"

    # Run restore script
    export BACKUP_DIR="${TEST_BACKUP_DIR}"
    export POSTGRES_DB="${TEST_DB_NAME}"
    export BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY}"
    export REQUIRE_CONFIRMATION="false"  # Skip confirmation prompt

    if "${SCRIPT_DIR}/restore-postgres.sh" "${BACKUP_FILENAME}" >> "${TEST_BACKUP_DIR}/test.log" 2>&1; then
        log_test_pass "Restore script executed successfully"
    else
        log_test_fail "Restore script failed (check ${TEST_BACKUP_DIR}/test.log)"
        cat "${TEST_BACKUP_DIR}/test.log"
        return 1
    fi

    # Verify restored data
    local user_count
    user_count=$(psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-clinicaltools}" -d "${TEST_DB_NAME}" -t -c "SELECT COUNT(*) FROM test_users;" | tr -d ' ')

    if [[ "${user_count}" -eq 3 ]]; then
        log_test_pass "Restored data verified: 3 users"
    else
        log_test_fail "Restored data mismatch: expected 3 users, got ${user_count}"
    fi

    # Verify immutability rules restored
    local rule_count
    rule_count=$(psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-clinicaltools}" -d "${TEST_DB_NAME}" -t -c "SELECT COUNT(*) FROM pg_rules WHERE tablename = 'test_audit_logs' AND rulename IN ('no_update_audit_logs', 'no_delete_audit_logs');" | tr -d ' ')

    if [[ "${rule_count}" -eq 2 ]]; then
        log_test_pass "Immutability rules restored (2 rules)"
    else
        log_test_fail "Immutability rules not restored"
    fi
}

test_backup_encryption() {
    log_info "Testing backup encryption..."

    # Try to read backup file without decryption (should fail)
    local backup_file="${TEST_BACKUP_DIR}/${BACKUP_FILENAME}"

    if file "${backup_file}" | grep -q "openssl"; then
        log_test_pass "Backup file is encrypted (OpenSSL format)"
    else
        log_test_fail "Backup file may not be properly encrypted"
    fi

    # Try to decrypt with wrong password (should fail)
    if openssl enc -aes-256-cbc -d -pbkdf2 -iter 100000 -in "${backup_file}" -pass "pass:wrong_password" 2>&1 | grep -q "bad decrypt"; then
        log_test_pass "Encryption validation: Wrong password rejected"
    else
        log_test_fail "Encryption validation: Wrong password not rejected"
    fi
}

print_summary() {
    echo ""
    echo "==================================================================="
    echo "Test Summary"
    echo "==================================================================="
    echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
    echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"
    echo "==================================================================="

    if [[ ${TESTS_FAILED} -eq 0 ]]; then
        echo -e "${GREEN}ALL TESTS PASSED ✓${NC}"
        echo ""
        echo "Backup and restore procedures are working correctly."
        echo ""
        echo "Production usage:"
        echo "  - Backup: ./scripts/backup-postgres.sh"
        echo "  - Restore: ./scripts/restore-postgres.sh <backup_filename>"
        echo "  - Schedule: Add to cron for daily backups"
        echo ""
        return 0
    else
        echo -e "${RED}SOME TESTS FAILED ✗${NC}"
        echo ""
        echo "Check logs in: ${TEST_BACKUP_DIR}/test.log"
        return 1
    fi
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    echo "==================================================================="
    echo "PostgreSQL Backup/Restore Test Suite"
    echo "==================================================================="
    echo ""

    # Load environment variables if .env exists
    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        log_info "Loading environment from .env"
        set -a
        source "${PROJECT_ROOT}/.env"
        set +a
    fi

    # Run tests
    check_prerequisites
    create_test_database
    verify_test_data
    test_backup_script
    test_backup_encryption
    test_restore_script

    # Print summary
    print_summary
}

main "$@"
