#!/bin/bash
#
# PostgreSQL Backup Script for Clinical Care Tools
# 
# This script creates encrypted, compressed backups of the PostgreSQL database.
# Designed to be run by cron for automated daily backups.
#
# Usage:
#   ./backup_database.sh              # Creates backup with default settings
#   ./backup_database.sh --encrypt    # Creates encrypted backup (requires GPG key)
#   ./backup_database.sh --s3         # Uploads to S3 after local backup
#
# Environment Variables:
#   BACKUP_DIR        - Backup storage directory (default: /backups)
#   POSTGRES_HOST     - PostgreSQL host (default: postgres)
#   POSTGRES_PORT     - PostgreSQL port (default: 5432)
#   POSTGRES_USER     - PostgreSQL user (default: postgres)
#   POSTGRES_DB       - PostgreSQL database (default: clinical_care_tools)
#   POSTGRES_PASSWORD - PostgreSQL password (required for non-Docker)
#   RETENTION_DAYS    - Days to keep backups (default: 30)
#   GPG_RECIPIENT     - GPG key ID for encryption (optional)
#   AWS_S3_BUCKET     - S3 bucket for remote backup (optional)
#
# Requirements:
#   - pg_dump (PostgreSQL client)
#   - gzip
#   - gpg (for encryption)
#   - aws cli (for S3 upload)
#

set -euo pipefail

# Configuration with defaults
BACKUP_DIR="${BACKUP_DIR:-/backups}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-clinical_care_tools}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Timestamp for backup file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${POSTGRES_DB}_${TIMESTAMP}"
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"

# Parse arguments
ENCRYPT=false
UPLOAD_S3=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --encrypt)
            ENCRYPT=true
            shift
            ;;
        --s3)
            UPLOAD_S3=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

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

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

log_info "Starting PostgreSQL backup for ${POSTGRES_DB}"
log_info "Backup file: ${BACKUP_FILE}"

# Perform backup using pg_dump
# Using custom format for better compression and parallel restore capability
if command -v docker &> /dev/null && docker ps -q -f name=clinical-care-postgres &> /dev/null; then
    # Docker environment
    log_info "Using Docker for backup"
    docker exec clinical-care-postgres pg_dump \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --format=plain \
        --no-owner \
        --no-privileges \
        | gzip > "${BACKUP_FILE}"
else
    # Direct connection
    log_info "Using direct connection for backup"
    PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --format=plain \
        --no-owner \
        --no-privileges \
        | gzip > "${BACKUP_FILE}"
fi

# Get backup file size
BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
log_info "Backup completed. Size: ${BACKUP_SIZE}"

# Encrypt if requested
if [ "${ENCRYPT}" = true ]; then
    if [ -z "${GPG_RECIPIENT:-}" ]; then
        log_error "GPG_RECIPIENT not set. Cannot encrypt backup."
        exit 1
    fi
    
    log_info "Encrypting backup with GPG..."
    gpg --encrypt --recipient "${GPG_RECIPIENT}" "${BACKUP_FILE}"
    rm "${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE}.gpg"
    log_info "Backup encrypted: ${BACKUP_FILE}"
fi

# Upload to S3 if requested
if [ "${UPLOAD_S3}" = true ]; then
    if [ -z "${AWS_S3_BUCKET:-}" ]; then
        log_error "AWS_S3_BUCKET not set. Cannot upload to S3."
        exit 1
    fi
    
    log_info "Uploading backup to S3: ${AWS_S3_BUCKET}"
    aws s3 cp "${BACKUP_FILE}" "s3://${AWS_S3_BUCKET}/backups/${POSTGRES_DB}/"
    log_info "Backup uploaded to S3"
fi

# Cleanup old backups
log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."
DELETED_COUNT=$(find "${BACKUP_DIR}" -name "${POSTGRES_DB}_*.sql.gz*" -type f -mtime +${RETENTION_DAYS} -delete -print | wc -l)
log_info "Deleted ${DELETED_COUNT} old backup(s)"

# List recent backups
log_info "Recent backups:"
ls -lht "${BACKUP_DIR}"/*.sql.gz* 2>/dev/null | head -5 || log_warn "No backups found"

log_info "Backup process completed successfully"

# Create metadata file
METADATA_FILE="${BACKUP_FILE}.meta"
cat > "${METADATA_FILE}" << EOF
{
  "database": "${POSTGRES_DB}",
  "host": "${POSTGRES_HOST}",
  "timestamp": "${TIMESTAMP}",
  "file": "${BACKUP_FILE}",
  "size_bytes": $(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}"),
  "encrypted": ${ENCRYPT},
  "uploaded_s3": ${UPLOAD_S3}
}
EOF

log_info "Metadata saved to ${METADATA_FILE}"

exit 0
