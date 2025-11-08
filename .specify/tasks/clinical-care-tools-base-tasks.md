# Tasks: Clinical Care Tools Base Application

**Plan Reference**: `.specify/plans/clinical-care-tools-base-plan.md` (v1.1.0)
**Specification Reference**: `.specify/specifications/clinical-care-tools-base-app.md` (v1.1.0)
**Estimated Total Time**: ~310 hours (11 weeks, 2 developers)
**Dependencies**:
- Docker 24.0+
- Docker Compose 2.20+
- MedCAT models (SNOMED-CT, 2-5 GB)
- Python 3.10+, Node 18+

---

## Phase 0: Environment Setup & MedCAT Model Preparation (~20 hours)

### Task 0.1: Install Docker and Docker Compose

**Goal**: Install and configure Docker Desktop with appropriate resource limits for development

**Prerequisites**:
- Workstation with 8+ GB RAM, 4+ CPU cores
- Windows/Linux OS

**Steps**:
1. **Download and Install**
   - Download Docker Desktop 24.0+ from docker.com
   - Install with default settings
   - Restart machine if required
2. **Configure Resources**
   - Open Docker Desktop settings
   - Set RAM: 8 GB minimum
   - Set CPUs: 4 cores minimum
   - Set disk space: 50 GB
3. **Verify Installation**
   - Run `docker --version`
   - Run `docker-compose --version`
   - Run `docker run hello-world`

**Acceptance Criteria**:
- [ ] Docker version ≥24.0
- [ ] Docker Compose version ≥2.20
- [ ] Docker Desktop shows 8GB RAM, 4 CPU cores allocated
- [ ] `docker run hello-world` executes successfully

**Files Created/Modified**:
- None (system-level installation)

**Estimated Time**: 1 hour

**Testing**:
- Manual: `docker --version` shows correct version
- Manual: `docker-compose --version` shows correct version
- Manual: `docker run hello-world` outputs success message

---

### Task 0.2: Download MedCAT Models

**Goal**: Download and verify SNOMED-CT MedCAT models from Model Zoo

**Prerequisites**:
- Task 0.1 completed
- Network access to MedCAT Model Zoo or model provider

**Steps**:
1. **Create Models Directory**
   - Create `medcat_models/` in project root
   - Create subdirectories: `snomed/`, `umls/` (if needed)
2. **Download Models**
   - Download SNOMED-CT model (2-5 GB, may take 1-4 hours)
   - Use wget/curl with resume support: `wget -c <model-url>`
   - Store in `medcat_models/snomed/`
3. **Verify Model Integrity**
   - Check file size matches expected
   - Verify checksum if provided: `sha256sum model.zip`
   - Extract model: `unzip model.zip`

**Acceptance Criteria**:
- [ ] `medcat_models/snomed/` directory exists
- [ ] Model files extracted successfully
- [ ] Checksum verification passed (if applicable)
- [ ] Model size ≥1 GB (typical SNOMED model)

**Files Created/Modified**:
- `medcat_models/snomed/model.dat` (or similar)
- `medcat_models/snomed/config.json`

**Estimated Time**: 8 hours (mostly waiting for download)

**Testing**:
- Manual: `ls -lh medcat_models/snomed/` shows model files
- Manual: File sizes match expected values

---

### Task 0.3: Create Initial Docker Compose Configuration

**Goal**: Create docker-compose.yml with all 5 services (frontend, backend, postgres, redis, medcat)

**Prerequisites**:
- Task 0.1 completed
- Task 0.2 completed

**Steps**:
1. **Create docker-compose.yml**
   - Define 5 services: frontend, backend, postgres, redis, medcat-service
   - Configure networks (single bridge network)
   - Configure volumes: postgres_data, redis_data, medcat_models, backend_logs
2. **Create .env Template**
   - Database credentials
   - Redis configuration
   - JWT secret key (placeholder)
   - MedCAT model paths
3. **Configure Health Checks**
   - PostgreSQL: `pg_isready`
   - Redis: `redis-cli ping`
   - Backend: `/health` endpoint (to be implemented)
   - Frontend: HTTP 200 on :8080
   - MedCAT: `/api/info` endpoint

**Acceptance Criteria**:
- [ ] `docker-compose.yml` exists with all 5 services defined
- [ ] `.env.template` exists with all required variables
- [ ] All volumes defined in docker-compose.yml
- [ ] Health checks configured for all services
- [ ] `docker-compose config` validates successfully

**Files Created/Modified**:
- `docker-compose.yml` - Main orchestration file
- `.env.template` - Environment variables template
- `.gitignore` - Add `.env` to prevent secret commits

**Estimated Time**: 3 hours

**Testing**:
- Manual: `docker-compose config` validates YAML syntax
- Manual: Check all 5 services defined
- Manual: Check all volumes defined

---

### Task 0.4: Setup PostgreSQL Database

**Goal**: Start PostgreSQL container, create database, and verify connectivity

**Prerequisites**:
- Task 0.3 completed

**Steps**:
1. **Copy Environment Template**
   - `cp .env.template .env`
   - Generate secure database password
   - Set `POSTGRES_PASSWORD`, `POSTGRES_USER`, `POSTGRES_DB`
2. **Start PostgreSQL**
   - `docker-compose up -d postgres`
   - Wait for health check to pass
3. **Verify Connection**
   - Connect from host: `psql -h localhost -U postgres -d clinical_care_tools`
   - Test query: `SELECT version();`
4. **Install Client Tools** (if needed)
   - Install `psql` on host machine
   - Install `pg_dump` for backups

**Acceptance Criteria**:
- [ ] PostgreSQL container running
- [ ] Database `clinical_care_tools` created
- [ ] Can connect from host machine
- [ ] Health check passing
- [ ] `SELECT version();` returns PostgreSQL 15+

**Files Created/Modified**:
- `.env` - Production environment variables (gitignored)

**Estimated Time**: 2 hours

**Testing**:
- Manual: `docker-compose ps` shows postgres as healthy
- Manual: `psql` connection successful
- Manual: Query executes successfully

---

### Task 0.5: Setup Redis Cache

**Goal**: Start Redis container with persistence configured

**Prerequisites**:
- Task 0.3 completed

**Steps**:
1. **Configure Redis in docker-compose.yml**
   - Add Redis command args: `--save 60 1000 --appendonly yes`
   - Set maxmemory: 512mb
   - Set eviction policy: allkeys-lru
2. **Start Redis**
   - `docker-compose up -d redis`
   - Wait for health check
3. **Verify Redis**
   - Connect: `redis-cli -h localhost -p 6379`
   - Test: `PING` → `PONG`
   - Test TTL: `SETEX test 10 "value"` then `GET test` then wait 10s then `GET test`

**Acceptance Criteria**:
- [ ] Redis container running
- [ ] `PING` returns `PONG`
- [ ] TTL expiration works correctly
- [ ] Health check passing
- [ ] Persistence configured (RDB + AOF)

**Files Created/Modified**:
- `docker-compose.yml` - Updated with Redis configuration

**Estimated Time**: 1 hour

**Testing**:
- Manual: `docker-compose ps` shows redis as healthy
- Manual: `redis-cli PING` returns `PONG`
- Manual: TTL test passes

---

### Task 0.6: Setup MedCAT Service

**Goal**: Start MedCAT Service container and verify model loading

**Prerequisites**:
- Task 0.2 completed (models downloaded)
- Task 0.3 completed

**Steps**:
1. **Configure MedCAT Service**
   - Map model volume: `medcat_models:/cat/models:ro`
   - Set environment: `MODEL_PATH=/cat/models/snomed/model.dat`
   - Configure port: 5000
2. **Start MedCAT Service**
   - `docker-compose up -d medcat-service`
   - Monitor logs: `docker-compose logs -f medcat-service`
   - Wait for "Model loaded successfully" message (may take 30-60 seconds)
3. **Verify MedCAT**
   - Test `/api/info` endpoint: `curl http://localhost:5000/api/info`
   - Test text processing: `curl -X POST http://localhost:5000/api/process -H "Content-Type: application/json" -d '{"text": "Patient has diabetes"}'`

**Acceptance Criteria**:
- [ ] MedCAT Service container running
- [ ] Model loads in <60 seconds
- [ ] `/api/info` returns 200 with model info
- [ ] `/api/process` extracts "diabetes" entity
- [ ] Health check passing

**Files Created/Modified**:
- `docker-compose.yml` - Updated with MedCAT Service configuration

**Estimated Time**: 2 hours

**Testing**:
- Manual: `curl http://localhost:5000/api/info` returns 200
- Manual: Sample text processing extracts medical entities
- Manual: Logs show "Model loaded successfully"

---

### Task 0.7: Create Environment Verification Script

**Goal**: Automated script to verify all components are healthy

**Prerequisites**:
- Tasks 0.1-0.6 completed

**Steps**:
1. **Create Verification Script**
   - Create `scripts/verify-environment.sh`
   - Check Docker installed
   - Check Docker Compose installed
   - Check all volumes exist
   - Check PostgreSQL connection
   - Check Redis PING
   - Check MedCAT Service health
2. **Test Script**
   - Run `chmod +x scripts/verify-environment.sh`
   - Run `./scripts/verify-environment.sh`
   - Should output ✅ for all checks

**Acceptance Criteria**:
- [ ] Script exists and is executable
- [ ] All checks pass (Docker, Compose, volumes, services)
- [ ] Script exits with code 0 on success
- [ ] Script exits with code 1 on any failure
- [ ] Clear error messages for each failure

**Files Created/Modified**:
- `scripts/verify-environment.sh` - Environment verification script
- `README.md` - Add "Environment Setup" section with script usage

**Estimated Time**: 1 hour

**Testing**:
- Manual: Run script with all services up → exit code 0
- Manual: Stop postgres → run script → exit code 1 with clear error
- Manual: Restart postgres → run script → exit code 0

---

## Phase 1: Core Infrastructure (~60 hours)

### Task 1.1: Create Backend Project Structure

