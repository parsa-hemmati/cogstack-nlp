# Skill: Technical Plan to Task Breakdown

**Purpose**: Convert technical plans into actionable implementation tasks following Test-Driven Development (TDD)

**Domain**: Agile Development, Task Planning, Test-Driven Development, Healthcare Software

**When to Use**:
- After technical plan approval
- Before implementation begins
- When estimating development effort
- When planning sprints

**Skill Type**: Planning & Execution

---

## Core Expertise

This skill guides you in converting `.specify/plans/*.md` files into granular task lists (`.specify/tasks/*.md`) that developers can execute sequentially or in parallel.

### Task Breakdown Principles

1. **Granular Tasks**: Each task completable in 1-2 hours
2. **TDD Approach**: Write tests first, then implementation
3. **Clear Dependencies**: Explicit prerequisites for each task
4. **Independent When Possible**: Maximize parallel execution
5. **Specific Acceptance Criteria**: Measurable definition of "done"
6. **Atomic Commits**: Each task = one git commit

---

## Task Template Structure

```markdown
# Tasks: {Feature Name}

**Plan Reference**: `.specify/plans/{feature-name}-plan.md`
**Estimated Total Time**: {X hours}
**Dependencies**: {External dependencies or prerequisites}

---

## Task {N}: {Short Descriptive Title}

**Goal**: {What this task accomplishes in 1-2 sentences}

**Prerequisites**:
- {What must exist before starting this task}
- {Completed tasks this depends on}

**Steps**:
1. **Write tests** (TDD approach)
   - {Specific test file to create}
   - {What test cases to write}
2. **Implement**
   - {Specific file(s) to create/modify}
   - {What code to write}
3. **Verify**
   - {How to run tests}
   - {Expected test output}

**Acceptance Criteria**:
- [ ] {Specific, testable criterion}
- [ ] {Another criterion}
- [ ] All tests passing
- [ ] Code coverage ≥ 80% for new code

**Files Created/Modified**:
- `{path/to/file.py}` - {Description}
- `tests/{path/to/test_file.py}` - {Test description}

**Estimated Time**: {X hours}

**Testing**:
- Unit tests: {Number of tests}
- Integration tests: {Number if applicable}
- Manual testing: {Steps if needed}

---
```

---

## Example: Breaking Down "User Authentication" Feature

### From Technical Plan → Task List

**Technical Plan Summary**:
- JWT-based authentication
- PostgreSQL users table
- Login endpoint
- Token validation middleware
- Password hashing with bcrypt

**Task Breakdown**:

