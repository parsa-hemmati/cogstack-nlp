#!/bin/bash
#
# PostgreSQL Restore Script for Clinical Care Tools
#
# Restores a PostgreSQL database from a backup file.
# Supports compressed (.gz) and encrypted (.gpg) backups.
#
# Usage:
#   ./restore_database.sh backup_file.sql.gz
#   ./restore_database.sh backup_file.sql.gz.gpg  # For encrypted backups
#   ./restore_database.sh backup_file.sql.gz --verify-only  # Verify backup integrity only
#
# Environment Variables:
#   POSTGRES_HOST     - PostgreSQL host (default: postgres)
#   POSTGRES_PORT     - PostgreSQL port (default: 5432)
#   POSTGRES_USER     - PostgreSQL user (default: postgres)
#   POSTGRES_DB       - PostgreSQL database (default: clinical_care_tools)
#   POSTGRES_PASSWORD - PostgreSQL password (required for non-Docker)
#

set -euo pipefail

# Configuration with defaults
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-clinical_care_tools}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Parse arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file> [--verify-only]"
    exit 1
fi

BACKUP_FILE="$1"
VERIFY_ONLY=false

if [ "${2:-}" = "--verify-only" ]; then
    VERIFY_ONLY=true
fi

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    log_error "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

log_info "=== PostgreSQL Restore Process ==="
log_info "Backup file: ${BACKUP_FILE}"
log_info "Target database: ${POSTGRES_DB}"

# Determine file type and prepare for restore
TEMP_FILE=""
CLEANUP_TEMP=false

if [[ "${BACKUP_FILE}" == *.gpg ]]; then
    log_info "Detected encrypted backup. Decrypting..."
    TEMP_FILE="${BACKUP_FILE%.gpg}"
    gpg --decrypt --output "${TEMP_FILE}" "${BACKUP_FILE}"
    BACKUP_FILE="${TEMP_FILE}"
    CLEANUP_TEMP=true
    log_info "Decrypted to: ${TEMP_FILE}"
fi

# Verify backup integrity
log_info "Verifying backup integrity..."
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    if gzip -t "${BACKUP_FILE}" 2>/dev/null; then
        log_info "Backup integrity verified (gzip OK)"
    else
        log_error "Backup file is corrupted!"
        exit 1
    fi
fi

if [ "${VERIFY_ONLY}" = true ]; then
    log_info "Verification complete. Exiting (--verify-only mode)"
    [ "${CLEANUP_TEMP}" = true ] && rm -f "${TEMP_FILE}"
    exit 0
fi

# Confirmation prompt
log_warn "WARNING: This will OVERWRITE the database '${POSTGRES_DB}'"
echo -n "Are you sure you want to continue? (yes/no): "
read -r CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    log_info "Restore cancelled by user"
    [ "${CLEANUP_TEMP}" = true ] && rm -f "${TEMP_FILE}"
    exit 0
fi

# Create a pre-restore backup
log_info "Creating pre-restore backup..."
PRE_RESTORE_BACKUP="/tmp/pre_restore_${POSTGRES_DB}_$(date +%Y%m%d_%H%M%S).sql.gz"

if command -v docker &> /dev/null && docker ps -q -f name=clinical-care-postgres &> /dev/null; then
    docker exec clinical-care-postgres pg_dump \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        | gzip > "${PRE_RESTORE_BACKUP}" 2>/dev/null || true
else
    PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        | gzip > "${PRE_RESTORE_BACKUP}" 2>/dev/null || true
fi

log_info "Pre-restore backup saved to: ${PRE_RESTORE_BACKUP}"

# Perform restore
log_info "Starting restore process..."

if command -v docker &> /dev/null && docker ps -q -f name=clinical-care-postgres &> /dev/null; then
    # Docker environment
    log_info "Using Docker for restore"
    
    # Drop and recreate database
    docker exec clinical-care-postgres psql -U "${POSTGRES_USER}" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();" postgres
    docker exec clinical-care-postgres psql -U "${POSTGRES_USER}" -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" postgres
    docker exec clinical-care-postgres psql -U "${POSTGRES_USER}" -c "CREATE DATABASE ${POSTGRES_DB};" postgres
    
    # Restore data
    gunzip -c "${BACKUP_FILE}" | docker exec -i clinical-care-postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
else
    # Direct connection
    log_info "Using direct connection for restore"
    
    # Drop and recreate database
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();" postgres
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" postgres
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -c "CREATE DATABASE ${POSTGRES_DB};" postgres
    
    # Restore data
    gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
fi

# Cleanup temp files
[ "${CLEANUP_TEMP}" = true ] && rm -f "${TEMP_FILE}"

log_info "=== Restore Complete ==="
log_info "Database '${POSTGRES_DB}' has been restored from backup"
log_info "Pre-restore backup available at: ${PRE_RESTORE_BACKUP}"

# Verify restore
log_info "Verifying restore..."
if command -v docker &> /dev/null && docker ps -q -f name=clinical-care-postgres &> /dev/null; then
    TABLE_COUNT=$(docker exec clinical-care-postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
else
    TABLE_COUNT=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
fi

log_info "Restored database contains ${TABLE_COUNT// /} tables"

exit 0