**Goal**: Initialize FastAPI project with proper directory structure

**Prerequisites**:
- Phase 0 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/test_project_structure.py`
   - Test: All required directories exist
   - Test: `__init__.py` in all packages
2. **Implement**
   - Create `backend/` directory
   - Create subdirectories: `app/`, `tests/`, `alembic/`
   - Create `app/` subdirectories: `api/`, `core/`, `models/`, `schemas/`, `services/`, `db/`
   - Create `__init__.py` in all packages
   - Create `requirements.txt` with FastAPI, SQLAlchemy, etc.
3. **Verify**
   - Run: `pytest tests/test_project_structure.py`
   - All directories should exist

**Acceptance Criteria**:
- [ ] All directories created
- [ ] All `__init__.py` files present
- [ ] `requirements.txt` complete
- [ ] Tests passing
- [ ] Python imports work: `from app.core import config`

**Files Created/Modified**:
- `backend/app/__init__.py`
- `backend/app/api/__init__.py`
- `backend/app/core/__init__.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/__init__.py`
- `backend/app/services/__init__.py`
- `backend/app/db/__init__.py`
- `backend/requirements.txt`
- `tests/test_project_structure.py`

**Estimated Time**: 1 hour

**Testing**:
- Unit tests: 5 tests (directory existence)
- Manual: `python -c "from app.core import config"` works

---

### Task 1.2: Create Database Configuration Module

**Goal**: Database connection management with async SQLAlchemy

**Prerequisites**:
- Task 1.1 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/test_database.py`
   - Test: Database URL format
   - Test: Connection pool settings
   - Test: Session creation
2. **Implement**
   - Create `app/db/base.py` with SQLAlchemy setup
   - Create `app/db/session.py` with async session factory
   - Create `app/core/config.py` with database URL from environment
   - Configure connection pool (min=5, max=20)
3. **Verify**
   - Run: `pytest tests/unit/test_database.py`

**Acceptance Criteria**:
- [ ] Database URL reads from environment
- [ ] Connection pool configured correctly
- [ ] Async session factory works
- [ ] Tests passing
- [ ] Code coverage ≥80%

**Files Created/Modified**:
- `backend/app/db/base.py` - SQLAlchemy base setup
- `backend/app/db/session.py` - Async session factory
- `backend/app/core/config.py` - Configuration management
- `tests/unit/test_database.py` - Database tests

**Estimated Time**: 2 hours

**Testing**:
- Unit tests: 8 tests (config, pool, session)

---

### Task 1.3: Create Users Database Model

**Goal**: SQLAlchemy model for users table with password hashing

**Prerequisites**:
- Task 1.2 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/models/test_user.py`
   - Test: User creation
   - Test: Password hashing (bcrypt)
   - Test: Password verification
   - Test: UUID primary key generation
2. **Implement**
   - Create `app/models/user.py` with User model
   - Fields: id (UUID), username, email, password_hash, role, is_active, can_break_glass, created_at, updated_at
   - Add password hashing methods
   - Add __repr__ for debugging
3. **Verify**
   - Run: `pytest tests/unit/models/test_user.py`

**Acceptance Criteria**:
- [ ] User model defined with all fields
- [ ] Password hash != plaintext password
- [ ] Password verification works
- [ ] UUID auto-generated on creation
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/models/user.py` - User model
- `tests/unit/models/test_user.py` - User model tests

**Estimated Time**: 2 hours

**Testing**:
- Unit tests: 10 tests (creation, hashing, verification, constraints)

---

### Task 1.4: Create Alembic Migration for Users Table

**Goal**: Database migration to create users table

**Prerequisites**:
- Task 1.3 completed

**Steps**:
1. **Setup Alembic**
   - Run: `alembic init alembic`
   - Configure `alembic.ini` with database URL
   - Update `alembic/env.py` to import models
2. **Create Migration**
   - Run: `alembic revision --autogenerate -m "create users table"`
   - Review generated migration
   - Test forward migration: `alembic upgrade head`
   - Test rollback: `alembic downgrade -1`
3. **Verify**
   - Connect to database
   - Check table exists: `\dt users`
   - Check columns: `\d users`

**Acceptance Criteria**:
- [ ] Alembic configured
- [ ] Migration file created
- [ ] `alembic upgrade head` succeeds
- [ ] Users table exists in database
- [ ] All columns present with correct types
- [ ] Constraints (UNIQUE, CHECK) applied

**Files Created/Modified**:
- `backend/alembic.ini` - Alembic configuration
- `backend/alembic/env.py` - Migration environment
- `backend/alembic/versions/001_create_users_table.py` - Migration

**Estimated Time**: 1.5 hours

**Testing**:
- Manual: `alembic upgrade head` succeeds
- Manual: Table exists in database
- Manual: `alembic downgrade -1` removes table

---

### Task 1.5: Create JWT Token Generation Service

**Goal**: Service to create and verify JWT tokens

**Prerequisites**:
- Task 1.3 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_auth_service.py`
   - Test: Token creation includes sub, role, exp, iat, jti
   - Test: Token verification returns payload
   - Test: Expired token raises exception
   - Test: Invalid signature raises exception
2. **Implement**
   - Create `app/services/auth_service.py`
   - Function: `create_access_token(user_id, role)` → dict
   - Function: `verify_token(token)` → payload
   - Use python-jose for JWT
   - 8-hour expiry
3. **Verify**
   - Run: `pytest tests/unit/services/test_auth_service.py`

**Acceptance Criteria**:
- [ ] Token contains sub, role, exp, iat, jti
- [ ] Token expires after 8 hours
- [ ] Verify returns correct payload
- [ ] Invalid tokens raise HTTPException(401)
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/services/auth_service.py` - JWT service
- `tests/unit/services/test_auth_service.py` - Auth service tests

**Estimated Time**: 2 hours

**Testing**:
- Unit tests: 12 tests (creation, verification, expiry, invalid)

---

### Task 1.6: Create Login API Endpoint

**Goal**: POST /api/v1/auth/login endpoint with username/password authentication

**Prerequisites**:
- Task 1.4 completed (users table exists)
- Task 1.5 completed (JWT service)

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_auth_api.py`
   - Test: Login with valid credentials returns token
   - Test: Login with invalid password returns 401
   - Test: Login with non-existent user returns 401
   - Test: Token format is correct
2. **Implement**
   - Create `app/api/v1/endpoints/auth.py`
   - POST `/api/v1/auth/login` endpoint
   - Validate credentials
   - Return access token, token_type, expires_at, user object
   - Use Pydantic schemas for request/response
3. **Verify**
   - Run: `pytest tests/integration/test_auth_api.py`

**Acceptance Criteria**:
- [ ] Login endpoint returns 200 with token on success
- [ ] Login endpoint returns 401 on invalid credentials
- [ ] Token can be used for subsequent requests
- [ ] Password not exposed in response
- [ ] Tests passing (≥85% coverage)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/auth.py` - Auth endpoints
- `backend/app/schemas/auth.py` - Auth schemas (LoginRequest, LoginResponse)
- `tests/integration/test_auth_api.py` - Auth API tests

**Estimated Time**: 2.5 hours

**Testing**:
- Integration tests: 8 tests (success, failures, token format)

---

### Task 1.7: Create Session Management Models and API

**Goal**: Database model for sessions with creation/validation/timeout

**Prerequisites**:
- Task 1.5 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/models/test_session.py`
   - Test: Session creation
   - Test: Session expiry after 8 hours
   - Test: Session binding (IP hash, user-agent hash)
   - Test: Max 2 concurrent sessions per user
2. **Implement**
   - Create `app/models/session.py` with Session model
   - Fields: id, user_id, token_jti, expires_at, ip_hash, user_agent_hash, created_at, last_activity
   - Create session CRUD in `app/services/session_service.py`
   - Create POST `/api/v1/auth/logout` endpoint
3. **Create Migration**
   - `alembic revision -m "create sessions table"`
   - Run: `alembic upgrade head`
4. **Verify**
   - Run: `pytest tests/unit/models/test_session.py`

**Acceptance Criteria**:
- [ ] Session model defined
- [ ] Session expires after 8 hours of inactivity
- [ ] IP and user-agent binding prevents hijacking
- [ ] Max 2 sessions per user enforced
- [ ] Logout invalidates session
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/models/session.py` - Session model
- `backend/app/services/session_service.py` - Session CRUD
- `backend/alembic/versions/002_create_sessions_table.py` - Migration
- `tests/unit/models/test_session.py` - Session tests

**Estimated Time**: 3 hours

**Testing**:
- Unit tests: 15 tests (creation, expiry, binding, concurrency)

---

### Task 1.8: Create RBAC Permission System

**Goal**: Role-based access control with permission decorators

**Prerequisites**:
- Task 1.3 completed (User model with role)

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/test_rbac.py`
   - Test: Admin has all permissions
   - Test: Clinician has patient access
   - Test: Researcher has read-only
   - Test: Permission decorator blocks unauthorized
2. **Implement**
   - Create `app/core/permissions.py`
   - Define role permissions:
     - admin: user:*, project:*, task:*, document:*, module:*
     - clinician: patient:*, document:read, module:patient-search
     - researcher: patient:read, document:read, module:analytics
   - Create `@require_permission` decorator
   - Create `get_current_user` dependency
3. **Verify**
   - Run: `pytest tests/unit/test_rbac.py`

**Acceptance Criteria**:
- [ ] All roles have defined permissions
- [ ] Permission decorator enforces access control
- [ ] 403 returned for unauthorized access
- [ ] get_current_user extracts user from JWT
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/core/permissions.py` - RBAC implementation
- `backend/app/core/dependencies.py` - FastAPI dependencies
- `tests/unit/test_rbac.py` - RBAC tests

**Estimated Time**: 2.5 hours

**Testing**:
- Unit tests: 12 tests (permissions, decorator, roles)

---

### Task 1.9: Create Audit Logging Service

**Goal**: Comprehensive audit logging for all user actions