```markdown
# Tasks: User Authentication

**Plan Reference**: `.specify/plans/authentication-plan.md`
**Estimated Total Time**: 12 hours
**Dependencies**: PostgreSQL database running, Alembic migrations configured

---

## Task 1: Create Users Database Table

**Goal**: Create users table with UUID primary keys, email/username fields, and audit timestamps

**Prerequisites**:
- PostgreSQL container running (docker-compose up postgres)
- Alembic configured in project

**Steps**:
1. **Write migration**
   - Create Alembic migration file: `alembic revision -m "create_users_table"`
   - Add users table DDL (id, username, email, password_hash, role, is_active, created_at, updated_at)
   - Add indexes (email, username, role)
   - Add constraints (email format, username min length)
2. **Test migration**
   - Run `alembic upgrade head`
   - Verify table created: `psql -c "\d users"`
   - Run `alembic downgrade -1`
   - Verify table dropped
3. **Document schema**
   - Add SQL schema to technical plan

**Acceptance Criteria**:
- [ ] Migration file created in `alembic/versions/`
- [ ] `upgrade()` function creates users table with all fields
- [ ] `downgrade()` function drops users table
- [ ] Indexes created on email, username, role
- [ ] Check constraints added (email format, username length)
- [ ] Migration runs successfully: `alembic upgrade head`
- [ ] Migration rolls back successfully: `alembic downgrade -1`

**Files Created/Modified**:
- `alembic/versions/001_create_users_table.py` - Database migration

**Estimated Time**: 1 hour

**Testing**:
- Manual: Run migration up/down, verify with `\d users`

---

## Task 2: Create User Model (SQLAlchemy)

**Goal**: Create SQLAlchemy User model class with relationships and helper methods

**Prerequisites**:
- Task 1 completed (users table exists)

**Steps**:
1. **Write model tests first** (TDD)
   - Create `tests/unit/models/test_user.py`
   - Test: User creation with valid data
   - Test: Email validation (invalid format raises error)
   - Test: Username minimum length validation
   - Test: Password hashing (password_hash != plain password)
   - Test: `verify_password()` method works
2. **Implement User model**
   - Create `app/models/user.py`
   - Add User class inheriting from Base
   - Add fields: id, username, email, password_hash, role, is_active, created_at, updated_at
   - Add `set_password()` method (bcrypt hashing)
   - Add `verify_password()` method (bcrypt verification)
3. **Run tests**
   - `pytest tests/unit/models/test_user.py -v`
   - All tests should pass

**Acceptance Criteria**:
- [ ] User model class created in `app/models/user.py`
- [ ] All fields match database schema
- [ ] `set_password()` method hashes password with bcrypt
- [ ] `verify_password()` method validates password
- [ ] Email validation using Pydantic validator
- [ ] Username min length = 3 characters
- [ ] Unit tests written and passing (5 tests minimum)
- [ ] Test coverage ≥ 90% for user.py

**Files Created/Modified**:
- `app/models/user.py` - User SQLAlchemy model
- `app/models/__init__.py` - Export User model
- `tests/unit/models/test_user.py` - Unit tests for User model

**Estimated Time**: 1.5 hours

**Testing**:
```bash
pytest tests/unit/models/test_user.py -v --cov=app/models/user
```

Expected: 5+ tests passing, coverage ≥90%

---

## Task 3: Create User Pydantic Schemas

**Goal**: Create Pydantic schemas for User API request/response validation

**Prerequisites**:
- Task 2 completed (User model exists)

**Steps**:
1. **Write schema tests first** (TDD)
   - Create `tests/unit/schemas/test_user_schemas.py`
   - Test: UserCreate validates email format
   - Test: UserCreate requires password (min 8 chars)
   - Test: UserResponse excludes password_hash
   - Test: UserUpdate allows partial updates
2. **Implement schemas**
   - Create `app/schemas/user.py`
   - Add `UserBase` (shared fields: username, email)
   - Add `UserCreate` (inherits UserBase, adds password)
   - Add `UserUpdate` (all fields optional)
   - Add `UserResponse` (inherits UserBase, adds id, role, created_at, excludes password)
3. **Run tests**
   - `pytest tests/unit/schemas/test_user_schemas.py -v`

**Acceptance Criteria**:
- [ ] UserBase schema with common fields
- [ ] UserCreate schema with password validation (min 8 chars, required)
- [ ] UserUpdate schema with all optional fields
- [ ] UserResponse schema without password_hash field
- [ ] Email validation using Pydantic validator
- [ ] Unit tests written and passing (4+ tests)
- [ ] Test coverage ≥ 85% for user schemas

**Files Created/Modified**:
- `app/schemas/user.py` - Pydantic User schemas
- `app/schemas/__init__.py` - Export User schemas
- `tests/unit/schemas/test_user_schemas.py` - Unit tests

**Estimated Time**: 1 hour

**Testing**:
```bash
pytest tests/unit/schemas/test_user_schemas.py -v --cov=app/schemas/user
```

---

## Task 4: Implement JWT Token Generation

**Goal**: Create JWT token creation and validation functions

**Prerequisites**:
- Task 2 completed (User model exists)
- Environment variable `JWT_SECRET_KEY` set

**Steps**:
1. **Write JWT tests first** (TDD)
   - Create `tests/unit/security/test_jwt.py`
   - Test: `create_access_token()` returns valid JWT
   - Test: `verify_token()` validates correct token
   - Test: `verify_token()` rejects expired token
   - Test: `verify_token()` rejects invalid signature
2. **Implement JWT functions**
   - Create `app/security/jwt.py`
   - Add `create_access_token(user_id, role)` → JWT string
   - Add `verify_token(token)` → user_id or None
   - Use python-jose library (HS256 algorithm)
   - Set token expiry: 8 hours
3. **Run tests**
   - `pytest tests/unit/security/test_jwt.py -v`

**Acceptance Criteria**:
- [ ] `create_access_token()` creates JWT with sub (user_id), role, exp, iat, jti
- [ ] Token expiry set to 8 hours from creation
- [ ] `verify_token()` decodes valid tokens successfully
- [ ] `verify_token()` returns None for expired/invalid tokens
- [ ] Secret key loaded from environment variable
- [ ] Unit tests written and passing (4+ tests)
- [ ] Test coverage ≥ 90%

**Files Created/Modified**:
- `app/security/jwt.py` - JWT token functions
- `app/security/__init__.py` - Export JWT functions
- `tests/unit/security/test_jwt.py` - Unit tests

**Estimated Time**: 1.5 hours

**Testing**:
```bash
pytest tests/unit/security/test_jwt.py -v --cov=app/security/jwt
```

---

## Task 5: Create Login Endpoint

**Goal**: Implement POST /api/v1/auth/login endpoint with password validation and JWT token generation

**Prerequisites**:
- Task 1-4 completed (User model, schemas, JWT functions exist)
- Database has at least one test user

**Steps**:
1. **Write endpoint tests first** (TDD)
   - Create `tests/integration/test_auth_endpoints.py`
   - Test: Login with valid credentials returns 200 + token
   - Test: Login with invalid password returns 401
   - Test: Login with non-existent user returns 401
   - Test: Token from login response is valid JWT
2. **Implement login endpoint**
   - Create `app/routers/auth.py`
   - Add `POST /api/v1/auth/login` route
   - Validate username/password in request body (Pydantic schema)
   - Query database for user by username
   - Verify password using `user.verify_password()`
   - Create JWT token using `create_access_token()`
   - Return `{"access_token": token, "token_type": "bearer"}`
3. **Test endpoint**
   - `pytest tests/integration/test_auth_endpoints.py -v`
   - Manual test: `curl -X POST http://localhost:8000/api/v1/auth/login -d '{"username":"test","password":"password123"}'`

