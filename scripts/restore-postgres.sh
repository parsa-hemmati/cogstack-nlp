#!/usr/bin/env bash
# PostgreSQL Restore Script with Decryption
# Version: 1.0.0
# Purpose: Restore PostgreSQL database from encrypted backup
# Usage: ./scripts/restore-postgres.sh <backup_filename>
# Example: ./scripts/restore-postgres.sh clinical_care_tools_2025-11-18_02-00-00.sql.gz.enc
# Warning: This will OVERWRITE the existing database!

set -euo pipefail  # Exit on error, undefined variable, or pipe failure
IFS=$'\n\t'        # Set Internal Field Separator to newline and tab

# =============================================================================
# Configuration
# =============================================================================

# Backup directory (must match backup script)
BACKUP_DIR="${BACKUP_DIR:-/var/backups/clinical_care_tools}"

# PostgreSQL connection details (from .env or environment)
POSTGRES_USER="${POSTGRES_USER:-clinicaltools}"
POSTGRES_DB="${POSTGRES_DB:-clinical_care_tools}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?ERROR: POSTGRES_PASSWORD environment variable is required}"

# Encryption password (MUST match backup encryption key)
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:?ERROR: BACKUP_ENCRYPTION_KEY environment variable is required}"

# Temporary files (cleaned up on exit)
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
TEMP_GZIP="/tmp/restore_${TIMESTAMP}.sql.gz"
TEMP_SQL="/tmp/restore_${TIMESTAMP}.sql"

# Logging
LOG_FILE="${BACKUP_DIR}/restore.log"

# Confirmation required flag (set to "false" to skip confirmation prompt)
REQUIRE_CONFIRMATION="${REQUIRE_CONFIRMATION:-true}"

# =============================================================================
# Functions
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

cleanup() {
    # Remove temporary files on exit
    if [[ -f "${TEMP_SQL}" ]]; then
        rm -f "${TEMP_SQL}"
    fi
    if [[ -f "${TEMP_GZIP}" ]]; then
        rm -f "${TEMP_GZIP}"
    fi
}

trap cleanup EXIT

usage() {
    cat << EOF
Usage: $0 <backup_filename>

Restore PostgreSQL database from encrypted backup.

Arguments:
  backup_filename    Name of backup file in ${BACKUP_DIR}/
                     Example: clinical_care_tools_2025-11-18_02-00-00.sql.gz.enc

Environment Variables:
  POSTGRES_USER              PostgreSQL username (default: clinicaltools)
  POSTGRES_DB                PostgreSQL database name (default: clinical_care_tools)
  POSTGRES_HOST              PostgreSQL host (default: localhost)
  POSTGRES_PORT              PostgreSQL port (default: 5432)
  POSTGRES_PASSWORD          PostgreSQL password (REQUIRED)
  BACKUP_ENCRYPTION_KEY      Backup encryption key (REQUIRED)
  BACKUP_DIR                 Backup directory (default: /var/backups/clinical_care_tools)
  REQUIRE_CONFIRMATION       Require confirmation (default: true)

Examples:
  # Restore from backup (with confirmation)
  ./scripts/restore-postgres.sh clinical_care_tools_2025-11-18_02-00-00.sql.gz.enc

  # Restore without confirmation (automated scripts)
  REQUIRE_CONFIRMATION=false ./scripts/restore-postgres.sh clinical_care_tools_2025-11-18_02-00-00.sql.gz.enc

  # List available backups
  ls -lh ${BACKUP_DIR}/clinical_care_tools_*.sql.gz.enc

EOF
    exit 1
}

check_dependencies() {
    local deps=("psql" "gzip" "openssl")
    for cmd in "${deps[@]}"; do
        if ! command -v "${cmd}" &> /dev/null; then
            log "ERROR" "Required command not found: ${cmd}"
            log "ERROR" "Install with: apt-get install postgresql-client gzip openssl"
            exit 1
        fi
    done
}