**Prerequisites**:
- Task 1.3 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_audit_service.py`
   - Test: Audit log creation
   - Test: WHO (user_id), WHAT (action), WHEN (timestamp), WHERE (IP)
   - Test: Immutability (UPDATE/DELETE blocked)
2. **Implement**
   - Create `app/models/audit_log.py`
   - Fields: id, timestamp, user_id, username, action, resource_type, resource_id, ip_address, user_agent, details (JSONB)
   - Create `app/services/audit_service.py`
   - Create database rules to prevent UPDATE/DELETE
3. **Create Migration**
   - `alembic revision -m "create audit_logs table"`
   - Add PostgreSQL rules in migration
   - Run: `alembic upgrade head`
4. **Verify**
   - Run: `pytest tests/unit/services/test_audit_service.py`

**Acceptance Criteria**:
- [ ] Audit log captures WHO/WHAT/WHEN/WHERE
- [ ] JSONB details field for flexible data
- [ ] UPDATE/DELETE blocked by PostgreSQL rules
- [ ] Partition by month for performance
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/models/audit_log.py` - Audit log model
- `backend/app/services/audit_service.py` - Audit service
- `backend/alembic/versions/003_create_audit_logs_table.py` - Migration with immutability rules
- `tests/unit/services/test_audit_service.py` - Audit service tests

**Estimated Time**: 3 hours

**Testing**:
- Unit tests: 10 tests (logging, immutability, queries)

---

### Task 1.10: Create Health Check Endpoint

**Goal**: /health endpoint for monitoring and Docker health checks

**Prerequisites**:
- Task 1.2 completed (database connection)

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_health.py`
   - Test: GET /health returns 200
   - Test: Response includes database status
   - Test: Response includes service version
2. **Implement**
   - Create `app/api/v1/endpoints/health.py`
   - GET `/health` endpoint
   - Check database connection
   - Return {status, version, database, timestamp}
3. **Update docker-compose.yml**
   - Add health check: `curl -f http://localhost:8000/health || exit 1`
4. **Verify**
   - Run: `pytest tests/integration/test_health.py`
   - Manual: `curl http://localhost:8000/health`

**Acceptance Criteria**:
- [ ] Health endpoint returns 200 when healthy
- [ ] Health endpoint returns 503 when unhealthy
- [ ] Database status included
- [ ] Docker health check uses endpoint
- [ ] Tests passing

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/health.py` - Health endpoint
- `docker-compose.yml` - Updated with backend health check
- `tests/integration/test_health.py` - Health endpoint tests

**Estimated Time**: 1.5 hours

**Testing**:
- Integration tests: 5 tests (healthy, unhealthy, response format)

---

### Task 1.11: Create Frontend Project Structure (Vue 3 + Vite)

**Goal**: Initialize Vue 3 project with TypeScript and Vuetify

**Prerequisites**:
- Phase 0 completed

**Steps**:
1. **Initialize Vue Project**
   - Run: `npm create vite@latest frontend -- --template vue-ts`
   - Install Vuetify: `npm install vuetify@3.7`
   - Install Pinia: `npm install pinia`
   - Install Vue Router: `npm install vue-router`
   - Install Axios: `npm install axios`
2. **Configure Vuetify**
   - Create `src/plugins/vuetify.ts`
   - Import Material Design Icons
   - Configure theme (primary: blue, secondary: orange)
3. **Create Directory Structure**
   - `src/components/` - Reusable components
   - `src/views/` - Page components
   - `src/stores/` - Pinia stores
   - `src/services/` - API clients
   - `src/router/` - Vue Router config
   - `src/types/` - TypeScript types
4. **Create Basic App Structure**
   - Create `App.vue` with Vuetify layout
   - Create `router/index.ts` with routes
   - Create `main.ts` with all plugins

**Acceptance Criteria**:
- [ ] Vue 3 project initialized
- [ ] All dependencies installed
- [ ] Vuetify configured
- [ ] Directory structure created
- [ ] `npm run dev` starts dev server
- [ ] App loads at localhost:8080

**Files Created/Modified**:
- `frontend/package.json`
- `frontend/src/main.ts`
- `frontend/src/App.vue`
- `frontend/src/plugins/vuetify.ts`
- `frontend/src/router/index.ts`
- `frontend/vite.config.ts`

**Estimated Time**: 2 hours

**Testing**:
- Manual: `npm run dev` starts successfully
- Manual: Browser shows Vuetify app

---

### Task 1.12: Create First-Time Setup Script

**Goal**: Script to create admin user and initialize database

**Prerequisites**:
- Task 1.4 completed (database migrations)

**Steps**:
1. **Create Setup Script**
   - Create `scripts/first-time-setup.py`
   - Check if users table is empty
   - Create admin user if not exists
   - Create initial modules (patient-search, timeline, etc.)
   - Set module enabled=true
2. **Test Script**
   - Run: `python scripts/first-time-setup.py`
   - Verify admin user created
   - Verify modules initialized

**Acceptance Criteria**:
- [ ] Script creates admin user with secure password
- [ ] Script is idempotent (can run multiple times safely)
- [ ] Admin user can login immediately
- [ ] Modules initialized in database
- [ ] Clear success message printed

**Files Created/Modified**:
- `backend/scripts/first-time-setup.py` - Setup script
- `backend/README.md` - Add setup instructions

**Estimated Time**: 2 hours

**Testing**:
- Manual: Run script → admin user created
- Manual: Run script again → no duplicate error
- Manual: Login as admin works

---

## Phase 2: User & Project Management (~30 hours)

### Task 2.1: Create User CRUD API Endpoints

**Goal**: REST API for user management (GET, POST, PATCH)

**Prerequisites**:
- Phase 1 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_users_api.py`
   - Test: GET /api/v1/users (admin only)
   - Test: POST /api/v1/users (admin only, creates user)
   - Test: PATCH /api/v1/users/{id} (admin only, updates user)
   - Test: Non-admin returns 403
2. **Implement**
   - Create `app/api/v1/endpoints/users.py`
   - Create `app/schemas/user.py` (UserCreate, UserUpdate, UserResponse)
   - Create `app/services/user_service.py` (CRUD operations)
   - All endpoints require admin permission
3. **Verify**
   - Run: `pytest tests/integration/test_users_api.py`

**Acceptance Criteria**:
- [ ] GET /users returns all users (admin only)
- [ ] POST /users creates user with hashed password
- [ ] PATCH /users/{id} updates user
- [ ] New users have must_change_password=true
- [ ] Audit logs created for all operations
- [ ] Tests passing (≥85% coverage)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/users.py` - User endpoints
- `backend/app/schemas/user.py` - User schemas
- `backend/app/services/user_service.py` - User service
- `tests/integration/test_users_api.py` - User API tests

**Estimated Time**: 3 hours

**Testing**:
- Integration tests: 15 tests (CRUD operations, permissions, validation)

---

### Task 2.2: Create Projects Database Model and API

**Goal**: Projects for organizing work, with team members

**Prerequisites**:
- Phase 1 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/models/test_project.py`
   - Test: Project creation
   - Test: Project-user relationship (many-to-many)
2. **Implement**
   - Create `app/models/project.py`
   - Fields: id, name, description, created_by, created_at, updated_at
   - Create `app/models/project_member.py` (link table)
   - Fields: project_id, user_id, role, added_at, added_by
3. **Create Migration**
   - `alembic revision -m "create projects and project_members tables"`
   - Run: `alembic upgrade head`
4. **Create API**
   - Create `app/api/v1/endpoints/projects.py`
   - GET /projects, POST /projects, PATCH /projects/{id}
   - POST /projects/{id}/members, DELETE /projects/{id}/members/{user_id}
5. **Verify**
   - Run tests

**Acceptance Criteria**:
- [ ] Project model defined
- [ ] Many-to-many relationship with users
- [ ] CRUD API endpoints work
- [ ] Only project members can access project
- [ ] Audit logs for all operations
- [ ] Tests passing (≥85% coverage)

**Files Created/Modified**:
- `backend/app/models/project.py`
- `backend/app/models/project_member.py`
- `backend/app/api/v1/endpoints/projects.py`
- `backend/app/schemas/project.py`
- `backend/alembic/versions/004_create_projects_tables.py`
- `tests/unit/models/test_project.py`
- `tests/integration/test_projects_api.py`

**Estimated Time**: 4 hours

**Testing**:
- Unit tests: 8 tests (model relationships)
- Integration tests: 12 tests (CRUD, membership)

---

### Task 2.3: Create Tasks Database Model and API

**Goal**: Tasks for project work assignment

