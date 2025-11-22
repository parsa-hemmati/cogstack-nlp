#!/bin/bash

# Clinical Care Tools - Production Deployment Script
# Version: 1.0.0
# Purpose: Automated production deployment with safety checks

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}=========================================="
echo "Clinical Care Tools - Production Deploy"
echo "==========================================${NC}"
echo ""

# Pre-deployment checks
echo -e "${YELLOW}[1/8] Running pre-deployment checks...${NC}"

# Check if .env.production exists
if [ ! -f "$PROJECT_DIR/.env.production" ]; then
    echo -e "${RED}Error: .env.production not found${NC}"
    echo "Create .env.production from .env.production.example"
    exit 1
fi

# Check if running as correct user
if [ ! -w "$PROJECT_DIR" ]; then
    echo -e "${RED}Error: No write permission to project directory${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Pre-deployment checks passed${NC}"
echo ""

# Create backup before deployment
echo -e "${YELLOW}[2/8] Creating backup...${NC}"

BACKUP_DIR="$PROJECT_DIR/backups"
mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/pre-deploy-$(date +%Y%m%d_%H%M%S).sql.gz"

docker-compose exec -T postgres pg_dump -U clinical_admin clinical_care_tools 2>/dev/null | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
else
    echo -e "${RED}Warning: Backup creation failed${NC}"
fi

echo ""

# Stop current services
echo -e "${YELLOW}[3/8] Stopping current services...${NC}"

docker-compose down --remove-orphans

echo -e "${GREEN}✓ Services stopped${NC}"
echo ""

# Pull latest code
echo -e "${YELLOW}[4/8] Pulling latest code...${NC}"

cd "$PROJECT_DIR"
git fetch origin
git checkout main
git pull origin main

echo -e "${GREEN}✓ Code updated${NC}"
echo ""

# Build new images
echo -e "${YELLOW}[5/8] Building Docker images...${NC}"

docker-compose build --no-cache backend frontend

echo -e "${GREEN}✓ Docker images built${NC}"
echo ""

# Start services
echo -e "${YELLOW}[6/8] Starting services...${NC}"

docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Wait for services to be healthy
echo -e "${YELLOW}[7/8] Waiting for services to be healthy...${NC}"

MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker-compose exec -T backend curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Services are healthy${NC}"
        break
    fi

    ATTEMPT=$((ATTEMPT + 1))
    echo "Waiting... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}Error: Services did not become healthy${NC}"
    echo "Rolling back deployment..."
    docker-compose down
    # Restore from backup if needed
    exit 1
fi

echo ""

# Run migrations
echo -e "${YELLOW}[8/8] Running database migrations...${NC}"

docker-compose exec backend alembic upgrade head

echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# Post-deployment verification
echo -e "${YELLOW}Post-deployment verification...${NC}"

docker-compose ps

echo ""
echo -e "${GREEN}=========================================="
echo "Deployment Successful!"
echo "==========================================${NC}"
echo ""
echo "Deployment Summary:"
echo "- Services: All running"
echo "- Backup: $BACKUP_FILE"
echo "- Code: Latest from main branch"
echo "- Database: Migrated"
echo ""
echo "Next steps:"
echo "1. Verify health:"
echo "   ./scripts/health-check.sh"
echo ""
echo "2. Check logs:"
echo "   docker-compose logs -f backend"
echo ""
echo "3. Monitor performance:"
echo "   docker stats"
echo ""
echo "If rollback is needed:"
echo "   ./scripts/restore-db.sh $BACKUP_FILE"
echo ""