**Acceptance Criteria**:
- [ ] POST /api/v1/auth/login endpoint created
- [ ] Request body validated (username, password required)
- [ ] Password verification using bcrypt
- [ ] JWT token returned on success
- [ ] 401 error for invalid credentials
- [ ] Integration tests written and passing (4+ tests)
- [ ] Manual curl test successful

**Files Created/Modified**:
- `app/routers/auth.py` - Authentication endpoints
- `app/main.py` - Include auth router
- `tests/integration/test_auth_endpoints.py` - Integration tests

**Estimated Time**: 2 hours

**Testing**:
```bash
# Integration tests
pytest tests/integration/test_auth_endpoints.py -v

# Manual test
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Expected response:
# {"access_token": "eyJ...", "token_type": "bearer", "expires_at": "2025-11-09T00:00:00Z"}
```

---

## Task 6: Create Authentication Dependency

**Goal**: Create FastAPI dependency for token validation on protected endpoints

**Prerequisites**:
- Task 4 completed (JWT functions exist)
- Task 5 completed (login endpoint works)

**Steps**:
1. **Write dependency tests first** (TDD)
   - Create `tests/unit/dependencies/test_auth.py`
   - Test: `get_current_user()` returns User for valid token
   - Test: `get_current_user()` raises 401 for missing token
   - Test: `get_current_user()` raises 401 for invalid token
   - Test: `get_current_user()` raises 401 for expired token
2. **Implement dependency**
   - Create `app/dependencies/auth.py`
   - Add `get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db))` → User
   - Extract token from Authorization header
   - Verify token using `verify_token()`
   - Query database for user
   - Raise HTTPException(401) if invalid
3. **Test dependency**
   - `pytest tests/unit/dependencies/test_auth.py -v`

**Acceptance Criteria**:
- [ ] `get_current_user()` dependency created
- [ ] Extracts token from Authorization header (Bearer scheme)
- [ ] Validates token using `verify_token()`
- [ ] Queries database for user by ID from token
- [ ] Returns User object if valid
- [ ] Raises HTTPException(401) for invalid/missing/expired token
- [ ] Unit tests written and passing (4+ tests)

**Files Created/Modified**:
- `app/dependencies/auth.py` - Authentication dependency
- `app/dependencies/__init__.py` - Export dependency
- `tests/unit/dependencies/test_auth.py` - Unit tests

**Estimated Time**: 1.5 hours

**Testing**:
```bash
pytest tests/unit/dependencies/test_auth.py -v --cov=app/dependencies/auth
```

---

## Task 7: Create Protected Endpoint Example

**Goal**: Create GET /api/v1/users/me endpoint (requires authentication) as example

**Prerequisites**:
- Task 6 completed (authentication dependency exists)