**Prerequisites**:
- Task 2.2 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/models/test_task.py`
   - Test: Task creation
   - Test: Task assignment to user
   - Test: Task status transitions
2. **Implement**
   - Create `app/models/task.py`
   - Fields: id, project_id, title, description, assigned_to, status, priority, due_date, created_by, created_at, updated_at
   - Status enum: pending, in_progress, completed, blocked
   - Priority enum: low, medium, high, urgent
3. **Create Migration**
   - `alembic revision -m "create tasks table"`
   - Run: `alembic upgrade head`
4. **Create API**
   - GET /projects/{id}/tasks, POST /projects/{id}/tasks
   - PATCH /tasks/{id}, DELETE /tasks/{id}
5. **Verify**
   - Run tests

**Acceptance Criteria**:
- [ ] Task model defined with all fields
- [ ] Tasks belong to projects
- [ ] Users can update their assigned tasks
- [ ] Audit logs for task changes
- [ ] Tests passing (≥85% coverage)

**Files Created/Modified**:
- `backend/app/models/task.py`
- `backend/app/api/v1/endpoints/tasks.py`
- `backend/app/schemas/task.py`
- `backend/alembic/versions/005_create_tasks_table.py`
- `tests/unit/models/test_task.py`
- `tests/integration/test_tasks_api.py`

**Estimated Time**: 3 hours

**Testing**:
- Unit tests: 10 tests (model, status, priority)
- Integration tests: 12 tests (CRUD, assignment, filtering)

---

### Task 2.4: Create User Management Frontend Component

**Goal**: Vue component for admin to manage users

**Prerequisites**:
- Task 1.11 completed (Vue project)
- Task 2.1 completed (User API)

**Steps**:
1. **Create API Service**
   - Create `frontend/src/services/api.ts` (Axios client with auth interceptor)
   - Create `frontend/src/services/users.ts` (fetchUsers, createUser, updateUser)
2. **Create Pinia Store**
   - Create `frontend/src/stores/user.ts`
   - State: users[], loading, error
   - Actions: fetchUsers, createUser, updateUser
3. **Create Components**
   - Create `frontend/src/views/UserManagement.vue`
   - v-data-table for user list
   - v-dialog for create/edit user form
   - v-snackbar for success/error messages
4. **Add Router**
   - Add `/users` route (admin only)

**Acceptance Criteria**:
- [ ] User list displays all users
- [ ] Create user dialog works
- [ ] Edit user dialog works
- [ ] Success/error messages display
- [ ] Loading states show
- [ ] Only admin can access

**Files Created/Modified**:
- `frontend/src/services/api.ts`
- `frontend/src/services/users.ts`
- `frontend/src/stores/user.ts`
- `frontend/src/views/UserManagement.vue`
- `frontend/src/router/index.ts`

**Estimated Time**: 4 hours

**Testing**:
- Manual: Create user → appears in list
- Manual: Edit user → changes saved
- Manual: Non-admin → redirected

---

### Task 2.5: Create Project Management Frontend Component

**Goal**: Vue component to create and manage projects

**Prerequisites**:
- Task 2.2 completed (Projects API)
- Task 2.4 completed (Frontend structure)

**Steps**:
1. **Create API Service**
   - Create `frontend/src/services/projects.ts`
2. **Create Pinia Store**
   - Create `frontend/src/stores/project.ts`
3. **Create Components**
   - Create `frontend/src/views/ProjectManagement.vue`
   - v-data-table for project list
   - v-dialog for create/edit project
   - v-chip for team members
   - Add/remove member functionality
4. **Add Router**
   - Add `/projects` route

**Acceptance Criteria**:
- [ ] Project list displays all projects
- [ ] Create project works
- [ ] Add/remove members works
- [ ] Only project members see project details
- [ ] Success/error messages display

**Files Created/Modified**:
- `frontend/src/services/projects.ts`
- `frontend/src/stores/project.ts`
- `frontend/src/views/ProjectManagement.vue`
- `frontend/src/router/index.ts`

**Estimated Time**: 4 hours

**Testing**:
- Manual: Create project → appears in list
- Manual: Add member → member has access
- Manual: Remove member → member loses access

---

### Task 2.6: Create Task List Frontend Component

**Goal**: Vue component to view and manage tasks

**Prerequisites**:
- Task 2.3 completed (Tasks API)
- Task 2.4 completed (Frontend structure)

**Steps**:
1. **Create API Service**
   - Create `frontend/src/services/tasks.ts`
2. **Create Pinia Store**
   - Create `frontend/src/stores/task.ts`
3. **Create Components**
   - Create `frontend/src/views/TaskList.vue`
   - v-data-table with filters (status, priority, assigned to)
   - v-dialog for create/edit task
   - Drag-and-drop for status changes (optional)
4. **Add Router**
   - Add `/tasks` route

**Acceptance Criteria**:
- [ ] Task list displays user's tasks
- [ ] Filter by status/priority works
- [ ] Create task works
- [ ] Update task status works
- [ ] Due dates highlighted when overdue

**Files Created/Modified**:
- `frontend/src/services/tasks.ts`
- `frontend/src/stores/task.ts`
- `frontend/src/views/TaskList.vue`
- `frontend/src/router/index.ts`

**Estimated Time**: 3 hours

**Testing**:
- Manual: Create task → appears in list
- Manual: Change status → updates in database
- Manual: Filter tasks → shows filtered results

---

### Task 2.7: Create E2E Test for User Management Workflow

**Goal**: End-to-end test for admin creating user who can login

**Prerequisites**:
- Task 2.4 completed

**Steps**:
1. **Setup Playwright**
   - Install: `npm install -D @playwright/test`
   - Configure: `playwright.config.ts`
2. **Write E2E Test**
   - Create `frontend/tests/e2e/user-management.spec.ts`
   - Test: Admin login → Navigate to users → Create user → Logout → New user login → Change password
3. **Verify**
   - Run: `npx playwright test`

**Acceptance Criteria**:
- [ ] Playwright configured
- [ ] E2E test passes
- [ ] Test covers full workflow
- [ ] Screenshots captured on failure

**Files Created/Modified**:
- `frontend/playwright.config.ts`
- `frontend/tests/e2e/user-management.spec.ts`

**Estimated Time**: 2 hours

**Testing**:
- E2E test: 1 test (complete user lifecycle)

---

## Phase 3: Document Upload & PHI Extraction (~40 hours)

### Task 3.1: Create Documents Database Model

**Goal**: Model for encrypted document storage

**Prerequisites**:
- Phase 2 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/models/test_document.py`
   - Test: Document creation
   - Test: SHA-256 hash generated
   - Test: Content encrypted
2. **Implement**
   - Create `app/models/document.py`
   - Fields: id, filename, content_type, content_hash, encrypted_content, encryption_algorithm, file_size, uploaded_by, project_id, processing_status, created_at
   - Processing status enum: pending, processing, completed, failed
3. **Create Migration**
   - `alembic revision -m "create documents table"`
   - Add unique constraint on content_hash
   - Add index on content_hash
   - Run: `alembic upgrade head`

**Acceptance Criteria**:
- [ ] Document model defined
- [ ] SHA-256 hash auto-generated
- [ ] Content stored as BYTEA
- [ ] Unique constraint on content_hash
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/models/document.py`
- `backend/alembic/versions/006_create_documents_table.py`
- `tests/unit/models/test_document.py`

**Estimated Time**: 2 hours

**Testing**:
- Unit tests: 8 tests (creation, hashing, encryption field)

---

### Task 3.2: Create Document Encryption Service

**Goal**: AES-256 encryption/decryption for document content

**Prerequisites**:
- Task 3.1 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_encryption_service.py`
   - Test: Encrypt plaintext → ciphertext
   - Test: Decrypt ciphertext → original plaintext
   - Test: Different plaintexts → different ciphertexts (random IV)
   - Test: Wrong key → decryption fails
2. **Implement**
   - Create `app/services/encryption_service.py`
   - Use AES-256-GCM (authenticated encryption)
   - Generate random IV for each encryption
   - Store IV prepended to ciphertext
   - Read key from environment variable
3. **Verify**
   - Run: `pytest tests/unit/services/test_encryption_service.py`

**Acceptance Criteria**:
- [ ] AES-256-GCM encryption
- [ ] Random IV for each encryption
- [ ] Encryption key from environment
- [ ] Decryption returns original content
- [ ] Tests passing (≥95% coverage - security critical)

**Files Created/Modified**:
- `backend/app/services/encryption_service.py`
- `tests/unit/services/test_encryption_service.py`

**Estimated Time**: 2 hours

**Testing**:
- Unit tests: 10 tests (encrypt, decrypt, IV randomness, key validation)

---

### Task 3.3: Create Document Deduplication Service

**Goal**: SHA-256 hash-based deduplication with Redis cache

**Prerequisites**:
- Task 3.1 completed
- Phase 0 completed (Redis running)

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_deduplication_service.py`
   - Test: Same content → same hash
   - Test: Cache hit for duplicate document
   - Test: Cache miss → database lookup
   - Test: New document → cache updated
2. **Implement**
   - Create `app/services/deduplication_service.py`
   - Function: `check_duplicate(content_hash)` → document_id or None
   - Check Redis first: `GET doc_hash:{hash}`
   - Check database if cache miss
   - Update cache with 30-day TTL
3. **Verify**
   - Run: `pytest tests/unit/services/test_deduplication_service.py`

**Acceptance Criteria**:
- [ ] SHA-256 hash computed correctly
- [ ] Redis cache checked first (fast path)
- [ ] Database fallback works
- [ ] Cache updated after database lookup
- [ ] 30-day TTL set on cache entries
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/services/deduplication_service.py`
- `tests/unit/services/test_deduplication_service.py`

**Estimated Time**: 2.5 hours

**Testing**:
- Unit tests: 12 tests (hashing, cache, database, TTL)

---

### Task 3.4: Create Document Upload API Endpoint

**Goal**: POST /api/v1/documents/upload with encryption and deduplication

**Prerequisites**:
- Task 3.2 completed (encryption)
- Task 3.3 completed (deduplication)

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_documents_api.py`
   - Test: Upload new document → status=processing
   - Test: Upload duplicate → status=duplicate, existing document_id returned
   - Test: Document encrypted in database
   - Test: Audit log created for upload
2. **Implement**
   - Create `app/api/v1/endpoints/documents.py`
   - POST `/api/v1/documents/upload`
   - Accept multipart/form-data (file)
   - Compute SHA-256 hash
   - Check deduplication
   - Encrypt content
   - Store in database
   - Return document_id and status
3. **Verify**
   - Run: `pytest tests/integration/test_documents_api.py`

**Acceptance Criteria**:
- [ ] Upload endpoint accepts RTF files
- [ ] Content encrypted before storage
- [ ] Duplicates detected and returned
- [ ] Document hash stored
- [ ] Audit log: DOCUMENT_UPLOAD action
- [ ] Tests passing (≥85% coverage)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/documents.py`
- `backend/app/schemas/document.py`
- `tests/integration/test_documents_api.py`

**Estimated Time**: 3 hours

**Testing**:
- Integration tests: 10 tests (upload, dedup, encryption, errors)

---

### Task 3.5: Create MedCAT Client Service

**Goal**: Async client to call MedCAT Service with retry logic

