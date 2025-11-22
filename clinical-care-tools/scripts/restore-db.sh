#!/bin/bash

# Clinical Care Tools - Database Restore Script
# Version: 1.0.0
# Purpose: Restore database from backup file

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}Usage: ./restore-db.sh <backup_file>${NC}"
    echo ""
    echo "Example:"
    echo "  ./restore-db.sh backups/clinical-care-tools_20250108_120000.sql.gz"
    echo ""
    echo "Available backups:"
    ls -1 backups/*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"
BACKUP_DIR="$(dirname "$0")/../backups"

# Resolve path
if [[ ! "$BACKUP_FILE" = /* ]]; then
    BACKUP_FILE="$(pwd)/$BACKUP_FILE"
fi

# Check if backup exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo -e "${YELLOW}=========================================="
echo "Clinical Care Tools - Database Restore"
echo "==========================================${NC}"
echo ""
echo "Backup file: $BACKUP_FILE"
echo "Size: $BACKUP_SIZE"
echo ""

# Confirmation
echo -e "${RED}WARNING: This will overwrite the current database!${NC}"
read -p "Are you sure you want to restore? (type 'yes' to confirm): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Create pre-restore backup
echo -e "${YELLOW}Creating backup of current database before restore...${NC}"
PRE_RESTORE_BACKUP="$BACKUP_DIR/pre-restore-$(date +%Y%m%d_%H%M%S).sql.gz"

if docker-compose exec -T postgres pg_dump -U clinical_admin clinical_care_tools 2>/dev/null | gzip > "$PRE_RESTORE_BACKUP"; then
    echo -e "${GREEN}✓ Pre-restore backup created: $PRE_RESTORE_BACKUP${NC}"
else
    echo -e "${YELLOW}Warning: Could not create pre-restore backup${NC}"
fi

echo ""

# Drop and recreate database
echo -e "${YELLOW}Preparing database...${NC}"

docker-compose exec -T postgres psql -U clinical_admin -c "DROP DATABASE IF EXISTS clinical_care_tools;"
docker-compose exec -T postgres psql -U clinical_admin -c "CREATE DATABASE clinical_care_tools;"

echo -e "${GREEN}✓ Database prepared${NC}"
echo ""

# Restore from backup
echo -e "${YELLOW}Restoring from backup...${NC}"

if [ "${BACKUP_FILE##*.}" = "gz" ]; then
    gunzip -c "$BACKUP_FILE" | docker-compose exec -T postgres psql -U clinical_admin -d clinical_care_tools
else
    cat "$BACKUP_FILE" | docker-compose exec -T postgres psql -U clinical_admin -d clinical_care_tools
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Restore completed successfully${NC}"
else
    echo -e "${RED}✗ Restore failed${NC}"
    echo "Rolling back to pre-restore state..."
    gunzip -c "$PRE_RESTORE_BACKUP" | docker-compose exec -T postgres psql -U clinical_admin -d clinical_care_tools
    exit 1
fi

echo ""

# Verify restoration
echo -e "${YELLOW}Verifying restoration...${NC}"

TABLE_COUNT=$(docker-compose exec -T postgres psql -U clinical_admin -d clinical_care_tools -c "\dt" | wc -l)

if [ $TABLE_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ Database restored with tables: $((TABLE_COUNT - 3))${NC}"
else
    echo -e "${RED}✗ Database verification failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Restoration Successful!"
echo "==========================================${NC}"
echo ""
echo "Pre-restore backup saved at: $PRE_RESTORE_BACKUP"
echo ""
echo "Next steps:"
echo "1. Verify the database content is correct"
echo "2. Restart services if needed: docker-compose restart backend"
echo "3. Monitor logs: docker-compose logs -f backend"
echo ""
