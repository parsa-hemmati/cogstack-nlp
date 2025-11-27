#!/bin/bash

# Clinical Care Tools - Environment Verification Script
# Purpose: Verify all infrastructure components are healthy
# Usage: ./scripts/verify-environment.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

echo "=========================================="
echo "Clinical Care Tools - Environment Check"
echo "=========================================="
echo ""

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        FAILURES=$((FAILURES + 1))
    fi
}

# Check Docker installed
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_status 0 "Docker installed: $DOCKER_VERSION"
else
    print_status 1 "Docker not installed"
fi

# Check Docker Compose installed
echo "Checking Docker Compose installation..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    print_status 0 "Docker Compose installed: $COMPOSE_VERSION"
else
    print_status 1 "Docker Compose not installed"
fi

# Check Docker daemon running
echo "Checking Docker daemon..."
if docker info &> /dev/null; then
    print_status 0 "Docker daemon running"
else
    print_status 1 "Docker daemon not running"
    exit 1
fi

# Check if docker-compose.yml exists
echo "Checking configuration files..."
if [ -f "docker-compose.yml" ]; then
    print_status 0 "docker-compose.yml exists"
else
    print_status 1 "docker-compose.yml not found"
    exit 1
fi

# Validate docker-compose.yml
echo "Validating Docker Compose configuration..."
if docker-compose config &> /dev/null; then
    print_status 0 "Docker Compose configuration valid"
else
    print_status 1 "Docker Compose configuration invalid"
    exit 1
fi

# Check if .env exists
echo "Checking environment configuration..."
if [ -f ".env" ]; then
    print_status 0 ".env file exists"
else
    echo -e "${YELLOW}⚠️  .env file not found. Copy .env.template to .env and configure.${NC}"
fi

# Check if containers are running
echo ""
echo "Checking services..."

# PostgreSQL
if docker-compose ps postgres | grep -q "Up"; then
    print_status 0 "PostgreSQL container running"

    # Check PostgreSQL connection
    if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
        print_status 0 "PostgreSQL accepting connections"
    else
        print_status 1 "PostgreSQL not accepting connections"
    fi
else
    echo -e "${YELLOW}⚠️  PostgreSQL container not running${NC}"
fi

# Redis
if docker-compose ps redis | grep -q "Up"; then
    print_status 0 "Redis container running"

    # Check Redis connection
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        print_status 0 "Redis responding to PING"
    else
        print_status 1 "Redis not responding"
    fi
else
    echo -e "${YELLOW}⚠️  Redis container not running${NC}"
fi

# CogStack-ModelServe
if docker-compose ps cogstack-modelserve | grep -q "Up"; then
    print_status 0 "CogStack-ModelServe container running"

    # Check CogStack-ModelServe health
    if curl -f http://localhost:8001/api/health &> /dev/null; then
        print_status 0 "CogStack-ModelServe health check passing"
    else
        print_status 1 "CogStack-ModelServe health check failing"
    fi
else
    echo -e "${YELLOW}⚠️  CogStack-ModelServe container not running${NC}"
fi

# Backend
if docker-compose ps backend | grep -q "Up"; then
    print_status 0 "Backend container running"

    # Check Backend health
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_status 0 "Backend health check passing"
    else
        echo -e "${YELLOW}⚠️  Backend health check failing (may not be implemented yet)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Backend container not running${NC}"
fi

# Frontend
if docker-compose ps frontend | grep -q "Up"; then
    print_status 0 "Frontend container running"

    # Check Frontend
    if curl -f http://localhost:8080 &> /dev/null; then
        print_status 0 "Frontend responding"
    else
        echo -e "${YELLOW}⚠️  Frontend not responding${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Frontend container not running${NC}"
fi

# Check volumes
echo ""
echo "Checking Docker volumes..."
if docker volume ls | grep -q "clinical-care-tools_postgres_data"; then
    print_status 0 "PostgreSQL data volume exists"
else
    echo -e "${YELLOW}⚠️  PostgreSQL data volume not found${NC}"
fi

if docker volume ls | grep -q "clinical-care-tools_redis_data"; then
    print_status 0 "Redis data volume exists"
else
    echo -e "${YELLOW}⚠️  Redis data volume not found${NC}"
fi

# Check models directory
echo ""
echo "Checking MedCAT models..."
if [ -d "models" ]; then
    print_status 0 "Models directory exists"

    # Check if models exist
    MODEL_COUNT=$(find models -type f -name "*.zip" 2>/dev/null | wc -l)
    if [ $MODEL_COUNT -gt 0 ]; then
        print_status 0 "Found $MODEL_COUNT model file(s)"
    else
        echo -e "${YELLOW}⚠️  No model files found in models/ directory${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Models directory not found. Create models/ and download MedCAT models.${NC}"
fi

# Summary
echo ""
echo "=========================================="
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo "=========================================="
    exit 0
else
    echo -e "${RED}❌ $FAILURES check(s) failed${NC}"
    echo "=========================================="
    exit 1
fi