**Prerequisites**:
- Phase 0 completed (MedCAT Service running)

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_medcat_client.py`
   - Test: Successful entity extraction
   - Test: Retry on failure (3 attempts)
   - Test: Circuit breaker after 5 consecutive failures
   - Mock MedCAT Service responses
2. **Implement**
   - Create `app/services/medcat_client.py`
   - Use httpx.AsyncClient
   - Use tenacity for retries (3 attempts, exponential backoff 4-10s)
   - POST /api/process with {"text": "..."}
   - Parse response: entities list
3. **Verify**
   - Run: `pytest tests/unit/services/test_medcat_client.py`

**Acceptance Criteria**:
- [ ] Async HTTP client
- [ ] 3 retry attempts with exponential backoff
- [ ] Circuit breaker prevents cascade failures
- [ ] Entities parsed correctly
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/services/medcat_client.py`
- `tests/unit/services/test_medcat_client.py`

**Estimated Time**: 3 hours

**Testing**:
- Unit tests: 15 tests (success, retries, circuit breaker, parsing)

---

### Task 3.6: Create PHI Classifier Service

**Goal**: Classify entities as PHI (name, NHS number, address, DOB) or clinical

**Prerequisites**:
- Task 3.5 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_phi_classifier.py`
   - Test: "NHS number" → phi_nhs_number
   - Test: "patient name" → phi_name
   - Test: "diabetes" → clinical
   - Test: "address" → phi_address
2. **Implement**
   - Create `app/services/phi_classifier.py`
   - Function: `classify_entity(entity)` → entity_type
   - Use CUI lookup and keyword matching
   - Return: phi_name, phi_nhs_number, phi_dob, phi_address, or clinical
3. **Verify**
   - Run: `pytest tests/unit/services/test_phi_classifier.py`

**Acceptance Criteria**:
- [ ] PHI entities correctly classified
- [ ] Clinical entities not flagged as PHI
- [ ] CUI C1547728 → phi_nhs_number
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/services/phi_classifier.py`
- `tests/unit/services/test_phi_classifier.py`

**Estimated Time**: 2 hours

**Testing**:
- Unit tests: 12 tests (classification accuracy)

---

### Task 3.7: Create Extracted Entities Database Model

**Goal**: Model for storing PHI and clinical entities

**Prerequisites**:
- Task 3.1 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/models/test_extracted_entity.py`
   - Test: Entity creation
   - Test: Relationship to document
   - Test: Relationship to patient (nullable)
2. **Implement**
   - Create `app/models/extracted_entity.py`
   - Fields: id, document_id, patient_id (nullable), entity_type, cui, pretty_name, start_char, end_char, accuracy, meta_anns (JSONB), created_at
   - Entity type enum: phi_name, phi_nhs_number, phi_dob, phi_address, clinical
3. **Create Migration**
   - `alembic revision -m "create extracted_entities table"`
   - Add indexes on document_id, patient_id, entity_type
   - Run: `alembic upgrade head`

**Acceptance Criteria**:
- [ ] ExtractedEntity model defined
- [ ] Relationship to documents
- [ ] Relationship to patients (for aggregation)
- [ ] Meta-annotations stored as JSONB
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/models/extracted_entity.py`
- `backend/alembic/versions/007_create_extracted_entities_table.py`
- `tests/unit/models/test_extracted_entity.py`

**Estimated Time**: 2 hours

**Testing**:
- Unit tests: 8 tests (model, relationships, indexes)

---

### Task 3.8: Create Patients Database Model

**Goal**: Model for aggregated patient records

**Prerequisites**:
- Task 3.7 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/models/test_patient.py`
   - Test: Patient creation
   - Test: NHS number unique constraint
   - Test: Relationship to extracted entities
2. **Implement**
   - Create `app/models/patient.py`
   - Fields: id, nhs_number (unique), full_name, date_of_birth, address, first_seen_at, last_seen_at, document_count
3. **Create Migration**
   - `alembic revision -m "create patients table"`
   - Add unique constraint on nhs_number
   - Add index on nhs_number
   - Run: `alembic upgrade head`

**Acceptance Criteria**:
- [ ] Patient model defined
- [ ] NHS number unique and indexed
- [ ] Relationship to extracted entities
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/models/patient.py`
- `backend/alembic/versions/008_create_patients_table.py`
- `tests/unit/models/test_patient.py`

**Estimated Time**: 1.5 hours

**Testing**:
- Unit tests: 6 tests (model, constraints, relationships)

---

### Task 3.9: Create PHI Extraction Background Job

**Goal**: Background task to process document with MedCAT and extract PHI

**Prerequisites**:
- Tasks 3.5, 3.6, 3.7, 3.8 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_phi_extraction.py`
   - Test: Document uploaded → entities extracted
   - Test: PHI entities classified correctly
   - Test: Patient aggregated by NHS number
   - Test: Document status updated to completed
2. **Implement**
   - Create `app/services/document_processing_service.py`
   - Function: `process_document(document_id)`
     1. Decrypt document content
     2. Call MedCAT Service
     3. Classify entities (PHI vs clinical)
     4. Store entities in extracted_entities table
     5. Aggregate patient data (update or insert)
     6. Update document status to completed
   - Use FastAPI BackgroundTasks to run async
3. **Update Upload Endpoint**
   - Queue background task after upload
4. **Verify**
   - Run: `pytest tests/integration/test_phi_extraction.py`

**Acceptance Criteria**:
- [ ] Document content decrypted for processing only
- [ ] MedCAT extracts entities correctly
- [ ] PHI classified and stored separately
- [ ] Patient aggregated by NHS number
- [ ] Document status updated
- [ ] Audit log: PHI_EXTRACT action
- [ ] Tests passing (≥85% coverage)

**Files Created/Modified**:
- `backend/app/services/document_processing_service.py`
- `backend/app/api/v1/endpoints/documents.py` (updated to queue job)
- `tests/integration/test_phi_extraction.py`

**Estimated Time**: 4 hours

**Testing**:
- Integration tests: 12 tests (extraction workflow, patient aggregation, status)

---

### Task 3.10: Create Patient Aggregation Service

**Goal**: Match and merge patient records by NHS number

**Prerequisites**:
- Task 3.8 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_patient_aggregation.py`
   - Test: Same NHS number → update existing patient
   - Test: New NHS number → create new patient
   - Test: Name conflict → log warning, use most recent
   - Test: Fuzzy match on name+DOB (fallback)
2. **Implement**
   - Create `app/services/patient_aggregation_service.py`
   - Function: `aggregate_patient(nhs_number, name, dob, address)`
   - Primary: Match by NHS number
   - Fallback: Fuzzy match by name+DOB (>80% similarity)
   - Update patient fields if newer data available
3. **Verify**
   - Run: `pytest tests/unit/services/test_patient_aggregation.py`

**Acceptance Criteria**:
- [ ] NHS number primary matching works
- [ ] Fuzzy matching fallback works
- [ ] Patient fields updated with latest data
- [ ] Conflicts logged for review
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/services/patient_aggregation_service.py`
- `tests/unit/services/test_patient_aggregation.py`

**Estimated Time**: 3 hours

**Testing**:
- Unit tests: 15 tests (matching, fuzzy, updates, conflicts)

---

### Task 3.11: Create Document Upload Frontend Component

**Goal**: Vue component to upload RTF documents

**Prerequisites**:
- Task 3.4 completed (Upload API)

**Steps**:
1. **Create API Service**
   - Create `frontend/src/services/documents.ts`
   - Function: `uploadDocument(file, projectId)`
2. **Create Component**
   - Create `frontend/src/components/DocumentUpload.vue`
   - v-file-input for RTF files
   - Upload progress indicator
   - Duplicate detection message
   - Processing status display
3. **Add to Project View**
   - Add DocumentUpload component to project detail page

**Acceptance Criteria**:
- [ ] File input accepts .rtf files
- [ ] Upload shows progress
- [ ] Duplicate message displayed clearly
- [ ] Processing status updates
- [ ] Success/error messages display

**Files Created/Modified**:
- `frontend/src/services/documents.ts`
- `frontend/src/components/DocumentUpload.vue`
- `frontend/src/views/ProjectDetail.vue` (updated)

**Estimated Time**: 3 hours

**Testing**:
- Manual: Upload RTF → processing status shown
- Manual: Upload duplicate → duplicate message shown

---

### Task 3.12: Create PHI De-Identification Tests

**Goal**: Security tests to verify PHI is never exposed

**Prerequisites**:
- Task 3.9 completed

**Steps**:
1. **Write Security Tests**
   - Create `tests/security/test_phi_logging.py`
   - Test: Upload document → no PHI in application logs
   - Test: Process document → no PHI in logs
   - Test: API response → no direct PHI returned
   - Capture all log output with caplog
2. **Implement Log Sanitization** (if needed)
   - Add log sanitizer to remove PHI patterns
   - Configure logger to use sanitizer
3. **Verify**
   - Run: `pytest tests/security/test_phi_logging.py`

**Acceptance Criteria**:
- [ ] No NHS numbers in logs (10-digit pattern)
- [ ] No patient names in logs
- [ ] No addresses in logs
- [ ] Only document IDs and patient IDs in logs
- [ ] Audit logs capture PHI access (separate from app logs)
- [ ] Tests passing (100% - security critical)

**Files Created/Modified**:
- `tests/security/test_phi_logging.py`
- `backend/app/core/logging.py` (log sanitizer if needed)

**Estimated Time**: 2 hours

**Testing**:
- Security tests: 10 tests (PHI detection in logs, audit trail)

---

## Phase 4: Module System & Patient Search (~50 hours)

### Task 4.1: Create Modules Database Model

**Goal**: Model for module registry and configuration

**Prerequisites**:
- Phase 3 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/models/test_module.py`
   - Test: Module creation
   - Test: Module enabled/disabled
   - Test: Module configuration (JSONB)
2. **Implement**
   - Create `app/models/module.py`
   - Fields: id, name, display_name, description, version, enabled, config (JSONB), icon, permissions (ARRAY), created_at, updated_at
3. **Create Migration**
   - `alembic revision -m "create modules table"`
   - Insert seed modules: patient-search, timeline-view, clinical-decision-support
   - Run: `alembic upgrade head`

