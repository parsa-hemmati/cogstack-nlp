#!/bin/bash

# Clinical Care Tools - Health Check Script
# Version: 1.0.0
# Purpose: Verify all services are running and healthy

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "Clinical Care Tools - Health Check"
echo "==========================================${NC}"
echo ""

FAILED=0

# Function to check service health
check_service() {
    local service=$1
    local endpoint=$2
    local timeout=${3:-5}

    echo -ne "Checking $service... "

    if curl -s --connect-timeout $timeout "$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Function to check container status
check_container() {
    local container=$1
    echo -ne "Checking container $container... "

    if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Check Docker
echo -e "${YELLOW}=== Docker Status ===${NC}"
if ! docker --version > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✓ Docker is running${NC}"
fi
echo ""

# Check containers
echo -e "${YELLOW}=== Container Status ===${NC}"
check_container "clinical-care-db"
check_container "clinical-care-cache"
check_container "clinical-care-nlp"
check_container "clinical-care-backend"
check_container "clinical-care-frontend"
echo ""

# Check services
echo -e "${YELLOW}=== Service Health ===${NC}"
check_service "PostgreSQL" "http://localhost:5432" 2
check_service "Redis" "http://localhost:6379" 2
check_service "Backend API" "http://localhost:8000/api/health"
check_service "NLP Service" "http://localhost:8001/api/health"
check_service "Frontend" "http://localhost:8080" 10
echo ""

# Check database connection
echo -e "${YELLOW}=== Database Health ===${NC}"
echo -ne "Checking database connectivity... "

if docker-compose exec -T postgres psql -U clinical_admin -d clinical_care_tools -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected${NC}"
else
    echo -e "${RED}✗ Failed to connect${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Check disk space
echo -e "${YELLOW}=== Disk Usage ===${NC}"
DISK_USAGE=$(df / | awk 'NR==2 {print int($5)}')
echo "Disk usage: ${DISK_USAGE}%"

if [ $DISK_USAGE -gt 90 ]; then
    echo -e "${RED}Warning: Disk usage is critically high${NC}"
    FAILED=$((FAILED + 1))
elif [ $DISK_USAGE -gt 80 ]; then
    echo -e "${YELLOW}Warning: Disk usage is high${NC}"
else
    echo -e "${GREEN}✓ Disk usage is healthy${NC}"
fi
echo ""

# Check memory usage
echo -e "${YELLOW}=== Memory Usage ===${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo ""

# Check recent errors in logs
echo -e "${YELLOW}=== Recent Errors ===${NC}"
ERROR_COUNT=$(docker-compose logs --tail=100 2>/dev/null | grep -i "error\|exception\|fatal" | wc -l)

if [ $ERROR_COUNT -gt 0 ]; then
    echo -e "${YELLOW}Found $ERROR_COUNT recent errors:${NC}"
    docker-compose logs --tail=100 2>/dev/null | grep -i "error\|exception\|fatal" | head -10
else
    echo -e "${GREEN}✓ No recent errors${NC}"
fi
echo ""

# API endpoint checks
echo -e "${YELLOW}=== API Endpoint Status ===${NC}"

echo "GET /api/health"
curl -s http://localhost:8000/api/health | jq '.' 2>/dev/null || echo "Failed to connect"
echo ""

# Summary
echo -e "${BLUE}=========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
else
    echo -e "${RED}✗ $FAILED checks failed${NC}"
fi
echo "==========================================${NC}"
echo ""

exit $FAILED
