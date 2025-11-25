#!/usr/bin/env bash
# PostgreSQL Backup Script with Encryption
# Version: 1.0.0
# Purpose: Automated PostgreSQL backup with gzip compression and AES-256 encryption
# Usage: ./scripts/backup-postgres.sh
# Schedule: Run daily via cron (e.g., 0 2 * * * /path/to/backup-postgres.sh)
# Retention: 30 days (configurable via BACKUP_RETENTION_DAYS)
# HIPAA Compliance: Encrypted backups, immutable audit logs, 8-year retention requirement

set -euo pipefail  # Exit on error, undefined variable, or pipe failure
IFS=$'\n\t'        # Set Internal Field Separator to newline and tab

# =============================================================================
# Configuration
# =============================================================================

# Backup directory (must exist and be writable)
BACKUP_DIR="${BACKUP_DIR:-/var/backups/clinical_care_tools}"

# Backup retention in days (30 days default, 2920 days for HIPAA compliance)
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# PostgreSQL connection details (from .env or environment)
POSTGRES_USER="${POSTGRES_USER:-clinicaltools}"
POSTGRES_DB="${POSTGRES_DB:-clinical_care_tools}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?ERROR: POSTGRES_PASSWORD environment variable is required}"

# Encryption password (MUST be set in environment or .env file)
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:?ERROR: BACKUP_ENCRYPTION_KEY environment variable is required}"

# Backup filename format: clinical_care_tools_YYYY-MM-DD_HH-MM-SS.sql.gz.enc
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILENAME="clinical_care_tools_${TIMESTAMP}.sql.gz.enc"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

# Temporary files (cleaned up on exit)
TEMP_SQL="/tmp/backup_${TIMESTAMP}.sql"
TEMP_GZIP="/tmp/backup_${TIMESTAMP}.sql.gz"

# Logging
LOG_FILE="${BACKUP_DIR}/backup.log"

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

check_dependencies() {
    local deps=("pg_dump" "gzip" "openssl")
    for cmd in "${deps[@]}"; do
        if ! command -v "${cmd}" &> /dev/null; then
            log "ERROR" "Required command not found: ${cmd}"
            log "ERROR" "Install with: apt-get install postgresql-client gzip openssl"
            exit 1
        fi
    done
}