**Acceptance Criteria**:
- [ ] Module model defined
- [ ] Seed modules inserted
- [ ] Configuration stored as JSONB
- [ ] Permissions array for access control
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/models/module.py`
- `backend/alembic/versions/009_create_modules_table.py`
- `tests/unit/models/test_module.py`

**Estimated Time**: 2 hours

**Testing**:
- Unit tests: 8 tests (model, config, permissions)

---

### Task 4.2: Create Module Registry Service

**Goal**: Dynamic module loading and registration

**Prerequisites**:
- Task 4.1 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_module_registry.py`
   - Test: List enabled modules
   - Test: Get module by name
   - Test: Module configuration access
2. **Implement**
   - Create `app/services/module_registry.py`
   - Function: `get_enabled_modules()` → list of modules
   - Function: `get_module(name)` → module or None
   - Function: `register_module_routes(app, module_name)`
3. **Verify**
   - Run: `pytest tests/unit/services/test_module_registry.py`

**Acceptance Criteria**:
- [ ] Registry returns enabled modules only
- [ ] Module lookup by name works
- [ ] Configuration accessible
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/services/module_registry.py`
- `tests/unit/services/test_module_registry.py`

**Estimated Time**: 2 hours

**Testing**:
- Unit tests: 10 tests (list, get, config)

---

### Task 4.3: Create Patient Search API Endpoint

**Goal**: Search patients by clinical concept with meta-annotation filtering

**Prerequisites**:
- Phase 3 completed (patients and entities exist)
- Task 4.2 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_patient_search_api.py`
   - Test: Search "diabetes" → returns patients with diabetes
   - Test: Filter Negation=Affirmed → excludes "no diabetes"
   - Test: Filter Experiencer=Patient → excludes family history
   - Test: Pagination works (limit, offset)
2. **Implement**
   - Create `app/api/v1/modules/patient_search.py`
   - POST `/api/v1/modules/patient-search/search`
   - Request: concept, meta_annotation_filters, limit, offset
   - Query extracted_entities table
   - Join with patients table
   - Apply meta-annotation filters
   - Return patient list with concept matches
3. **Verify**
   - Run: `pytest tests/integration/test_patient_search_api.py`

**Acceptance Criteria**:
- [ ] Search by concept works
- [ ] Meta-annotation filters work correctly
- [ ] Negation filter excludes negated mentions
- [ ] Experiencer filter excludes family history
- [ ] Pagination works
- [ ] Audit log: PATIENT_SEARCH action
- [ ] Tests passing (≥85% coverage)

**Files Created/Modified**:
- `backend/app/api/v1/modules/patient_search.py`
- `backend/app/schemas/patient_search.py`
- `tests/integration/test_patient_search_api.py`

**Estimated Time**: 4 hours

**Testing**:
- Integration tests: 15 tests (search, filters, pagination, audit)

---

### Task 4.4: Create Patient Search Frontend Component

**Goal**: Vue component for searching patients by clinical concept

**Prerequisites**:
- Task 4.3 completed

**Steps**:
1. **Create API Service**
   - Create `frontend/src/services/patient-search.ts`
2. **Create Component**
   - Create `frontend/src/modules/patient-search/PatientSearch.vue`
   - v-text-field for concept input
   - v-checkbox-group for meta-annotation filters (Negation, Experiencer, Temporality)
   - v-data-table for results
   - v-pagination for paging
3. **Create Route**
   - Add `/modules/patient-search` route

**Acceptance Criteria**:
- [ ] Search input accepts concept
- [ ] Meta-annotation filters work
- [ ] Results display patient ID (not PHI)
- [ ] Pagination works
- [ ] Loading states show

**Files Created/Modified**:
- `frontend/src/services/patient-search.ts`
- `frontend/src/modules/patient-search/PatientSearch.vue`
- `frontend/src/router/index.ts`

**Estimated Time**: 4 hours

**Testing**:
- Manual: Search "diabetes" → results shown
- Manual: Filter Negation → results change

---

## Phase 5: Session Security & Break-Glass (~30 hours)

### Task 5.1: Implement Session Binding with IP and User-Agent Hashing

**Goal**: Prevent session hijacking by binding sessions to IP and user-agent

**Prerequisites**:
- Task 1.7 completed (Session model)

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_session_security.py`
   - Test: Login creates session with IP/UA hash
   - Test: Request with different IP → 401
   - Test: Request with different user-agent → 401
   - Test: Legitimate request → 200
2. **Implement**
   - Update `app/services/session_service.py`
   - Hash IP address: `hashlib.sha256(ip.encode()).hexdigest()`
   - Hash user-agent: `hashlib.sha256(ua.encode()).hexdigest()`
   - Store hashes in session record
   - Validate on each request in auth middleware
3. **Verify**
   - Run: `pytest tests/integration/test_session_security.py`

**Acceptance Criteria**:
- [ ] Session created with IP and UA hashes
- [ ] Mismatched IP returns 401
- [ ] Mismatched UA returns 401
- [ ] Audit log: SESSION_HIJACK_DETECTED
- [ ] Tests passing (≥95% coverage - security critical)

**Files Created/Modified**:
- `backend/app/services/session_service.py` (updated)
- `backend/app/core/dependencies.py` (updated with session validation)
- `tests/integration/test_session_security.py`

**Estimated Time**: 3 hours

**Testing**:
- Integration tests: 12 tests (binding, hijack detection, audit)

---

### Task 5.2: Implement Idle Timeout (15 Minutes)

**Goal**: Automatic session expiration after 15 minutes of inactivity

**Prerequisites**:
- Task 1.7 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_session_timeout.py`
   - Test: Activity updates last_activity timestamp
   - Test: 15 minutes idle → session invalid
   - Test: Activity resets idle timer
2. **Implement**
   - Update session validation to check `last_activity`
   - Update `last_activity` on each request
   - Return 401 if `now() - last_activity > 15 minutes`
3. **Verify**
   - Run: `pytest tests/unit/services/test_session_timeout.py`

**Acceptance Criteria**:
- [ ] last_activity updated on each request
- [ ] 15 minutes idle → 401
- [ ] Activity resets timer
- [ ] Clear error message: "Session expired due to inactivity"
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/services/session_service.py` (updated)
- `tests/unit/services/test_session_timeout.py`

**Estimated Time**: 2 hours

**Testing**:
- Unit tests: 8 tests (timeout, reset, edge cases)

---

### Task 5.3: Implement Concurrent Session Limit (Max 2)

**Goal**: Limit users to maximum 2 concurrent sessions

**Prerequisites**:
- Task 1.7 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_concurrent_sessions.py`
   - Test: User can have 2 sessions
   - Test: 3rd login → oldest session invalidated
   - Test: Logout → session count decreases
2. **Implement**
   - Update login endpoint
   - Count active sessions for user
   - If ≥2, delete oldest session
   - Create new session
3. **Verify**
   - Run: `pytest tests/integration/test_concurrent_sessions.py`

**Acceptance Criteria**:
- [ ] Max 2 sessions per user
- [ ] 3rd login invalidates oldest
- [ ] Audit log: SESSION_EVICTED
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/auth.py` (updated)
- `tests/integration/test_concurrent_sessions.py`

**Estimated Time**: 2.5 hours

**Testing**:
- Integration tests: 10 tests (concurrency, eviction, edge cases)

---

### Task 5.4: Create Break-Glass Access Model and API

**Goal**: Emergency 60-minute access with security notifications

**Prerequisites**:
- Task 1.3 completed (User model with can_break_glass field)

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_break_glass.py`
   - Test: Authorized user can request break-glass
   - Test: Unauthorized user returns 403
   - Test: Access expires after 60 minutes
   - Test: Security team notified
2. **Implement**
   - Create `app/models/break_glass_event.py`
   - Fields: id, user_id, patient_id, reason, access_granted_at, access_expires_at, accessed_resources (JSONB)
   - POST `/api/v1/auth/break-glass`
   - Grant 60-minute temporary access
   - Send notifications to security team
3. **Create Migration**
   - `alembic revision -m "create break_glass_events table"`
   - Run: `alembic upgrade head`
4. **Verify**
   - Run: `pytest tests/integration/test_break_glass.py`

**Acceptance Criteria**:
- [ ] only users with can_break_glass=true can request
- [ ] Access expires after 60 minutes
- [ ] Security team notified immediately
- [ ] All accessed resources logged
- [ ] Audit log: BREAK_GLASS_ACCESS
- [ ] Tests passing (≥95% coverage - security critical)

**Files Created/Modified**:
- `backend/app/models/break_glass_event.py`
- `backend/app/api/v1/endpoints/auth.py` (updated)
- `backend/alembic/versions/010_create_break_glass_events_table.py`
- `tests/integration/test_break_glass.py`

**Estimated Time**: 4 hours

**Testing**:
- Integration tests: 15 tests (authorization, expiry, notifications, audit)

---

### Task 5.5: Create Security Notification Service

**Goal**: Real-time notifications for security events

**Prerequisites**:
- Task 5.4 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_notification_service.py`
   - Test: Break-glass → email sent
   - Test: Session hijack → email sent
   - Test: Failed login attempts (5+) → email sent
2. **Implement**
   - Create `app/services/notification_service.py`
   - Function: `notify_security_team(event_type, details)`
   - Use SMTP for email (configurable)
   - Use Redis pub/sub for real-time dashboard (future)
3. **Verify**
   - Run: `pytest tests/unit/services/test_notification_service.py`

**Acceptance Criteria**:
- [ ] Email sent for break-glass events
- [ ] Email sent for session hijacking
- [ ] Email contains event details
- [ ] Configurable recipients
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/services/notification_service.py`
- `tests/unit/services/test_notification_service.py`

**Estimated Time**: 3 hours

**Testing**:
- Unit tests: 12 tests (email sending, templates, error handling)

---

### Task 5.6: Create Force Logout API Endpoint

**Goal**: Admin can force logout specific user or all sessions

