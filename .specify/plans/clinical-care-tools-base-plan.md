# Technical Plan: Clinical Care Tools Base Application

**Version**: 1.2.0
**Date**: 2025-11-08
**Status**: Ready for Implementation
**Author**: AI Assistant (Claude Code)
**Based on Specification**: `.specify/specifications/clinical-care-tools-base-app.md` (v1.1.0)

**Version History**:
- v1.0.0 (2025-11-08): Initial technical plan with 7 phases
- v1.1.0 (2025-11-08): Added Phase 0, Redis, deduplication, PHI tests, scaling strategy
- v1.2.0 (2025-11-08): Replaced custom MedCAT Service with CogStack-ModelServe, added CogStack-NiFi compatibility layer

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [API Design](#api-design)
4. [Database Schema & Migrations](#database-schema--migrations)
5. [Component Design](#component-design)
6. [Security Architecture](#security-architecture)
7. [MedCAT Integration](#medcat-integration)
8. [PHI Extraction Workflow](#phi-extraction-workflow)
9. [Testing Strategy](#testing-strategy)
10. [Deployment Architecture](#deployment-architecture)
11. [Performance Requirements](#performance-requirements)
12. [Risks & Mitigations](#risks--mitigations)
13. [Implementation Phases](#implementation-phases)

---

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│ Workstation (Windows/Linux + Docker)                                │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Docker Compose Network                                        │   │
│  │                                                                │   │
│  │  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐  │   │
│  │  │  Frontend   │      │  Backend    │      │ PostgreSQL  │  │   │
│  │  │  (Vue 3 +   │◀────▶│  (FastAPI)  │◀────▶│   15+       │  │   │
│  │  │   Vuetify)  │      │             │      │             │  │   │
│  │  │             │      │      │      │      │             │  │   │
│  │  │ :8080       │      │ :8000│      │      │ :5432       │  │   │
│  │  └─────────────┘      └──────┼──────┘      └─────────────┘  │   │
│  │                              │                                │   │
│  │                              ├──────────┐                     │   │
│  │                              ▼          ▼                     │   │
│  │                       ┌──────────────┐ ┌─────────────┐       │   │
│  │                       │ CogStack-    │ │   Redis     │       │   │
│  │                       │ ModelServe   │ │   7.2+      │       │   │
│  │                       │ (MedCAT NLP) │ │  (Sessions, │       │   │
│  │                       │ :8001        │ │   Cache)    │       │   │
│  │                       └──────────────┘ │ :6379       │       │   │
│  │                                        └─────────────┘       │   │
│  │                                                               │   │
│  │  Volumes:                                                     │   │
│  │  - postgres_data (persistent database)                       │   │
│  │  - redis_data (session store, cache)                         │   │
│  │  - medcat_models (CogStack-ModelServe models: SNOMED, DeID)  │   │
│  │  - backend_logs (application + audit logs)                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Remote Desktop Users (Clinicians via RDP/VNC)                 │   │
│  │                                                                │   │
│  │  User 1 ─┐                                                    │   │
│  │  User 2 ─┼─▶ Browser ──▶ http://localhost:8080               │   │
│  │  User 3 ─┘                                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### Frontend (Vue 3 + TypeScript + Vuetify)
- **Purpose**: User interface for clinicians and administrators
- **Key Features**:
  - Multi-user authentication (login/logout)
  - Project and task management interfaces
  - Module-specific UIs (patient search, timeline, CDS)
  - Admin configuration panel
  - User activity monitoring
- **Framework**: Vue 3.5 with Composition API, TypeScript, Vuetify 3.7
- **State Management**: Pinia for user/config/module state
- **Routing**: Vue Router 4 with authentication guards
- **HTTP Client**: Axios with interceptors for auth tokens

#### Backend (FastAPI + Python)
- **Purpose**: REST API, business logic, authentication, audit logging
- **Key Features**:
  - JWT-based authentication
  - Role-based access control (RBAC)
  - Comprehensive audit logging (WHO/WHAT/WHEN/WHERE)
  - Module registry and dynamic loading
  - CogStack-ModelServe client integration (NLP processing)
  - Background job processing (document processing)
  - RESTful API standardization (CogStack-NiFi compatible)
- **Framework**: FastAPI 0.115+ for async performance
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic for database schema management
- **Task Queue**: FastAPI BackgroundTasks for async jobs

#### Database (PostgreSQL)
- **Purpose**: Persistent storage for users, projects, tasks, audit logs
- **Key Features**:
  - ACID compliance for data integrity
  - JSONB for flexible configuration
  - UUID primary keys for distributed-ready design
  - Immutable audit logs (PostgreSQL rules)
  - Connection pooling (10 connections, max overflow 20)
- **Version**: PostgreSQL 15+
- **Backup Strategy**: Daily automated backups with 8-year retention

#### Redis
- **Purpose**: Session store, caching layer, future job queue
- **Key Features**:
  - Session storage with automatic expiration (TTL)
  - Cache for frequently accessed patient/concept data
  - Document deduplication tracking (SHA-256 hashes)
  - Pub/sub for future real-time notifications
  - Prepared for distributed session management
- **Version**: Redis 7.2+
- **Persistence**: RDB snapshots every 5 minutes, AOF for durability

#### CogStack-ModelServe
- **Purpose**: Production-ready NLP model serving for clinical document processing
- **Repository**: https://github.com/CogStack/CogStack-ModelServe
- **Key Features**:
  - Medical entity recognition with multiple models (SNOMED-CT, ICD-10, UMLS)
  - Meta-annotation classification (Negation, Temporality, Experiencer, Certainty)
  - De-identification (PII detection: names, NHS numbers, dates, addresses)
  - Concept linking to clinical terminologies
  - FastAPI-based REST API with automatic OpenAPI docs
  - Built-in authentication (token-based, optional for MVP)
  - Model versioning with MLflow integration (optional for MVP)
  - Monitoring with Grafana + Prometheus (optional for MVP)
- **Deployment**: Minimal deployment for MVP (core API only), full stack in Phase 2+
- **Integration**: REST API client (`POST /api/process` for single document, `POST /api/process_bulk` for batch)
- **Model Storage**: Shared volume accessible by all users
- **Port**: 8001 (vs standard 8000 to avoid conflict with backend)
- **Why CogStack-ModelServe**: Production-tested, actively maintained, comprehensive governance, saves ~20 hours of custom development

### Core + Modules Architecture

The application follows a **Core + Modules** pattern for extensibility:

**Core Responsibilities**:
- Authentication & authorization
- Audit logging
- User & project management
- Configuration management
- Module registry & dynamic loading
- Database connection management

**Module Responsibilities**:
- Feature-specific functionality (e.g., patient search)
- Feature-specific API endpoints
- Feature-specific database tables
- Feature-specific UI components
- Self-contained and independently deployable

**Module Registration Flow**:
1. Module defines `register_module(app)` function
2. Core discovers modules in `app/modules/` directory
3. Core calls `register_module()` on app startup
4. Module registers routes, permissions, migrations
5. Frontend loads module routes dynamically

---

## Technology Stack

### Backend Technologies

| Technology | Version | Rationale |
|------------|---------|-----------|
| **Python** | 3.10+ | CogStack-ModelServe compatibility, modern async/await, type hints |
| **FastAPI** | 0.115+ | Async, automatic OpenAPI docs, Pydantic validation, proven in CogStack-ModelServe |
| **Pydantic** | 2.0+ | Schema validation, serialization, type safety |
| **SQLAlchemy** | 2.0+ | ORM with async support, proven in production |
| **Alembic** | 1.13+ | Database migration management |
| **python-jose** | 3.3+ | JWT token generation/validation |
| **passlib** | 1.7+ | Password hashing with bcrypt |
| **httpx** | 0.27+ | Async HTTP client for CogStack-ModelServe API |
| **pytest** | 8.0+ | Testing framework with async support |
| **pytest-asyncio** | 0.23+ | Async test support |

### Frontend Technologies

| Technology | Version | Rationale |
|------------|---------|-----------|
| **Vue** | 3.5+ | Composition API, TypeScript support, proven in MedCAT Trainer (65 components) |
| **TypeScript** | 5.0+ | Type safety, IDE autocomplete, maintainability |
| **Vuetify** | 3.7+ | Material Design, proven healthcare UI patterns, comprehensive component library |
| **Pinia** | 2.0+ | State management with TypeScript support |
| **Axios** | 1.7+ | HTTP client with interceptors for auth tokens |
| **Vue Router** | 4.0+ | SPA routing with navigation guards |
| **Vite** | 6.3+ | Fast HMR, optimized builds, proven in MedCAT Trainer |
| **Vitest** | 2.0+ | Fast unit testing, Vite-native |
| **Playwright** | 1.45+ | E2E testing, cross-browser support |

### Infrastructure Technologies

| Technology | Version | Rationale |
|------------|---------|-----------|
| **Docker** | 24.0+ | Container runtime, proven in MedCAT ecosystem (29 compose files) |
| **Docker Compose** | 2.20+ | Multi-container orchestration for single workstation |
| **PostgreSQL** | 15+ | JSONB support, full-text search, ACID compliance, proven (95 migrations in Trainer) |
| **Redis** | 7.2+ | Session store, caching layer, job queue for future scaling |

### Alternatives Considered & Rejected

**Django REST Framework vs FastAPI**:
- ✅ **FastAPI chosen**: Faster (async-first), auto OpenAPI docs, lighter weight, Pydantic validation built-in
- ❌ Django DRF rejected: Heavier, sync-first (WSGI), requires separate OpenAPI tooling

**MongoDB vs PostgreSQL**:
- ✅ **PostgreSQL chosen**: ACID compliance critical for healthcare, JSONB provides flexibility, stronger relational integrity
- ❌ MongoDB rejected: Lacks transactional guarantees, harder audit trail, not proven in MedCAT ecosystem

**React vs Vue**:
- ✅ **Vue chosen**: Existing MedCAT Trainer uses Vue, team familiarity, 65 reusable components, simpler reactivity
- ❌ React rejected: Steeper learning curve, more boilerplate, no existing component library

**OIDC/Keycloak vs JWT**:
- ✅ **JWT chosen**: Simple for single workstation, no external dependencies, sufficient for 10 users
- ❌ OIDC rejected: Overly complex for single workstation, requires additional infrastructure

---

## API Design

### OpenAPI Specification Structure

All API endpoints will be documented using OpenAPI 3.1 specification. The complete spec will be auto-generated by FastAPI at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### API Versioning

- **Base URL**: `http://localhost:8000/api/v1`
- **Versioning Strategy**: URL-based (`/api/v1`, `/api/v2`)
- **Deprecation Policy**: v1 supported for minimum 12 months after v2 release

### Authentication Endpoints

#### POST /api/v1/auth/login

**Purpose**: User authentication with username/password

**Request**:
```json
{
  "username": "clinician1",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_at": "2025-11-09T00:00:00Z",
  "user": {
    "id": "uuid",
    "username": "clinician1",
    "email": "clinician1@hospital.com",
    "role": "clinician",
    "must_change_password": false
  }
}
```

**Errors**:
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account locked (too many failed attempts)
- `423 Locked`: Must change password on first login

**Audit Log**: Action `LOGIN_SUCCESS` or `LOGIN_FAILURE`

---

#### POST /api/v1/auth/logout

**Purpose**: Invalidate current session

**Headers**: `Authorization: Bearer {token}`

**Response** (200 OK):
```json
{
  "message": "Logged out successfully"
}
```

**Audit Log**: Action `LOGOUT`

---

#### GET /api/v1/auth/me

**Purpose**: Get current user information

**Headers**: `Authorization: Bearer {token}`

**Response** (200 OK):
```json
{
  "id": "uuid",
  "username": "clinician1",
  "email": "clinician1@hospital.com",
  "role": "clinician",
  "is_active": true,
  "last_login": "2025-11-08T12:00:00Z",
  "permissions": ["patient:search", "patient:view", "task:view"]
}
```

**Errors**:
- `401 Unauthorized`: Invalid/expired token

---

### User Management Endpoints

#### GET /api/v1/users

**Purpose**: List all users (admin only)

**Headers**: `Authorization: Bearer {token}`

**Query Parameters**:
- `page` (integer, default: 1)
- `page_size` (integer, default: 20, max: 100)
- `role` (string, optional): Filter by role
- `is_active` (boolean, optional): Filter by active status

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "uuid",
      "username": "clinician1",
      "email": "clinician1@hospital.com",
      "role": "clinician",
      "is_active": true,
      "last_login": "2025-11-08T12:00:00Z",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

**Errors**:
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not admin user

**Audit Log**: Action `USER_LIST`

---

#### POST /api/v1/users

**Purpose**: Create new user (admin only)

**Headers**: `Authorization: Bearer {token}`

**Request**:
```json
{
  "username": "clinician2",
  "email": "clinician2@hospital.com",
  "password": "TemporaryPassword123!",
  "role": "clinician"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "username": "clinician2",
  "email": "clinician2@hospital.com",
  "role": "clinician",
  "is_active": true,
  "must_change_password": true,
  "created_at": "2025-11-08T12:00:00Z"
}
```

**Errors**:
- `400 Bad Request`: Validation error (weak password, invalid email)
- `409 Conflict`: Username or email already exists
- `403 Forbidden`: Not admin user

**Audit Log**: Action `USER_CREATE`

---

#### GET /api/v1/users/{user_id}

**Purpose**: Get user details

**Headers**: `Authorization: Bearer {token}`

**Response** (200 OK):
```json
{
  "id": "uuid",
  "username": "clinician1",
  "email": "clinician1@hospital.com",
  "role": "clinician",
  "is_active": true,
  "last_login": "2025-11-08T12:00:00Z",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-11-08T12:00:00Z"
}
```

**Errors**:
- `404 Not Found`: User does not exist
- `403 Forbidden`: Cannot view other users (unless admin)

**Audit Log**: Action `USER_VIEW`

---

#### PATCH /api/v1/users/{user_id}

**Purpose**: Update user (partial update)

**Headers**: `Authorization: Bearer {token}`

**Request** (all fields optional):
```json
{
  "email": "newemail@hospital.com",
  "role": "researcher",
  "is_active": false
}
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "username": "clinician1",
  "email": "newemail@hospital.com",
  "role": "researcher",
  "is_active": false,
  "updated_at": "2025-11-08T12:30:00Z"
}
```

**Errors**:
- `404 Not Found`: User does not exist
- `403 Forbidden`: Cannot modify other users (unless admin)
- `409 Conflict`: Email already in use

**Audit Log**: Action `USER_UPDATE` with `details` showing changed fields

---

### Project Management Endpoints

#### GET /api/v1/projects

**Purpose**: List projects (user sees only their projects)

**Headers**: `Authorization: Bearer {token}`

**Query Parameters**:
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)
- `status` (string, optional): Filter by status
- `project_type` (string, optional): Filter by type

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Diabetes Patient Cohort",
      "description": "Identify all diabetes patients for quality improvement",
      "project_type": "patient_search",
      "status": "active",
      "created_at": "2025-01-01T00:00:00Z",
      "created_by": {
        "id": "uuid",
        "username": "admin1"
      },
      "member_count": 3
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

**Audit Log**: Action `PROJECT_LIST`

---

#### POST /api/v1/projects

**Purpose**: Create new project (admin only)

**Headers**: `Authorization: Bearer {token}`

**Request**:
```json
{
  "name": "Sepsis Early Detection",
  "description": "Identify sepsis cases in emergency department",
  "project_type": "patient_search",
  "configuration": {
    "search_criteria": ["sepsis", "septicemia"],
    "medcat_model": "umls_sm_v1"
  }
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "name": "Sepsis Early Detection",
  "description": "Identify sepsis cases in emergency department",
  "project_type": "patient_search",
  "status": "active",
  "configuration": {...},
  "created_at": "2025-11-08T12:00:00Z",
  "created_by": {
    "id": "uuid",
    "username": "admin1"
  }
}
```

**Errors**:
- `400 Bad Request`: Validation error
- `409 Conflict`: Project name already exists
- `403 Forbidden`: Not admin user

**Audit Log**: Action `PROJECT_CREATE`

---

#### POST /api/v1/projects/{project_id}/members

**Purpose**: Add user to project (admin or project owner)

**Headers**: `Authorization: Bearer {token}`

**Request**:
```json
{
  "user_id": "uuid",
  "role": "member"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "user_id": "uuid",
  "role": "member",
  "joined_at": "2025-11-08T12:00:00Z"
}
```

**Errors**:
- `404 Not Found`: Project or user does not exist
- `409 Conflict`: User already member of project
- `403 Forbidden`: Not authorized

**Audit Log**: Action `PROJECT_MEMBER_ADD`

---

### Task Management Endpoints

#### GET /api/v1/tasks

**Purpose**: List tasks for current user

**Headers**: `Authorization: Bearer {token}`

**Query Parameters**:
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)
- `status` (string, optional): Filter by status
- `project_id` (uuid, optional): Filter by project

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Review 100 diabetes cases",
      "description": "Validate MedCAT annotations",
      "task_type": "review",
      "status": "in_progress",
      "priority": "high",
      "due_date": "2025-11-15T00:00:00Z",
      "project": {
        "id": "uuid",
        "name": "Diabetes Patient Cohort"
      },
      "assigned_to": {
        "id": "uuid",
        "username": "clinician1"
      },
      "created_at": "2025-11-01T00:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

**Audit Log**: Action `TASK_LIST`

---

#### POST /api/v1/tasks

**Purpose**: Create new task (admin or project owner)

**Headers**: `Authorization: Bearer {token}`

**Request**:
```json
{
  "project_id": "uuid",
  "assigned_to": "uuid",
  "name": "Annotate 50 clinical notes",
  "description": "Review and correct MedCAT annotations",
  "task_type": "annotation",
  "priority": "medium",
  "due_date": "2025-11-20T00:00:00Z",
  "configuration": {
    "document_ids": ["uuid1", "uuid2"],
    "annotation_guidelines_url": "http://..."
  }
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "assigned_to": {...},
  "name": "Annotate 50 clinical notes",
  "status": "pending",
  "created_at": "2025-11-08T12:00:00Z"
}
```

**Errors**:
- `400 Bad Request`: Validation error
- `404 Not Found`: Project or user does not exist
- `403 Forbidden`: Not authorized

**Audit Log**: Action `TASK_CREATE`

---

#### PATCH /api/v1/tasks/{task_id}

**Purpose**: Update task (assignee or admin)

**Headers**: `Authorization: Bearer {token}`

**Request** (all fields optional):
```json
{
  "status": "complete",
  "completed_at": "2025-11-08T12:00:00Z"
}
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "status": "complete",
  "completed_at": "2025-11-08T12:00:00Z",
  "updated_at": "2025-11-08T12:00:00Z"
}
```

**Errors**:
- `404 Not Found`: Task does not exist
- `403 Forbidden`: Not authorized (not assignee or admin)

**Audit Log**: Action `TASK_UPDATE` with changed fields

---

### Audit Log Endpoints

#### GET /api/v1/audit-logs

**Purpose**: Query audit logs (admin only)

**Headers**: `Authorization: Bearer {token}`

**Query Parameters**:
- `page` (integer, default: 1)
- `page_size` (integer, default: 50, max: 200)
- `user_id` (uuid, optional): Filter by user
- `action` (string, optional): Filter by action
- `resource_type` (string, optional): Filter by resource type
- `start_date` (ISO datetime, optional): Filter by date range
- `end_date` (ISO datetime, optional): Filter by date range

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "username": "clinician1",
      "action": "PATIENT_VIEW",
      "resource_type": "patient",
      "resource_id": "P12345",
      "resource_name": "John Doe (NHS: 1234567890)",
      "details": {
        "search_query": "diabetes"
      },
      "ip_address": "192.168.1.100",
      "session_id": "uuid",
      "timestamp": "2025-11-08T12:00:00Z"
    }
  ],
  "total": 1000,
  "page": 1,
  "page_size": 50,
  "pages": 20
}
```

**Errors**:
- `403 Forbidden`: Not admin user

**Audit Log**: Action `AUDIT_LOG_QUERY` (log who queries logs)

---

### Module Endpoints

#### GET /api/v1/modules

**Purpose**: List installed modules

**Headers**: `Authorization: Bearer {token}`

**Response** (200 OK):
```json
{
  "modules": [
    {
      "id": "uuid",
      "name": "patient-search",
      "display_name": "Patient Search",
      "description": "Search for patients by medical concepts",
      "version": "1.0.0",
      "is_enabled": true,
      "permissions": ["patient:search", "patient:view"],
      "routes": [
        {"path": "/patient-search", "name": "Patient Search"}
      ]
    }
  ]
}
```

**Audit Log**: Action `MODULE_LIST`

---

#### PATCH /api/v1/modules/{module_id}

**Purpose**: Enable/disable module (admin only)

**Headers**: `Authorization: Bearer {token}`

**Request**:
```json
{
  "is_enabled": false
}
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "name": "patient-search",
  "is_enabled": false,
  "updated_at": "2025-11-08T12:00:00Z"
}
```

**Errors**:
- `404 Not Found`: Module does not exist
- `403 Forbidden`: Not admin user

**Audit Log**: Action `MODULE_UPDATE`

---

### Health & Status Endpoints

#### GET /health

**Purpose**: Health check endpoint (no auth required)

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-08T12:00:00Z",
  "services": {
    "database": "healthy",
    "medcat_service": "healthy"
  }
}
```

**Use Case**: Docker health checks, monitoring systems

---

#### GET /api/v1/version

**Purpose**: Get application version information

**Response** (200 OK):
```json
{
  "version": "1.0.0",
  "build_date": "2025-11-08",
  "commit": "abc123de",
  "environment": "production"
}
```

---

### Error Response Format

All error responses follow this format:

```json
{
  "detail": "User-friendly error message",
  "error_code": "ENTITY_NOT_FOUND",
  "field_errors": {
    "email": ["Invalid email format"]
  },
  "request_id": "abc123def456",
  "timestamp": "2025-11-08T12:00:00Z"
}
```

**Standard Error Codes**:
- `ENTITY_NOT_FOUND` (404): Resource does not exist
- `VALIDATION_ERROR` (400): Request validation failed
- `AUTHENTICATION_REQUIRED` (401): Missing or invalid token
- `PERMISSION_DENIED` (403): Insufficient permissions
- `CONFLICT` (409): Resource conflict (duplicate)
- `RATE_LIMIT_EXCEEDED` (429): Too many requests
- `INTERNAL_SERVER_ERROR` (500): Unexpected server error

---

## Database Schema & Migrations

### Migration Strategy

**Tool**: Alembic for SQLAlchemy migrations

**Migration Naming Convention**:
```
001_create_users_table.py
002_create_projects_tables.py
003_create_audit_logs_table.py
004_add_session_security_fields.py
```

**Migration Process**:
1. Create migration: `alembic revision -m "description"`
2. Implement `upgrade()` and `downgrade()` functions
3. Test migration: `alembic upgrade head`
4. Test rollback: `alembic downgrade -1`
5. Commit migration file to git

**Backward Compatibility**:
- Additive changes only (no breaking changes in v1.x)
- Provide data migrations for schema changes
- Test rollback path for every migration

### Core Database Tables

See specification section 7 (Database Schema) for complete DDL.

**Summary of Core Tables**:
1. **users** - User accounts with authentication
2. **projects** - Project definitions
3. **project_members** - User membership in projects
4. **tasks** - Work assignments for users
5. **audit_logs** - Immutable audit trail
6. **modules** - Installed module registry
7. **sessions** - Active user sessions (JWT tracking)

### PHI Extraction Tables

**documents**:
- Stores encrypted RTF clinical documents (~50KB)
- AES-256 encryption at rest
- SHA-256 hash for deduplication
- Links to `uploaded_by` user

**extracted_entities**:
- Structured data from MedCAT processing
- PHI entities (NHS number, name, DOB, address)
- Clinical entities (conditions, medications, procedures)
- Meta-annotations (Negation, Experiencer, Temporality, Certainty)
- Links to `source_document_id`

**patients**:
- Aggregated patient records
- Primary matching via NHS number (10 digits)
- Fallback matching via fuzzy name + DOB matching
- Links to `source_document_ids` array (JSONB)

### Clinical Safety Tables

**clinical_overrides**:
- Tracks clinician disagreements with system
- System value vs override value
- Reason and severity tracking
- Reviewed flag for quality improvement

**critical_findings**:
- Urgent clinical alerts (sepsis, acute MI, critical labs)
- Acknowledged flag
- Auto-escalation if not acknowledged within 4 hours
- Expires after 48 hours

**clinical_incidents**:
- Incident reporting integration
- Incident type, severity, hospital incident ID
- Investigated flag for clinical governance

### Session Security Tables

Enhanced `sessions` table with:
- `ip_address_hash` - SHA-256 of IP address
- `user_agent_hash` - SHA-256 of user-agent
- `is_suspicious` - Flag for suspicious activity
- `suspicious_change_count` - Count of IP/UA changes
- `force_logout` - Admin force logout flag
- `force_logout_reason` - Reason for force logout
- `force_logout_by` - Admin who forced logout

**break_glass_events**:
- Emergency access tracking
- Reason, clinical justification
- Duration (default 60 minutes)
- Access expires automatically
- Reviewed flag for post-access review
- Security notification sent immediately

### Data Retention Tables

**deidentified_mappings**:
- Original patient ID to anonymized token mapping
- For research use after retention period

**deidentified_documents**:
- De-identified clinical content
- Patient token (not identifiable)
- Document year only (not full date)

### Indexing Strategy

**Performance Indexes**:
- Foreign keys (always indexed)
- Frequently queried fields (username, email, status)
- Timestamp fields (created_at, updated_at, expires_at)
- JSONB fields (GIN indexes for concept search)

**Full-Text Search**:
- PostgreSQL full-text search on document content
- GIN index on tsvector column

**Partitioning Strategy**:
- `audit_logs` partitioned by month (large table, time-series data)
- Improves query performance for date range queries

---

## Component Design

### Backend Service Layer Pattern

```python
# app/services/user_service.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.services.audit_service import AuditService
from app.security.password import hash_password
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Business logic for user management"""

    def __init__(self, db: AsyncSession, audit: AuditService):
        self.db = db
        self.audit = audit

    async def create_user(
        self,
        user_data: UserCreate,
        created_by: User
    ) -> User:
        """Create new user with audit logging"""

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            role=user_data.role,
            must_change_password=True,
            created_by=created_by.id
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Audit log
        await self.audit.log(
            user_id=created_by.id,
            action="USER_CREATE",
            resource_type="user",
            resource_id=str(user.id),
            resource_name=user.username,
            details={"role": user.role}
        )

        logger.info(f"User created: {user.username} (role: {user.role})")

        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return await self.db.get(User, user_id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db.execute(
            select(User).where(User.username == username, User.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update_user(
        self,
        user_id: str,
        user_data: UserUpdate,
        updated_by: User
    ) -> Optional[User]:
        """Update user with audit logging"""

        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Track changes for audit
        changes = {}

        # Update fields
        if user_data.email is not None and user_data.email != user.email:
            changes["email"] = {"old": user.email, "new": user_data.email}
            user.email = user_data.email

        if user_data.role is not None and user_data.role != user.role:
            changes["role"] = {"old": user.role, "new": user_data.role}
            user.role = user_data.role

        if user_data.is_active is not None and user_data.is_active != user.is_active:
            changes["is_active"] = {"old": user.is_active, "new": user_data.is_active}
            user.is_active = user_data.is_active

        user.updated_by = updated_by.id
        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)

        # Audit log
        await self.audit.log(
            user_id=updated_by.id,
            action="USER_UPDATE",
            resource_type="user",
            resource_id=str(user.id),
            resource_name=user.username,
            details={"changes": changes}
        )

        return user
```

### Frontend Component Pattern (Vue 3 Composition API)

```vue
<!-- components/UserManagement.vue -->
<template>
  <v-container>
    <v-card>
      <v-card-title>
        <h2>User Management</h2>
        <v-spacer />
        <v-btn color="primary" @click="openCreateDialog">
          <v-icon left>mdi-account-plus</v-icon>
          Create User
        </v-btn>
      </v-card-title>

      <v-card-text>
        <!-- Filters -->
        <v-row>
          <v-col cols="12" md="4">
            <v-select
              v-model="filters.role"
              :items="roleOptions"
              label="Filter by Role"
              clearable
              @update:model-value="fetchUsers"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="filters.is_active"
              :items="activeOptions"
              label="Filter by Status"
              clearable
              @update:model-value="fetchUsers"
            />
          </v-col>
        </v-row>

        <!-- Data Table -->
        <v-data-table
          :items="users"
          :headers="headers"
          :loading="loading"
          :items-per-page="pageSize"
          @update:page="onPageChange"
        >
          <template #item.is_active="{ item }">
            <v-chip :color="item.is_active ? 'success' : 'error'" size="small">
              {{ item.is_active ? 'Active' : 'Inactive' }}
            </v-chip>
          </template>

          <template #item.actions="{ item }">
            <v-btn
              icon="mdi-pencil"
              size="small"
              @click="openEditDialog(item)"
            />
            <v-btn
              icon="mdi-delete"
              size="small"
              color="error"
              @click="confirmDelete(item)"
            />
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="600">
      <v-card>
        <v-card-title>
          {{ editingUser ? 'Edit User' : 'Create User' }}
        </v-card-title>

        <v-card-text>
          <v-form ref="form" v-model="formValid">
            <v-text-field
              v-model="formData.username"
              label="Username"
              :rules="[rules.required, rules.minLength(3)]"
              :disabled="!!editingUser"
            />

            <v-text-field
              v-model="formData.email"
              label="Email"
              type="email"
              :rules="[rules.required, rules.email]"
            />

            <v-text-field
              v-if="!editingUser"
              v-model="formData.password"
              label="Temporary Password"
              type="password"
              :rules="[rules.required, rules.minLength(8)]"
            />

            <v-select
              v-model="formData.role"
              :items="roleOptions"
              label="Role"
              :rules="[rules.required]"
            />

            <v-switch
              v-if="editingUser"
              v-model="formData.is_active"
              label="Active"
            />
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn @click="dialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            :disabled="!formValid"
            :loading="saving"
            @click="saveUser"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useSnackbar } from '@/composables/snackbar'
import type { User, UserCreate, UserUpdate } from '@/types'

const userStore = useUserStore()
const { showSuccess, showError } = useSnackbar()

const users = ref<User[]>([])
const loading = ref(false)
const dialog = ref(false)
const saving = ref(false)
const formValid = ref(false)
const editingUser = ref<User | null>(null)

const filters = reactive({
  role: null as string | null,
  is_active: null as boolean | null
})

const formData = reactive({
  username: '',
  email: '',
  password: '',
  role: '',
  is_active: true
})

const headers = [
  { title: 'Username', key: 'username' },
  { title: 'Email', key: 'email' },
  { title: 'Role', key: 'role' },
  { title: 'Status', key: 'is_active' },
  { title: 'Last Login', key: 'last_login' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const roleOptions = [
  { title: 'Admin', value: 'admin' },
  { title: 'Clinician', value: 'clinician' },
  { title: 'Researcher', value: 'researcher' }
]

const activeOptions = [
  { title: 'Active', value: true },
  { title: 'Inactive', value: false }
]

const rules = {
  required: (v: string) => !!v || 'Required',
  minLength: (min: number) => (v: string) => v.length >= min || `Min ${min} characters`,
  email: (v: string) => /.+@.+\..+/.test(v) || 'Invalid email'
}

const fetchUsers = async () => {
  loading.value = true
  try {
    users.value = await userStore.fetchUsers(filters)
  } catch (error: any) {
    showError(error.message || 'Failed to fetch users')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editingUser.value = null
  formData.username = ''
  formData.email = ''
  formData.password = ''
  formData.role = ''
  formData.is_active = true
  dialog.value = true
}

const openEditDialog = (user: User) => {
  editingUser.value = user
  formData.username = user.username
  formData.email = user.email
  formData.role = user.role
  formData.is_active = user.is_active
  dialog.value = true
}

const saveUser = async () => {
  saving.value = true
  try {
    if (editingUser.value) {
      await userStore.updateUser(editingUser.value.id, formData as UserUpdate)
      showSuccess('User updated successfully')
    } else {
      await userStore.createUser(formData as UserCreate)
      showSuccess('User created successfully')
    }
    dialog.value = false
    await fetchUsers()
  } catch (error: any) {
    showError(error.message || 'Failed to save user')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchUsers()
})
</script>
```

### Pinia Store Pattern

```typescript
// stores/user.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User, UserCreate, UserUpdate } from '@/types'
import { userApi } from '@/services/api'

export const useUserStore = defineStore('user', () => {
  const currentUser = ref<User | null>(null)
  const users = ref<User[]>([])

  const fetchCurrentUser = async () => {
    const response = await userApi.getCurrentUser()
    currentUser.value = response.data
    return currentUser.value
  }

  const fetchUsers = async (filters?: any) => {
    const response = await userApi.getUsers(filters)
    users.value = response.data.items
    return users.value
  }

  const createUser = async (userData: UserCreate) => {
    const response = await userApi.createUser(userData)
    users.value.push(response.data)
    return response.data
  }

  const updateUser = async (userId: string, userData: UserUpdate) => {
    const response = await userApi.updateUser(userId, userData)
    const index = users.value.findIndex(u => u.id === userId)
    if (index !== -1) {
      users.value[index] = response.data
    }
    return response.data
  }

  const logout = async () => {
    await userApi.logout()
    currentUser.value = null
  }

  return {
    currentUser,
    users,
    fetchCurrentUser,
    fetchUsers,
    createUser,
    updateUser,
    logout
  }
})
```

---

## Security Architecture

### Authentication Flow (JWT)

```
1. User submits credentials (username + password)
   ↓
2. Backend validates credentials
   - Query user by username
   - Verify password (bcrypt.verify)
   - Check account status (is_active, locked_until)
   ↓
3. Backend creates JWT token
   - Payload: {sub: user_id, role: role, exp: 8 hours, iat: now, jti: uuid}
   - Sign with HS256 algorithm + SECRET_KEY
   ↓
4. Backend creates session record
   - Token hash (SHA-256)
   - IP address hash
   - User-agent hash
   ↓
5. Backend returns token + user info to frontend
   ↓
6. Frontend stores token in sessionStorage (not localStorage)
   ↓
7. Frontend includes token in Authorization header for all requests
   - Header: "Authorization: Bearer {token}"
   ↓
8. Backend validates token on each request
   - Verify JWT signature
   - Check expiration
   - Query session (token_hash, force_logout = false)
   - Validate IP/user-agent binding (detect hijacking)
   - Update last_activity timestamp
   ↓
9. If valid → Process request
   If invalid → 401 Unauthorized → Frontend redirects to login
```

### Session Security Features

**Session Binding** (Hijack Detection):
```python
async def validate_session(token: str, request: Request, db: AsyncSession):
    # Verify JWT
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    # Get session
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = await db.execute(
        select(Session).where(
            Session.token_hash == token_hash,
            Session.force_logout == False
        )
    )
    session = session.scalar_one_or_none()
    if not session:
        raise HTTPException(401, "Session terminated")

    # Check IP binding (allow some variance for DHCP)
    current_ip_hash = hashlib.sha256(request.client.host.encode()).hexdigest()
    if current_ip_hash != session.ip_address_hash:
        session.is_suspicious = True
        session.suspicious_change_count += 1
        await db.commit()

        if session.suspicious_change_count > 3:
            await alert_security_team(session)
            raise HTTPException(401, "Suspicious activity detected")

    # Check user-agent binding (strict - immediate rejection)
    current_ua_hash = hashlib.sha256(request.headers.get("user-agent", "").encode()).hexdigest()
    if current_ua_hash != session.user_agent_hash:
        await audit_log(action="SESSION_HIJACK_DETECTED", session_id=session.id)
        await db.delete(session)
        await db.commit()
        raise HTTPException(401, "Session invalid - security violation")

    # Update last activity
    session.last_activity = datetime.utcnow()
    await db.commit()

    return session
```

**Idle Timeout** (15 minutes):
```python
@app.middleware("http")
async def check_session_activity(request: Request, call_next):
    # Skip for public endpoints
    if request.url.path in ["/health", "/api/v1/auth/login"]:
        return await call_next(request)

    # Get session from token
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    if not token:
        return await call_next(request)

    # Check last activity
    session = await get_session_by_token(token)
    if session and session.last_activity < datetime.utcnow() - timedelta(minutes=15):
        await db.delete(session)
        await db.commit()
        return JSONResponse(
            status_code=401,
            content={"detail": "Session expired due to inactivity"}
        )

    return await call_next(request)
```

**Concurrent Session Limits** (max 2):
```python
async def create_session(user_id: str, token: str, request: Request, db: AsyncSession):
    # Check existing sessions
    result = await db.execute(
        select(Session).where(Session.user_id == user_id).order_by(Session.created_at.desc())
    )
    sessions = result.scalars().all()

    # Enforce limit (max 2 sessions per user)
    if len(sessions) >= 2:
        # Terminate oldest session
        oldest = sessions[-1]
        await db.delete(oldest)
        await db.commit()

        # Notify user (email or in-app notification)
        await notify_user(user_id, "Previous session terminated due to new login")

    # Create new session
    session = Session(
        user_id=user_id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        ip_address_hash=hashlib.sha256(request.client.host.encode()).hexdigest(),
        user_agent_hash=hashlib.sha256(request.headers.get("user-agent", "").encode()).hexdigest(),
        expires_at=datetime.utcnow() + timedelta(hours=8)
    )
    db.add(session)
    await db.commit()

    return session
```

### Break-Glass Access (Emergency Access)

```python
@router.post("/api/v1/auth/break-glass")
async def request_break_glass_access(
    request: BreakGlassRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate user has break-glass permission
    if not current_user.can_break_glass:
        raise HTTPException(403, "User not authorized for break-glass access")

    # Validate reason is substantive (min 20 characters)
    if len(request.reason) < 20:
        raise HTTPException(400, "Reason must be detailed (min 20 characters)")

    # Create break-glass event
    event = BreakGlassEvent(
        user_id=current_user.id,
        patient_id=request.patient_id,
        reason=request.reason,
        clinical_justification=request.clinical_justification,
        duration_minutes=60,  # Default 60 minutes
        access_expires_at=datetime.utcnow() + timedelta(minutes=60)
    )
    db.add(event)

    # Audit log
    await audit_log(
        user_id=current_user.id,
        action="BREAK_GLASS_ACCESS",
        resource_type="patient",
        resource_id=request.patient_id,
        details={"reason": request.reason}
    )

    # IMMEDIATE notifications (email + SMS)
    await notify_security_team(event)
    await notify_clinical_governance_lead(event)

    await db.commit()

    # Grant temporary access (create special token or session flag)
    temp_token = create_temp_access_token(
        user_id=current_user.id,
        patient_id=request.patient_id,
        expires_in_minutes=60
    )

    return {
        "access_granted": True,
        "expires_at": event.access_expires_at.isoformat(),
        "temp_token": temp_token
    }
```

### Authorization (RBAC)

```python
# app/security/permissions.py
from enum import Enum
from functools import wraps
from fastapi import HTTPException, Depends

class Permission(str, Enum):
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Project management
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"

    # Task management
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"

    # Patient data
    PATIENT_SEARCH = "patient:search"
    PATIENT_VIEW = "patient:view"
    PATIENT_EXPORT = "patient:export"

    # Admin
    AUDIT_VIEW = "audit:view"
    MODULE_MANAGE = "module:manage"
    SYSTEM_CONFIG = "system:config"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    "admin": [
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE,
        Permission.TASK_CREATE, Permission.TASK_READ, Permission.TASK_UPDATE, Permission.TASK_DELETE,
        Permission.PATIENT_SEARCH, Permission.PATIENT_VIEW, Permission.PATIENT_EXPORT,
        Permission.AUDIT_VIEW, Permission.MODULE_MANAGE, Permission.SYSTEM_CONFIG
    ],
    "clinician": [
        Permission.PROJECT_READ,
        Permission.TASK_READ, Permission.TASK_UPDATE,
        Permission.PATIENT_SEARCH, Permission.PATIENT_VIEW
    ],
    "researcher": [
        Permission.PROJECT_READ,
        Permission.PATIENT_SEARCH, Permission.PATIENT_EXPORT
    ]
}

def require_permission(permission: Permission):
    """Decorator to enforce permission on endpoint"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: User = Depends(get_current_user), **kwargs):
            if permission not in ROLE_PERMISSIONS.get(user.role, []):
                raise HTTPException(403, f"Permission denied: {permission}")
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator

# Usage in endpoint
@router.post("/api/v1/users", dependencies=[Depends(require_permission(Permission.USER_CREATE))])
async def create_user(user_data: UserCreate):
    ...
```

### Encryption

**Password Hashing** (bcrypt):
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)
```

**Document Encryption** (AES-256):
```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

# Load encryption key from environment (32 bytes for AES-256)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY").encode()

def encrypt_document(plaintext: bytes) -> bytes:
    """Encrypt document with AES-256-CBC"""
    iv = os.urandom(16)  # Initialization vector
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad to 16-byte blocks
    padding_length = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([padding_length] * padding_length)

    ciphertext = encryptor.update(padded) + encryptor.finalize()

    # Return IV + ciphertext (IV needed for decryption)
    return iv + ciphertext

def decrypt_document(ciphertext: bytes) -> bytes:
    """Decrypt AES-256-CBC encrypted document"""
    iv = ciphertext[:16]
    actual_ciphertext = ciphertext[16:]

    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    padded = decryptor.update(actual_ciphertext) + decryptor.finalize()

    # Remove padding
    padding_length = padded[-1]
    return padded[:-padding_length]
```

### Audit Logging

**Comprehensive Audit Trail**:
```python
class AuditService:
    """Centralized audit logging service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Create immutable audit log entry

        Examples:
            await audit.log(
                user_id=user.id,
                action="PATIENT_VIEW",
                resource_type="patient",
                resource_id="P12345",
                resource_name="John Doe (NHS: 1234567890)",
                details={"search_query": "diabetes"},
                ip_address="192.168.1.100",
                session_id="uuid"
            )
        """
        try:
            # Get username (denormalized for immutability)
            username = "system"
            if user_id:
                user = await self.db.get(User, user_id)
                username = user.username if user else f"user-{user_id}"

            audit_log = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                details=details or {},
                ip_address=ip_address,
                session_id=session_id
            )

            self.db.add(audit_log)
            await self.db.flush()

            logger.info(
                f"AUDIT: user={username} action={action} resource={resource_type}/{resource_id}"
            )

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise - audit logging failure shouldn't break application
```

**Audit Actions**:
- Authentication: `LOGIN_SUCCESS`, `LOGIN_FAILURE`, `LOGOUT`
- User Management: `USER_CREATE`, `USER_UPDATE`, `USER_DELETE`, `USER_VIEW`, `USER_LIST`
- Project Management: `PROJECT_CREATE`, `PROJECT_UPDATE`, `PROJECT_DELETE`, `PROJECT_VIEW`, `PROJECT_MEMBER_ADD`, `PROJECT_MEMBER_REMOVE`
- Task Management: `TASK_CREATE`, `TASK_UPDATE`, `TASK_DELETE`, `TASK_VIEW`, `TASK_ASSIGN`
- PHI Access: `PATIENT_SEARCH`, `PATIENT_VIEW`, `PATIENT_EXPORT`, `DOCUMENT_UPLOAD`, `DOCUMENT_VIEW`
- System: `MODULE_ENABLE`, `MODULE_DISABLE`, `CONFIG_UPDATE`, `BREAK_GLASS_ACCESS`

---

## CogStack-ModelServe Integration

### Overview

We use **CogStack-ModelServe** (https://github.com/CogStack/CogStack-ModelServe) as our production-ready NLP model serving platform instead of building a custom MedCAT Service.

**Benefits**:
- ✅ Production-tested model serving (vs custom implementation)
- ✅ Built-in authentication, monitoring, model versioning
- ✅ Multiple models: SNOMED-CT, ICD-10, UMLS, de-identification
- ✅ FastAPI-based with automatic OpenAPI documentation
- ✅ Active maintenance by CogStack team
- ✅ Saves ~20 hours of custom development

**Deployment Strategy**:
- **MVP (Phase 0-1)**: Minimal deployment (core API + SNOMED + DeID models)
- **Production (Phase 2+)**: Full stack (+ MLflow, Grafana, Prometheus, authentication)

### CogStack-ModelServe Client (Async with Built-in Retry)

```python
# app/clients/modelserve_client.py
import httpx
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CogStackModelServeClient:
    """Async client for CogStack-ModelServe REST API

    Uses CogStack-ModelServe for production-ready NLP model serving.
    Repository: https://github.com/CogStack/CogStack-ModelServe

    Supports:
    - SNOMED-CT concept extraction
    - De-identification (PII detection)
    - ICD-10, UMLS (future)
    """

    def __init__(
        self,
        base_url: str = "http://cogstack-modelserve:8000",
        api_token: Optional[str] = None,
        timeout: int = 300
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {}
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"
        self.client = httpx.AsyncClient(timeout=timeout, headers=self.headers)

    async def process_text(
        self,
        text: str,
        model_name: str = "medcat_snomed"
    ) -> List[Dict[str, Any]]:
        """
        Process text with CogStack-ModelServe and return entities

        Args:
            text: Clinical text to process
            model_name: Model to use (medcat_snomed, medcat_deid, medcat_icd10, etc.)

        Returns:
            List of entities with structure:
            {
                "cui": "C0004238",
                "pretty_name": "Atrial Flutter",
                "start": 45,
                "end": 60,
                "type_ids": ["SNOMED-CT"],
                "types": ["Disorder"],
                "source_value": "atrial flutter",
                "acc": 0.95,  # confidence score
                "context_similarity": 0.87,
                "meta_anns": {
                    "Negation": {"value": "Affirmed", "confidence": 0.99},
                    "Experiencer": {"value": "Patient", "confidence": 0.98},
                    "Temporality": {"value": "Current", "confidence": 0.96},
                    "Certainty": {"value": "Definite", "confidence": 0.94}
                }
            }

        Note: CogStack-ModelServe has built-in retry logic and error handling.
        """
        try:
            logger.info(f"Processing text with CogStack-ModelServe (model: {model_name}, length: {len(text)})")

            response = await self.client.post(
                f"{self.base_url}/api/process",
                json={
                    "text": text,
                    "model_name": model_name
                }
            )
            response.raise_for_status()

            result = response.json()
            entities = result.get("entities", [])

            logger.info(f"CogStack-ModelServe extracted {len(entities)} entities")

            return entities

        except httpx.HTTPError as e:
            logger.error(f"CogStack-ModelServe API error: {e}")
            raise Exception(f"CogStack-ModelServe processing failed: {e}")

    async def process_text_bulk(
        self,
        texts: List[str],
        model_name: str = "medcat_snomed"
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch process multiple documents (more efficient than single processing)

        Args:
            texts: List of clinical texts
            model_name: Model to use

        Returns:
            List of entity lists (one per input text)
        """
        try:
            logger.info(f"Batch processing {len(texts)} documents with CogStack-ModelServe")

            response = await self.client.post(
                f"{self.base_url}/api/process_bulk",
                json={
                    "texts": texts,
                    "model_name": model_name
                }
            )
            response.raise_for_status()

            result = response.json()
            return result.get("results", [])

        except httpx.HTTPError as e:
            logger.error(f"CogStack-ModelServe bulk API error: {e}")
            raise Exception(f"CogStack-ModelServe bulk processing failed: {e}")

    async def detect_phi(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect PHI/PII using CogStack-ModelServe de-identification model

        Args:
            text: Clinical text potentially containing PHI

        Returns:
            List of PHI entities (names, NHS numbers, dates, addresses, etc.)
        """
        return await self.process_text(text, model_name="medcat_deid")

    async def classify_entity_type(self, entity: Dict[str, Any]) -> str:
        """
        Classify entity as PHI or clinical concept

        Note: With CogStack-ModelServe, we can use separate models:
        - medcat_snomed for clinical concepts
        - medcat_deid for PHI detection

        This is more accurate than heuristic-based classification.

        Returns: 'phi_name', 'phi_nhs_number', 'phi_address', 'phi_dob', 'clinical'
        """
        cui = entity.get("cui", "")
        types = entity.get("types", [])
        pretty_name = entity.get("pretty_name", "").lower()

        # If processed with medcat_deid model, classify based on types
        if "Person" in types or "Name" in types:
            return "phi_name"
        elif "NHS Number" in types or "Medical Record Number" in types:
            return "phi_nhs_number"
        elif "Address" in types or "Location" in types:
            return "phi_address"
        elif "Date" in types and any(word in pretty_name for word in ["birth", "dob"]):
            return "phi_dob"
        else:
            return "clinical"

    async def health_check(self) -> bool:
        """Check if CogStack-ModelServe is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            return response.status_code == 200
        except:
            return False

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from CogStack-ModelServe"""
        try:
            response = await self.client.get(f"{self.base_url}/api/models")
            response.raise_for_status()
            return response.json().get("models", [])
        except:
            return []
```

### CogStack-NiFi Compatibility Layer

To ensure future convergence with **CogStack-NiFi** for enterprise deployments, we implement RESTful API standardization:

```python
# app/api/v1/nifi_compatible.py
"""
NiFi-compatible REST API endpoints

CogStack-NiFi expects standardized REST interfaces for integration.
These endpoints follow CogStack ecosystem conventions for easy NiFi workflow integration.

Future Migration Path:
1. MVP: Direct REST API calls from frontend → backend → CogStack-ModelServe
2. Enterprise: Apache NiFi orchestrates workflows → backend APIs → CogStack-ModelServe
3. NiFi processors can call these endpoints without modification
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/nifi", tags=["NiFi Compatible"])

class DocumentProcessingRequest(BaseModel):
    """Standard request format for document processing (NiFi compatible)"""
    document_id: str
    content: str  # or content_url for large documents
    metadata: Dict[str, Any] = {}

class DocumentProcessingResponse(BaseModel):
    """Standard response format (NiFi compatible)"""
    document_id: str
    status: str  # "success", "failed", "partial"
    entities: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_time_ms: int

@router.post("/process_document", response_model=DocumentProcessingResponse)
async def process_document(
    request: DocumentProcessingRequest,
    modelserve: CogStackModelServeClient = Depends(get_modelserve_client)
):
    """
    Process a single document with NLP extraction (NiFi compatible)

    This endpoint can be called by Apache NiFi processors in enterprise deployments.
    """
    start_time = time.time()

    try:
        # Process with CogStack-ModelServe
        entities = await modelserve.process_text(request.content)

        processing_time = int((time.time() - start_time) * 1000)

        return DocumentProcessingResponse(
            document_id=request.document_id,
            status="success",
            entities=entities,
            metadata=request.metadata,
            processing_time_ms=processing_time
        )
    except Exception as e:
        return DocumentProcessingResponse(
            document_id=request.document_id,
            status="failed",
            entities=[],
            metadata={"error": str(e)},
            processing_time_ms=int((time.time() - start_time) * 1000)
        )

# Additional NiFi-compatible endpoints for batch processing, status checking, etc.
```

**Migration Path to CogStack-NiFi**:
1. **Phase 0-2 (MVP)**: Direct API integration (frontend → backend → CogStack-ModelServe)
2. **Phase 3+ (Enterprise)**: Add Apache NiFi workflows (NiFi → backend APIs → CogStack-ModelServe)
3. **Benefits**: NiFi handles complex orchestration, our APIs remain unchanged

---

## PHI Extraction Workflow

### 4-Step Workflow

```
Step 1: Document Upload
  ↓
  - User uploads RTF file (~50KB)
  - Backend encrypts with AES-256
  - Store in PostgreSQL BYTEA column
  - Compute SHA-256 hash for deduplication
  - Create audit log (DOCUMENT_UPLOAD)
  ↓
Step 2: CogStack-ModelServe Processing (Async)
  ↓
  - Decrypt document in-memory (never persist unencrypted)
  - POST to CogStack-ModelServe (2 models: medcat_snomed + medcat_deid)
  - Extract clinical entities (SNOMED concepts)
  - Extract PHI entities (names, NHS numbers, dates, addresses)
  - Classify entity types (PHI vs clinical)
  - Insert into extracted_entities table
  - Update document.nlp_status = 'complete'
  ↓
Step 3: Patient Aggregation
  ↓
  - Query PHI entities (NHS number, name, DOB, address)
  - Match via NHS number (primary, 10 digits)
  - Fallback: Fuzzy match via name + DOB
  - UPDATE or INSERT patients table
  - Link document via source_document_ids array (JSONB)
  ↓
Step 4: Search & Timeline Access
  ↓
  - Patient Search: Query by clinical concepts with meta-annotation filters
  - Timeline View: Chronological clinical events for patient
```

### Implementation

**Step 1: Document Upload Endpoint**:
```python
@router.post("/api/v1/documents")
async def upload_document(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service)
):
    # Read file content
    content = await file.read()

    # Validate file size (<1MB)
    if len(content) > 1024 * 1024:
        raise HTTPException(400, "File too large (max 1MB)")

    # Encrypt
    encrypted_content = encrypt_document(content)
    content_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicates
    existing = await db.execute(
        select(Document).where(Document.content_hash == content_hash)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Duplicate document (SHA-256 hash match)")

    # Create document record
    document = Document(
        filename=file.filename,
        content=encrypted_content,
        content_hash=content_hash,
        file_size=len(content),
        uploaded_by=user.id,
        medcat_status='pending'
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Audit log
    await audit.log(
        user_id=user.id,
        action="DOCUMENT_UPLOAD",
        resource_type="document",
        resource_id=str(document.id),
        details={"filename": file.filename, "size": len(content)}
    )

    # Trigger async CogStack-ModelServe processing
    background_tasks.add_task(process_document, document.id)

    return document
```

**Step 2: CogStack-ModelServe Processing (Background Task)**:
```python
async def process_document(document_id: str):
    """Process document with CogStack-ModelServe (background task)"""
    async with AsyncSessionLocal() as db:
        # Get document
        document = await db.get(Document, document_id)
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        try:
            # Update status
            document.medcat_status = 'processing'
            await db.commit()

            # Decrypt
            plaintext = decrypt_document(document.content)
            text = plaintext.decode('utf-8')

            # Process with CogStack-ModelServe (2 models: SNOMED + DeID)
            modelserve = CogStackModelServeClient(base_url=os.getenv("MODELSERVE_URL", "http://cogstack-modelserve:8000"))

            # Extract clinical concepts (SNOMED)
            clinical_entities = await modelserve.process_text(text, model_name="medcat_snomed")

            # Extract PHI (de-identification)
            phi_entities = await modelserve.detect_phi(text)

            # Combine all entities
            entities = clinical_entities + phi_entities

            # Classify and store entities
            for entity in entities:
                entity_type = await modelserve.classify_entity_type(entity)

                extracted_entity = ExtractedEntity(
                    source_document_id=document.id,
                    cui=entity['cui'],
                    pretty_name=entity['pretty_name'],
                    entity_type=entity_type,
                    start_pos=entity['start'],
                    end_pos=entity['end'],
                    text=text[entity['start']:entity['end']],
                    meta_annotations=entity.get('meta_anns', {}),
                    confidence=entity.get('confidence', 1.0)
                )
                db.add(extracted_entity)

            # Update status
            document.nlp_status = 'complete'
            document.processed_at = datetime.utcnow()
            await db.commit()

            logger.info(f"Document {document_id} processed with CogStack-ModelServe: {len(entities)} entities")

        except Exception as e:
            logger.error(f"CogStack-ModelServe processing failed for {document_id}: {e}")
            document.nlp_status = 'failed'
            document.error_message = str(e)
            await db.commit()
```

**Step 3: Patient Aggregation**:
```python
async def aggregate_patient_from_document(document_id: str):
    """Aggregate patient record from extracted PHI entities"""
    async with AsyncSessionLocal() as db:
        # Query PHI entities
        result = await db.execute(
            select(ExtractedEntity).where(
                ExtractedEntity.source_document_id == document_id,
                ExtractedEntity.entity_type.like('phi_%')
            )
        )
        phi_entities = result.scalars().all()

        # Extract PHI values
        nhs_number = None
        name = None
        dob = None
        address = None

        for entity in phi_entities:
            if entity.entity_type == 'phi_nhs_number':
                nhs_number = entity.text
            elif entity.entity_type == 'phi_name':
                name = entity.text
            elif entity.entity_type == 'phi_dob':
                dob = parse_date(entity.text)
            elif entity.entity_type == 'phi_address':
                address = entity.text

        # Primary matching: NHS number
        patient = None
        if nhs_number:
            result = await db.execute(
                select(Patient).where(Patient.nhs_number == nhs_number)
            )
            patient = result.scalar_one_or_none()

        # Fallback matching: Fuzzy name + DOB
        if not patient and name and dob:
            result = await db.execute(
                select(Patient).where(
                    func.levenshtein(Patient.name, name) <= 3,
                    Patient.date_of_birth == dob
                )
            )
            patient = result.scalar_one_or_none()

        # Update or create patient
        if patient:
            # Update existing patient
            if document_id not in patient.source_document_ids:
                patient.source_document_ids.append(document_id)
            patient.updated_at = datetime.utcnow()
        else:
            # Create new patient
            patient = Patient(
                nhs_number=nhs_number,
                name=name,
                date_of_birth=dob,
                address=address,
                source_document_ids=[document_id]
            )
            db.add(patient)

        await db.commit()

        logger.info(f"Patient aggregated from document {document_id}: {patient.id}")
```

---

## Testing Strategy

### Test Pyramid

```
      /\
     /  \    E2E (5%)           - 5-10 critical user journeys
    /----\                        (Playwright, full stack)
   /      \  Integration (25%)   - API contract tests
  /--------\                       (TestClient, database, MedCAT mock)
 /          \ Unit (70%)          - Pure function tests
/____________\                     (pytest, no external deps)
```

### Unit Testing (pytest)

**Target Coverage**: ≥80% overall, ≥90% for critical paths (auth, audit, PHI)

**Example Unit Tests**:
```python
# tests/unit/services/test_user_service.py
import pytest
from app.services.user_service import UserService
from app.schemas import UserCreate

@pytest.mark.asyncio
async def test_create_user_hashes_password(db_session, audit_service):
    """Test that user creation hashes password"""
    # Arrange
    service = UserService(db_session, audit_service)
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="PlainPassword123",
        role="clinician"
    )
    admin = User(id="admin-id", username="admin")

    # Act
    user = await service.create_user(user_data, admin)

    # Assert
    assert user.password_hash != "PlainPassword123"
    assert user.password_hash.startswith("$2b$")  # bcrypt prefix
    assert len(user.password_hash) == 60  # bcrypt hash length

@pytest.mark.asyncio
async def test_create_user_sets_must_change_password(db_session, audit_service):
    """Test that new users must change password on first login"""
    # Arrange
    service = UserService(db_session, audit_service)
    user_data = UserCreate(username="test", email="test@example.com", password="pass", role="clinician")
    admin = User(id="admin-id", username="admin")

    # Act
    user = await service.create_user(user_data, admin)

    # Assert
    assert user.must_change_password == True

@pytest.mark.asyncio
async def test_create_user_logs_audit_entry(db_session, audit_service):
    """Test that user creation logs audit entry"""
    # Arrange
    service = UserService(db_session, audit_service)
    user_data = UserCreate(username="test", email="test@example.com", password="pass", role="clinician")
    admin = User(id="admin-id", username="admin")

    # Act
    user = await service.create_user(user_data, admin)

    # Assert
    audit_service.log.assert_called_once()
    call_args = audit_service.log.call_args[1]
    assert call_args['action'] == "USER_CREATE"
    assert call_args['resource_type'] == "user"
    assert call_args['resource_id'] == str(user.id)
```

### Integration Testing (TestClient)

**Example Integration Tests**:
```python
# tests/integration/test_auth_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user):
    """Test successful login returns token"""
    # Arrange
    credentials = {
        "username": "testuser",
        "password": "Password123"
    }

    # Act
    response = await async_client.post("/api/v1/auth/login", json=credentials)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_at" in data
    assert data["user"]["username"] == "testuser"

@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient, test_user):
    """Test login with invalid password returns 401"""
    # Arrange
    credentials = {
        "username": "testuser",
        "password": "WrongPassword"
    }

    # Act
    response = await async_client.post("/api/v1/auth/login", json=credentials)

    # Assert
    assert response.status_code == 401
    data = response.json()
    assert "Invalid username or password" in data["detail"]

@pytest.mark.asyncio
async def test_login_logs_audit_entry(async_client: AsyncClient, test_user, db_session):
    """Test successful login creates audit log"""
    # Arrange
    credentials = {"username": "testuser", "password": "Password123"}

    # Act
    response = await async_client.post("/api/v1/auth/login", json=credentials)

    # Assert
    assert response.status_code == 200

    # Query audit logs
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "LOGIN_SUCCESS").order_by(AuditLog.timestamp.desc())
    )
    audit_log = result.scalar_one()
    assert audit_log.username == "testuser"
    assert audit_log.resource_type == "auth"

@pytest.mark.asyncio
async def test_protected_endpoint_requires_token(async_client: AsyncClient):
    """Test protected endpoint returns 401 without token"""
    # Act
    response = await async_client.get("/api/v1/auth/me")

    # Assert
    assert response.status_code == 401
```

### E2E Testing (Playwright)

**Example E2E Tests**:
```typescript
// tests/e2e/user-management.spec.ts
import { test, expect } from '@playwright/test'

test('admin can create user and user can login', async ({ page }) => {
  // Admin login
  await page.goto('http://localhost:8080/login')
  await page.fill('input[name="username"]', 'admin1')
  await page.fill('input[name="password"]', 'AdminPassword123')
  await page.click('button[type="submit"]')

  // Wait for dashboard
  await expect(page).toHaveURL('http://localhost:8080/dashboard')

  // Navigate to user management
  await page.click('text=User Management')
  await expect(page).toHaveURL('http://localhost:8080/users')

  // Create new user
  await page.click('button:has-text("Create User")')
  await page.fill('input[label="Username"]', 'newclinician')
  await page.fill('input[label="Email"]', 'newclinician@hospital.com')
  await page.fill('input[label="Temporary Password"]', 'TempPassword123')
  await page.selectOption('select[label="Role"]', 'clinician')
  await page.click('button:has-text("Save")')

  // Verify success message
  await expect(page.locator('.v-snackbar--active')).toContainText('User created successfully')

  // Logout
  await page.click('[aria-label="User Menu"]')
  await page.click('text=Logout')

  // Login as new user
  await page.fill('input[name="username"]', 'newclinician')
  await page.fill('input[name="password"]', 'TempPassword123')
  await page.click('button[type="submit"]')

  // Should be prompted to change password
  await expect(page).toHaveURL('http://localhost:8080/change-password')
  await expect(page.locator('h1')).toContainText('Change Password')
})

test('clinician can view assigned tasks', async ({ page }) => {
  // Login as clinician
  await page.goto('http://localhost:8080/login')
  await page.fill('input[name="username"]', 'clinician1')
  await page.fill('input[name="password"]', 'Password123')
  await page.click('button[type="submit"]')

  // Navigate to tasks
  await page.click('text=My Tasks')
  await expect(page).toHaveURL('http://localhost:8080/tasks')

  // Verify tasks visible
  await expect(page.locator('.v-data-table')).toBeVisible()
  await expect(page.locator('td')).toContainText('Review 100 diabetes cases')

  // Filter by status
  await page.selectOption('select[label="Filter by Status"]', 'in_progress')

  // Verify filtered results
  const rows = page.locator('tbody tr')
  await expect(rows).toHaveCount(2)
})
```

### PHI De-Identification Validation Tests

**Critical Requirement**: Ensure PHI is properly identified, protected, and never exposed in logs or unencrypted storage.

**Test Categories**:

#### 1. PHI Identification Tests (Unit)
```python
# tests/unit/test_phi_extraction.py
import pytest
from app.clients.modelserve_client import CogStackModelServeClient
from app.services.phi_classifier import PHIClassifier

@pytest.mark.asyncio
async def test_phi_extraction_identifies_nhs_number():
    """Test that NHS numbers are correctly identified as PHI"""
    # Arrange
    text = "Patient NHS number: 1234567890"
    modelserve = CogStackModelServeClient()

    # Act
    entities = await modelserve.detect_phi(text)  # Use de-identification model

    # Assert
    nhs_entities = [e for e in entities if e['type'] == 'phi_nhs_number']
    assert len(nhs_entities) > 0
    assert '1234567890' in nhs_entities[0]['pretty_name']

@pytest.mark.asyncio
async def test_phi_extraction_identifies_patient_names():
    """Test that patient names are correctly identified as PHI"""
    # Arrange
    text = "Patient name: John Smith, DOB: 01/01/1980"
    modelserve = CogStackModelServeClient()

    # Act
    entities = await modelserve.detect_phi(text)  # Use de-identification model

    # Assert
    name_entities = [e for e in entities if e['type'] == 'phi_name']
    assert len(name_entities) > 0
    assert 'John Smith' in [e['pretty_name'] for e in name_entities]

@pytest.mark.asyncio
async def test_phi_classification_distinguishes_phi_from_clinical():
    """Test that PHI classifier correctly separates PHI from clinical entities"""
    # Arrange
    classifier = PHIClassifier()
    phi_entity = {"cui": "C1547728", "pretty_name": "NHS number"}
    clinical_entity = {"cui": "C0011849", "pretty_name": "diabetes mellitus"}

    # Act
    phi_type = classifier.classify(phi_entity)
    clinical_type = classifier.classify(clinical_entity)

    # Assert
    assert phi_type == "phi_nhs_number"
    assert clinical_type == "clinical"
```

#### 2. PHI Protection Tests (Integration)
```python
# tests/integration/test_phi_protection.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_document_stored_encrypted(async_client: AsyncClient, test_document):
    """Test that uploaded documents are encrypted in database"""
    # Arrange
    files = {"file": ("test.rtf", test_document, "application/rtf")}

    # Act
    response = await async_client.post("/api/v1/documents/upload", files=files)
    document_id = response.json()["id"]

    # Assert - Query database directly
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one()

    # Document content should be encrypted (not plaintext)
    assert document.encrypted_content != test_document
    assert document.encrypted_content.startswith(b'encrypted:')  # Custom prefix
    assert document.encryption_algorithm == "AES-256-GCM"

@pytest.mark.asyncio
async def test_phi_entities_stored_separately(async_client: AsyncClient, test_document):
    """Test that PHI entities are stored in separate table"""
    # Arrange
    files = {"file": ("patient_letter.rtf", test_document, "application/rtf")}

    # Act
    response = await async_client.post("/api/v1/documents/upload", files=files)
    document_id = response.json()["id"]

    # Wait for processing
    await asyncio.sleep(2)

    # Assert - PHI entities in extracted_entities table
    result = await db.execute(
        select(ExtractedEntity).where(
            ExtractedEntity.document_id == document_id,
            ExtractedEntity.entity_type.in_(['phi_name', 'phi_nhs_number', 'phi_dob', 'phi_address'])
        )
    )
    phi_entities = result.scalars().all()
    assert len(phi_entities) > 0
```

#### 3. PHI Logging Tests (Security)
```python
# tests/security/test_phi_logging.py
import pytest
import logging
from io import StringIO

@pytest.mark.asyncio
async def test_phi_not_in_application_logs(async_client, test_document, caplog):
    """Test that PHI never appears in application logs"""
    # Arrange
    caplog.set_level(logging.DEBUG)  # Capture all logs
    files = {"file": ("patient_letter.rtf", test_document, "application/rtf")}

    # Act
    response = await async_client.post("/api/v1/documents/upload", files=files)

    # Assert - Check all log messages
    for record in caplog.records:
        # PHI should NEVER appear in logs
        assert "1234567890" not in record.message  # NHS number
        assert "John Smith" not in record.message  # Patient name
        assert "123 Main Street" not in record.message  # Address

        # Only document IDs should appear
        assert record.message.count(response.json()["id"]) >= 0

@pytest.mark.asyncio
async def test_phi_access_logged_to_audit_trail(async_client, test_user):
    """Test that PHI access is logged to audit trail"""
    # Arrange
    patient_id = "patient-123"

    # Act
    response = await async_client.get(f"/api/v1/patients/{patient_id}")

    # Assert - Check audit logs
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.action == "PHI_ACCESS",
            AuditLog.resource_id == patient_id
        ).order_by(AuditLog.timestamp.desc())
    )
    audit_log = result.scalar_one()
    assert audit_log.user_id == test_user.id
    assert audit_log.resource_type == "patient"
    assert audit_log.details is not None
```

#### 4. De-Identification Tests (Functional)
```python
# tests/functional/test_deidentification.py
import pytest

@pytest.mark.asyncio
async def test_patient_aggregation_by_nhs_number():
    """Test that patients are correctly aggregated by NHS number"""
    # Arrange
    doc1_text = "Patient NHS: 1234567890, Name: John Smith, diabetes"
    doc2_text = "NHS number 1234567890, pneumonia diagnosis"

    # Act
    await process_document(doc1_text)
    await process_document(doc2_text)

    # Assert - Should create ONE patient record
    result = await db.execute(select(Patient).where(Patient.nhs_number == "1234567890"))
    patients = result.scalars().all()
    assert len(patients) == 1

    # Patient record should have aggregated data
    patient = patients[0]
    assert patient.nhs_number == "1234567890"
    assert patient.full_name == "John Smith"

    # Both documents linked to same patient
    result = await db.execute(
        select(ExtractedEntity).where(ExtractedEntity.patient_id == patient.id)
    )
    entities = result.scalars().all()
    assert len({e.document_id for e in entities}) == 2  # 2 different documents

@pytest.mark.asyncio
async def test_patient_search_excludes_direct_phi():
    """Test that patient search API does not return direct PHI"""
    # Arrange
    await create_test_patient(
        nhs_number="1234567890",
        full_name="John Smith",
        dob="1980-01-01",
        address="123 Main Street"
    )

    # Act
    response = await async_client.get("/api/v1/patients/search?concept=diabetes")

    # Assert - Response should not contain direct PHI
    data = response.json()
    assert response.status_code == 200

    for patient in data["results"]:
        # Should have patient ID only
        assert "id" in patient

        # Should NOT have direct PHI (unless explicitly requested and authorized)
        assert "nhs_number" not in patient
        assert "full_name" not in patient
        assert "address" not in patient

        # Can have aggregated clinical concepts
        assert "concepts" in patient
```

### Performance Testing

**Tools**: Locust for load testing

**Test Scenarios**:
1. **Concurrent Logins**: 10 users login simultaneously
2. **API Load**: 100 requests/sec to patient search endpoint
3. **Database Stress**: 1000 concurrent audit log writes
4. **Document Upload**: 50 concurrent document uploads

**Acceptance Criteria**:
- P95 response time <500ms for all API endpoints
- No errors under 10 concurrent users
- Database connection pool never exhausted

---

## Deployment Architecture

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: clinical_tools_postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-clinical_care_tools}
      POSTGRES_USER: ${POSTGRES_USER:-clinicaltools}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
      POSTGRES_HOST_AUTH_METHOD: scram-sha-256
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    networks:
      - clinical_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-clinicaltools}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    restart: unless-stopped
    read_only: true
    tmpfs:
      - /tmp
      - /var/run/postgresql

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: 3.10
    container_name: clinical_tools_backend
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-clinicaltools}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-clinical_care_tools}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:?JWT_SECRET_KEY is required}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY:?ENCRYPTION_KEY is required}
      MEDCAT_SERVICE_URL: ${MEDCAT_SERVICE_URL:-http://medcat-service:5000}
      ENVIRONMENT: ${ENVIRONMENT:-development}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS:-http://localhost:8080}
    volumes:
      - backend_logs:/var/log/clinical_tools
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    networks:
      - clinical_network
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NODE_VERSION: 20
    container_name: clinical_tools_frontend
    environment:
      VITE_API_URL: ${VITE_API_URL:-http://localhost:8000}
      VITE_ENVIRONMENT: ${ENVIRONMENT:-development}
    ports:
      - "${FRONTEND_PORT:-8080}:8080"
    networks:
      - clinical_network
    depends_on:
      - backend
    restart: unless-stopped

  medcat-service:
    image: cogstacksystems/medcat-service:latest
    container_name: medcat_service
    environment:
      MODEL_PACK_PATH: /app/models/model_pack.zip
      WORKERS: ${MEDCAT_WORKERS:-2}
    volumes:
      - medcat_models:/app/models:ro
    ports:
      - "${MEDCAT_PORT:-5000}:5000"
    networks:
      - clinical_network
    deploy:
      resources:
        reservations:
          memory: 4G
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  backend_logs:
    driver: local
  medcat_models:
    driver: local

networks:
  clinical_network:
    driver: bridge
```

### Environment Variables (.env)

```bash
# Database
POSTGRES_DB=clinical_care_tools
POSTGRES_USER=clinicaltools
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD
POSTGRES_PORT=5432

# Backend
BACKEND_PORT=8000
JWT_SECRET_KEY=CHANGE_ME_256_BIT_KEY  # openssl rand -hex 32
ENCRYPTION_KEY=CHANGE_ME_32_BYTES_KEY  # openssl rand -base64 32
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:8080

# Frontend
FRONTEND_PORT=8080
VITE_API_URL=http://localhost:8000

# MedCAT
MEDCAT_SERVICE_URL=http://medcat-service:5000
MEDCAT_PORT=5000
MEDCAT_WORKERS=2
```

### First-Time Setup Script

```bash
#!/bin/bash
# scripts/first-time-setup.sh
# Run after docker-compose up to initialize system

set -e

echo "Clinical Care Tools - First Time Setup"
echo "======================================="

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Run database migrations
echo "Running database migrations..."
docker-compose exec backend alembic upgrade head

# Create admin user
echo ""
echo "Creating admin user..."
read -p "Admin username: " ADMIN_USERNAME
read -sp "Admin password: " ADMIN_PASSWORD
echo ""

docker-compose exec backend python -m app.cli create-admin \
    --username "$ADMIN_USERNAME" \
    --password "$ADMIN_PASSWORD" \
    --email "admin@localhost"

# Load MedCAT model (if provided)
if [ -f "./models/model_pack.zip" ]; then
    echo ""
    echo "Loading MedCAT model..."
    docker-compose exec medcat-service python -m medcat load-model /app/models/model_pack.zip
fi

# Initialize modules
echo ""
echo "Initializing modules..."
docker-compose exec backend python -m app.cli init-modules

echo ""
echo "Setup complete!"
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:8080"
echo "  Backend API: http://localhost:8000/docs"
echo "  Admin username: $ADMIN_USERNAME"
echo ""
echo "For remote access, configure RDP to this workstation."
```

### Backup Script

```bash
#!/bin/bash
# scripts/backup-postgres.sh
# Daily automated backup (run via cron: 0 2 * * * /path/to/backup-postgres.sh)

set -e

BACKUP_DIR="/backups/$(date +%Y-%m-%d)"
POSTGRES_CONTAINER="clinical_tools_postgres"
POSTGRES_USER="clinicaltools"
POSTGRES_DB="clinical_care_tools"
RETENTION_DAYS=2920  # 8 years (2920 days)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Perform backup (custom format for pg_restore)
echo "Starting PostgreSQL backup..."
docker exec "$POSTGRES_CONTAINER" pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -Fc \
    -Z 9 \
    > "$BACKUP_DIR/database.dump"

# Verify backup integrity
echo "Verifying backup..."
pg_restore --list "$BACKUP_DIR/database.dump" > /dev/null

# Encrypt backup (AES-256)
echo "Encrypting backup..."
tar czf - "$BACKUP_DIR" | \
    openssl enc -aes-256-cbc -salt -pbkdf2 \
    -pass file:/etc/clinical-tools/backup-password.txt \
    -out "$BACKUP_DIR.tar.gz.enc"

# Remove unencrypted backup
rm -rf "$BACKUP_DIR"

# Copy to offsite storage
echo "Copying to offsite storage..."
cp "$BACKUP_DIR.tar.gz.enc" /mnt/nas/clinical-backups/

# Purge old backups (>8 years)
echo "Purging old backups..."
find /mnt/nas/clinical-backups/ -name "*.tar.gz.enc" -mtime +$RETENTION_DAYS -delete

echo "Backup complete: $BACKUP_DIR.tar.gz.enc"
```

---

## Performance Requirements

### Response Time Targets

| Endpoint | Target (P95) | Max Acceptable |
|----------|--------------|----------------|
| User login | <200ms | 500ms |
| API endpoints (GET) | <300ms | 500ms |
| API endpoints (POST/PUT) | <500ms | 1000ms |
| Patient search | <500ms | 1000ms |
| Document upload | <1s | 3s |
| MedCAT processing | <30s | 60s |
| Audit log query | <800ms | 1500ms |

### Concurrent User Capacity

- **Target**: 10 concurrent users
- **Max**: 15 concurrent users (with degraded performance)

### Database Performance

- **Connection pooling**: 10 connections (min 5, max overflow 20)
- **Query timeout**: 30 seconds
- **Slow query logging**: >500ms

### Frontend Performance

- **First Contentful Paint (FCP)**: <1.5s
- **Time to Interactive (TTI)**: <3s
- **Largest Contentful Paint (LCP)**: <2.5s

---

## Document Deduplication Strategy

### Problem Statement

Multiple users may upload the same clinical document (e.g., same discharge letter uploaded by different clinicians), causing:
- Wasted MedCAT processing time (~30 seconds per document)
- Duplicate storage (~50 KB per document)
- Inconsistent patient records
- Confusion about which document version is canonical

### Solution: SHA-256 Hash-Based Deduplication

**Strategy**: Compute SHA-256 hash of document content before processing. Check if hash exists in Redis cache or database before accepting upload.

### Implementation

#### 1. Document Upload Flow with Deduplication

```python
# app/api/endpoints/documents.py
from hashlib import sha256
import aioredis

@router.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile,
    project_id: UUID,
    user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db)
):
    # Read file content
    content = await file.read()

    # Compute SHA-256 hash
    content_hash = sha256(content).hexdigest()

    # Check Redis cache first (fast)
    cached_doc_id = await redis.get(f"doc_hash:{content_hash}")
    if cached_doc_id:
        # Document already processed
        await audit_log(
            user_id=user.id,
            action="DOCUMENT_DUPLICATE_DETECTED",
            resource_id=cached_doc_id,
            details={"hash": content_hash, "project_id": str(project_id)}
        )

        # Link existing document to this project (if not already linked)
        await link_document_to_project(cached_doc_id, project_id)

        return {
            "id": cached_doc_id,
            "status": "duplicate",
            "message": "Document already processed. Linked to your project."
        }

    # Check database (if not in Redis cache)
    result = await db.execute(
        select(Document).where(Document.content_hash == content_hash)
    )
    existing_doc = result.scalar_one_or_none()

    if existing_doc:
        # Document exists in DB but not in cache - update cache
        await redis.setex(
            f"doc_hash:{content_hash}",
            86400 * 30,  # Cache for 30 days
            str(existing_doc.id)
        )

        await link_document_to_project(existing_doc.id, project_id)

        return {
            "id": str(existing_doc.id),
            "status": "duplicate",
            "message": "Document already processed. Linked to your project."
        }

    # New document - proceed with upload and encryption
    encrypted_content = encrypt_aes_256(content)

    document = Document(
        filename=file.filename,
        content_type=file.content_type,
        content_hash=content_hash,
        encrypted_content=encrypted_content,
        encryption_algorithm="AES-256-GCM",
        uploaded_by=user.id,
        project_id=project_id,
        file_size=len(content)
    )

    db.add(document)
    await db.commit()

    # Cache the hash → document ID mapping
    await redis.setex(
        f"doc_hash:{content_hash}",
        86400 * 30,  # 30 days
        str(document.id)
    )

    # Queue for MedCAT processing
    await queue_medcat_processing(document.id)

    return {
        "id": str(document.id),
        "status": "processing",
        "message": "Document uploaded and queued for processing."
    }
```

#### 2. Database Schema Update

```sql
-- Add content_hash column to documents table
ALTER TABLE documents
ADD COLUMN content_hash VARCHAR(64) NOT NULL,
ADD CONSTRAINT documents_content_hash_unique UNIQUE (content_hash);

-- Create index for fast hash lookups
CREATE INDEX idx_documents_content_hash ON documents(content_hash);

-- Create document_projects link table (many-to-many)
CREATE TABLE document_projects (
    document_id UUID NOT NULL REFERENCES documents(id),
    project_id UUID NOT NULL REFERENCES projects(id),
    linked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    linked_by UUID NOT NULL REFERENCES users(id),

    PRIMARY KEY (document_id, project_id)
);
```

#### 3. Redis Cache Configuration

```yaml
# docker-compose.yml
redis:
  image: redis:7.2-alpine
  command: >
    redis-server
    --save 60 1000
    --appendonly yes
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
```

**Cache Keys**:
- `doc_hash:{sha256}` → `{document_id}` (TTL: 30 days)
- Eviction policy: LRU (least recently used)

### Benefits

- ✅ **Performance**: Saves ~30 seconds MedCAT processing per duplicate
- ✅ **Storage**: Saves ~50 KB per duplicate document
- ✅ **Consistency**: Single source of truth for each unique document
- ✅ **Cost**: Reduces MedCAT compute costs
- ✅ **User Experience**: Instant response for duplicates

### Edge Cases

**Scenario 1: Same document, different filename**
- **Detection**: SHA-256 hash identical → duplicate detected
- **Action**: Link to existing document, notify user

**Scenario 2: Different document, same filename**
- **Detection**: SHA-256 hash different → new document
- **Action**: Upload as new document

**Scenario 3: Document modified after upload**
- **Detection**: SHA-256 hash different → new document
- **Action**: Upload as new version (different document_id)

**Scenario 4: User intentionally re-uploads for re-processing**
- **User action**: Admin can force re-upload with `?force=true` parameter
- **Action**: Bypass deduplication check, create new document record

### Monitoring

**Metrics to track**:
- Deduplication rate: `duplicates / total_uploads`
- Cache hit rate: `redis_hits / (redis_hits + db_checks)`
- Storage saved: `duplicate_count * avg_file_size`
- Processing time saved: `duplicate_count * 30 seconds`

---

## Scaling Strategy: Upgrade Path Beyond Single Workstation

### Current Architecture (Single Workstation)

**Capacity**: 10 concurrent users, 1 workstation, shared Docker Compose deployment

**Limitations**:
- No horizontal scaling
- Single point of failure
- Limited to workstation resources (CPU, RAM, disk)
- No geographic distribution

### Scaling Triggers

**When to scale**:
1. **User load**: >10 concurrent users
2. **Performance**: Response times >1 second
3. **Availability**: Uptime requirements >99.5% (need redundancy)
4. **Geographic**: Multiple hospital sites
5. **Compliance**: Data residency requirements

### Tier 1: Vertical Scaling (Single Workstation Optimization)

**Capacity**: 20-30 concurrent users

**Changes**:
- Upgrade workstation hardware (32 GB RAM, 8 cores)
- Add GPU for MedCAT processing (2-3x speedup)
- Use NVMe SSD for PostgreSQL (faster I/O)
- Increase PostgreSQL connection pool (max 30 connections)
- Add Redis memory (2 GB)

**Cost**: ~$2,000 hardware upgrade
**Timeline**: 1-2 days

---

### Tier 2: Multi-Node Deployment (Small Cluster)

**Capacity**: 50-100 concurrent users

#### Architecture Changes

```
┌─────────────────────────────────────────────────────────────────────┐
│ Hospital Network                                                     │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Load Balancer (nginx)                                           │ │
│  │ :443 (HTTPS)                                                    │ │
│  └────────┬───────────────────────────────────────────────────────┘ │
│           │                                                           │
│  ┌────────┼────────────────┐                                         │
│  │        │                │                                         │
│  ▼        ▼                ▼                                         │
│ ┌────┐  ┌────┐           ┌────┐                                     │
│ │App │  │App │    ...    │App │  (3 replicas)                       │
│ │ 1  │  │ 2  │           │ N  │                                      │
│ └──┬─┘  └──┬─┘           └──┬─┘                                     │
│    │       │                │                                        │
│    └───────┼────────────────┘                                        │
│            │                                                          │
│  ┌─────────┴─────────────────────────────┐                          │
│  │                                         │                          │
│  ▼                                         ▼                          │
│ ┌────────────────┐            ┌────────────────────┐                │
│ │ PostgreSQL     │            │ Redis Cluster      │                │
│ │ Primary +      │            │ (3 nodes)          │                │
│ │ 2 Replicas     │            │                    │                │
│ └────────────────┘            └────────────────────┘                │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ MedCAT Service Pool (3 instances)                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

#### Key Changes

1. **Load Balancer** (nginx or HAProxy)
   - Distributes requests across backend replicas
   - SSL termination
   - Health checks
   - Session sticky routing (via Redis sessions)

2. **Backend Application Replicas** (3+ instances)
   - Stateless FastAPI containers
   - Shared Redis for sessions
   - Horizontal autoscaling based on CPU/memory

3. **PostgreSQL High Availability**
   - Primary + 2 read replicas (Patroni + etcd)
   - Automatic failover (<30 seconds)
   - Write to primary, reads from replicas
   - Connection pooling via PgBouncer

4. **Redis Cluster** (3 nodes)
   - High availability via Redis Sentinel
   - Automatic failover
   - Shared sessions across all app instances

5. **MedCAT Service Pool**
   - 3+ MedCAT instances for parallel processing
   - Load balanced via internal DNS
   - Shared model volume (NFS or CephFS)

#### Migration Steps

1. **Week 1: Infrastructure Setup**
   - Deploy Kubernetes cluster (K3s for edge) or Docker Swarm
   - Configure shared storage (NFS/Ceph)
   - Setup PostgreSQL replication
   - Setup Redis cluster

2. **Week 2: Application Changes**
   - Move sessions from PostgreSQL to Redis
   - Update connection strings for replicas
   - Implement health check endpoints
   - Add graceful shutdown handlers

3. **Week 3: Load Balancer & Testing**
   - Configure nginx load balancer
   - Setup SSL certificates
   - Load testing with 50 concurrent users
   - Failover testing

4. **Week 4: Migration & Cutover**
   - Blue-green deployment
   - Gradual traffic shift (10% → 50% → 100%)
   - Monitor performance and errors
   - Rollback plan ready

**Cost**: ~$10,000 (3 servers) + ~40 hours labor
**Timeline**: 4 weeks

---

### Tier 3: Cloud-Native Deployment (Enterprise Scale)

**Capacity**: 500+ concurrent users, multi-site

#### Architecture

- **Kubernetes** (AWS EKS, Azure AKS, or on-prem)
- **Managed PostgreSQL** (AWS RDS, Azure Database for PostgreSQL)
- **Managed Redis** (AWS ElastiCache, Azure Cache for Redis)
- **Object Storage** (S3, Azure Blob) for documents
- **CDN** (CloudFront, Azure CDN) for frontend assets
- **Auto-scaling**: 5-50 backend pods based on load
- **Geographic distribution**: Multi-region deployment

**Cost**: ~$5,000/month cloud infrastructure
**Timeline**: 8-12 weeks

---

### Backward Compatibility

**All scaling tiers maintain**:
- Same API contracts (OpenAPI spec unchanged)
- Same database schema
- Same authentication flow
- Same frontend code
- Same Docker images

**Environment Variables**: Different configs, same codebase

```bash
# Single workstation (.env)
DATABASE_URL=postgresql://localhost:5432/clinical_care_tools
REDIS_URL=redis://localhost:6379

# Multi-node (.env)
DATABASE_URL=postgresql://postgres-primary:5432/clinical_care_tools
DATABASE_REPLICA_URLS=postgresql://postgres-replica-1:5432/...,postgresql://postgres-replica-2:5432/...
REDIS_URL=redis://redis-sentinel:26379/0
REDIS_SENTINEL_NODES=redis-sentinel-1:26379,redis-sentinel-2:26379
```

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **MedCAT Service downtime** | High | Medium | Retry logic (3 attempts), circuit breaker, queue for offline processing |
| **Database migration failure** | High | Low | Backup before migration, test in staging, rollback script, alembic downgrade |
| **JWT secret key leak** | Critical | Low | Rotate keys, environment variables only, never commit to git, 256-bit random |
| **Session hijacking** | High | Medium | IP/user-agent binding, suspicious activity detection, force logout, 2-session limit |
| **Slow MedCAT processing** | Medium | High | Background jobs (FastAPI BackgroundTasks), progress tracking, user notification |
| **Document storage overflow** | Medium | Medium | Retention policy (8 years), automated purging, compression, monitor disk usage |
| **Concurrent user limit exceeded** | Medium | Low | Connection pooling limits, rate limiting (429), user feedback |
| **PHI exposure in logs** | Critical | Medium | Code review, no PHI in application logs, audit logs only, sanitize error messages |
| **Password brute force** | High | Medium | Account lockout (5 failed attempts, 15-minute cooldown), CAPTCHA (future), rate limiting |
| **Data loss** | Critical | Low | Daily backups (automated), offsite storage, monthly restore tests, RAID storage |

---

## Implementation Phases

### Phase 0: Environment Setup & MedCAT Model Preparation (Week 0, ~20 hours)

**Goal**: Prepare development environment, download MedCAT models, verify all infrastructure components

**Why This Phase**: Environment setup and model preparation often take longer than expected due to:
- Large model downloads (2-5 GB)
- Dependency conflicts
- Docker configuration issues
- Network connectivity problems
- Model compatibility verification

**Tasks**:
1. **Development Workstation Setup** (~3 hours)
   - Install Docker Desktop 24.0+ (Windows/Linux)
   - Install Docker Compose 2.20+
   - Configure Docker resource limits (8 GB RAM, 4 CPU cores minimum)
   - Verify Docker installation: `docker --version`, `docker-compose --version`

2. **MedCAT Model Download** (~8 hours, mostly waiting)
   - Download SNOMED-CT model from MedCAT Model Zoo (or custom model)
   - Download UMLS model (if required)
   - Verify model integrity (checksums)
   - Extract models to `medcat_models/` directory
   - Test model loading with simple MedCAT script

3. **Docker Compose Initial Configuration** (~3 hours)
   - Create initial `docker-compose.yml` with all services
   - Create `.env` file template with required variables
   - Create shared volumes: `postgres_data`, `redis_data`, `medcat_models`, `backend_logs`
   - Test `docker-compose up` with empty services (health checks)

4. **Database Setup** (~2 hours)
   - Start PostgreSQL container
   - Create initial database: `clinical_care_tools`
   - Create database user with appropriate permissions
   - Test database connection from host machine
   - Install PostgreSQL client tools (psql, pg_dump)

5. **Redis Setup** (~1 hour)
   - Start Redis container
   - Configure persistence (RDB + AOF)
   - Test Redis connection: `redis-cli ping`
   - Verify TTL expiration works

6. **MedCAT Service Setup** (~2 hours)
   - Build/pull MedCAT Service Docker image
   - Configure model paths in environment variables
   - Start MedCAT Service
   - Test `/api/info` endpoint
   - Test simple text processing: POST `/api/process`

7. **Verification Script** (~1 hour)
   - Create `scripts/verify-environment.sh` to check:
     - Docker and Docker Compose installed
     - All volumes created
     - PostgreSQL accepting connections
     - Redis responding to PING
     - MedCAT Service processing text
     - Models loaded successfully
   - Run verification script and fix any issues

**Deliverables**:
- Running Docker Compose environment with all services
- MedCAT models downloaded and verified
- PostgreSQL database created and accessible
- Redis cache operational
- MedCAT Service processing test documents
- Verification script passing all checks
- Documentation of any environment-specific issues

**Acceptance Criteria**:
- ✅ `docker-compose up` starts all 5 services (frontend, backend, postgres, redis, medcat)
- ✅ All health checks passing
- ✅ MedCAT models load in <30 seconds
- ✅ MedCAT can process sample clinical text
- ✅ PostgreSQL accepts connections
- ✅ Redis PING returns PONG
- ✅ `scripts/verify-environment.sh` exits with status 0
- ✅ Team members can replicate setup from documentation

**Common Issues & Fixes**:
- **Docker out of memory**: Increase Docker Desktop RAM to 8+ GB
- **Model download timeout**: Use wget/curl with resume support
- **PostgreSQL auth failure**: Check `POSTGRES_HOST_AUTH_METHOD` in docker-compose.yml
- **MedCAT model not found**: Verify volume mount paths match model directory
- **Redis permission denied**: Check volume ownership: `chown -R 999:999 redis_data/`

---

### Phase 1: Core Infrastructure (Week 1-2, ~60 hours)

**Goal**: Docker Compose environment with PostgreSQL, authentication, audit logging

**Tasks**:
1. Setup Docker Compose (postgres, backend, frontend services)
2. Database schema (users, projects, project_members, tasks, audit_logs, modules, sessions tables)
3. Alembic migrations (7 core migrations)
4. JWT authentication (login, logout, token validation)
5. Session management (create, validate, timeout, force logout)
6. RBAC implementation (roles, permissions, decorators)
7. Audit logging service (comprehensive WHO/WHAT/WHEN/WHERE)
8. First-time setup script (admin user creation, module initialization)
9. Health check endpoint
10. Unit tests (≥80% coverage for auth, audit)

**Deliverables**:
- Running Docker Compose environment
- Database with core tables
- Login/logout endpoints
- Audit log trail
- Admin user creation

**Acceptance Criteria**:
- `docker-compose up` starts all services
- Admin can login at `http://localhost:8080`
- All API requests logged to audit_logs table
- Health check returns 200 OK
- Tests pass: `pytest tests/`

---

### Phase 2: User & Project Management (Week 3, ~30 hours)

**Goal**: Admin UI for user management, project creation, task assignment

**Tasks**:
1. User CRUD API endpoints (GET, POST, PATCH for users)
2. Project CRUD API endpoints
3. Project membership API (add/remove users from projects)
4. Task CRUD API endpoints
5. Frontend user management component (Vue + Vuetify)
6. Frontend project management component
7. Frontend task list component
8. Integration tests for user/project APIs
9. E2E test: Admin creates user → user logs in

**Deliverables**:
- User management UI (create, edit, deactivate users)
- Project management UI
- Task assignment UI

**Acceptance Criteria**:
- Admin can create users with roles
- Admin can create projects and assign users
- Admin can create tasks and assign to users
- Users see only their assigned tasks
- All operations logged to audit trail

---

### Phase 3: Document Upload & PHI Extraction (Week 4, ~40 hours)

**Goal**: Document upload with encryption, MedCAT integration, PHI extraction workflow

**Tasks**:
1. Document upload API endpoint (AES-256 encryption)
2. MedCAT client (async, retry logic)
3. Background job processing (FastAPI BackgroundTasks)
4. PHI extraction workflow (4 steps: upload → process → aggregate → search)
5. ExtractedEntity table and model
6. Patient table and model
7. Patient aggregation logic (NHS number matching, fuzzy name+DOB)
8. Document processing status tracking
9. Unit tests for encryption, MedCAT client
10. Integration tests for document upload → PHI extraction

**Deliverables**:
- Document upload UI
- Encrypted document storage
- MedCAT integration
- Patient aggregation
- PHI entities extracted to structured tables

**Acceptance Criteria**:
- RTF documents uploaded and encrypted
- MedCAT processes documents asynchronously
- PHI entities extracted (NHS number, name, DOB, address)
- Patients aggregated via NHS number matching
- All operations logged with DOCUMENT_UPLOAD, PHI_EXTRACT actions

---

### Phase 4: Module System & Patient Search Module (Week 5-6, ~50 hours)

**Goal**: Pluggable module system with Patient Search as first module

**Tasks**:
1. Module registry (database table, module loader)
2. Module registration API (backend discovers modules)
3. Frontend module loader (dynamic route registration)
4. Patient Search module (first module implementation)
   - API: POST /api/v1/modules/patient-search/search
   - Frontend: PatientSearch.vue component
   - Service: PatientSearchService (business logic)
5. Meta-annotation filtering (Negation, Experiencer, Temporality)
6. Search results display (confidence scores, meta-annotations)
7. Module enable/disable toggle (admin UI)
8. Unit tests for module loader
9. Integration tests for patient search
10. E2E test: Clinician searches for patients → views results

**Deliverables**:
- Module system (registry, loader, dynamic routes)
- Patient Search module (fully functional)
- Meta-annotation filtering
- Admin module management UI

**Acceptance Criteria**:
- Modules discovered automatically from `app/modules/` directory
- Patient Search module registered and enabled
- Clinicians can search by medical concepts
- Results filtered by meta-annotations (95% precision)
- Admin can enable/disable modules without code changes

---

### Phase 5: Session Security & Break-Glass Access (Week 7, ~30 hours)

**Goal**: Enhanced session security and emergency access mechanisms

**Tasks**:
1. Session binding (IP hash, user-agent hash)
2. Session hijacking detection
3. Idle timeout (15 minutes)
4. Concurrent session limits (max 2)
5. Admin force logout
6. Break-glass access API
7. Break-glass access UI
8. Post-access review workflow
9. Security notification system (email alerts)
10. Unit tests for session security
11. Integration tests for break-glass

**Deliverables**:
- Session security enhancements
- Break-glass emergency access
- Security alerts
- Post-access review dashboard

**Acceptance Criteria**:
- Sessions bound to IP and user-agent
- Session hijacking detected and blocked
- Idle sessions terminated after 15 minutes
- Users limited to 2 concurrent sessions
- Break-glass access granted with 60-minute expiry
- Security team notified immediately
- Post-access review completed within 24 hours

---

### Phase 6: Data Retention & Clinical Safety (Week 8, ~30 hours)

**Goal**: Automated data retention, clinical safety mechanisms

**Tasks**:
1. Data retention policies (documents: 8 years, audit logs: 7 years)
2. Legal hold workflow (flag + reason + owner)
3. Automated purging scripts (cron jobs)
4. Anonymization for research use
5. Clinical overrides table and API
6. Critical findings table and API
7. Clinical incidents table and integration
8. Patient Safety Dashboard (admin UI)
9. Auto-escalation for critical findings (4-hour threshold)
10. Unit tests for purging, anonymization, clinical safety

**Deliverables**:
- Automated data purging (respects retention policies)
- Legal hold mechanism
- Clinical override tracking
- Critical finding alerts
- Patient Safety Dashboard

**Acceptance Criteria**:
- Data purged automatically after retention period
- Legal holds prevent purging
- Clinician overrides tracked for quality improvement
- Critical findings escalated if not acknowledged within 4 hours
- Admin views Patient Safety Dashboard with alerts

---

### Phase 7: Testing, Documentation & Deployment (Week 9-10, ~50 hours)

**Goal**: Comprehensive testing, production deployment, documentation

**Tasks**:
1. Increase test coverage to ≥80% (unit tests)
2. Integration tests for all critical paths
3. E2E tests for 5-10 user journeys (Playwright)
4. Performance testing (Locust: 10 concurrent users)
5. Security audit (code review, penetration testing)
6. API documentation (OpenAPI spec review)
7. Deployment documentation (installation, configuration, maintenance)
8. User documentation (clinician guide, admin guide)
9. Training materials (videos, screenshots)
10. Production deployment checklist
11. Disaster recovery testing (restore from backup)

**Deliverables**:
- Test coverage ≥80%
- Performance validated (10 concurrent users, P95 <500ms)
- Security audit passed
- Complete documentation (deployment, user, admin)
- Production-ready release

**Acceptance Criteria**:
- All tests passing (unit, integration, E2E)
- Performance targets met (P95 response times)
- No critical security vulnerabilities
- Documentation complete and reviewed
- Backup/restore tested successfully
- First production deployment successful

---

## Summary

This Technical Plan provides comprehensive guidance for implementing the Clinical Care Tools Base Application. The plan covers:

1. **Architecture**: Core + Modules pattern for extensibility, Redis for sessions/cache
2. **Technology Stack**: FastAPI + Vue 3 + PostgreSQL + Redis + Docker
3. **API Design**: RESTful endpoints with OpenAPI documentation
4. **Database**: 13 core tables with migrations, audit trail, PHI storage
5. **Security**: JWT auth, RBAC, session binding, break-glass access, AES-256 encryption
6. **MedCAT Integration**: Async client with retry logic, PHI extraction workflow
7. **Document Deduplication**: SHA-256 hash-based duplicate detection, Redis caching
8. **PHI Validation**: Comprehensive test suite for de-identification and protection
9. **Testing**: Test pyramid (70% unit, 25% integration, 5% E2E), ≥80% coverage, PHI-specific tests
10. **Deployment**: Docker Compose, single workstation, RDP access
11. **Scaling Strategy**: 3-tier upgrade path (vertical → multi-node → cloud-native)
12. **Performance**: <500ms API responses, 10 concurrent users (20-30 with vertical scaling)
13. **Implementation**: 8 phases (Phase 0 + 7 implementation phases) over 11 weeks (~310 hours total)

**Key Enhancements (v1.1)**:
- ✅ Phase 0 added for environment setup and MedCAT model preparation (~20 hours)
- ✅ Redis integrated for session management, caching, and deduplication
- ✅ Document deduplication strategy to prevent duplicate uploads
- ✅ PHI validation tests for compliance verification
- ✅ 3-tier scaling strategy documented (10 → 30 → 100+ users)

**Next Steps**:
1. User reviews and approves this Technical Plan
2. Create Task Breakdown using `tech-plan-to-tasks` skill
3. Begin Phase 0: Environment Setup & MedCAT Model Preparation

---

**Plan Author**: AI Assistant (Claude Code)
**Date**: 2025-11-08
**Version**: 1.1.0
**Estimated Implementation Time**: 11 weeks (2 developers)
**Total Estimated Hours**: ~310 hours (Phase 0: 20h, Phases 1-7: 290h)