**Steps**:
1. **Write endpoint tests first** (TDD)
   - Add to `tests/integration/test_auth_endpoints.py`
   - Test: GET /users/me with valid token returns 200 + user data
   - Test: GET /users/me without token returns 401
   - Test: GET /users/me with invalid token returns 401
2. **Implement endpoint**
   - Add to `app/routers/auth.py`
   - Add `GET /api/v1/users/me` route
   - Use `current_user: User = Depends(get_current_user)` dependency
   - Return UserResponse schema (excludes password)
3. **Test endpoint**
   - `pytest tests/integration/test_auth_endpoints.py::test_get_current_user -v`
   - Manual test with curl using token from login

**Acceptance Criteria**:
- [ ] GET /api/v1/users/me endpoint created
- [ ] Requires valid JWT token in Authorization header
- [ ] Returns current user data (UserResponse schema)
- [ ] 401 error if token missing/invalid
- [ ] Integration tests written and passing (3+ tests)
- [ ] Manual curl test successful

**Files Created/Modified**:
- `app/routers/auth.py` - Add /users/me endpoint
- `tests/integration/test_auth_endpoints.py` - Add tests

**Estimated Time**: 1 hour

**Testing**:
```bash
# Get token first
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}' | jq -r '.access_token')

# Test protected endpoint
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# Expected: {"id": "...", "username": "testuser", "email": "...", "role": "clinician"}
```

---

## Task 8: Add Audit Logging for Authentication

**Goal**: Log all login attempts (success and failure) to audit_logs table

**Prerequisites**:
- Task 5 completed (login endpoint exists)
- Audit logs table exists in database

**Steps**:
1. **Write audit logging tests**
   - Add to `tests/integration/test_auth_endpoints.py`
   - Test: Successful login creates audit log entry (action: LOGIN_SUCCESS)
   - Test: Failed login creates audit log entry (action: LOGIN_FAILURE)
   - Test: Audit log includes IP address and user-agent
2. **Implement audit logging**
   - Create `app/services/audit_service.py`
   - Add `log_auth_attempt(username, success, ip, user_agent, details)`
   - Modify login endpoint to call audit service
   - Log both success and failure
3. **Test audit logging**
   - `pytest tests/integration/test_auth_endpoints.py -v`
   - Manual: Query audit_logs table after login

**Acceptance Criteria**:
- [ ] AuditService class created with `log_auth_attempt()` method
- [ ] Login endpoint logs successful attempts (action: LOGIN_SUCCESS)
- [ ] Login endpoint logs failed attempts (action: LOGIN_FAILURE)
- [ ] Audit logs include IP address from request
- [ ] Audit logs include user-agent from request headers
- [ ] Integration tests verify audit logs created (2+ tests)
- [ ] Manual verification: SELECT * FROM audit_logs shows entries

**Files Created/Modified**:
- `app/services/audit_service.py` - Audit logging service
- `app/routers/auth.py` - Add audit logging calls
- `tests/integration/test_auth_endpoints.py` - Add audit tests

**Estimated Time**: 1.5 hours

**Testing**:
```bash
# Run integration tests
pytest tests/integration/test_auth_endpoints.py::test_login_audit_logging -v

# Manual verification
docker-compose exec postgres psql -U clinicaltools -d clinical_care_tools \
  -c "SELECT action, username, ip_address, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 5;"
```

---

## Summary

**Total Tasks**: 8
**Total Estimated Time**: 12 hours
**Parallel Tasks**: Tasks 3 and 4 can run in parallel (both depend on Task 2)
**Critical Path**: Task 1 → Task 2 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8