**Prerequisites**:
- Task 1.7 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_force_logout.py`
   - Test: Admin can force logout user
   - Test: All user sessions invalidated
   - Test: User returns 401 on next request
   - Test: Audit log created
2. **Implement**
   - POST `/api/v1/admin/users/{user_id}/force-logout`
   - Delete all sessions for user
   - Send notification to user
3. **Verify**
   - Run: `pytest tests/integration/test_force_logout.py`

**Acceptance Criteria**:
- [ ] Admin only endpoint
- [ ] All user sessions deleted
- [ ] User notified
- [ ] Audit log: FORCE_LOGOUT
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/admin.py`
- `tests/integration/test_force_logout.py`

**Estimated Time**: 2 hours

**Testing**:
- Integration tests: 8 tests (force logout, permissions, audit)

---

## Phase 6: Data Retention & Clinical Safety (~30 hours)

### Task 6.1: Create Automated Purging Service

**Goal**: Delete old data per retention policy (8 years documents, 7 years audit, 90 days sessions)

**Prerequisites**:
- Phase 3 completed (documents exist)

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_data_retention.py`
   - Test: Documents >8 years old marked for deletion
   - Test: Legal hold prevents deletion
   - Test: Audit logs >7 years deleted
   - Test: Sessions >90 days deleted
2. **Implement**
   - Create `app/services/data_retention_service.py`
   - Function: `purge_old_data()`
   - Check legal_hold flag before deletion
   - Delete documents >8 years (unless legal hold)
   - Delete audit logs >7 years
   - Delete sessions >90 days
   - Log all deletions
3. **Create Scheduled Job**
   - Use APScheduler or cron
   - Run daily at 2 AM
4. **Verify**
   - Run: `pytest tests/unit/services/test_data_retention.py`

**Acceptance Criteria**:
- [ ] Documents >8 years deleted (respect legal hold)
- [ ] Audit logs >7 years deleted
- [ ] Sessions >90 days deleted
- [ ] Deletion count logged
- [ ] Runs daily automatically
- [ ] Tests passing (≥95% coverage - compliance critical)

**Files Created/Modified**:
- `backend/app/services/data_retention_service.py`
- `backend/app/core/scheduler.py` (APScheduler setup)
- `tests/unit/services/test_data_retention.py`

**Estimated Time**: 4 hours

**Testing**:
- Unit tests: 15 tests (retention periods, legal hold, scheduling)

---

### Task 6.2: Create Legal Hold Workflow

**Goal**: Admin can place legal hold on documents to prevent deletion

**Prerequisites**:
- Task 3.1 completed (Document model)

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_legal_hold.py`
   - Test: Admin can place legal hold
   - Test: Legal hold prevents deletion
   - Test: Legal hold can be removed
   - Test: Audit log created
2. **Implement**
   - POST `/api/v1/admin/documents/{id}/legal-hold`
   - Set legal_hold=true, legal_hold_reason, legal_hold_by
   - DELETE `/api/v1/admin/documents/{id}/legal-hold`
   - Remove legal hold
3. **Verify**
   - Run: `pytest tests/integration/test_legal_hold.py`

**Acceptance Criteria**:
- [ ] Admin only endpoints
- [ ] Legal hold prevents deletion
- [ ] Reason required
- [ ] Audit log: LEGAL_HOLD_PLACED, LEGAL_HOLD_REMOVED
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/admin.py` (updated)
- `tests/integration/test_legal_hold.py`

**Estimated Time**: 2.5 hours

**Testing**:
- Integration tests: 10 tests (place, remove, deletion prevention, audit)

---

### Task 6.3: Create Clinical Override Tracking

**Goal**: Log when clinicians override system recommendations

**Prerequisites**:
- Phase 4 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/models/test_clinical_override.py`
   - Test: Override creation
   - Test: Justification required
2. **Implement**
   - Create `app/models/clinical_override.py`
   - Fields: id, user_id, patient_id, recommendation_type, recommendation_value, override_value, justification, created_at
   - POST `/api/v1/clinical-overrides`
3. **Create Migration**
   - `alembic revision -m "create clinical_overrides table"`
   - Run: `alembic upgrade head`
4. **Verify**
   - Run tests

**Acceptance Criteria**:
- [ ] Override model defined
- [ ] Justification required (min 20 chars)
- [ ] Audit log: CLINICAL_OVERRIDE
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/models/clinical_override.py`
- `backend/app/api/v1/endpoints/clinical_overrides.py`
- `backend/alembic/versions/011_create_clinical_overrides_table.py`
- `tests/unit/models/test_clinical_override.py`

**Estimated Time**: 3 hours

**Testing**:
- Unit tests: 10 tests (model, validation, audit)

---

### Task 6.4: Create Critical Finding Alert System

**Goal**: Alert clinicians to critical findings (e.g., cancer, acute MI)

**Prerequisites**:
- Phase 3 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_critical_findings.py`
   - Test: Critical concept detected → alert created
   - Test: Clinician notified
   - Test: Alert acknowledged → timestamp recorded
2. **Implement**
   - Create `app/models/critical_finding_alert.py`
   - Fields: id, patient_id, concept_cui, concept_name, severity, acknowledged_by, acknowledged_at, created_at
   - Create alert service
   - Check extracted entities for critical concepts
   - Create alert if detected
   - Notify assigned clinician
3. **Create Migration**
   - `alembic revision -m "create critical_finding_alerts table"`
   - Run: `alembic upgrade head`
4. **Verify**
   - Run tests

**Acceptance Criteria**:
- [ ] Critical findings detected automatically
- [ ] Clinician notified (email + dashboard)
- [ ] Alert acknowledgment tracked
- [ ] Configurable critical concept list
- [ ] Audit log: CRITICAL_FINDING_DETECTED, CRITICAL_FINDING_ACKNOWLEDGED
- [ ] Tests passing (≥95% coverage - safety critical)

**Files Created/Modified**:
- `backend/app/models/critical_finding_alert.py`
- `backend/app/services/critical_finding_service.py`
- `backend/alembic/versions/012_create_critical_finding_alerts_table.py`
- `tests/integration/test_critical_findings.py`

**Estimated Time**: 4 hours

**Testing**:
- Integration tests: 15 tests (detection, notification, acknowledgment)

---

### Task 6.5: Create Clinical Incident Reporting

**Goal**: Report and track clinical safety incidents

**Prerequisites**:
- Phase 3 completed

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/models/test_clinical_incident.py`
   - Test: Incident creation
   - Test: Severity classification
   - Test: Investigation workflow
2. **Implement**
   - Create `app/models/clinical_incident.py`
   - Fields: id, incident_type, severity, description, patient_id, reported_by, investigated_by, resolution, status, created_at, resolved_at
   - Incident types: data_accuracy, system_error, user_error, safety_concern
   - Severity: low, medium, high, critical
   - Status: reported, under_investigation, resolved
   - POST `/api/v1/clinical-incidents`
3. **Create Migration**
   - `alembic revision -m "create clinical_incidents table"`
   - Run: `alembic upgrade head`
4. **Verify**
   - Run tests

**Acceptance Criteria**:
- [ ] Incident model defined
- [ ] All clinicians can report
- [ ] Admin can investigate
- [ ] Resolution required before closing
- [ ] Audit log: INCIDENT_REPORTED, INCIDENT_RESOLVED
- [ ] Tests passing (≥90% coverage)

**Files Created/Modified**:
- `backend/app/models/clinical_incident.py`
- `backend/app/api/v1/endpoints/clinical_incidents.py`
- `backend/alembic/versions/013_create_clinical_incidents_table.py`
- `tests/unit/models/test_clinical_incident.py`

**Estimated Time**: 3.5 hours

**Testing**:
- Unit tests: 12 tests (model, workflow, permissions)

---

## Phase 7: Testing & Deployment (~50 hours)

### Task 7.1: Increase Unit Test Coverage to ≥80%

**Goal**: Comprehensive unit test coverage across all modules

**Prerequisites**:
- All previous phases completed

**Steps**:
1. **Run Coverage Report**
   - Run: `pytest --cov=app --cov-report=html`
   - Identify gaps in coverage
2. **Write Missing Tests**
   - Focus on untested functions
   - Focus on edge cases
   - Focus on error handling
3. **Verify**
   - Run: `pytest --cov=app --cov-report=term-missing`
   - Coverage ≥80%

**Acceptance Criteria**:
- [ ] Overall coverage ≥80%
- [ ] Auth module ≥90%
- [ ] PHI handling ≥90%
- [ ] All critical paths ≥95%
- [ ] No missing test files

**Files Created/Modified**:
- Multiple test files (various modules)

**Estimated Time**: 8 hours

**Testing**:
- Unit tests: ~50 additional tests to reach 80% coverage

---

### Task 7.2: Create Integration Tests for Critical Paths

**Goal**: Full API integration tests for critical workflows

**Prerequisites**:
- Task 7.1 completed

**Steps**:
1. **Write Integration Tests**
   - Create `tests/integration/test_full_workflow.py`
   - Test: Document upload → PHI extraction → patient search
   - Test: User creation → login → task assignment
   - Test: Break-glass access → resource access → expiry
2. **Verify**
   - Run: `pytest tests/integration/`

**Acceptance Criteria**:
- [ ] All critical workflows tested
- [ ] Database state verified at each step
- [ ] Audit logs verified
- [ ] All tests passing

**Files Created/Modified**:
- `tests/integration/test_full_workflow.py`
- `tests/integration/test_auth_workflow.py`
- `tests/integration/test_security_workflow.py`

**Estimated Time**: 6 hours

**Testing**:
- Integration tests: ~30 tests (complete workflows)

---

### Task 7.3: Create E2E Tests for User Journeys

**Goal**: Playwright tests for complete user workflows

**Prerequisites**:
- All frontend components completed

**Steps**:
1. **Write E2E Tests**
   - Create `frontend/tests/e2e/clinician-workflow.spec.ts`
   - Test: Clinician login → upload document → search patients → view results
   - Create `frontend/tests/e2e/admin-workflow.spec.ts`
   - Test: Admin login → create user → assign to project → create task
2. **Configure Playwright**
   - Update `playwright.config.ts` for CI/CD
   - Add screenshots on failure
   - Add video recording
3. **Verify**
   - Run: `npx playwright test`

**Acceptance Criteria**:
- [ ] 5-10 critical user journeys tested
- [ ] All E2E tests passing
- [ ] Screenshots captured on failure
- [ ] Video recording available

**Files Created/Modified**:
- `frontend/tests/e2e/clinician-workflow.spec.ts`
- `frontend/tests/e2e/admin-workflow.spec.ts`
- `frontend/tests/e2e/patient-search.spec.ts`
- `frontend/playwright.config.ts` (updated)

**Estimated Time**: 8 hours

**Testing**:
- E2E tests: 8-10 complete user journeys

---

### Task 7.4: Performance Testing with Locust

**Goal**: Load test with 10 concurrent users, validate P95 <500ms

**Prerequisites**:
- All backend APIs completed

**Steps**:
1. **Create Locust Tests**
   - Create `tests/performance/locustfile.py`
   - Simulate 10 concurrent users
   - Test scenarios: login, document upload, patient search
   - Run for 10 minutes
2. **Run Performance Tests**
   - Run: `locust -f tests/performance/locustfile.py --host=http://localhost:8000`
   - Ramp to 10 users over 60 seconds
   - Sustain for 10 minutes