verify_postgres_connection() {
    log "INFO" "Verifying PostgreSQL connection..."
    export PGPASSWORD="${POSTGRES_PASSWORD}"

    if ! pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" &> /dev/null; then
        log "ERROR" "PostgreSQL is not accepting connections"
        log "ERROR" "Check if postgres service is running: docker-compose ps postgres"
        exit 1
    fi

    log "INFO" "PostgreSQL connection verified"
}

confirm_restore() {
    if [[ "${REQUIRE_CONFIRMATION}" != "true" ]]; then
        log "INFO" "Confirmation skipped (REQUIRE_CONFIRMATION=false)"
        return 0
    fi

    log "WARN" "==================================================================="
    log "WARN" "WARNING: This will OVERWRITE the existing database!"
    log "WARN" "==================================================================="
    log "WARN" "Database: ${POSTGRES_DB}"
    log "WARN" "Host: ${POSTGRES_HOST}:${POSTGRES_PORT}"
    log "WARN" "Backup file: ${BACKUP_FILENAME}"
    log "WARN" ""
    log "WARN" "All existing data will be PERMANENTLY DELETED!"
    log "WARN" ""

    read -r -p "Are you sure you want to continue? (Type 'yes' to confirm): " confirmation

    if [[ "${confirmation}" != "yes" ]]; then
        log "INFO" "Restore cancelled by user"
        exit 0
    fi

    log "INFO" "User confirmed restore operation"
}

verify_backup_file() {
    local backup_file="$1"

    if [[ ! -f "${backup_file}" ]]; then
        log "ERROR" "Backup file not found: ${backup_file}"
        log "ERROR" "Available backups:"
        ls -lh "${BACKUP_DIR}"/clinical_care_tools_*.sql.gz.enc 2>&1 | tee -a "${LOG_FILE}"
        exit 1
    fi

    local file_size
    file_size=$(stat -c%s "${backup_file}")

    if [[ "${file_size}" -lt 1024 ]]; then
        log "ERROR" "Backup file is suspiciously small: ${file_size} bytes"
        exit 1
    fi

    log "INFO" "Backup file verified: $(du -h "${backup_file}" | cut -f1)"
}

decrypt_backup() {
    local backup_file="$1"

    log "INFO" "Decrypting backup with AES-256-CBC..."

    # OpenSSL decryption options (must match encryption parameters)
    if ! openssl enc \
        -aes-256-cbc \
        -d \
        -pbkdf2 \
        -iter 100000 \
        -in "${backup_file}" \
        -out "${TEMP_GZIP}" \
        -pass "pass:${BACKUP_ENCRYPTION_KEY}" 2>> "${LOG_FILE}"; then
        log "ERROR" "OpenSSL decryption failed with exit code $?"
        log "ERROR" "Possible causes:"
        log "ERROR" "  - Incorrect BACKUP_ENCRYPTION_KEY"
        log "ERROR" "  - Corrupted backup file"
        exit 1
    fi

    local gzip_size
    gzip_size=$(du -h "${TEMP_GZIP}" | cut -f1)
    log "INFO" "Decryption completed: ${gzip_size}"
}

decompress_backup() {
    log "INFO" "Decompressing backup with gunzip..."

    if ! gunzip -c "${TEMP_GZIP}" > "${TEMP_SQL}"; then
        log "ERROR" "gunzip decompression failed with exit code $?"
        log "ERROR" "Backup file may be corrupted"
        exit 1
    fi

    local sql_size
    sql_size=$(du -h "${TEMP_SQL}" | cut -f1)
    log "INFO" "Decompression completed: ${sql_size}"
}