create_backup_dir() {
    if [[ ! -d "${BACKUP_DIR}" ]]; then
        log "INFO" "Creating backup directory: ${BACKUP_DIR}"
        mkdir -p "${BACKUP_DIR}"
        chmod 700 "${BACKUP_DIR}"  # Owner only (security)
    fi
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

dump_database() {
    log "INFO" "Starting PostgreSQL dump..."
    export PGPASSWORD="${POSTGRES_PASSWORD}"

    # pg_dump options:
    # --clean: Drop objects before recreating (for restore)
    # --if-exists: Use IF EXISTS when dropping objects
    # --create: Include CREATE DATABASE statement
    # --no-owner: Skip ownership commands (for portability)
    # --no-acl: Skip access privileges (for portability)
    # --format=plain: Plain SQL format (human-readable, compresses well)
    # --verbose: Verbose output to stderr

    if ! pg_dump \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --clean \
        --if-exists \
        --create \
        --no-owner \
        --no-acl \
        --format=plain \
        --verbose \
        > "${TEMP_SQL}" 2>> "${LOG_FILE}"; then
        log "ERROR" "pg_dump failed with exit code $?"
        exit 1
    fi

    local sql_size
    sql_size=$(du -h "${TEMP_SQL}" | cut -f1)
    log "INFO" "Database dump completed: ${sql_size}"
}

compress_backup() {
    log "INFO" "Compressing backup with gzip..."

    # gzip options:
    # -9: Maximum compression (slower but smaller)
    # -c: Write to stdout (preserve original file for encryption)

    if ! gzip -9 -c "${TEMP_SQL}" > "${TEMP_GZIP}"; then
        log "ERROR" "gzip compression failed with exit code $?"
        exit 1
    fi

    local gzip_size
    gzip_size=$(du -h "${TEMP_GZIP}" | cut -f1)
    log "INFO" "Compression completed: ${gzip_size}"
}

encrypt_backup() {
    log "INFO" "Encrypting backup with AES-256-CBC..."

    # OpenSSL encryption options:
    # enc: Encryption/decryption
    # -aes-256-cbc: AES-256 with CBC mode (HIPAA-compliant)
    # -salt: Use salt in key derivation (prevents rainbow table attacks)
    # -pbkdf2: Use PBKDF2 for key derivation (recommended by NIST)
    # -iter 100000: 100,000 iterations for PBKDF2 (slow brute force)
    # -in: Input file (gzipped SQL)
    # -out: Output file (encrypted)
    # -pass: Password (from environment variable)

    if ! openssl enc \
        -aes-256-cbc \
        -salt \
        -pbkdf2 \
        -iter 100000 \
        -in "${TEMP_GZIP}" \
        -out "${BACKUP_PATH}" \
        -pass "pass:${BACKUP_ENCRYPTION_KEY}" 2>> "${LOG_FILE}"; then
        log "ERROR" "OpenSSL encryption failed with exit code $?"
        exit 1
    fi

    local enc_size
    enc_size=$(du -h "${BACKUP_PATH}" | cut -f1)
    log "INFO" "Encryption completed: ${enc_size}"
}

verify_backup() {
    log "INFO" "Verifying backup file..."

    if [[ ! -f "${BACKUP_PATH}" ]]; then
        log "ERROR" "Backup file not found: ${BACKUP_PATH}"
        exit 1
    fi

    local file_size
    file_size=$(stat -c%s "${BACKUP_PATH}")

    if [[ "${file_size}" -lt 1024 ]]; then
        log "ERROR" "Backup file is suspiciously small: ${file_size} bytes"
        exit 1
    fi

    # Verify file can be decrypted (quick test)
    if ! openssl enc \
        -aes-256-cbc \
        -d \
        -pbkdf2 \
        -iter 100000 \
        -in "${BACKUP_PATH}" \
        -pass "pass:${BACKUP_ENCRYPTION_KEY}" \
        | gzip -t 2>> "${LOG_FILE}"; then
        log "ERROR" "Backup verification failed (cannot decrypt or decompress)"
        exit 1
    fi

    log "INFO" "Backup verification successful"
}

cleanup_old_backups() {
    log "INFO" "Cleaning up backups older than ${BACKUP_RETENTION_DAYS} days..."

    local deleted_count=0

    # Find and delete old backups
    while IFS= read -r old_backup; do
        log "INFO" "Deleting old backup: $(basename "${old_backup}")"
        rm -f "${old_backup}"
        ((deleted_count++))
    done < <(find "${BACKUP_DIR}" -name "clinical_care_tools_*.sql.gz.enc" -type f -mtime "+${BACKUP_RETENTION_DAYS}")

    if [[ ${deleted_count} -gt 0 ]]; then
        log "INFO" "Deleted ${deleted_count} old backup(s)"
    else
        log "INFO" "No old backups to delete"
    fi
}

calculate_backup_stats() {
    local backup_count
    backup_count=$(find "${BACKUP_DIR}" -name "clinical_care_tools_*.sql.gz.enc" -type f | wc -l)

    local total_size
    total_size=$(du -sh "${BACKUP_DIR}" | cut -f1)

    log "INFO" "Backup statistics:"
    log "INFO" "  - Total backups: ${backup_count}"
    log "INFO" "  - Total size: ${total_size}"
    log "INFO" "  - Retention policy: ${BACKUP_RETENTION_DAYS} days"
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    log "INFO" "==================================================================="
    log "INFO" "PostgreSQL Backup Script - Starting"
    log "INFO" "==================================================================="
    log "INFO" "Backup file: ${BACKUP_FILENAME}"

    # Pre-flight checks
    check_dependencies
    create_backup_dir
    verify_postgres_connection

    # Backup workflow
    dump_database
    compress_backup
    encrypt_backup
    verify_backup

    # Post-backup maintenance
    cleanup_old_backups
    calculate_backup_stats

    log "INFO" "==================================================================="
    log "INFO" "PostgreSQL Backup Script - Completed Successfully"
    log "INFO" "==================================================================="
    log "INFO" "Backup location: ${BACKUP_PATH}"
    log "INFO" "To restore: ./scripts/restore-postgres.sh ${BACKUP_FILENAME}"
}

# Run main function
main "$@"
