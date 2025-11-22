# Development Setup Guide

Complete guide for setting up the Clinical Care Tools development environment locally.

## Prerequisites

Before starting, ensure you have:

- **Docker & Docker Compose** (v20.10+)
  - [Install Docker](https://docs.docker.com/get-docker/)
  - Verify: `docker --version && docker-compose --version`

- **Git** (v2.30+)
  - [Install Git](https://git-scm.com/downloads)
  - Verify: `git --version`

- **Python 3.9+** (for local development without Docker)
  - [Install Python](https://www.python.org/downloads/)
  - Verify: `python3 --version`

- **Node.js 16+** (for frontend development)
  - [Install Node.js](https://nodejs.org/)
  - Verify: `node --version && npm --version`

- **System Resources**
  - RAM: 8GB minimum (16GB recommended for NLP service)
  - Disk: 50GB available (for models and data)
  - CPU: 4 cores minimum (8 cores recommended)

## Quick Start (5 minutes)

### 1. Clone Repository

```bash
git clone https://github.com/CogStack/clinical-care-tools.git
cd clinical-care-tools
```

### 2. Copy Environment Variables

```bash
cp .env.example .env.development
```

Edit `.env.development` if needed (defaults work for development):

```bash
# Optional: Change database password
POSTGRES_PASSWORD=your-secure-password
SECRET_KEY=your-development-secret
```

### 3. Download Models (First Time Only)

The MedCAT models are large (~2GB). Download them to the `models/` directory:

```bash
# Create models directory
mkdir -p models

# Download models (this takes time - ~30 minutes)
# Option 1: Using provided script
./scripts/download-models.sh

# Option 2: Manual download from MedCAT releases
# https://github.com/CogStack/MedCAT/releases
# Extract to ./models/
```

### 4. Start All Services

```bash
# Start containers in detached mode
docker-compose up -d

# Or watch logs while starting
docker-compose up

# In another terminal, wait for services to be healthy
docker-compose ps
```

### 5. Access Application

Once services are healthy:

- **Frontend**: http://localhost:8080
- **Backend API Docs**: http://localhost:8000/api/docs
- **MedCAT Health**: http://localhost:8001/api/health

### 6. Login

Default credentials (change these!):
- **Username**: admin
- **Password**: admin123

## Detailed Setup by Component

### Backend Setup

For backend-only development:

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development tools

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Backend Services Needed**:
- PostgreSQL (can run in Docker)
- Redis (can run in Docker)
- MedCAT Service (can run in Docker)

```bash
# Start only backend dependencies
docker-compose up -d postgres redis cogstack-modelserve

# Then start FastAPI locally
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --reload
```

### Frontend Setup

For frontend-only development:

```bash
cd frontend

# Install dependencies
npm install

# Start development server with hot reload
npm run dev

# Or build for production
npm run build

# Run tests
npm run test
```

**Frontend Services Needed**:
- Backend API running on http://localhost:8000

Update frontend `.env.local` if API is elsewhere:

```bash
# frontend/.env.local
VITE_API_BASE_URL=http://localhost:8000
```

### Database Setup

Connect to PostgreSQL:

```bash
# Using Docker
docker-compose exec postgres psql -U clinical_admin -d clinical_care_tools

# Or locally installed PostgreSQL
psql -h localhost -U clinical_admin -d clinical_care_tools

# Initial password: changeme (default in .env.example)
```

Run migrations:

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Alembic
pip install alembic sqlalchemy

# Run migrations
alembic upgrade head

# Create tables
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### Redis Setup

Redis is used for:
- Session storage
- Cache layer
- Job queues
- Rate limiting

Check Redis is running:

```bash
docker-compose exec redis redis-cli ping
# Response: PONG

# View cache contents
docker-compose exec redis redis-cli
> KEYS *
> GET {key-name}
> FLUSHDB  # Clear all cache (development only!)
```

### MedCAT Service Setup

The NLP service requires downloaded models:

```bash
# Check service is running
curl http://localhost:8001/api/health

# Test extraction
curl -X POST http://localhost:8001/api/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient has type 2 diabetes and hypertension",
    "model_name": "medcat-model"
  }'
```

## Environment Configuration

### .env Files

The project uses environment-specific `.env` files:

```
.env.example          # Template (git-tracked)
.env.development      # Development local overrides (git-ignored)
.env.production       # Production template (git-tracked)
.env.staging          # Staging template (git-tracked)
```

### Key Environment Variables

#### Database
```bash
DATABASE_URL=postgresql://clinical_admin:changeme@localhost:5432/clinical_care_tools
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

#### Redis
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600  # 1 hour
```

#### NLP Service
```bash
COGSTACK_MODELSERVE_URL=http://localhost:8001
COGSTACK_TIMEOUT=30  # seconds
```

#### Security
```bash
SECRET_KEY=development-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8
JWT_REFRESH_DAYS=7
```

#### Application
```bash
ENVIRONMENT=development
LOG_LEVEL=info
WORKERS=4
CORS_ORIGINS=http://localhost:8080,http://localhost:3000
```

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_users.py -v

# Run specific test
pytest tests/unit/test_users.py::test_create_user -v
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm run test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run tests in watch mode
npm run test:watch
```

## Troubleshooting Development Setup

### Docker Issues

**Problem**: "Cannot connect to Docker daemon"
```bash
# Solution: Ensure Docker is running
sudo systemctl start docker  # Linux
open -a Docker  # macOS
# Or start Docker Desktop application
```

**Problem**: "Permission denied while trying to connect to Docker"
```bash
# Solution: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**Problem**: "Insufficient disk space"
```bash
# Solution: Clean up Docker
docker system prune -a --volumes
# Free up at least 50GB
```

### Database Issues

**Problem**: "connection refused" on port 5432
```bash
# Solution: Check PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

**Problem**: "FATAL: password authentication failed"
```bash
# Solution: Check credentials in .env.development
# Default is: POSTGRES_PASSWORD=changeme

# Reset password
docker-compose restart postgres
```

### Frontend Issues

**Problem**: "CORS error" when calling API
```bash
# Solution: Update CORS_ORIGINS in .env
CORS_ORIGINS=http://localhost:8080,http://localhost:3000

# Restart backend
docker-compose restart backend
```

**Problem**: "Cannot find module" in frontend
```bash
# Solution: Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### NLP Service Issues

**Problem**: "MedCAT service not responding"
```bash
# Solution: Check service is healthy
docker-compose ps cogstack-modelserve

# View logs
docker-compose logs cogstack-modelserve

# Restart service
docker-compose restart cogstack-modelserve

# Verify models exist
docker-compose exec cogstack-modelserve ls -la /models
```

**Problem**: "Models not found"
```bash
# Solution: Download models
mkdir -p models
./scripts/download-models.sh

# Or manually download from:
# https://github.com/CogStack/MedCAT/releases
```

## Development Workflow

### Typical Development Session

```bash
# 1. Start all services
docker-compose up -d

# 2. Check services are healthy
docker-compose ps

# 3. For backend development
cd backend
source venv/bin/activate
# Edit code...
# Tests run on file save with --reload

# 4. For frontend development
cd frontend
# Edit code...
npm run dev
# Changes reload automatically

# 5. After changes, run full test suite
pytest tests/  # Backend
npm test      # Frontend

# 6. Check code quality
flake8 .
black .
eslint .

# 7. Commit changes
git add .
git commit -m "feat: description"
git push
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feat/my-feature

# Make changes and commit regularly
git add .
git commit -m "feat: describe change"

# Push to remote
git push -u origin feat/my-feature

# Create pull request on GitHub
```

## VS Code Setup

### Extensions (Recommended)

1. **Python**
   - Extension: ms-python.python
   - Provides debugging, linting, formatting

2. **Pylance**
   - Extension: ms-python.vscode-pylance
   - Python language server

3. **Prettier**
   - Extension: esbenp.prettier-vscode
   - Code formatting for JavaScript/TypeScript

4. **ESLint**
   - Extension: dbaeumer.vscode-eslint
   - JavaScript/TypeScript linting

5. **Thunder Client** or **REST Client**
   - For testing API endpoints

### Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend",
        "DATABASE_URL": "postgresql://clinical_admin:changeme@localhost:5432/clinical_care_tools",
        "COGSTACK_MODELSERVE_URL": "http://localhost:8001"
      }
    }
  ]
}
```

## Performance Tips

### For Faster Development

1. **Use Docker volume mounts** for code (automatic reload)
   - Already configured in docker-compose.yml

2. **Use hot reload** in development
   - Backend: `--reload` flag with Uvicorn
   - Frontend: `npm run dev` with Vite

3. **Cache dependencies**
   - Frontend: Docker layer caching
   - Backend: Python wheels caching

4. **Increase resources** if slow
   - Edit docker-compose.yml limits
   - Allocate more RAM to Docker Desktop

### Reducing Model Load Time

```bash
# Models are loaded on first request (~2 minutes)
# Subsequent requests are cached