restore_database() {
    log "INFO" "Restoring database from SQL dump..."
    export PGPASSWORD="${POSTGRES_PASSWORD}"

    # psql options:
    # -h: Host
    # -p: Port
    # -U: Username
    # -d: Database (use 'postgres' to connect before CREATE DATABASE)
    # -f: SQL file to execute
    # -v ON_ERROR_STOP=1: Stop on first error

    # First, drop and recreate the database (SQL file contains CREATE DATABASE)
    log "INFO" "Executing SQL restore..."

    if ! psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d postgres \
        -v ON_ERROR_STOP=1 \
        -f "${TEMP_SQL}" \
        >> "${LOG_FILE}" 2>&1; then
        log "ERROR" "psql restore failed with exit code $?"
        log "ERROR" "Check ${LOG_FILE} for details"
        exit 1
    fi

    log "INFO" "Database restore completed successfully"
}

verify_restore() {
    log "INFO" "Verifying database restore..."
    export PGPASSWORD="${POSTGRES_PASSWORD}"

    # Check if database exists and is accessible
    if ! psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -c "SELECT 1;" &> /dev/null; then
        log "ERROR" "Restored database is not accessible"
        exit 1
    fi

    # Count tables (should be > 0)
    local table_count
    table_count=$(psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

    if [[ "${table_count}" -eq 0 ]]; then
        log "ERROR" "No tables found in restored database"
        exit 1
    fi

    log "INFO" "Database verification successful"
    log "INFO" "  - Database: ${POSTGRES_DB}"
    log "INFO" "  - Tables: ${table_count}"

    # Check for critical tables (audit_logs, users, patients, documents)
    local critical_tables=("audit_logs" "users" "patients" "documents")
    for table in "${critical_tables[@]}"; do
        if psql \
            -h "${POSTGRES_HOST}" \
            -p "${POSTGRES_PORT}" \
            -U "${POSTGRES_USER}" \
            -d "${POSTGRES_DB}" \
            -t -c "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '${table}';" | grep -q 1; then
            log "INFO" "  - Table '${table}': ✓ Present"
        else
            log "WARN" "  - Table '${table}': ✗ Missing (may be expected for fresh install)"
        fi
    done

    # Check audit logs are still immutable (PostgreSQL rules)
    if psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -t -c "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'audit_logs';" | grep -q 1; then
        local rule_count
        rule_count=$(psql \
            -h "${POSTGRES_HOST}" \
            -p "${POSTGRES_PORT}" \
            -U "${POSTGRES_USER}" \
            -d "${POSTGRES_DB}" \
            -t -c "SELECT COUNT(*) FROM pg_rules WHERE tablename = 'audit_logs' AND rulename IN ('no_update_audit_logs', 'no_delete_audit_logs');" | tr -d ' ')

        if [[ "${rule_count}" -eq 2 ]]; then
            log "INFO" "  - Audit log immutability: ✓ Enforced (2 rules)"
        else
            log "ERROR" "  - Audit log immutability: ✗ Missing rules (HIPAA VIOLATION!)"
            log "ERROR" "    Run migrations to recreate: alembic upgrade head"
        fi
    fi
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    # Check arguments
    if [[ $# -ne 1 ]]; then
        log "ERROR" "Missing backup filename argument"
        usage
    fi

    BACKUP_FILENAME="$1"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

    log "INFO" "==================================================================="
    log "INFO" "PostgreSQL Restore Script - Starting"
    log "INFO" "==================================================================="
    log "INFO" "Backup file: ${BACKUP_FILENAME}"

    # Pre-flight checks
    check_dependencies
    verify_postgres_connection
    verify_backup_file "${BACKUP_PATH}"
    confirm_restore

    # Restore workflow
    decrypt_backup "${BACKUP_PATH}"
    decompress_backup
    restore_database
    verify_restore

    log "INFO" "==================================================================="
    log "INFO" "PostgreSQL Restore Script - Completed Successfully"
    log "INFO" "==================================================================="
    log "INFO" "Database '${POSTGRES_DB}' has been restored from backup"
    log "INFO" "Backup: ${BACKUP_FILENAME}"
}

# Run main function
main "$@"