**Dependencies Graph**:
```
Task 1 (Users table)
  ↓
Task 2 (User model)
  ├─→ Task 3 (Schemas)
  └─→ Task 4 (JWT)
        ↓
      Task 5 (Login endpoint)
        ↓
      Task 6 (Auth dependency)
        ↓
      Task 7 (Protected endpoint)
        ↓
      Task 8 (Audit logging)
```
```

---

## Task Breakdown Guidelines

### 1. Identify Implementation Units

From the technical plan, identify logical units of work:
- Database tables/migrations
- Models (SQLAlchemy, Pydantic)
- Services/business logic
- API endpoints
- Frontend components
- Integration points
- Tests
- Documentation

### 2. Order by Dependency

Create dependency graph:
- Database schema first (migrations)
- Models next (ORM classes)
- Services (business logic)
- API endpoints (routes)
- Frontend (components, views)
- Tests alongside each unit

### 3. Size Appropriately

**Too large** (>2 hours):
- "Implement patient search feature" → Break into: API endpoint, frontend component, search service, tests

**Too small** (<30 minutes):
- "Add import statement" → Combine with related task

**Just right** (1-2 hours):
- "Create User model with password hashing and validation tests"
- "Implement login endpoint with JWT token generation"
- "Create patient search API endpoint with pagination"

### 4. Write Clear Acceptance Criteria

**Bad** (vague):
- ✗ "Code works"
- ✗ "Tests pass"

**Good** (specific, measurable):
- ✓ "Login endpoint returns 200 status code with valid JWT token containing user_id, role, and 8-hour expiry"
- ✓ "Password validation rejects passwords shorter than 8 characters with error message 'Password must be at least 8 characters'"
- ✓ "Unit test coverage ≥ 85% for auth.py module"

### 5. Specify Test Requirements

For each task, define:
- Number of unit tests expected
- Integration tests needed
- E2E tests (if applicable)
- Coverage target (usually ≥80%)
- Manual testing steps

### 6. Use TDD Order

**Always**:
1. Write tests first (TDD)
2. Implement to pass tests
3. Refactor if needed
4. Verify tests still pass

### 7. Document Files Changed

List all files created/modified:
- Source files
- Test files
- Migration files
- Configuration files

This helps with:
- Code review scoping
- Git commit atomicity
- Merge conflict prevention

---

## Common Task Patterns

### Pattern: Database Table Creation

```markdown
## Task: Create {Table Name} Table

**Goal**: Create {table_name} table with {key features}

**Steps**:
1. Write Alembic migration
2. Test migration (up and down)
3. Document schema in plan

**Acceptance Criteria**:
- [ ] Migration file created
- [ ] All fields, indexes, constraints defined
- [ ] Migration runs successfully
- [ ] Downgrade works

**Estimated Time**: 1 hour
```

### Pattern: Model Implementation

```markdown
## Task: Create {Model Name} Model

**Goal**: Create SQLAlchemy {Model} class with {features}

**Steps**:
1. Write model unit tests (TDD)
2. Implement model class
3. Run tests

**Acceptance Criteria**:
- [ ] Model class created
- [ ] All fields match database
- [ ] Helper methods implemented
- [ ] Unit tests passing (X+ tests)
- [ ] Coverage ≥ 90%

**Estimated Time**: 1.5 hours
```

### Pattern: API Endpoint

```markdown
## Task: Create {Endpoint} API Endpoint

**Goal**: Implement {METHOD} {path} endpoint for {purpose}

**Steps**:
1. Write integration tests (TDD)
2. Implement endpoint
3. Add to OpenAPI docs
4. Test manually

**Acceptance Criteria**:
- [ ] Endpoint created
- [ ] Request/response validation
- [ ] Error handling (4xx, 5xx)
- [ ] Integration tests passing
- [ ] OpenAPI docs updated
- [ ] Manual curl test successful

**Estimated Time**: 2 hours
```

### Pattern: Frontend Component

```markdown
## Task: Create {Component} Vue Component

**Goal**: Build {ComponentName} component for {purpose}

**Steps**:
1. Write component unit tests (Vitest)
2. Implement component (Composition API + TypeScript)
3. Add to Storybook (if applicable)
4. Test in browser

**Acceptance Criteria**:
- [ ] Component created with <script setup lang="ts">
- [ ] Props typed with TypeScript
- [ ] Emits defined
- [ ] Unit tests passing (X+ tests)
- [ ] Accessibility (ARIA labels, keyboard nav)
- [ ] Visual testing in browser

**Estimated Time**: 2 hours
```

---

## Usage

When creating task breakdown from technical plan:

1. **Read technical plan completely**
2. **Extract implementation phases** (already ordered)
3. **Break each phase into tasks** (1-2 hours each)
4. **Define dependencies** (what must exist first)
5. **Write TDD steps** (tests first, then implementation)
6. **Set clear acceptance criteria** (specific, measurable)
7. **Estimate time** (realistic, add buffer)
8. **Review for completeness** (all plan sections covered)

**Output**: Save to `.specify/tasks/{feature-name}-tasks.md`

**Execution**: Implement tasks sequentially (or parallel if independent)

**Tracking**: Mark tasks completed as you go, update CONTEXT.md with each commit
