#!/bin/bash

# Clinical Care Tools - Development Environment Setup Script
# Version: 1.0.0
# Purpose: Automated setup for development environment

set -e  # Exit on error

echo "=========================================="
echo "Clinical Care Tools - Development Setup"
echo "=========================================="
echo ""

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}[1/5] Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Create environment file
echo -e "${YELLOW}[2/5] Setting up environment variables...${NC}"

if [ ! -f ".env.development" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env.development
        echo -e "${GREEN}✓ Created .env.development from .env.example${NC}"
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env.development already exists${NC}"
fi

echo ""

# Create necessary directories
echo -e "${YELLOW}[3/5] Creating directories...${NC}"

mkdir -p models
mkdir -p backups
mkdir -p logs

echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Pull/build Docker images
echo -e "${YELLOW}[4/5] Building Docker images...${NC}"

docker-compose build --no-cache backend frontend

echo -e "${GREEN}✓ Docker images built${NC}"
echo ""

# Start services
echo -e "${YELLOW}[5/5] Starting services...${NC}"

docker-compose up -d

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Wait for services to be healthy:"
echo "   docker-compose ps"
echo ""
echo "2. Run migrations:"
echo "   docker-compose exec backend alembic upgrade head"
echo ""
echo "3. Access the application:"
echo "   Frontend:  http://localhost:8080"
echo "   Backend:   http://localhost:8000/api/docs"
echo "   Database:  localhost:5432 (user: clinical_admin)"
echo ""
echo "4. Default credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   (Change these immediately!)"
echo ""
echo "For more information, see:"
echo "- Setup Guide: docs/SETUP.md"
echo "- Architecture: docs/ARCHITECTURE.md"
echo ""
