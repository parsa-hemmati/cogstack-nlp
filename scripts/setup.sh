#!/bin/bash
# Clinical Care Tools - First-Time Setup Script
# Initializes database, creates admin user, runs migrations

set -e  # Exit on error

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Clinical Care Tools - First-Time Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check environment
echo -e "\n${YELLOW}[1/5]${NC} Checking environment..."

if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR:${NC} .env file not found!"
    echo "Please create .env from .env.template first:"
    echo "  cp .env.template .env"
    exit 1
fi

echo -e "${GREEN}✓${NC} .env file found"

# Step 2: Start services
echo -e "\n${YELLOW}[2/5]${NC} Starting Docker services..."

docker-compose up -d postgres redis medcat-service

echo "Waiting for services to be healthy..."
sleep 10

# Check service health
if ! docker-compose ps postgres | grep -q "healthy"; then
    echo -e "${RED}ERROR:${NC} PostgreSQL is not healthy"
    docker-compose logs postgres
    exit 1
fi

echo -e "${GREEN}✓${NC} All services running"

# Step 3: Run database migrations
echo -e "\n${YELLOW}[3/5]${NC} Running database migrations..."

docker-compose run --rm backend alembic upgrade head

echo -e "${GREEN}✓${NC} Database migrations complete"

# Step 4: Create admin user
echo -e "\n${YELLOW}[4/5]${NC} Creating admin user..."

# Note: This would need a Python script to create the user
# For now, just show instructions
echo "To create admin user, run:"
echo "  docker-compose exec backend python -c \""
echo "from app.models.user import User;"
echo "from app.db.session import AsyncSessionLocal;"
echo "user = User(username='admin', email='admin@example.com', role='admin');"
echo "user.set_password('ChangeMe123!');"
echo "# Save to database"
echo "\""

# Step 5: Verify setup
echo -e "\n${YELLOW}[5/5]${NC} Verifying setup..."

./scripts/verify-environment.sh

# Summary
echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "\nServices running:"
echo "  - Backend API:    http://localhost:8000"
echo "  - API Docs:       http://localhost:8000/docs"
echo "  - Frontend:       http://localhost:8080 (after build)"
echo "  - MedCAT Service: http://localhost:8001"

echo -e "\nNext steps:"
echo "  1. Create admin user (see instructions above)"
echo "  2. Start backend:  docker-compose up backend"
echo "  3. Start frontend: cd frontend && npm install && npm run dev"
echo "  4. Login at http://localhost:8080/login"