3. **Analyze Results**
   - Check P95 response times
   - Check error rate
   - Check database connection pool usage

**Acceptance Criteria**:
- [ ] P95 login <200ms
- [ ] P95 API calls <500ms
- [ ] P95 document upload <2s
- [ ] Error rate <1%
- [ ] Database connections <20

**Files Created/Modified**:
- `tests/performance/locustfile.py`
- `docs/performance/results.md` (performance test results)

**Estimated Time**: 5 hours

**Testing**:
- Performance tests: 3 scenarios (login, upload, search)

---

### Task 7.5: Security Audit and Penetration Testing

**Goal**: Security review and vulnerability assessment

**Prerequisites**:
- All features completed

**Steps**:
1. **Code Security Review**
   - Review all auth/PHI handling code
   - Check for SQL injection vulnerabilities
   - Check for XSS vulnerabilities
   - Check for secrets in code
2. **Dependency Security Scan**
   - Run: `pip-audit` for Python
   - Run: `npm audit` for frontend
   - Fix all critical/high vulnerabilities
3. **Manual Penetration Testing**
   - Test JWT tampering
   - Test session hijacking
   - Test RBAC bypass attempts
   - Test PHI exposure in logs/responses
4. **Document Findings**
   - Create security report
   - Fix all critical issues
   - Document mitigation for medium/low

**Acceptance Criteria**:
- [ ] No critical vulnerabilities
- [ ] No high vulnerabilities
- [ ] All secrets in environment variables
- [ ] Security report documented
- [ ] Fixes committed

**Files Created/Modified**:
- `docs/security/audit-report.md`
- Multiple files (security fixes)

**Estimated Time**: 8 hours

**Testing**:
- Manual security testing

---

### Task 7.6: Create API Documentation

**Goal**: Complete OpenAPI specification and user guide

**Prerequisites**:
- All APIs completed

**Steps**:
1. **Review OpenAPI Spec**
   - Access http://localhost:8000/docs
   - Verify all endpoints documented
   - Add descriptions and examples
   - Add response schemas
2. **Create API Guide**
   - Create `docs/api/README.md`
   - Authentication guide
   - Common workflows
   - Error codes reference
   - Rate limiting (if applicable)
3. **Test Examples**
   - Run all curl examples in documentation
   - Verify responses match documentation

**Acceptance Criteria**:
- [ ] OpenAPI spec complete
- [ ] All endpoints have descriptions
- [ ] All request/response schemas documented
- [ ] Examples tested and working
- [ ] API guide published

**Files Created/Modified**:
- `docs/api/README.md`
- `backend/app/api/v1/endpoints/*.py` (add docstrings)

**Estimated Time**: 4 hours

**Testing**:
- Manual: Test all documented examples

---

### Task 7.7: Create Deployment Documentation

**Goal**: Installation, configuration, and maintenance guides

**Prerequisites**:
- All features completed

**Steps**:
1. **Create Installation Guide**
   - Create `docs/deployment/installation.md`
   - Prerequisites (Docker, models)
   - Installation steps
   - First-time setup
   - Verification
2. **Create Configuration Guide**
   - Create `docs/deployment/configuration.md`
   - Environment variables
   - Database setup
   - MedCAT configuration
   - Security settings
3. **Create Maintenance Guide**
   - Create `docs/deployment/maintenance.md`
   - Backup procedures
   - Restore procedures
   - Log rotation
   - Monitoring
   - Troubleshooting

**Acceptance Criteria**:
- [ ] Installation guide complete
- [ ] Configuration guide complete
- [ ] Maintenance guide complete
- [ ] All guides tested from scratch
- [ ] Common issues documented

**Files Created/Modified**:
- `docs/deployment/installation.md`
- `docs/deployment/configuration.md`
- `docs/deployment/maintenance.md`

**Estimated Time**: 5 hours

**Testing**:
- Manual: Follow installation guide on fresh machine

---

### Task 7.8: Create User Documentation

**Goal**: Clinician and admin user guides

**Prerequisites**:
- All UI completed

**Steps**:
1. **Create Clinician Guide**
   - Create `docs/users/clinician-guide.md`
   - Login and navigation
   - Document upload
   - Patient search
   - Viewing results
   - Break-glass access
2. **Create Admin Guide**
   - Create `docs/users/admin-guide.md`
   - User management
   - Project management
   - Module configuration
   - Audit log review
   - Incident management
3. **Add Screenshots**
   - Capture screenshots for each workflow
   - Add to documentation

**Acceptance Criteria**:
- [ ] Clinician guide complete with screenshots
- [ ] Admin guide complete with screenshots
- [ ] Guides reviewed by non-technical user
- [ ] Feedback incorporated

**Files Created/Modified**:
- `docs/users/clinician-guide.md`
- `docs/users/admin-guide.md`
- `docs/users/screenshots/*.png`

**Estimated Time**: 4 hours

**Testing**:
- Manual: Non-technical user follows guide

---

### Task 7.9: Create Production Deployment Checklist

**Goal**: Step-by-step checklist for production deployment

**Prerequisites**:
- Task 7.7 completed

**Steps**:
1. **Create Checklist**
   - Create `docs/deployment/production-checklist.md`
   - Pre-deployment: backups, testing, security review
   - Deployment: steps in order
   - Post-deployment: verification, monitoring, rollback plan
2. **Test Checklist**
   - Run through checklist on staging environment
   - Update based on gaps found

**Acceptance Criteria**:
- [ ] Checklist complete
- [ ] Checklist tested on staging
- [ ] Rollback plan documented
- [ ] Contact information included

**Files Created/Modified**:
- `docs/deployment/production-checklist.md`

**Estimated Time**: 2 hours

**Testing**:
- Manual: Run through checklist on staging

---

### Task 7.10: First Production Deployment

**Goal**: Deploy to production workstation

**Prerequisites**:
- All previous tasks completed
- Production workstation ready
- Backups configured

**Steps**:
1. **Pre-Deployment**
   - Run all tests locally
   - Run security audit
   - Create backup of existing system (if any)
   - Review checklist
2. **Deployment**
   - Follow production checklist
   - Install Docker and dependencies
   - Download MedCAT models
   - Configure environment variables
   - Run `docker-compose up -d`
   - Run first-time setup script
   - Run verification script
3. **Post-Deployment**
   - Test login as admin
   - Test document upload
   - Test patient search
   - Verify audit logs
   - Monitor performance
   - Document any issues

**Acceptance Criteria**:
- [ ] All services running
- [ ] Health checks passing
- [ ] Admin can login
- [ ] Document upload works
- [ ] MedCAT processing works
- [ ] Patient search works
- [ ] Performance targets met (P95 <500ms)
- [ ] No critical errors in logs

**Files Created/Modified**:
- Production `.env` file
- `docs/deployment/production-deployment-log.md` (deployment notes)

**Estimated Time**: 6 hours

**Testing**:
- Manual: Complete production verification

---

## Summary

**Total Tasks**: ~90 tasks across 8 phases
**Total Estimated Time**: ~310 hours (11 weeks, 2 developers)
**Average Task Time**: ~3.4 hours

### Phase Summary

| Phase | Tasks | Hours | Weeks |
|-------|-------|-------|-------|
| Phase 0: Environment Setup | 7 | 20 | 0.5 |
| Phase 1: Core Infrastructure | 12 | 60 | 1.5 |
| Phase 2: User & Project Management | 7 | 30 | 1 |
| Phase 3: Document Upload & PHI Extraction | 12 | 40 | 1 |
| Phase 4: Module System & Patient Search | 4+ | 50 | 1.5 |
| Phase 5: Session Security & Break-Glass | 6 | 30 | 1 |
| Phase 6: Data Retention & Clinical Safety | 5 | 30 | 1 |
| Phase 7: Testing & Deployment | 10 | 50 | 1.5 |

### Implementation Order

**Sequential Phases**: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7

**Parallel Opportunities**:
- Frontend tasks can run parallel to backend (within same phase)
- Testing tasks (7.1-7.3) can run parallel
- Documentation tasks (7.6-7.8) can run parallel

### Success Metrics

- [ ] All 90 tasks completed
- [ ] Test coverage ≥80% (≥90% for critical paths)
- [ ] Performance: P95 API calls <500ms
- [ ] Security: 0 critical vulnerabilities
- [ ] Deployment: Production running successfully
- [ ] Documentation: Complete user and deployment guides

---

**Next Steps**:
1. Assign tasks to developers
2. Begin Phase 0: Environment Setup
3. Track progress in project management tool
4. Update task status as completed
5. Document any deviations or issues in CONTEXT.md

**Good luck with the implementation!** 🚀
