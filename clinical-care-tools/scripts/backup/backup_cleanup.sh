#!/bin/bash
#
# Backup Cleanup Script for Clinical Care Tools
#
# Implements backup retention policy:
# - Keep daily backups for RETENTION_DAILY days
# - Keep weekly backups for RETENTION_WEEKLY weeks
# - Keep monthly backups for RETENTION_MONTHLY months
#
# Usage:
#   ./backup_cleanup.sh              # Dry run (shows what would be deleted)
#   ./backup_cleanup.sh --execute    # Actually delete old backups
#
# Environment Variables:
#   BACKUP_DIR          - Backup storage directory (default: /backups)
#   RETENTION_DAILY     - Days to keep daily backups (default: 7)
#   RETENTION_WEEKLY    - Weeks to keep weekly backups (default: 4)
#   RETENTION_MONTHLY   - Months to keep monthly backups (default: 12)
#   POSTGRES_DB         - Database name for backup file matching (default: clinical_care_tools)
#

set -euo pipefail

# Configuration with defaults
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAILY="${RETENTION_DAILY:-7}"
RETENTION_WEEKLY="${RETENTION_WEEKLY:-4}"
RETENTION_MONTHLY="${RETENTION_MONTHLY:-12}"
POSTGRES_DB="${POSTGRES_DB:-clinical_care_tools}"

# Parse arguments
DRY_RUN=true
if [ "${1:-}" = "--execute" ]; then
    DRY_RUN=false
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_delete() {
    echo -e "${RED}[DELETE]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_keep() {
    echo -e "${BLUE}[KEEP]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_info "=== Backup Cleanup Process ==="
log_info "Backup directory: ${BACKUP_DIR}"
log_info "Retention policy:"
log_info "  - Daily: ${RETENTION_DAILY} days"
log_info "  - Weekly: ${RETENTION_WEEKLY} weeks"
log_info "  - Monthly: ${RETENTION_MONTHLY} months"

if [ "${DRY_RUN}" = true ]; then
    log_warn "DRY RUN MODE - No files will be deleted"
    log_warn "Use --execute to actually delete files"
fi

echo ""

# Get all backup files sorted by date (newest first)
BACKUPS=$(find "${BACKUP_DIR}" -name "${POSTGRES_DB}_*.sql.gz*" -type f 2>/dev/null | sort -r)

if [ -z "${BACKUPS}" ]; then
    log_warn "No backup files found matching pattern: ${POSTGRES_DB}_*.sql.gz*"
    exit 0
fi

# Calculate retention dates
TODAY=$(date +%Y%m%d)
DAILY_CUTOFF=$(date -d "${RETENTION_DAILY} days ago" +%Y%m%d 2>/dev/null || date -v-${RETENTION_DAILY}d +%Y%m%d)
WEEKLY_CUTOFF=$(date -d "$((RETENTION_WEEKLY * 7)) days ago" +%Y%m%d 2>/dev/null || date -v-$((RETENTION_WEEKLY * 7))d +%Y%m%d)
MONTHLY_CUTOFF=$(date -d "${RETENTION_MONTHLY} months ago" +%Y%m%d 2>/dev/null || date -v-${RETENTION_MONTHLY}m +%Y%m%d)

# Track which weekly/monthly backups we're keeping
declare -A KEPT_WEEKLY
declare -A KEPT_MONTHLY

DELETE_COUNT=0
KEEP_COUNT=0
DELETE_SIZE=0

for BACKUP in ${BACKUPS}; do
    FILENAME=$(basename "${BACKUP}")
    
    # Extract date from filename (format: database_YYYYMMDD_HHMMSS.sql.gz)
    BACKUP_DATE=$(echo "${FILENAME}" | grep -oE '[0-9]{8}' | head -1)
    
    if [ -z "${BACKUP_DATE}" ]; then
        log_warn "Cannot parse date from: ${FILENAME}"
        continue
    fi
    
    # Calculate week and month
    BACKUP_WEEK="${BACKUP_DATE:0:4}-$(date -d "${BACKUP_DATE}" +%V 2>/dev/null || date -j -f "%Y%m%d" "${BACKUP_DATE}" +%V)"
    BACKUP_MONTH="${BACKUP_DATE:0:6}"
    
    KEEP=false
    REASON=""
    
    # Rule 1: Keep all backups from the last RETENTION_DAILY days
    if [ "${BACKUP_DATE}" -ge "${DAILY_CUTOFF}" ]; then
        KEEP=true
        REASON="daily retention"
    # Rule 2: Keep one backup per week for RETENTION_WEEKLY weeks
    elif [ "${BACKUP_DATE}" -ge "${WEEKLY_CUTOFF}" ]; then
        if [ -z "${KEPT_WEEKLY[${BACKUP_WEEK}]:-}" ]; then
            KEEP=true
            REASON="weekly retention"
            KEPT_WEEKLY[${BACKUP_WEEK}]=1
        fi
    # Rule 3: Keep one backup per month for RETENTION_MONTHLY months
    elif [ "${BACKUP_DATE}" -ge "${MONTHLY_CUTOFF}" ]; then
        if [ -z "${KEPT_MONTHLY[${BACKUP_MONTH}]:-}" ]; then
            KEEP=true
            REASON="monthly retention"
            KEPT_MONTHLY[${BACKUP_MONTH}]=1
        fi
    fi
    
    # Get file size
    FILE_SIZE=$(stat -f%z "${BACKUP}" 2>/dev/null || stat -c%s "${BACKUP}")
    FILE_SIZE_MB=$((FILE_SIZE / 1024 / 1024))
    
    if [ "${KEEP}" = true ]; then
        log_keep "${FILENAME} (${FILE_SIZE_MB}MB) - ${REASON}"
        KEEP_COUNT=$((KEEP_COUNT + 1))
    else
        log_delete "${FILENAME} (${FILE_SIZE_MB}MB) - exceeds retention"
        DELETE_COUNT=$((DELETE_COUNT + 1))
        DELETE_SIZE=$((DELETE_SIZE + FILE_SIZE))
        
        if [ "${DRY_RUN}" = false ]; then
            rm -f "${BACKUP}"
            # Also remove metadata file if exists
            rm -f "${BACKUP}.meta"
        fi
    fi
done

echo ""
log_info "=== Cleanup Summary ==="
log_info "Backups kept: ${KEEP_COUNT}"
log_info "Backups deleted: ${DELETE_COUNT}"
log_info "Space freed: $((DELETE_SIZE / 1024 / 1024)) MB"

if [ "${DRY_RUN}" = true ] && [ "${DELETE_COUNT}" -gt 0 ]; then
    echo ""
    log_warn "Run with --execute to actually delete ${DELETE_COUNT} backup(s)"
fi

exit 0
