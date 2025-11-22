#!/bin/bash

# Clinical Care Tools - Database Backup Script
# Version: 1.0.0
# Purpose: Automated database backup with compression and retention

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_DIR="$(dirname "$0")/../backups"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/clinical-care-tools_${BACKUP_DATE}.sql.gz"
RETENTION_DAYS=${RETENTION_DAYS:-30}  # Keep 30 days by default

mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}Starting database backup...${NC}"
echo "Backup file: $BACKUP_FILE"
echo ""

# Create backup
echo "Creating backup..."
if docker-compose exec -T postgres pg_dump -U clinical_admin clinical_care_tools 2>/dev/null | gzip > "$BACKUP_FILE"; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Backup completed${NC}"
    echo "Size: $BACKUP_SIZE"
else
    echo -e "${RED}Error: Backup failed${NC}"
    exit 1
fi

echo ""

# List backups
echo "Recent backups:"
ls -lh "$BACKUP_DIR" | tail -10

echo ""

# Clean up old backups
echo "Removing backups older than $RETENTION_DAYS days..."
DELETED=$(find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete -print | wc -l)

if [ $DELETED -gt 0 ]; then
    echo "Deleted $DELETED old backup(s)"
fi

echo ""
echo -e "${GREEN}Backup completed successfully!${NC}"
echo ""
echo "Restore command:"
echo "  ./scripts/restore-db.sh $BACKUP_FILE"