# Pre-load models on startup
# Check cogstack-modelserve logs for "Model loaded"
docker-compose logs cogstack-modelserve | grep "Model loaded"
```

## Next Steps

After setup:

1. **Review Documentation**
   - Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
   - Read [API.md](API.md) for API reference

2. **Explore Code**
   - Backend: `backend/app/` main application code
   - Frontend: `frontend/src/` Vue components

3. **Run Examples**
   - Create a test patient in database
   - Upload a sample document
   - Test patient search

4. **Write Tests**
   - Add tests for new features
   - Aim for 80%+ coverage

5. **Join Development**
   - Pick an issue from GitHub Issues
   - Create a feature branch
   - Submit a pull request

## Getting Help

1. **Check logs**
   ```bash
   docker-compose logs -f <service-name>
   ```

2. **Health check**
   ```bash
   ./scripts/health-check.sh
   ```

3. **Review documentation**
   - [README.md](../README.md) - Overview
   - [ARCHITECTURE.md](ARCHITECTURE.md) - Design
   - [API.md](API.md) - Endpoints

4. **Open an issue**
   - Include error messages
   - Include environment details
   - Include steps to reproduce

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vue 3 Guide](https://vuejs.org/guide/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [MedCAT GitHub](https://github.com/CogStack/MedCAT)

---

**Last Updated**: 2025-01-08
**Version**: 1.0.0
