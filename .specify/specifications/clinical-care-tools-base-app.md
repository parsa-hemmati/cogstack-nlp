# Specification: Clinical Care Tools Base Application

**Version**: 1.1.0
**Date**: 2025-11-08
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]

**Version History**:
- **1.1.0** (2025-11-08): Added 5 CRITICAL sections for production readiness (Data Retention, Disaster Recovery, Clinical Safety, Break-Glass Access, Session Security)
- **1.0.0** (2025-11-08): Initial specification with Core + Modules architecture and PHI extraction workflow

---

## Table of Contents

1. [Context](#context)
2. [Goals](#goals)
3. [Non-Goals](#non-goals)
4. [User Stories](#user-stories)
5. [Requirements](#requirements)
6. [Architecture](#architecture)
7. [Database Schema](#database-schema)
8. [Authentication & Authorization](#authentication--authorization)
9. [Audit Logging](#audit-logging)
10. [Module System](#module-system)
11. [Deployment Model](#deployment-model)
12. [Constraints](#constraints)
13. [Acceptance Criteria](#acceptance-criteria)
14. [Alignment with Constitution](#alignment-with-constitution)
15. [Data Retention & Purging Policy](#data-retention--purging-policy)
16. [Disaster Recovery & Business Continuity](#disaster-recovery--business-continuity)
17. [Clinical Safety Mechanisms](#clinical-safety-mechanisms)
18. [Enhanced Authentication - Break-Glass Access](#enhanced-authentication---break-glass-access)
19. [Session Security Enhancements](#session-security-enhancements)
20. [Open Questions](#open-questions)

---

## Context

### Background

The CogStack NLP ecosystem includes three production-ready applications:
- **MedCAT v2**: Core NLP library (228 Python files, PyPI published)
- **MedCAT Trainer**: Annotation platform (Vue 3 + Django + PostgreSQL, 65 components, 95 migrations)
- **MedCAT Service**: REST API microservice (FastAPI, Docker deployment)

These tools serve **researchers and annotators** for model training and annotation workflows.

### The Gap

There is currently **no application for clinical care workflows** - tools that clinicians use during patient care delivery:
- Patient search and discovery
- Timeline visualization of patient history
- Real-time clinical decision support
- Cohort identification for research

### The Problem

We need a **base application** that:
1. **Runs on a single workstation** (not cloud-based SaaS)
2. **Supports multiple users** (admin + clinicians) accessing via remote desktop
3. **Isolates user work** (each user sees only their assigned tasks)
4. **Enables collaboration** (multiple users working on same project)
5. **Provides auditability** (track WHO did WHAT, WHEN for clinical governance)
6. **Supports modular features** (patient search, timeline, CDS as pluggable modules)

### Deployment Context

**Scenario**: Hospital/clinic workstation deployment
- **Admin** installs Docker Compose on single workstation (Windows/Linux)
- **Clinicians** RDP to workstation, open browser to `http://localhost:8080`
- **Data** stays entirely local (no cloud/SaaS)
- **Admin** manages system (Docker Compose hidden from clinicians)

**Why this deployment model?**
- **Data sovereignty**: Healthcare organizations require on-premise deployments
- **Regulatory compliance**: Easier HIPAA/GDPR compliance with local data
- **Cost**: No per-user SaaS fees
- **Simplicity**: Single workstation, no distributed infrastructure
- **Multi-user**: Multiple clinicians access same system via RDP

---

## Goals

### Primary Goals

1. **Multi-User Architecture** (P0)
   - Support admin + multiple clinician users on single workstation
   - User authentication with username/password (no OIDC - too complex)
   - Role-based access control (Admin, Clinician, Researcher roles)
   - User isolation (users see only their assigned tasks)

2. **Shared Resources** (P0)
   - Shared MedCAT model database (all users use same models)
   - Shared PostgreSQL database (centralized storage)
   - Shared document repository (clinical notes, reports)
   - Shared configuration (admin manages once)

3. **Collaborative Workflows** (P0)
   - Project-based access (multiple users work on same project)
   - Task assignment (admin assigns tasks to specific users)
   - No task overlap (user A's tasks don't interfere with user B's)
   - Shared results (annotations from multiple users train same model)

4. **Comprehensive Audit Logging** (P0)
   - Track WHO (user ID, username)
   - Track WHAT (action: view, create, update, delete)
   - Track WHEN (timestamp with timezone)
   - Track WHERE (IP address, session ID)
   - Track RESOURCE (patient ID, document ID, project ID)
   - Query audit logs (for compliance reporting)

5. **Modular Architecture** (P0)
   - Core base app (auth, audit, config, module loader)
   - Pluggable modules (patient search, timeline, CDS, cohort builder)
   - Module independence (disable modules without affecting core)
   - Module registry (discover and load modules dynamically)

### Secondary Goals

6. **Docker Compose Deployment** (P1)
   - Single `docker-compose.yml` file
   - Services: Frontend (Vue 3), Backend (FastAPI), PostgreSQL, MedCAT Service
   - Volume mounts for data persistence
   - Localhost networking only
   - First-time setup script

7. **Configuration Management** (P1)
   - Admin UI for configuration (no manual .env editing)
   - Module enable/disable toggles
   - User management (create, edit, delete users)
   - Project management (create projects, assign users)

8. **Performance** (P1)
   - API response time <500ms (P95)
   - Concurrent users: 10 (realistic for single workstation)
   - Database connection pooling
   - Caching for MedCAT model loading

---

## Non-Goals

1. **Cloud/SaaS Deployment** - This spec is for single-workstation only
2. **Horizontal Scaling** - No multi-server deployment (not needed for 10 users)
3. **OIDC/Keycloak** - Too complex for single workstation; using username/password
4. **Distributed Tracing** - Overkill for monolithic deployment
5. **Multi-Tenancy** - Single organization deployment
6. **Real-Time Collaboration** - No WebSockets/live updates (future consideration)
7. **Mobile Support** - Desktop browser only
8. **Offline Mode** - Requires network connection to workstation

---

## User Stories

### Admin User Stories

#### US-A1: System Installation
**As an** IT administrator  
**I want to** install the Clinical Care Tools Base App with Docker Compose  
**So that** clinicians can access the system on the workstation

**Acceptance Criteria**:
- [ ] Single `docker-compose.yml` file with all services
- [ ] First-run setup script creates admin user
- [ ] System accessible at `http://localhost:8080`
- [ ] Installation documentation <30 minutes
- [ ] Health check endpoint confirms all services running

---

#### US-A2: User Management
**As an** admin  
**I want to** create, edit, and delete user accounts  
**So that** I can control who has access to the system

**Acceptance Criteria**:
- [ ] Admin UI for user management (CRUD operations)
- [ ] Assign roles: Admin, Clinician, Researcher
- [ ] Set username and temporary password (user changes on first login)
- [ ] Deactivate users (soft delete, not hard delete for audit trail)
- [ ] View user activity logs

---

#### US-A3: Project Creation
**As an** admin  
**I want to** create projects and assign users  
**So that** teams can collaborate on specific clinical workflows

**Acceptance Criteria**:
- [ ] Create project with name, description, dataset
- [ ] Assign multiple users to project (project membership)
- [ ] Define project type (Patient Search, Timeline Review, CDS, etc.)
- [ ] Configure MedCAT model for project
- [ ] View project status and member activity

---

#### US-A4: Task Assignment
**As an** admin  
**I want to** assign specific tasks to users  
**So that** work is distributed and tracked

**Acceptance Criteria**:
- [ ] Create task with name, description, assigned user, project, due date
- [ ] Task types: Annotation, Search, Review, Validation
- [ ] View all tasks (filter by user, project, status)
- [ ] Update task status (Pending, In Progress, Complete)
- [ ] Reassign tasks if user unavailable

---

#### US-A5: Module Management
**As an** admin  
**I want to** enable/disable modules  
**So that** I can control which features are available to users

**Acceptance Criteria**:
- [ ] Admin UI shows installed modules (Patient Search, Timeline, CDS, etc.)
- [ ] Toggle module on/off (hot reload, no restart required)
- [ ] Configure module settings (API keys, thresholds, etc.)
- [ ] View module version and dependencies
- [ ] Uninstall modules (remove files, database tables)

---

### Clinician User Stories

#### US-C1: Login and Authentication
**As a** clinician  
**I want to** log in with my username and password  
**So that** I can securely access the system

**Acceptance Criteria**:
- [ ] Login page with username/password fields
- [ ] Session token stored securely (httpOnly cookie)
- [ ] Token expiry after 8 hours (workday)
- [ ] Force password change on first login
- [ ] Logout button visible on all pages

---

#### US-C2: View Assigned Tasks
**As a** clinician  
**I want to** see my assigned tasks  
**So that** I know what work I need to complete

**Acceptance Criteria**:
- [ ] Dashboard shows "My Tasks" list
- [ ] Filter tasks by status (Pending, In Progress, Complete)
- [ ] Sort tasks by due date, priority, project
- [ ] Click task to open related module (e.g., Patient Search)
- [ ] Mark task as complete when done

---

#### US-C3: Access Shared Resources
**As a** clinician  
**I want to** access shared documents and models  
**So that** I can perform my work using organizational resources

**Acceptance Criteria**:
- [ ] View documents in assigned projects (read-only or editable based on task)
- [ ] Use MedCAT models configured by admin
- [ ] See results from other team members (if project allows collaboration)
- [ ] Cannot access projects I'm not assigned to (403 Forbidden)

---

#### US-C4: Work Isolation
**As a** clinician  
**I want to** see only my tasks and assigned projects  
**So that** I'm not overwhelmed by other users' work

**Acceptance Criteria**:
- [ ] Dashboard shows only my tasks
- [ ] Project list shows only projects I'm a member of
- [ ] Search results scoped to my projects
- [ ] Cannot view/edit other users' annotations or tasks
- [ ] Admin users can see all projects (for oversight)

---

### Researcher User Stories

#### US-R1: Cohort Identification
**As a** researcher  
**I want to** create cohort queries across multiple projects  
**So that** I can identify study populations

**Acceptance Criteria**:
- [ ] Query builder UI (concepts, date ranges, meta-annotations)
- [ ] Execute query across assigned projects only
- [ ] View patient count and demographics
- [ ] Export cohort list (de-identified)
- [ ] Save query for re-use

---

## Requirements

### Functional Requirements

#### FR1: User Authentication
- **FR1.1**: System SHALL support username/password authentication
- **FR1.2**: System SHALL enforce password complexity (min 12 chars, uppercase, lowercase, number, special)
- **FR1.3**: System SHALL lock account after 5 failed login attempts
- **FR1.4**: System SHALL force password change on first login
- **FR1.5**: System SHALL expire sessions after 8 hours of inactivity

#### FR2: User Management
- **FR2.1**: Admin SHALL be able to create users (username, email, role, temporary password)
- **FR2.2**: Admin SHALL be able to edit user roles (Admin, Clinician, Researcher)
- **FR2.3**: Admin SHALL be able to deactivate users (soft delete)
- **FR2.4**: System SHALL prevent deletion of users with associated data (enforce referential integrity)
- **FR2.5**: System SHALL log all user management actions (audit trail)

#### FR3: Project Management
- **FR3.1**: Admin SHALL be able to create projects (name, description, dataset, MedCAT model)
- **FR3.2**: Admin SHALL be able to assign multiple users to projects (project membership)
- **FR3.3**: Users SHALL see only projects they are assigned to (unless admin)
- **FR3.4**: Admin SHALL be able to configure project settings (model, meta-annotations, task types)
- **FR3.5**: System SHALL track project status (Active, Complete, Archived)

#### FR4: Task Assignment
- **FR4.1**: Admin SHALL be able to create tasks (name, description, assigned user, project, due date)
- **FR4.2**: Users SHALL see only tasks assigned to them
- **FR4.3**: Users SHALL be able to update task status (In Progress, Complete)
- **FR4.4**: Admin SHALL be able to reassign tasks
- **FR4.5**: System SHALL prevent task deletion (only status change to "Cancelled")

#### FR5: Audit Logging
- **FR5.1**: System SHALL log all user actions (login, logout, view, create, update, delete)
- **FR5.2**: Audit log SHALL capture: user ID, username, action, resource type, resource ID, timestamp, IP address, session ID
- **FR5.3**: Audit logs SHALL be immutable (append-only, no deletion)
- **FR5.4**: Admin SHALL be able to query audit logs (filter by user, action, date range, resource)
- **FR5.5**: System SHALL export audit logs to CSV/JSON for compliance reporting

#### FR6: Module System
- **FR6.1**: System SHALL support pluggable modules (Patient Search, Timeline, CDS, Cohort Builder)
- **FR6.2**: Modules SHALL register with core app (module name, version, routes, permissions)
- **FR6.3**: Admin SHALL be able to enable/disable modules
- **FR6.4**: System SHALL load module routes dynamically (no core code changes required)
- **FR6.5**: Modules SHALL have independent database schemas (via Alembic migrations)

#### FR7: Shared Resources
- **FR7.1**: System SHALL provide shared MedCAT model storage (all users access same models)
- **FR7.2**: System SHALL provide shared document repository (scoped by project membership)
- **FR7.3**: System SHALL provide shared configuration store (admin manages, users read)
- **FR7.4**: System SHALL provide shared PostgreSQL database (connection pooling)

#### FR8: Configuration Management
- **FR8.1**: Admin SHALL configure system settings via UI (no manual .env editing)
- **FR8.2**: System SHALL support module-specific configuration (API keys, thresholds, feature flags)
- **FR8.3**: System SHALL validate configuration changes (schema validation)
- **FR8.4**: System SHALL apply configuration changes without restart (hot reload where possible)

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: API endpoints SHALL respond in <500ms (P95)
- **NFR1.2**: System SHALL support 10 concurrent users
- **NFR1.3**: Database queries SHALL use indexes (query plan analysis required)
- **NFR1.4**: MedCAT model loading SHALL be cached (no repeated loads)
- **NFR1.5**: Frontend page load SHALL be <2s (P95)

#### NFR2: Security
- **NFR2.1**: System SHALL use TLS 1.3 for all network communication (even localhost, for RDP scenarios)
- **NFR2.2**: System SHALL encrypt database at rest (PostgreSQL pgcrypto for PHI fields)
- **NFR2.3**: System SHALL use bcrypt for password hashing (cost factor 12)
- **NFR2.4**: System SHALL implement CSRF protection (SameSite cookies)
- **NFR2.5**: System SHALL sanitize all user inputs (SQL injection, XSS prevention)

#### NFR3: Reliability
- **NFR3.1**: System SHALL have <1 hour RTO (Recovery Time Objective) for backups
- **NFR3.2**: System SHALL automatically backup PostgreSQL daily
- **NFR3.3**: System SHALL log errors to persistent storage
- **NFR3.4**: System SHALL provide health check endpoints (startup, liveness, readiness)
- **NFR3.5**: System SHALL gracefully degrade if MedCAT Service unavailable (queue processing)

#### NFR4: Usability
- **NFR4.1**: Admin UI SHALL follow Material Design guidelines (consistency with MedCAT Trainer)
- **NFR4.2**: Clinician UI SHALL be keyboard-accessible (tab navigation)
- **NFR4.3**: System SHALL provide contextual help (tooltips, inline documentation)
- **NFR4.4**: System SHALL display actionable error messages (not "Error 500")
- **NFR4.5**: System SHALL meet WCAG 2.1 AA accessibility standards

#### NFR5: Maintainability
- **NFR5.1**: Code SHALL have 80% test coverage (100% for critical paths)
- **NFR5.2**: API SHALL follow OpenAPI 3.0 specification
- **NFR5.3**: Database migrations SHALL be versioned (Alembic)
- **NFR5.4**: Docker images SHALL be multi-stage builds (smaller images)
- **NFR5.5**: Documentation SHALL be maintained in Markdown (version controlled)

#### NFR6: Compliance
- **NFR6.1**: System SHALL comply with HIPAA Security Rule (audit logging, encryption, access controls)
- **NFR6.2**: System SHALL support GDPR right to erasure (data deletion workflow)
- **NFR6.3**: System SHALL enforce minimum necessary access (RBAC)
- **NFR6.4**: System SHALL provide audit trail for regulatory inspections
- **NFR6.5**: System SHALL document data flows (for DPIA - Data Protection Impact Assessment)

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  WORKSTATION (Single Machine)                                    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Docker Compose Network                                     │ │
│  │                                                              │ │
│  │  ┌──────────────┐     ┌──────────────┐    ┌──────────────┐│ │
│  │  │ Frontend     │     │ Backend      │    │ MedCAT       ││ │
│  │  │ (Vue 3 +     │────▶│ (FastAPI)    │───▶│ Service      ││ │
│  │  │  Vuetify)    │     │              │    │ (FastAPI)    ││ │
│  │  │              │     │ - Auth       │    │              ││ │
│  │  │ Port: 8080   │     │ - Audit      │    │ Port: 5000   ││ │
│  │  └──────────────┘     │ - Module Mgr │    └──────────────┘│ │
│  │                       │ - Projects   │                     │ │
│  │                       │ - Tasks      │                     │ │
│  │                       │              │                     │ │
│  │                       └───────┬──────┘                     │ │
│  │                               │                            │ │
│  │                               ▼                            │ │
│  │                       ┌──────────────┐                     │ │
│  │                       │ PostgreSQL   │                     │ │
│  │                       │              │                     │ │
│  │                       │ - Users      │                     │ │
│  │                       │ - Projects   │                     │ │
│  │                       │ - Tasks      │                     │ │
│  │                       │ - Audit Logs │                     │ │
│  │                       │ - Modules    │                     │ │
│  │                       │              │                     │ │
│  │                       │ Port: 5432   │                     │ │
│  │                       └──────────────┘                     │ │
│  │                                                              │ │
│  │  ┌────────────────────────────────────────────────────────┐│ │
│  │  │ Volumes (Data Persistence)                             ││ │
│  │  │ - postgres-data (database)                             ││ │
│  │  │ - medcat-models (shared models)                        ││ │
│  │  │ - documents (shared documents)                         ││ │
│  │  │ - logs (audit logs, application logs)                  ││ │
│  │  └────────────────────────────────────────────────────────┘│ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Remote Desktop Users (Clinicians access via RDP/VNC)      │ │
│  │                                                              │ │
│  │  User 1 ─┐                                                  │ │
│  │  User 2 ─┼─▶ Browser ──▶ http://localhost:8080             │ │
│  │  User 3 ─┘                                                  │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Frontend** | Vue 3.5 + TypeScript + Vuetify 3 | Proven in MedCAT Trainer (65 components); Material Design consistency |
| **Backend** | FastAPI 0.115.2 + Python 3.10+ | Lightweight, async support, automatic OpenAPI docs; proven in MedCAT Service |
| **Database** | PostgreSQL 17.6 | ACID compliance, proven in MedCAT Trainer (95 migrations); strong relational integrity |
| **ORM** | SQLAlchemy 2.0 | Type-safe, async support, migrations via Alembic |
| **Auth** | FastAPI Security + JWT | Simple username/password (no OIDC); bcrypt hashing |
| **Containerization** | Docker + Docker Compose | Proven deployment model in MedCAT ecosystem (29 compose files) |
| **Build Tool** | Vite 6.3.4 | Fast HMR, optimized builds (proven in MedCAT Trainer) |
| **Testing** | pytest (backend), Vitest (frontend) | Comprehensive test ecosystems |

### Core + Modules Pattern

```
Backend Structure:
app/
├── core/
│   ├── auth/              # Authentication & authorization
│   ├── audit/             # Audit logging
│   ├── config/            # Configuration management
│   ├── database/          # Database connection & models
│   ├── modules/           # Module registry & loader
│   └── api/               # Core API endpoints (health, version)
│
├── modules/
│   ├── patient_search/    # Patient Search Module
│   │   ├── api/           # FastAPI router
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── migrations/    # Alembic migrations
│   │
│   ├── timeline/          # Timeline Module
│   ├── cds/               # Clinical Decision Support Module
│   └── cohort/            # Cohort Builder Module

Frontend Structure:
frontend/
├── src/
│   ├── core/
│   │   ├── components/    # Shared UI components
│   │   ├── composables/   # Shared logic
│   │   ├── stores/        # Pinia stores (user, config)
│   │   ├── router/        # Vue Router core routes
│   │   └── services/      # API clients (auth, audit, config)
│   │
│   └── modules/
│       ├── patient-search/
│       │   ├── components/
│       │   ├── views/
│       │   ├── stores/
│       │   └── routes.ts  # Module routes
│       │
│       ├── timeline/
│       ├── cds/
│       └── cohort/
```

### Module Registration Pattern

**Backend (FastAPI)**:
```python
# modules/patient_search/api/router.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/patient-search", tags=["patient-search"])

@router.get("/search")
async def search_patients():
    ...

# modules/patient_search/__init__.py
def register_module(app):
    from .api.router import router
    app.include_router(router)
    return {
        "name": "patient-search",
        "version": "1.0.0",
        "permissions": ["patient_search.view", "patient_search.search"]
    }
```

**Frontend (Vue 3)**:
```typescript
// modules/patient-search/routes.ts
import { RouteRecordRaw } from 'vue-router'

export const patientSearchRoutes: RouteRecordRaw[] = [
  {
    path: '/patient-search',
    component: () => import('./views/PatientSearch.vue'),
    meta: { requiresAuth: true, permission: 'patient_search.view' }
  }
]

// modules/patient-search/index.ts
export const patientSearchModule = {
  name: 'patient-search',
  version: '1.0.0',
  routes: patientSearchRoutes,
  permissions: ['patient_search.view', 'patient_search.search']
}
```

---

## Database Schema

### Core Tables

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    role VARCHAR(50) NOT NULL,  -- 'admin', 'clinician', 'researcher'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
    failed_login_attempts INT NOT NULL DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE NULL,
    last_login TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),
    
    CONSTRAINT users_role_check CHECK (role IN ('admin', 'clinician', 'researcher')),
    CONSTRAINT users_failed_attempts_check CHECK (failed_login_attempts >= 0)
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
```

#### projects
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    project_type VARCHAR(100) NOT NULL,  -- 'patient_search', 'timeline', 'cds', 'cohort', 'annotation'
    status VARCHAR(50) NOT NULL DEFAULT 'active',  -- 'active', 'complete', 'archived'
    dataset_id UUID NULL,  -- Reference to shared dataset (future)
    medcat_model_id UUID NULL,  -- Reference to MedCAT model (future)
    configuration JSONB NOT NULL DEFAULT '{}',  -- Project-specific config
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_by UUID NOT NULL REFERENCES users(id),
    
    CONSTRAINT projects_status_check CHECK (status IN ('active', 'complete', 'archived'))
);

CREATE INDEX idx_projects_name ON projects(name);
CREATE INDEX idx_projects_type ON projects(project_type);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_by ON projects(created_by);
```

#### project_members
```sql
CREATE TABLE project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',  -- 'owner', 'member', 'viewer'
    joined_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    added_by UUID NOT NULL REFERENCES users(id),
    
    UNIQUE(project_id, user_id),
    CONSTRAINT project_members_role_check CHECK (role IN ('owner', 'member', 'viewer'))
);

CREATE INDEX idx_project_members_project ON project_members(project_id);
CREATE INDEX idx_project_members_user ON project_members(user_id);
CREATE INDEX idx_project_members_role ON project_members(role);
```

#### tasks
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    assigned_to UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    task_type VARCHAR(100) NOT NULL,  -- 'annotation', 'search', 'review', 'validation'
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'in_progress', 'complete', 'cancelled'
    priority VARCHAR(50) NOT NULL DEFAULT 'medium',  -- 'low', 'medium', 'high', 'urgent'
    due_date TIMESTAMP WITH TIME ZONE NULL,
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    configuration JSONB NOT NULL DEFAULT '{}',  -- Task-specific config (e.g., document IDs, search criteria)
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_by UUID NOT NULL REFERENCES users(id),
    
    CONSTRAINT tasks_status_check CHECK (status IN ('pending', 'in_progress', 'complete', 'cancelled')),
    CONSTRAINT tasks_priority_check CHECK (priority IN ('low', 'medium', 'high', 'urgent'))
);

CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_created_by ON tasks(created_by);
```

#### audit_logs
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NULL REFERENCES users(id),  -- NULL for system actions
    username VARCHAR(100) NOT NULL,  -- Denormalized for immutability
    action VARCHAR(100) NOT NULL,  -- 'login', 'logout', 'view', 'create', 'update', 'delete', 'search', 'export'
    resource_type VARCHAR(100) NOT NULL,  -- 'user', 'project', 'task', 'document', 'patient', etc.
    resource_id VARCHAR(255) NULL,  -- UUID or identifier of resource
    resource_name VARCHAR(255) NULL,  -- Human-readable name
    details JSONB NOT NULL DEFAULT '{}',  -- Additional context (e.g., search query, changed fields)
    ip_address INET NULL,
    session_id VARCHAR(255) NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Immutability: No updates or deletes allowed
    CONSTRAINT audit_logs_no_null_timestamp CHECK (timestamp IS NOT NULL)
);

-- Partition by month for performance (large table)
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_session ON audit_logs(session_id);

-- Prevent updates/deletes (immutable audit trail)
CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;
```

#### modules
```sql
CREATE TABLE modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,  -- 'patient-search', 'timeline', 'cds', 'cohort'
    display_name VARCHAR(255) NOT NULL,  -- 'Patient Search', 'Timeline View', etc.
    description TEXT NOT NULL DEFAULT '',
    version VARCHAR(50) NOT NULL,  -- Semantic versioning
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    configuration JSONB NOT NULL DEFAULT '{}',  -- Module-specific config
    permissions JSONB NOT NULL DEFAULT '[]',  -- Array of permission strings
    routes JSONB NOT NULL DEFAULT '[]',  -- Array of route definitions
    installed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    installed_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_modules_name ON modules(name);
CREATE INDEX idx_modules_enabled ON modules(is_enabled);
```

#### sessions
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,  -- SHA-256 hash of JWT token
    ip_address INET NULL,
    user_agent TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT sessions_expires_after_created CHECK (expires_at > created_at)
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token_hash);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- Auto-cleanup expired sessions (run daily)
CREATE INDEX idx_sessions_cleanup ON sessions(expires_at) WHERE expires_at < NOW();
```

#### documents
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL DEFAULT 'rtf',  -- 'rtf', 'txt', 'docx', 'pdf'
    file_size INT NOT NULL,  -- Bytes
    content BYTEA NOT NULL,  -- Encrypted RTF file content (AES-256)
    content_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash for deduplication
    encryption_key_id VARCHAR(100) NOT NULL,  -- Reference to encryption key (not stored in DB)

    -- Metadata
    document_type VARCHAR(100) NULL,  -- 'clinical_letter', 'discharge_summary', 'lab_report', etc.
    document_date DATE NULL,  -- Date on document (if extractable)
    author VARCHAR(255) NULL,  -- Document author (if available)

    -- Processing status
    medcat_status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'complete', 'failed'
    medcat_processed_at TIMESTAMP WITH TIME ZONE NULL,
    medcat_error TEXT NULL,

    -- PHI flags (for audit and access control)
    contains_phi BOOLEAN NOT NULL DEFAULT TRUE,  -- Always TRUE for clinical documents
    phi_types VARCHAR(255)[] NOT NULL DEFAULT ARRAY['NHS_NUMBER', 'NAME', 'ADDRESS', 'DOB'],

    -- Standard tracking
    uploaded_by UUID NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Access control (only project members can access)
    CONSTRAINT documents_file_size_check CHECK (file_size > 0 AND file_size < 10485760),  -- 10MB max
    CONSTRAINT documents_medcat_status_check CHECK (medcat_status IN ('pending', 'processing', 'complete', 'failed'))
);

CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_content_hash ON documents(content_hash);  -- Deduplication
CREATE INDEX idx_documents_medcat_status ON documents(medcat_status);
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);
CREATE INDEX idx_documents_document_type ON documents(document_type);
```

**Security Notes**:
- `content` column stores **AES-256 encrypted** RTF files
- Encryption key stored in **separate secure location** (not in database)
- `encryption_key_id` references key in Key Management System (KMS) or HSM
- Decryption only in-memory, never persisted unencrypted

#### extracted_entities
```sql
CREATE TABLE extracted_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- MedCAT extraction metadata
    cui VARCHAR(20) NOT NULL,  -- UMLS/SNOMED-CT concept ID
    concept_name VARCHAR(500) NOT NULL,  -- "National Health Service Number", "Person Name", "Date of Birth"
    source_value TEXT NOT NULL,  -- Actual text from document (e.g., "1234567890", "John Smith")
    start_char INT NOT NULL,  -- Character position in document
    end_char INT NOT NULL,
    confidence REAL NOT NULL,  -- MedCAT confidence (0.0 - 1.0)

    -- Meta-annotations (from MetaCAT)
    meta_annotations JSONB NOT NULL DEFAULT '{}',  -- {"Negation": "Affirmed", "Temporality": "Current", ...}

    -- Entity classification
    entity_type VARCHAR(100) NOT NULL,  -- 'PERSON', 'NHS_NUMBER', 'DATE', 'ADDRESS', 'CONDITION', 'MEDICATION', etc.
    is_phi BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE if this is identifiable PHI
    phi_category VARCHAR(100) NULL,  -- 'DIRECT_IDENTIFIER', 'QUASI_IDENTIFIER', 'CLINICAL_DATA'

    -- Structured data (for specific entity types)
    structured_data JSONB NULL,  -- Type-specific structured fields (e.g., {"nhs_number": "1234567890", "validated": true})

    -- Processing metadata
    extracted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    medcat_version VARCHAR(50) NOT NULL,  -- Version of MedCAT used for extraction

    CONSTRAINT extracted_entities_confidence_check CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT extracted_entities_position_check CHECK (end_char > start_char)
);

CREATE INDEX idx_extracted_entities_document ON extracted_entities(document_id);
CREATE INDEX idx_extracted_entities_project ON extracted_entities(project_id);
CREATE INDEX idx_extracted_entities_cui ON extracted_entities(cui);
CREATE INDEX idx_extracted_entities_entity_type ON extracted_entities(entity_type);
CREATE INDEX idx_extracted_entities_is_phi ON extracted_entities(is_phi);
CREATE INDEX idx_extracted_entities_structured_data_gin ON extracted_entities USING gin(structured_data);  -- Fast JSON queries
```

**Data Examples**:
```json
// NHS Number entity
{
  "cui": "C0027361",
  "concept_name": "National Health Service Number",
  "source_value": "1234567890",
  "entity_type": "NHS_NUMBER",
  "is_phi": true,
  "phi_category": "DIRECT_IDENTIFIER",
  "structured_data": {
    "nhs_number": "1234567890",
    "validated": true,
    "checksum_valid": true
  }
}

// Patient name entity
{
  "cui": "C0027365",
  "concept_name": "Person Name",
  "source_value": "John Smith",
  "entity_type": "PERSON",
  "is_phi": true,
  "phi_category": "DIRECT_IDENTIFIER",
  "structured_data": {
    "first_name": "John",
    "last_name": "Smith",
    "parsed_by": "spacy_ner"
  }
}

// Clinical condition entity
{
  "cui": "C0004238",
  "concept_name": "Atrial Flutter",
  "source_value": "atrial flutter",
  "entity_type": "CONDITION",
  "is_phi": false,
  "meta_annotations": {
    "Negation": "Affirmed",
    "Experiencer": "Patient",
    "Temporality": "Current",
    "Certainty": "Confirmed"
  }
}
```

#### patients
```sql
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Primary identifier (NHS number or MRN)
    nhs_number VARCHAR(10) UNIQUE NULL,  -- UK NHS number (10 digits)
    mrn VARCHAR(50) UNIQUE NULL,  -- Medical Record Number (if no NHS number)

    -- Demographics (extracted from documents)
    first_name VARCHAR(100) NULL,
    last_name VARCHAR(100) NULL,
    date_of_birth DATE NULL,
    gender VARCHAR(20) NULL,

    -- Address (structured from extraction)
    address_line1 VARCHAR(255) NULL,
    address_line2 VARCHAR(255) NULL,
    city VARCHAR(100) NULL,
    postcode VARCHAR(10) NULL,

    -- Aggregation metadata
    source_document_ids UUID[] NOT NULL DEFAULT ARRAY[]::UUID[],  -- Array of document IDs that contributed data
    last_updated_from UUID NULL REFERENCES documents(id),  -- Most recent document that updated this record
    confidence_score REAL NULL,  -- Aggregate confidence of patient matching

    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT patients_identifier_check CHECK (nhs_number IS NOT NULL OR mrn IS NOT NULL),
    CONSTRAINT patients_nhs_format_check CHECK (nhs_number IS NULL OR nhs_number ~ '^\d{10}$')
);

CREATE UNIQUE INDEX idx_patients_nhs_number ON patients(nhs_number) WHERE nhs_number IS NOT NULL;
CREATE UNIQUE INDEX idx_patients_mrn ON patients(mrn) WHERE mrn IS NOT NULL;
CREATE INDEX idx_patients_last_name ON patients(last_name);
CREATE INDEX idx_patients_postcode ON patients(postcode);
CREATE INDEX idx_patients_updated_at ON patients(updated_at DESC);
```

**Patient Record Aggregation Workflow**:
1. Document uploaded → MedCAT extracts entities → `extracted_entities` table
2. System identifies PHI entities (NHS number, name, DOB, address)
3. Patient matching algorithm:
   - If NHS number exists → link to existing patient OR create new patient
   - If no NHS number → use name + DOB fuzzy matching
4. Update `patients` table with aggregated demographics
5. Link document to patient via `source_document_ids` array

**Privacy Note**: `patients` table contains **identifiable PHI** and requires:
- Encryption at rest (PostgreSQL encryption)
- Strict access controls (only authorized users via RBAC)
- Comprehensive audit logging (all queries logged)

### Module-Specific Tables (Examples)

#### patient_search_results (Patient Search Module)
```sql
CREATE TABLE patient_search_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    query JSONB NOT NULL,  -- Search criteria (concepts, filters, date range)
    result_count INT NOT NULL,
    results JSONB NOT NULL,  -- Array of patient identifiers + metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_patient_search_task ON patient_search_results(task_id);
CREATE INDEX idx_patient_search_user ON patient_search_results(user_id);
```

#### timeline_views (Timeline Module)
```sql
CREATE TABLE timeline_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    patient_id VARCHAR(255) NOT NULL,  -- MRN or patient identifier
    viewed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_timeline_views_task ON timeline_views(task_id);
CREATE INDEX idx_timeline_views_user ON timeline_views(user_id);
CREATE INDEX idx_timeline_views_patient ON timeline_views(patient_id);
```

### Database Schema Summary

**Total Tables**: 13 core tables + module-specific tables

**Core Tables** (10):
1. `users` - User accounts
2. `projects` - Shared workspaces
3. `project_members` - Project membership
4. `tasks` - User assignments
5. `audit_logs` - Audit trail (immutable)
6. `modules` - Installed modules
7. `sessions` - Active user sessions
8. **`documents`** - Clinical documents (RTF files, encrypted, ~50KB each) **[NEW]**
9. **`extracted_entities`** - Structured data extracted by MedCAT (PHI + clinical data) **[NEW]**
10. **`patients`** - Aggregated patient records (from extracted entities) **[NEW]**

**Module Tables** (variable):
- Each module defines own tables
- Migrations managed via Alembic
- Foreign keys to core tables (tasks, users, projects)

**Key Design Decisions** (from user requirements):
1. **Shared MedCAT Models**: Single Docker volume, all users share models (no per-user duplication)
2. **Document Storage**: RTF files (~50KB) stored in PostgreSQL BYTEA (AES-256 encrypted)
3. **PHI Handling**: Documents contain PHI (NHS #, name, address, DOB) → extracted to structured data via MedCAT
4. **Patient Aggregation**: Multiple documents consolidated into single patient record (via NHS number matching)

---

## Authentication & Authorization

### Authentication Flow

**Inspired by MedCAT Trainer**: Django uses Token authentication; we'll use JWT for stateless auth.

#### 1. Login Flow

```
Client                    Backend                   Database
  │                          │                          │
  │  POST /api/v1/auth/login │                          │
  │  {username, password}    │                          │
  ├─────────────────────────▶│                          │
  │                          │  SELECT * FROM users     │
  │                          │  WHERE username=?        │
  │                          ├─────────────────────────▶│
  │                          │◀─────────────────────────┤
  │                          │  User record             │
  │                          │                          │
  │                          │  bcrypt.verify(password) │
  │                          │                          │
  │                          │  IF valid:               │
  │                          │    - Generate JWT token  │
  │                          │    - Insert session      │
  │                          │    - Log audit (login)   │
  │                          ├─────────────────────────▶│
  │                          │◀─────────────────────────┤
  │                          │                          │
  │ ◀─────────────────────────┤                          │
  │  {token, user, expires}  │                          │
```

#### 2. Token Structure (JWT)

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": "uuid",
    "username": "john.doe",
    "role": "clinician",
    "session_id": "uuid",
    "exp": 1730000000,
    "iat": 1729971200
  },
  "signature": "..."
}
```

#### 3. Authorization Pattern (RBAC)

**Roles**:
- `admin`: Full access (user management, project management, all modules)
- `clinician`: Access to assigned projects and tasks
- `researcher`: Access to cohort builder, analytics (read-only patient data)

**Permissions** (inspired by Django's permission system):
```
Format: <module>.<action>

Examples:
- users.view         (View user list)
- users.create       (Create new user)
- users.edit         (Edit user)
- users.delete       (Deactivate user)
- projects.view      (View projects)
- projects.create    (Create project)
- tasks.view         (View tasks)
- tasks.assign       (Assign tasks)
- patient_search.search  (Perform patient search)
- timeline.view      (View patient timeline)
- cds.configure      (Configure CDS rules)
- audit.view         (View audit logs)
```

**Role-Permission Mapping** (hardcoded initially, configurable later):
```python
ROLE_PERMISSIONS = {
    "admin": ["*"],  # All permissions
    "clinician": [
        "tasks.view",
        "tasks.update",
        "projects.view",
        "patient_search.search",
        "timeline.view",
    ],
    "researcher": [
        "projects.view",
        "cohort.search",
        "cohort.export",
        "analytics.view",
    ]
}
```

#### 4. FastAPI Dependency (Authorization Check)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = credentials.credentials
    payload = verify_jwt(token)  # Raises HTTPException if invalid
    user = await get_user_by_id(payload["user_id"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

async def require_permission(permission: str):
    def dependency(user: User = Depends(get_current_user)):
        if user.role == "admin":
            return user  # Admins have all permissions
        if not has_permission(user.role, permission):
            raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")
        return user
    return dependency

# Usage in routes:
@router.get("/api/v1/users")
async def list_users(user: User = Depends(require_permission("users.view"))):
    ...
```

### Password Policy

- **Minimum Length**: 12 characters
- **Complexity**: At least 1 uppercase, 1 lowercase, 1 number, 1 special character
- **Forbidden**: Common passwords (rockyou.txt top 10,000), username variations
- **Expiry**: 90 days (optional, configurable)
- **History**: Cannot reuse last 5 passwords (future feature)

### Account Lockout

- **Failed Attempts**: 5 consecutive failures → lock account for 30 minutes
- **Lockout Duration**: 30 minutes (configurable)
- **Unlock**: Admin can manually unlock OR wait for timeout
- **Notification**: Email admin on account lockout (optional)

---

## Audit Logging

### What to Log

**Inspired by MedCAT Trainer**: Tracks user actions on AnnotatedEntity, Project, Document models.

**Our Audit Events**:

| Action | Resource Type | Details |
|--------|---------------|---------|
| `login` | `user` | Login success/failure, IP address |
| `logout` | `user` | Session ID |
| `view` | `project`, `task`, `patient`, `document` | Resource ID, name |
| `create` | `user`, `project`, `task` | Resource ID, initial state |
| `update` | `user`, `project`, `task` | Resource ID, changed fields (before/after) |
| `delete` | `user`, `project`, `task` | Resource ID, final state |
| `search` | `patient` | Search query (concepts, filters) |
| `export` | `cohort`, `audit_log` | Export criteria, row count |
| `configure` | `module`, `system` | Config key, old/new value |

### Audit Log Service (Backend)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json

class AuditLogger:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log(
        self,
        user_id: str,
        username: str,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        resource_name: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        session_id: str | None = None
    ):
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            details=details or {},
            ip_address=ip_address,
            session_id=session_id,
            timestamp=datetime.utcnow()
        )
        self.db.add(audit_log)
        await self.db.commit()
        return audit_log

# Usage in routes:
@router.post("/api/v1/projects")
async def create_project(
    project: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    new_project = await project_service.create(project, user)
    
    # Audit log
    audit = AuditLogger(db)
    await audit.log(
        user_id=user.id,
        username=user.username,
        action="create",
        resource_type="project",
        resource_id=str(new_project.id),
        resource_name=new_project.name,
        details={"project_type": new_project.project_type},
        ip_address=request.client.host,
        session_id=user.session_id  # From JWT
    )
    
    return new_project
```

### Audit Log Query API

```python
@router.get("/api/v1/audit/logs")
async def query_audit_logs(
    user_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
    user: User = Depends(require_permission("audit.view")),
    db: AsyncSession = Depends(get_db)
):
    """Query audit logs with filters (admin only)"""
    query = select(AuditLog)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)
    
    query = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {"logs": logs, "count": len(logs)}
```

### Audit Log Export

```python
@router.get("/api/v1/audit/export")
async def export_audit_logs(
    format: str = "csv",  # csv, json
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    user: User = Depends(require_permission("audit.export")),
    db: AsyncSession = Depends(get_db)
):
    """Export audit logs for compliance reporting"""
    query = select(AuditLog)
    
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    if format == "csv":
        # Convert to CSV
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "timestamp", "username", "action", "resource_type", 
            "resource_id", "resource_name", "ip_address"
        ])
        writer.writeheader()
        for log in logs:
            writer.writerow({
                "timestamp": log.timestamp.isoformat(),
                "username": log.username,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_name": log.resource_name,
                "ip_address": log.ip_address
            })
        return Response(content=output.getvalue(), media_type="text/csv")
    
    else:  # JSON
        return {"logs": [log.dict() for log in logs]}
```

---

## PHI Extraction & Patient Data Workflow

### Overview

**Goal**: Transform unstructured clinical documents (RTF files with PHI) into structured, searchable patient records while maintaining security and auditability.

**Key Requirements** (from user):
- **Input**: RTF clinical letters (~50KB) containing NHS #, name, address, DOB, clinical notes
- **Processing**: MedCAT NLP extracts both PHI (demographics) and clinical data (conditions, medications)
- **Output**: Structured patient records searchable by demographics and clinical concepts
- **Security**: Encrypted storage, audit logging, strict access controls

### Workflow Steps

#### Step 1: Document Upload

```
Clinician → Upload RTF file → Backend API
  ↓
Backend validates:
- File size < 10MB
- File type = RTF (or txt, docx, pdf)
- User has project access
  ↓
Backend encrypts document:
- Generate AES-256 encryption key (or use existing project key)
- Encrypt RTF content
- Compute SHA-256 hash (for deduplication)
- Store in documents table
  ↓
Audit log:
- Action: "DOCUMENT_UPLOAD"
- User: clinician_id
- Resource: document_id
- Details: {filename, file_size, project_id}
```

**Database Insert**:
```sql
INSERT INTO documents (
    project_id, filename, file_type, file_size, content,
    content_hash, encryption_key_id, contains_phi, uploaded_by
) VALUES (
    'project-uuid', 'clinical_letter_2024.rtf', 'rtf', 45832,
    '\x...',  -- Encrypted bytes
    'sha256hash...', 'project-key-001', TRUE, 'user-uuid'
);
```

#### Step 2: MedCAT Processing (Asynchronous)

**Trigger**: Document upload completes OR manual "Process" button click

```
Background Worker (Celery/FastAPI BackgroundTasks)
  ↓
Load document:
- Query documents table
- Decrypt content in-memory (NEVER persist unencrypted)
- Convert RTF to plain text
  ↓
Call MedCAT Service:
- POST http://medcat-service:5000/api/process
- Body: {text: "decrypted plain text"}
- Response: Array of entities with CUIs, positions, meta-annotations
  ↓
For each entity returned by MedCAT:
  - Classify entity type (PHI vs clinical data)
  - If PHI: mark is_phi=TRUE, set phi_category
  - If clinical: mark is_phi=FALSE, store meta-annotations
  - Insert into extracted_entities table
  ↓
Update document status:
- medcat_status = 'complete'
- medcat_processed_at = NOW()
  ↓
Audit log:
- Action: "MEDCAT_PROCESSING_COMPLETE"
- Resource: document_id
- Details: {entity_count, phi_count, clinical_count}
```

**MedCAT Response Example**:
```json
{
  "annotations": [
    {
      "cui": "C0027361",
      "pretty_name": "National Health Service Number",
      "source_value": "1234567890",
      "start": 145,
      "end": 155,
      "confidence": 0.98
    },
    {
      "cui": "C0027365",
      "pretty_name": "Person Name",
      "source_value": "John Smith",
      "start": 12,
      "end": 22,
      "confidence": 0.95
    },
    {
      "cui": "C0004238",
      "pretty_name": "Atrial Flutter",
      "source_value": "atrial flutter",
      "start": 312,
      "end": 326,
      "confidence": 0.93,
      "meta_anns": {
        "Negation": "Affirmed",
        "Experiencer": "Patient",
        "Temporality": "Current"
      }
    }
  ]
}
```

**Database Inserts** (extracted_entities):
```sql
-- PHI entity: NHS Number
INSERT INTO extracted_entities (
    document_id, project_id, cui, concept_name, source_value,
    start_char, end_char, confidence, entity_type, is_phi, phi_category,
    structured_data
) VALUES (
    'doc-uuid', 'project-uuid', 'C0027361', 'National Health Service Number',
    '1234567890', 145, 155, 0.98, 'NHS_NUMBER', TRUE, 'DIRECT_IDENTIFIER',
    '{"nhs_number": "1234567890", "validated": true}'::jsonb
);

-- PHI entity: Patient Name
INSERT INTO extracted_entities (
    document_id, project_id, cui, concept_name, source_value,
    start_char, end_char, confidence, entity_type, is_phi, phi_category,
    structured_data
) VALUES (
    'doc-uuid', 'project-uuid', 'C0027365', 'Person Name',
    'John Smith', 12, 22, 0.95, 'PERSON', TRUE, 'DIRECT_IDENTIFIER',
    '{"first_name": "John", "last_name": "Smith"}'::jsonb
);

-- Clinical entity: Atrial Flutter
INSERT INTO extracted_entities (
    document_id, project_id, cui, concept_name, source_value,
    start_char, end_char, confidence, entity_type, is_phi,
    meta_annotations
) VALUES (
    'doc-uuid', 'project-uuid', 'C0004238', 'Atrial Flutter',
    'atrial flutter', 312, 326, 0.93, 'CONDITION', FALSE,
    '{"Negation": "Affirmed", "Experiencer": "Patient", "Temporality": "Current"}'::jsonb
);
```

#### Step 3: Patient Record Aggregation

**Trigger**: MedCAT processing completes

```
Background Worker
  ↓
Query PHI entities from document:
- SELECT * FROM extracted_entities
  WHERE document_id = ? AND is_phi = TRUE
  ↓
Extract demographics:
- NHS Number: entity_type='NHS_NUMBER'
- Name: entity_type='PERSON'
- DOB: entity_type='DATE' (with context "born", "DOB")
- Address: entity_type='ADDRESS'
  ↓
Patient Matching Logic:
  IF NHS number found:
    - Query patients table for existing NHS number
    - IF exists: UPDATE patient record
    - ELSE: INSERT new patient record
  ELSE:
    - Fuzzy match on name + DOB (if available)
    - IF high confidence match (>0.85): UPDATE
    - ELSE: INSERT new patient (assign MRN)
  ↓
Update patients table:
- Merge demographics from this document
- Append document_id to source_document_ids array
- Update confidence_score
- Set last_updated_from = document_id
  ↓
Audit log:
- Action: "PATIENT_RECORD_UPDATED" or "PATIENT_RECORD_CREATED"
- Resource: patient_id
- Details: {document_id, nhs_number, name}
```

**Database Operations**:
```sql
-- Check if patient exists
SELECT id, nhs_number, first_name, last_name, source_document_ids
FROM patients
WHERE nhs_number = '1234567890';

-- If exists: UPDATE
UPDATE patients
SET
    first_name = COALESCE(NULLIF(first_name, ''), 'John'),  -- Keep existing if not null
    last_name = COALESCE(NULLIF(last_name, ''), 'Smith'),
    date_of_birth = COALESCE(date_of_birth, '1960-03-15'),
    address_line1 = '123 Main Street',
    city = 'London',
    postcode = 'SW1A 1AA',
    source_document_ids = array_append(source_document_ids, 'doc-uuid'),
    last_updated_from = 'doc-uuid',
    updated_at = NOW()
WHERE id = 'patient-uuid';

-- If not exists: INSERT
INSERT INTO patients (
    nhs_number, first_name, last_name, date_of_birth,
    address_line1, city, postcode, source_document_ids,
    last_updated_from
) VALUES (
    '1234567890', 'John', 'Smith', '1960-03-15',
    '123 Main Street', 'London', 'SW1A 1AA',
    ARRAY['doc-uuid'], 'doc-uuid'
);
```

#### Step 4: Patient Search & Timeline Access

**Patient Search Module** (uses extracted_entities + patients):
```sql
-- Search for patients with "atrial flutter"
SELECT DISTINCT
    p.id, p.nhs_number, p.first_name, p.last_name, p.date_of_birth,
    e.cui, e.concept_name, e.source_value, e.confidence,
    e.meta_annotations
FROM patients p
JOIN documents d ON d.id = ANY(p.source_document_ids)
JOIN extracted_entities e ON e.document_id = d.id
WHERE
    e.cui = 'C0004238'  -- Atrial Flutter
    AND e.entity_type = 'CONDITION'
    AND e.is_phi = FALSE
    AND e.meta_annotations->>'Negation' = 'Affirmed'
    AND e.meta_annotations->>'Experiencer' = 'Patient'
    AND e.meta_annotations->>'Temporality' IN ('Current', 'Recent')
ORDER BY p.last_name, p.first_name;
```

**Timeline View Module** (chronological view of patient's clinical events):
```sql
-- Get all clinical events for patient (timeline)
SELECT
    d.filename, d.document_date, d.document_type,
    e.cui, e.concept_name, e.source_value, e.confidence,
    e.meta_annotations, e.entity_type
FROM patients p
JOIN documents d ON d.id = ANY(p.source_document_ids)
JOIN extracted_entities e ON e.document_id = d.id
WHERE
    p.nhs_number = '1234567890'
    AND e.is_phi = FALSE  -- Exclude PHI from timeline (show clinical data only)
ORDER BY d.document_date DESC, e.start_char ASC;
```

### Security Considerations

#### Encryption at Rest
- **Documents**: AES-256 encryption of `content` column in PostgreSQL
- **Encryption Keys**: Stored in separate KMS (Key Management System) or HSM (Hardware Security Module)
- **Key Rotation**: Quarterly (re-encrypt documents with new key)
- **Decryption**: Only in-memory, never persisted unencrypted

#### Access Controls
- **Document Access**: Only project members can view documents
- **Patient Access**: Only authorized roles (`clinician`, `admin`) can view patients table
- **PHI Access**: All queries to `documents`, `extracted_entities` (WHERE is_phi=TRUE), `patients` are audit logged
- **RBAC**: Enforced at API level via FastAPI dependencies

#### Audit Logging
Every action on PHI is logged:
```python
# Document upload
await audit_log(user_id, "DOCUMENT_UPLOAD", "document", document_id,
                details={"filename": filename, "file_size": file_size})

# Document view
await audit_log(user_id, "DOCUMENT_VIEW", "document", document_id,
                details={"project_id": project_id})

# Patient search
await audit_log(user_id, "PATIENT_SEARCH", "patient", None,
                details={"query": query_dict, "result_count": len(results)})

# Patient record view
await audit_log(user_id, "PATIENT_VIEW", "patient", patient_id,
                details={"nhs_number": nhs_number})
```

### De-Identification Considerations

**Current Approach**: Identifiable PHI stored (for clinical care use case)

**Future: De-Identification Module** (optional):
- **Goal**: Create de-identified dataset for research
- **Method**: Replace PHI with tokens (e.g., NHS # → PATIENT_001)
- **Implementation**:
  1. Create `deidentified_documents` table
  2. Copy documents, replace PHI entities with placeholders
  3. Create mapping table (token → real value) with restricted access
  4. Researchers access de-identified data only

**Compliance**:
- **GDPR Article 6**: Lawful basis for processing (clinical care)
- **GDPR Article 32**: Encryption and security measures ✓
- **HIPAA Security Rule**: Administrative, physical, technical safeguards ✓
- **NHS Data Security and Protection Toolkit**: Encryption, audit, access controls ✓

---

## Module System

### Module Registration (Backend)

**Inspired by MedCAT Trainer**: Django apps registered in `INSTALLED_APPS`.

**Our approach**: Dynamic module discovery and registration.

#### 1. Module Interface

```python
# app/core/modules/interface.py
from typing import Protocol
from fastapi import FastAPI

class ModuleInterface(Protocol):
    """Interface that all modules must implement"""
    
    name: str
    version: str
    permissions: list[str]
    
    def register(self, app: FastAPI) -> None:
        """Register module routes and dependencies"""
        ...
```

#### 2. Module Implementation Example

```python
# app/modules/patient_search/__init__.py
from fastapi import FastAPI
from .api import router

name = "patient-search"
version = "1.0.0"
permissions = ["patient_search.search", "patient_search.view", "patient_search.export"]

def register(app: FastAPI):
    """Register Patient Search module"""
    app.include_router(router, prefix="/api/v1/patient-search", tags=["patient-search"])
    print(f"✅ Registered module: {name} v{version}")
```

#### 3. Module Loader

```python
# app/core/modules/loader.py
import importlib
from pathlib import Path
from fastapi import FastAPI

class ModuleLoader:
    def __init__(self, app: FastAPI, modules_dir: Path):
        self.app = app
        self.modules_dir = modules_dir
        self.loaded_modules = {}
    
    def discover_modules(self) -> list[str]:
        """Find all modules in modules directory"""
        modules = []
        for module_dir in self.modules_dir.iterdir():
            if module_dir.is_dir() and (module_dir / "__init__.py").exists():
                modules.append(module_dir.name)
        return modules
    
    async def load_module(self, module_name: str):
        """Load a single module"""
        try:
            # Import module
            module = importlib.import_module(f"app.modules.{module_name}")
            
            # Check if module is enabled in database
            is_enabled = await self.check_module_enabled(module_name)
            if not is_enabled:
                print(f"⏭️ Skipping disabled module: {module_name}")
                return
            
            # Register module
            module.register(self.app)
            
            # Store module info
            self.loaded_modules[module_name] = {
                "name": module.name,
                "version": module.version,
                "permissions": module.permissions
            }
            
            print(f"✅ Loaded module: {module.name} v{module.version}")
        
        except Exception as e:
            print(f"❌ Failed to load module {module_name}: {e}")
    
    async def load_all_modules(self):
        """Load all discovered modules"""
        modules = self.discover_modules()
        for module_name in modules:
            await self.load_module(module_name)
        
        print(f"📦 Loaded {len(self.loaded_modules)} modules")
    
    async def check_module_enabled(self, module_name: str) -> bool:
        """Check if module is enabled in database"""
        # Query modules table
        from app.core.database import get_db
        async for db in get_db():
            result = await db.execute(
                select(Module).where(Module.name == module_name)
            )
            module = result.scalar_one_or_none()
            return module.is_enabled if module else False
```

#### 4. Application Startup (main.py)

```python
# app/main.py
from fastapi import FastAPI
from pathlib import Path
from app.core.modules.loader import ModuleLoader

app = FastAPI(title="Clinical Care Tools Base App")

@app.on_event("startup")
async def startup_event():
    # Load modules
    modules_dir = Path(__file__).parent / "modules"
    loader = ModuleLoader(app, modules_dir)
    await loader.load_all_modules()

@app.get("/api/v1/modules")
async def list_modules(user: User = Depends(require_permission("modules.view"))):
    """List all loaded modules"""
    return {"modules": loader.loaded_modules}
```

### Module Management UI (Admin)

**Admin can**:
- View installed modules (name, version, status)
- Enable/disable modules (updates `modules.is_enabled`)
- Configure module settings (updates `modules.configuration`)
- Uninstall modules (deletes module files and database records)

**API Endpoints**:
```
GET    /api/v1/admin/modules          # List modules
POST   /api/v1/admin/modules/install   # Install module (upload .zip)
PUT    /api/v1/admin/modules/{id}      # Update module (enable/disable, config)
DELETE /api/v1/admin/modules/{id}      # Uninstall module
```

---

## Deployment Model

### Docker Compose Structure

**Inspired by MedCAT Trainer**: `docker-compose-example-postgres.yml` with services, volumes, environment variables.

#### docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:17.6-alpine
    container_name: clinical-care-postgres
    restart: always
    environment:
      POSTGRES_DB: clinical_care
      POSTGRES_USER: ${DB_USER:-admin}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-change_me_in_production}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-admin}"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  # Backend (FastAPI)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: clinical-care-backend
    restart: always
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER:-admin}:${DB_PASSWORD:-change_me_in_production}@postgres:5432/clinical_care
      SECRET_KEY: ${SECRET_KEY:-generate_random_key_in_production}
      JWT_ALGORITHM: HS256
      JWT_EXPIRATION_HOURS: 8
      MEDCAT_SERVICE_URL: http://medcat-service:5000
      LOG_LEVEL: INFO
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - medcat-models:/app/models
      - documents:/app/documents
      - logs:/app/logs
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  # Frontend (Vue 3 + Vuetify)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: clinical-care-frontend
    restart: always
    depends_on:
      - backend
    ports:
      - "8080:80"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  # MedCAT Service (External)
  medcat-service:
    image: cogstacksystems/medcat-service:latest
    container_name: medcat-service
    restart: always
    volumes:
      - medcat-models:/app/models
    ports:
      - "5000:5000"
    environment:
      MODEL_PATH: /app/models/default_model.zip
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres-data:
    driver: local
  medcat-models:
    driver: local
  documents:
    driver: local
  logs:
    driver: local

networks:
  default:
    name: clinical-care-network
```

### First-Time Setup Script

#### setup.sh

```bash
#!/bin/bash
set -e

echo "🚀 Clinical Care Tools Base App - First-Time Setup"
echo "=================================================="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Please install Docker first."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose not found. Please install Docker Compose first."; exit 1; }

# Generate secret key
echo "🔐 Generating secret key..."
SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY=$SECRET_KEY" > .env

# Prompt for admin credentials
echo ""
echo "👤 Create Admin User"
read -p "Admin Username: " ADMIN_USERNAME
read -sp "Admin Password: " ADMIN_PASSWORD
echo ""
read -p "Admin Email: " ADMIN_EMAIL

echo "ADMIN_USERNAME=$ADMIN_USERNAME" >> .env
echo "ADMIN_PASSWORD=$ADMIN_PASSWORD" >> .env
echo "ADMIN_EMAIL=$ADMIN_EMAIL" >> .env

# Start services
echo ""
echo "🐳 Starting Docker Compose services..."
docker-compose up -d

# Wait for database
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker-compose exec -T postgres pg_isready -U admin; do
  sleep 1
done

# Run database migrations
echo "📊 Running database migrations..."
docker-compose exec -T backend alembic upgrade head

# Create admin user
echo "👤 Creating admin user..."
docker-compose exec -T backend python scripts/create_admin.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Access the application at: http://localhost:8080"
echo "👤 Login with username: $ADMIN_USERNAME"
echo ""
echo "📚 Next steps:"
echo "  1. Log in to the admin panel"
echo "  2. Upload a MedCAT model"
echo "  3. Create your first project"
echo "  4. Add users and assign tasks"
echo ""
```

### Backend Dockerfile

```dockerfile
# Multi-stage build
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Ensure scripts are executable
RUN chmod +x scripts/*.py

# Set PATH
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Environment Variables (.env.example)

```bash
# Database
DB_USER=admin
DB_PASSWORD=change_me_in_production
DB_NAME=clinical_care

# Backend
SECRET_KEY=generate_random_key_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8
LOG_LEVEL=INFO

# MedCAT Service
MEDCAT_SERVICE_URL=http://medcat-service:5000

# Admin User (for first-time setup)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me_on_first_login
ADMIN_EMAIL=admin@example.com
```

---

## Constraints

### Technical Constraints

1. **Single Workstation Deployment**
   - All services run on one machine
   - No distributed systems (no Kubernetes, no load balancers)
   - Localhost networking only
   - Maximum 10 concurrent users (realistic for workstation hardware)

2. **No OIDC/Keycloak**
   - Too complex for single workstation
   - Username/password authentication only
   - JWT for session management

3. **No Cloud Services**
   - No AWS/Azure/GCP integration
   - No SaaS dependencies
   - All data stored locally

4. **MedCAT Service Dependency**
   - Assumes MedCAT Service is available at `http://medcat-service:5000`
   - System degrades gracefully if service unavailable (queue requests)

5. **PostgreSQL Only**
   - No MySQL/SQLite/other databases
   - Leverages MedCAT Trainer's proven PostgreSQL setup

### Regulatory Constraints

1. **HIPAA Compliance**
   - Audit logging mandatory (no shortcuts)
   - Encryption at rest and in transit
   - Access controls (RBAC)
   - Data retention policies

2. **GDPR Compliance**
   - Right to erasure (delete user data)
   - Data portability (export user data)
   - Consent management (future feature)

3. **Clinical Governance**
   - Track WHO did WHAT, WHEN for all patient data access
   - Tamper-proof audit trail (immutable audit logs)
   - User accountability (no shared accounts)

### Organizational Constraints

1. **Small Team**
   - 1-3 developers (sequential development)
   - Must be maintainable by generalists (no microservices experts required)

2. **Limited Budget**
   - No commercial software licenses
   - Open-source only (PostgreSQL, FastAPI, Vue 3, Docker)

---

## Acceptance Criteria

### System-Level Acceptance Criteria

#### AC1: Installation
- [ ] **AC1.1**: Docker Compose setup completes in <10 minutes
- [ ] **AC1.2**: First-time setup script creates admin user successfully
- [ ] **AC1.3**: All services healthy (health checks pass)
- [ ] **AC1.4**: Frontend accessible at `http://localhost:8080`
- [ ] **AC1.5**: Backend API accessible at `http://localhost:8000`

#### AC2: Multi-User Support
- [ ] **AC2.1**: Admin can create 10 users via UI
- [ ] **AC2.2**: All 10 users can log in simultaneously (concurrent sessions)
- [ ] **AC2.3**: Each user sees only their assigned tasks (isolation)
- [ ] **AC2.4**: Users can collaborate on same project (shared data)

#### AC3: Authentication
- [ ] **AC3.1**: Login succeeds with valid username/password
- [ ] **AC3.2**: Login fails with invalid credentials (401 error)
- [ ] **AC3.3**: Account locks after 5 failed attempts
- [ ] **AC3.4**: Session expires after 8 hours
- [ ] **AC3.5**: Logout invalidates session token

#### AC4: Authorization
- [ ] **AC4.1**: Admin can access all projects and tasks
- [ ] **AC4.2**: Clinician can access only assigned projects (403 for others)
- [ ] **AC4.3**: Researcher can access cohort builder (permission check)
- [ ] **AC4.4**: Unauthorized users get 403 Forbidden

#### AC5: Audit Logging
- [ ] **AC5.1**: Login/logout events logged with IP address
- [ ] **AC5.2**: All patient data access logged (view, search, export)
- [ ] **AC5.3**: Admin can query audit logs (filter by user, date, action)
- [ ] **AC5.4**: Audit logs cannot be deleted or modified (immutability)
- [ ] **AC5.5**: Audit logs export to CSV for compliance reporting

#### AC6: Project Management
- [ ] **AC6.1**: Admin can create project with name, description, dataset
- [ ] **AC6.2**: Admin can assign multiple users to project
- [ ] **AC6.3**: Users see only projects they are assigned to
- [ ] **AC6.4**: Project members can view project details
- [ ] **AC6.5**: Non-members cannot access project (403 error)

#### AC7: Task Management
- [ ] **AC7.1**: Admin can create task assigned to specific user
- [ ] **AC7.2**: User can view assigned tasks in dashboard
- [ ] **AC7.3**: User can update task status (Pending → In Progress → Complete)
- [ ] **AC7.4**: User cannot view other users' tasks (unless admin)
- [ ] **AC7.5**: Admin can reassign tasks

#### AC8: Module System
- [ ] **AC8.1**: System loads all enabled modules on startup
- [ ] **AC8.2**: Admin can disable module (module routes removed)
- [ ] **AC8.3**: Admin can enable module (module routes added)
- [ ] **AC8.4**: Module configuration changes apply without restart
- [ ] **AC8.5**: Uninstalling module removes routes and database tables

#### AC9: Performance
- [ ] **AC9.1**: API response time <500ms (P95) with 10 concurrent users
- [ ] **AC9.2**: Frontend page load <2s (P95)
- [ ] **AC9.3**: Database queries use indexes (no table scans)
- [ ] **AC9.4**: MedCAT model loads once (cached for subsequent requests)

#### AC10: Security
- [ ] **AC10.1**: All passwords hashed with bcrypt (cost factor 12)
- [ ] **AC10.2**: JWT tokens signed with HS256 (secret key from .env)
- [ ] **AC10.3**: Session tokens stored in httpOnly cookies (no localStorage)
- [ ] **AC10.4**: CSRF protection enabled (SameSite cookies)
- [ ] **AC10.5**: No PHI in application logs (sanitized error messages)

#### AC11: Reliability
- [ ] **AC11.1**: PostgreSQL backup runs daily (automated)
- [ ] **AC11.2**: System recovers from backup in <1 hour (RTO)
- [ ] **AC11.3**: Health checks detect service failures (restart unhealthy services)
- [ ] **AC11.4**: Error logs persist to `/app/logs` volume
- [ ] **AC11.5**: System gracefully degrades if MedCAT Service unavailable

---

## Alignment with Constitution

This specification aligns with the **CogStack NLP Full Potential - Project Constitution** as follows:

### Principle 1: Patient Safety First ✅
- **FR5**: Comprehensive audit logging tracks all patient data access
- **NFR2**: Security controls prevent unauthorized access
- **AC10**: No PHI in logs, encrypted passwords, CSRF protection
- Meta-annotations will be enforced in modules (Patient Search, Timeline, CDS)

### Principle 2: Privacy by Design ✅
- **FR5**: Audit logging for ALL PHI access (no exceptions)
- **NFR2**: Encryption at rest (PostgreSQL pgcrypto) and in transit (TLS 1.3)
- **FR2**: Role-based access control (RBAC) with minimum necessary access
- **Audit Logs**: Immutable, tamper-proof (cannot be deleted or modified)

### Principle 3: Evidence-Based Development ✅
- **AC9**: Performance benchmarks defined (P95 latency <500ms, <2s page load)
- **NFR1**: Performance requirements measurable and testable
- **AC1-AC11**: Comprehensive acceptance criteria for validation
- User testing required before production (per constitution)

### Principle 4: Modularity and Composability ✅
- **FR6**: Module system with dynamic loading and registration
- **Architecture**: Core + Modules pattern (patient search, timeline, CDS as separate modules)
- **Module Independence**: Modules can be enabled/disabled without affecting core
- **API-Driven**: Modules communicate via REST APIs (no tight coupling)

### Principle 5: Open Standards and Interoperability ✅
- **Database Schema**: Standard PostgreSQL with JSONB for flexibility
- **API**: REST API with OpenAPI 3.0 specification
- **Docker**: Standard containerization (portable across environments)
- **FHIR**: Modules will implement FHIR R4 for EHR integration (future)

### Principle 6: Transparency and Explainability ✅
- **Audit Logs**: All actions tracked and queryable
- **User Roles**: Clear RBAC with documented permissions
- **Configuration**: Admin UI makes settings transparent (no hidden configs)
- **Documentation**: Comprehensive specification with diagrams and examples

### Principle 7: Performance and Scalability ✅
- **NFR1**: Performance requirements defined (10 concurrent users, <500ms API)
- **Database**: Connection pooling, indexed queries
- **Caching**: MedCAT model caching (no repeated loads)
- **Resource Limits**: Realistic for single workstation (no over-engineering)

### Principle 8: Developer Experience ✅
- **Architecture**: Clear separation of core and modules
- **Documentation**: Comprehensive spec with code examples
- **Testing**: 80% coverage requirement
- **Docker**: Single `docker-compose up` for local development

### Principle 9: Clinical Workflow Integration ✅
- **User Stories**: Focus on clinician workflows (assigned tasks, project collaboration)
- **Task System**: Mirrors real clinical workflows (annotation, search, review)
- **Project-Based**: Multi-user collaboration on shared clinical projects

### Principle 10: Continuous Improvement ✅
- **Module System**: Easy to add new features as pluggable modules
- **Configuration**: Admin can tune settings without code changes
- **Audit Logs**: Track usage patterns for improvement opportunities
- **Extensible Schema**: JSONB fields for future flexibility

---

## Data Retention & Purging Policy

### Overview

**Goal**: Comply with GDPR/HIPAA data retention requirements while maintaining clinical governance audit trails.

**Key Requirements**:
- GDPR Article 5(1)(e): Data minimization and storage limitation
- HIPAA §164.316(b)(2)(i): Retain documentation for 6 years
- NHS Records Management Code of Practice: Clinical records 8 years, audit trails 7 years
- Clinical governance: Maintain audit trails for legal discovery

### Retention Periods

#### Clinical Documents & PHI

| Data Type | Retention Period | Rationale | Purging Method |
|-----------|------------------|-----------|----------------|
| **Documents** (`documents` table) | **8 years** from last patient contact | NHS Records Management Code | Automated purge + audit log |
| **Extracted Entities** (`extracted_entities`) | **8 years** from extraction date | Clinical governance | Cascade delete with documents |
| **Patient Records** (`patients`) | **8 years** from last document | Active patient care | Manual review required |
| **Audit Logs** (`audit_logs`) | **7 years** from creation | Legal discovery, NHS guidance | Automated archive then purge |

#### System Data

| Data Type | Retention Period | Rationale | Purging Method |
|-----------|------------------|-----------|----------------|
| **User Sessions** (`sessions`) | **90 days** from expiry | Security analysis | Automated purge daily |
| **Tasks** (`tasks`) | **2 years** from completion | Workflow analysis | Automated purge quarterly |
| **Module Data** (e.g., `patient_search_results`) | **1 year** from creation | Performance analysis | Module-defined purge |

### Purging Mechanisms

#### Automated Purging (Daily Cron Job)

```sql
-- Purge expired sessions (daily)
DELETE FROM sessions
WHERE expires_at < NOW() - INTERVAL '90 days';

-- Purge old completed tasks (quarterly)
DELETE FROM tasks
WHERE status = 'complete'
  AND completed_at < NOW() - INTERVAL '2 years';

-- Archive old audit logs (monthly, before purge)
INSERT INTO audit_logs_archive
SELECT * FROM audit_logs
WHERE timestamp < NOW() - INTERVAL '7 years';

DELETE FROM audit_logs
WHERE timestamp < NOW() - INTERVAL '7 years';
```

#### Document Purging (Semi-Automated)

**Process**:
1. **Weekly Report**: Generate list of documents eligible for purging (>8 years old)
2. **Admin Review**: Admin reviews list, marks documents for purge or legal hold
3. **Grace Period**: 30-day grace period for appeals
4. **Execution**: Batch purge approved documents
5. **Audit**: Log all purges with admin approval

```sql
-- Mark documents for purge
UPDATE documents
SET
    medcat_status = 'pending_purge',
    updated_at = NOW(),
    updated_by = 'admin-uuid'
WHERE
    uploaded_at < NOW() - INTERVAL '8 years'
    AND medcat_status != 'legal_hold';

-- Execute purge (after grace period)
DELETE FROM documents
WHERE medcat_status = 'pending_purge'
  AND updated_at < NOW() - INTERVAL '30 days';
```

#### Patient Record Purging (Manual Only)

**Constraints**: Patients linked to multiple documents, complex legal requirements

**Process**:
1. **Eligibility**: Patient has no documents within 8 years
2. **Admin Review**: Manual review required (cannot be automated)
3. **Anonymization Option**: Convert to anonymous research record (optional)
4. **Purge**: Delete patient record and extracted entities

```sql
-- Find eligible patients
SELECT p.id, p.nhs_number, p.first_name, p.last_name,
       MAX(d.uploaded_at) AS last_document_date
FROM patients p
LEFT JOIN documents d ON d.id = ANY(p.source_document_ids)
GROUP BY p.id
HAVING MAX(d.uploaded_at) < NOW() - INTERVAL '8 years'
   OR MAX(d.uploaded_at) IS NULL;
```

### Legal Hold Procedures

**Trigger Events**:
- Litigation initiated
- Clinical incident investigation
- Regulatory inquiry (CQC, ICO)
- Patient complaint escalation

**Legal Hold Workflow**:

```sql
-- Add legal_hold flag to documents table
ALTER TABLE documents
ADD COLUMN legal_hold BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN legal_hold_reason TEXT NULL,
ADD COLUMN legal_hold_by UUID REFERENCES users(id),
ADD COLUMN legal_hold_at TIMESTAMP WITH TIME ZONE NULL;

-- Place document on legal hold
UPDATE documents
SET
    legal_hold = TRUE,
    legal_hold_reason = 'Litigation: Smith vs Hospital',
    legal_hold_by = 'admin-uuid',
    legal_hold_at = NOW()
WHERE id = 'document-uuid';

-- Prevent purging of legal hold documents
-- (already in purge query above: AND medcat_status != 'legal_hold')
```

**Legal Hold Notifications**:
- Email admin when legal hold placed
- Weekly report of active legal holds
- Alert if purge attempted on legal hold document

### Anonymization for Research

**Goal**: Retain clinical data value while removing PHI after retention period

**Workflow**:
1. **Eligibility**: Documents >8 years old, no legal hold
2. **Anonymization**:
   - Replace NHS number → `PATIENT_001`, `PATIENT_002`, etc.
   - Replace names → `John Smith` → `Patient A`
   - Replace addresses → `London` (city only)
   - Replace dates → Year only (2015, not 2015-03-15)
3. **De-identification Table**:

```sql
CREATE TABLE deidentified_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_patient_id UUID,  -- No FK (patient may be deleted)
    token VARCHAR(50) NOT NULL,  -- 'PATIENT_001'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),

    -- Access control: Only researchers with special permission
    CONSTRAINT deidentified_mappings_unique_token UNIQUE(token)
);

-- Separate table for anonymized data (not accessible to clinicians)
CREATE TABLE deidentified_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_document_id UUID,  -- No FK
    patient_token VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,  -- De-identified content
    document_type VARCHAR(100),
    document_year INT,  -- Year only
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Access Control**: Only `researcher` role with `deidentified_data.view` permission

### Compliance Reporting

**Monthly Reports** (automated):
- Documents purged this month
- Documents on legal hold
- Retention policy compliance rate (% within policy)

**Annual Audit** (manual):
- Review retention policy against current regulations
- Verify purge procedures executed correctly
- Update retention periods if regulations change

---

## Disaster Recovery & Business Continuity

### Overview

**Goal**: Ensure clinical care continuity even if primary workstation fails

**Key Metrics**:
- **RTO (Recovery Time Objective)**: 4 hours (half working day)
- **RPO (Recovery Point Objective)**: 24 hours (maximum acceptable data loss)
- **MTTR (Mean Time To Repair)**: <8 hours

### Backup Strategy

#### Automated Daily Backups

**Schedule**: Daily at 2:00 AM (low usage period)

**Backup Scope**:
```bash
# Docker volumes to backup
/var/lib/docker/volumes/clinical-care-tools_postgres-data
/var/lib/docker/volumes/clinical-care-tools_medcat-models
/var/lib/docker/volumes/clinical-care-tools_documents  # If using file storage
/var/lib/docker/volumes/clinical-care-tools_logs
```

**Backup Script** (`/scripts/backup.sh`):
```bash
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

# PostgreSQL dump (compressed)
docker exec postgres pg_dump -U clinicaltools -Fc clinical_care_tools \
  > "$BACKUP_DIR/database.dump"

# Verify backup integrity
pg_restore --list "$BACKUP_DIR/database.dump" > /dev/null
if [ $? -eq 0 ]; then
    echo "Backup verified successfully"
else
    echo "ERROR: Backup verification failed!" >&2
    exit 1
fi

# Copy volumes (rsync for incremental)
rsync -av /var/lib/docker/volumes/clinical-care-tools_medcat-models \
  "$BACKUP_DIR/medcat-models"

# Encrypt backup (AES-256)
tar czf - "$BACKUP_DIR" | openssl enc -aes-256-cbc -salt \
  -out "$BACKUP_DIR.tar.gz.enc" -pass file:/etc/backup.key

# Upload to network storage (NAS/external drive)
cp "$BACKUP_DIR.tar.gz.enc" /mnt/nas/clinical-backups/

# Retention: Keep daily backups for 30 days, weekly for 6 months
find /backups -name "*.tar.gz.enc" -mtime +30 -delete
```

**Cron Schedule**:
```cron
0 2 * * * /scripts/backup.sh >> /var/log/backup.log 2>&1
```

#### Weekly Full Backup

**Schedule**: Every Sunday 3:00 AM

**Includes**:
- Full PostgreSQL dump
- All Docker volumes
- Application logs
- Configuration files
- Encryption keys (stored separately, not on same server)

#### Offsite Backup

**Frequency**: Weekly

**Methods**:
- Option A: Copy to offsite NAS (hospital network)
- Option B: USB hard drive rotated offsite (physical security)
- Option C: Encrypted cloud backup (Azure/AWS with HIPAA BAA)

**Security**: All offsite backups AES-256 encrypted

### Backup Testing & Verification

#### Monthly Restore Test

**Procedure** (first Monday of each month):
1. Select random backup from previous month
2. Restore to test environment (separate workstation)
3. Verify data integrity (sample queries)
4. Verify application functionality (login, search)
5. Document results and time taken

**Acceptance Criteria**:
- Restore completes within 4 hours (meets RTO)
- Data loss <24 hours (meets RPO)
- Application functional after restore

#### Checksum Verification

**Daily**:
```bash
# Generate checksums during backup
sha256sum "$BACKUP_DIR/database.dump" > "$BACKUP_DIR/checksums.txt"

# Verify checksums monthly
sha256sum -c /backups/2024-11-01/checksums.txt
```

### Failover Procedures

#### Scenario 1: Workstation Hardware Failure

**Detection**: Workstation unresponsive, won't boot

**Response** (within 4 hours RTO):
1. **Notify Stakeholders** (0-15 mins):
   - Email admin list: "Primary workstation down, initiating DR"
   - SMS alerts to on-call staff

2. **Prepare Standby Workstation** (15-60 mins):
   - Boot standby workstation (pre-configured with Docker)
   - Verify network connectivity
   - Mount backup storage

3. **Restore from Backup** (60-180 mins):
   ```bash
   # Decrypt latest backup
   openssl enc -d -aes-256-cbc -in backup.tar.gz.enc \
     -out backup.tar.gz -pass file:/etc/backup.key

   # Extract
   tar xzf backup.tar.gz

   # Restore PostgreSQL
   docker exec -i postgres pg_restore -U clinicaltools -d clinical_care_tools \
     < database.dump

   # Restore volumes
   rsync -av backup/medcat-models/ /var/lib/docker/volumes/clinical-care-tools_medcat-models/

   # Start application
   docker-compose up -d
   ```

4. **Verify Functionality** (180-210 mins):
   - Test login
   - Test patient search
   - Test document upload
   - Test audit log query

5. **Resume Operations** (210-240 mins):
   - Email users: "System restored, resume work"
   - Monitor for issues for 24 hours

#### Scenario 2: Data Corruption Detected

**Detection**: Checksum mismatch, database errors, PHI anomalies

**Response**:
1. **Immediately Stop Write Operations**:
   ```bash
   # Put application in read-only mode
   docker exec postgres psql -U clinicaltools -d clinical_care_tools \
     -c "ALTER DATABASE clinical_care_tools SET default_transaction_read_only = ON;"
   ```

2. **Identify Corruption Extent**:
   - Run database integrity checks
   - Check audit logs for when corruption started
   - Identify affected tables

3. **Restore from Last Known Good Backup**:
   - Find most recent uncorrupted backup
   - Restore affected tables only (if possible)
   - Verify data integrity

4. **Manual Data Recovery** (if needed):
   - Review audit logs for recent changes
   - Manually re-enter lost data (since last backup)
   - Document recovery process

#### Scenario 3: Ransomware/Malware Attack

**Detection**: Files encrypted, ransom note, unusual file changes

**Response**:
1. **Immediate Isolation**:
   - Disconnect workstation from network
   - Power off workstation
   - Do NOT pay ransom

2. **Forensic Analysis** (IT security team):
   - Preserve evidence (memory dump, disk image)
   - Identify attack vector
   - Determine data breach scope

3. **Clean Restore**:
   - Wipe infected workstation
   - Reinstall OS and Docker from scratch
   - Restore from pre-infection backup
   - Scan backup for malware before restoring

4. **Post-Incident**:
   - Report to ICO (if data breach)
   - Review security controls
   - Implement additional safeguards

### Business Continuity During Downtime

#### Alternative Access Methods

**If Primary Workstation Down**:
- **Urgent Patient Care**: Access patient records via hospital EHR (not this system)
- **Non-Urgent Tasks**: Postpone until system restored
- **Read-Only Access**: If database restored but app broken, provide SQL query access to authorized users

#### Communication Plan

**Stakeholders**:
- Clinicians using system
- IT support staff
- Hospital management
- Patients (if data breach)

**Templates**:
```
Subject: [URGENT] Clinical Tools System Outage

The Clinical Care Tools system is currently unavailable due to [hardware failure].

Estimated restoration time: [4 hours] by [14:00]

Alternative: Access patient records via hospital EHR for urgent care.

Updates will be sent every hour.

IT Support: [phone] [email]
```

### Annual DR Test

**Full Disaster Recovery Drill** (once per year):
1. Simulate complete workstation failure
2. Execute full failover procedure
3. Invite observers (IT, clinical, management)
4. Measure RTO/RPO achievement
5. Document lessons learned
6. Update DR plan based on findings

---

## Clinical Safety Mechanisms

### Overview

**Goal**: Prevent patient harm from system errors, misuse, or data quality issues

**Key Standards**:
- NHS DCB0129: Clinical Safety Risk Management
- ISO 14971: Medical Devices Risk Management
- Clinical governance best practices

### Clinical Decision Override Tracking

#### Scenario

Clinician disagrees with CDS recommendation or search results

**Example**:
- System suggests "Atrial Flutter" based on MedCAT extraction
- Clinician reviews source document, determines it's actually "Atrial Fibrillation"
- Clinician overrides system finding

#### Schema

```sql
CREATE TABLE clinical_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    resource_type VARCHAR(100) NOT NULL,  -- 'extracted_entity', 'cds_recommendation', 'patient_match'
    resource_id UUID NOT NULL,
    system_value TEXT NOT NULL,  -- What system suggested
    override_value TEXT NOT NULL,  -- What clinician chose
    reason TEXT NOT NULL,  -- Required: Why override?
    severity VARCHAR(50) NOT NULL,  -- 'minor', 'moderate', 'major', 'critical'
    reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT clinical_overrides_severity_check CHECK (severity IN ('minor', 'moderate', 'major', 'critical'))
);

CREATE INDEX idx_clinical_overrides_user ON clinical_overrides(user_id);
CREATE INDEX idx_clinical_overrides_resource ON clinical_overrides(resource_type, resource_id);
CREATE INDEX idx_clinical_overrides_severity ON clinical_overrides(severity);
CREATE INDEX idx_clinical_overrides_reviewed ON clinical_overrides(reviewed) WHERE reviewed = FALSE;
```

#### Workflow

**UI Component** (shown when clinician questions system):
```vue
<template>
  <v-dialog v-model="showOverride">
    <v-card>
      <v-card-title>Override System Finding</v-card-title>
      <v-card-text>
        <p><strong>System found:</strong> {{ systemValue }}</p>
        <v-text-field
          v-model="overrideValue"
          label="Correct value"
          required
        />
        <v-textarea
          v-model="reason"
          label="Reason for override (required)"
          required
        />
        <v-select
          v-model="severity"
          :items="['minor', 'moderate', 'major', 'critical']"
          label="Clinical severity"
          hint="How significant is this discrepancy?"
        />
      </v-card-text>
      <v-card-actions>
        <v-btn @click="submitOverride">Submit Override</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
```

**Audit Log** (automatically generated):
```python
await audit_log(
    user_id=user.id,
    action="CLINICAL_OVERRIDE",
    resource_type="extracted_entity",
    resource_id=entity_id,
    details={
        "system_value": "Atrial Flutter (CUI: C0004239)",
        "override_value": "Atrial Fibrillation (CUI: C0004238)",
        "reason": "Review of source document shows 'AF' abbreviation refers to fibrillation, not flutter",
        "severity": "moderate"
    }
)
```

#### Override Review Process

**Weekly Review** (Clinical Governance Lead):
1. Query unreviewed overrides:
   ```sql
   SELECT * FROM clinical_overrides
   WHERE reviewed = FALSE
   ORDER BY severity DESC, created_at ASC;
   ```

2. Review each override:
   - Minor: Acknowledge and mark reviewed
   - Moderate: Discuss with clinician if pattern emerges
   - Major/Critical: Immediate investigation, potential incident report

3. **Quality Improvement**:
   - Identify systematic issues (e.g., MedCAT consistently misclassifying specific term)
   - Trigger model retraining if >10 overrides for same concept
   - Update clinical guidelines if needed

### Critical Finding Alerts

#### Scenario

Urgent clinical findings requiring immediate attention

**Examples**:
- Suspected sepsis
- Acute MI (myocardial infarction)
- Critical lab values (e.g., K+ >6.5)
- Safety alerts (drug interactions)

#### Schema

```sql
CREATE TABLE critical_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    finding_type VARCHAR(100) NOT NULL,  -- 'sepsis_alert', 'acute_mi', 'critical_lab', 'drug_interaction'
    severity VARCHAR(50) NOT NULL,  -- 'urgent', 'critical'
    description TEXT NOT NULL,
    source_document_id UUID REFERENCES documents(id),
    source_entity_ids UUID[] NOT NULL,  -- Array of extracted_entities IDs
    confidence REAL NOT NULL,

    -- Acknowledgment tracking
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE NULL,
    action_taken TEXT NULL,

    -- Escalation
    escalated BOOLEAN NOT NULL DEFAULT FALSE,
    escalated_to UUID REFERENCES users(id),
    escalated_at TIMESTAMP WITH TIME ZONE NULL,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,  -- Auto-dismiss after 48 hours

    CONSTRAINT critical_findings_severity_check CHECK (severity IN ('urgent', 'critical')),
    CONSTRAINT critical_findings_confidence_check CHECK (confidence >= 0.0 AND confidence <= 1.0)
);

CREATE INDEX idx_critical_findings_patient ON critical_findings(patient_id);
CREATE INDEX idx_critical_findings_acknowledged ON critical_findings(acknowledged) WHERE acknowledged = FALSE;
CREATE INDEX idx_critical_findings_expires ON critical_findings(expires_at) WHERE acknowledged = FALSE;
```

#### Alert Workflow

**Detection** (during MedCAT processing):
```python
# After extracting entities
for entity in extracted_entities:
    # Check against critical finding rules
    if entity.cui == 'C0243026' and entity.meta_annotations['Negation'] == 'Affirmed':  # Sepsis
        create_critical_finding(
            patient_id=patient_id,
            finding_type='sepsis_alert',
            severity='critical',
            description=f"Suspected sepsis detected in document {document.filename}",
            confidence=entity.confidence
        )

        # Send notification (email + in-app)
        notify_user(
            user_id=document.uploaded_by,
            message="CRITICAL: Suspected sepsis detected in uploaded document",
            priority='high'
        )
```

**Dashboard Widget** (always visible):
```vue
<v-alert
  v-if="criticalFindings.length > 0"
  type="error"
  prominent
  class="critical-findings-alert"
>
  <v-row align="center">
    <v-col>
      {{ criticalFindings.length }} Critical Finding(s) Require Attention
    </v-col>
    <v-col class="text-right">
      <v-btn @click="viewCriticalFindings">Review Now</v-btn>
    </v-col>
  </v-row>
</v-alert>
```

**Acknowledgment Workflow**:
1. Clinician reviews finding
2. Determines action (escalate, false positive, already managed)
3. Documents action taken
4. Marks acknowledged

**Auto-Escalation**: If not acknowledged within 4 hours, escalate to clinical lead

### Handover Procedures

#### Scenario

Staff changeover (shift change, annual leave, staff leaving)

**Challenge**: Ensure continuity of patient care and tasks

#### Task Reassignment

```sql
-- Reassign all pending tasks from outgoing user to incoming user
UPDATE tasks
SET
    assigned_to = 'incoming-user-uuid',
    updated_at = NOW(),
    updated_by = 'admin-uuid',
    configuration = jsonb_set(
        configuration,
        '{handover_notes}',
        to_jsonb('Reassigned from Dr. Smith (on leave) to Dr. Jones')
    )
WHERE
    assigned_to = 'outgoing-user-uuid'
    AND status IN ('pending', 'in_progress');
```

#### Handover Checklist

**UI Prompt** (when user marks themselves as "on leave"):
- [ ] Review all pending tasks
- [ ] Reassign urgent tasks to specific colleague
- [ ] Add handover notes to each task
- [ ] Notify project owners of absence
- [ ] Set auto-reply email

**Handover Notes** (stored in task configuration):
```json
{
  "handover_notes": "Patient Mrs. Smith (NHS: 1234567890) - Awaiting MRI results, due back 15th Nov. Check timeline for follow-up appointment.",
  "previous_owner": "user-uuid-outgoing",
  "handover_date": "2024-11-08T09:00:00Z"
}
```

### Clinical Incident Reporting

#### Integration with Hospital Incident System

**Trigger Events** (require incident report):
- System error affecting patient care
- Data loss or corruption
- Clinical override marked "critical" severity
- Critical finding missed or delayed
- Unauthorized PHI access

#### Schema

```sql
CREATE TABLE clinical_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_type VARCHAR(100) NOT NULL,  -- 'system_error', 'data_loss', 'missed_finding', 'unauthorized_access'
    severity VARCHAR(50) NOT NULL,  -- 'no_harm', 'near_miss', 'minor_harm', 'major_harm'
    description TEXT NOT NULL,
    patient_affected UUID REFERENCES patients(id),  -- NULL if no specific patient
    user_involved UUID REFERENCES users(id),
    root_cause TEXT NULL,
    corrective_action TEXT NULL,

    -- Hospital incident system integration
    hospital_incident_id VARCHAR(100) NULL,  -- External incident ID
    reported_to_hospital BOOLEAN NOT NULL DEFAULT FALSE,
    reported_at TIMESTAMP WITH TIME ZONE NULL,

    -- Investigation
    investigated BOOLEAN NOT NULL DEFAULT FALSE,
    investigated_by UUID REFERENCES users(id),
    investigation_notes TEXT NULL,
    investigation_complete_at TIMESTAMP WITH TIME ZONE NULL,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),

    CONSTRAINT clinical_incidents_severity_check CHECK (severity IN ('no_harm', 'near_miss', 'minor_harm', 'major_harm'))
);

CREATE INDEX idx_clinical_incidents_severity ON clinical_incidents(severity);
CREATE INDEX idx_clinical_incidents_investigated ON clinical_incidents(investigated) WHERE investigated = FALSE;
CREATE INDEX idx_clinical_incidents_patient ON clinical_incidents(patient_affected);
```

#### Workflow

**Automatic Incident Creation**:
```python
# Example: System error during MedCAT processing
try:
    entities = await medcat_service.process(document.content)
except Exception as e:
    # Log error
    logger.error(f"MedCAT processing failed: {e}")

    # Create incident
    incident = await create_clinical_incident(
        incident_type='system_error',
        severity='near_miss',  # No patient harm yet, but potential
        description=f"MedCAT processing failed for document {document.id}: {str(e)}",
        user_involved=document.uploaded_by
    )

    # Notify clinical governance lead
    notify_clinical_lead(incident)
```

**Investigation Workflow**:
1. Incident created → Email to clinical governance lead
2. Lead reviews incident → Assigns to investigator
3. Investigator gathers evidence (audit logs, screenshots, user interviews)
4. Root cause analysis
5. Corrective actions identified
6. Incident marked complete
7. Monthly review of all incidents (quality improvement)

### Patient Safety Dashboard

**Admin View**:
- Open critical findings (by severity)
- Unreviewed clinical overrides (by severity)
- Open clinical incidents (by type)
- System health metrics (uptime, error rates)

**Alerts**:
- >5 critical findings unacknowledged for >4 hours → Escalate to clinical director
- >10 clinical overrides of same concept → Trigger model review
- >3 clinical incidents in one week → Immediate review meeting

---

## Enhanced Authentication & Authorization

### Break-Glass Access

#### Scenario

**Emergency clinical situation** requiring immediate access to patient data:
- Clinician needs urgent access to patient record but not assigned to project
- Patient unconscious, cannot consent
- Life-threatening situation, no time for formal access request

#### Schema Enhancement

```sql
-- Add to users table
ALTER TABLE users
ADD COLUMN can_break_glass BOOLEAN NOT NULL DEFAULT FALSE;

-- Break-glass access log
CREATE TABLE break_glass_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    patient_id UUID NOT NULL REFERENCES patients(id),
    reason TEXT NOT NULL,  -- Required: Why emergency access needed
    clinical_justification TEXT NOT NULL,  -- Detailed justification
    accessed_resources JSONB NOT NULL DEFAULT '[]',  -- Array of resource IDs accessed
    duration_minutes INT NOT NULL DEFAULT 60,  -- How long access granted
    access_granted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    access_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Post-access review
    reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE NULL,
    review_outcome VARCHAR(50) NULL,  -- 'justified', 'questionable', 'inappropriate'
    review_notes TEXT NULL,

    -- Security team notification
    security_notified BOOLEAN NOT NULL DEFAULT TRUE,
    security_notified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT break_glass_review_outcome_check CHECK (
        review_outcome IS NULL OR review_outcome IN ('justified', 'questionable', 'inappropriate')
    )
);

CREATE INDEX idx_break_glass_user ON break_glass_events(user_id);
CREATE INDEX idx_break_glass_patient ON break_glass_events(patient_id);
CREATE INDEX idx_break_glass_reviewed ON break_glass_events(reviewed) WHERE reviewed = FALSE;
CREATE INDEX idx_break_glass_expires ON break_glass_events(access_expires_at);
```

#### Break-Glass Workflow

**UI Prompt**:
```vue
<v-dialog v-model="showBreakGlass" persistent max-width="600px">
  <v-card>
    <v-card-title class="error white--text">
      ⚠️ Emergency Access (Break-Glass)
    </v-card-title>
    <v-card-text>
      <v-alert type="warning" prominent>
        This access will be:
        - Logged and audited
        - Reviewed by clinical governance
        - Reported to security team
        - Limited to 60 minutes
      </v-alert>

      <v-text-field
        v-model="patientIdentifier"
        label="Patient NHS Number or MRN"
        required
      />

      <v-textarea
        v-model="reason"
        label="Emergency Reason (Required)"
        hint="E.g., 'Patient unconscious in A&E, need medication history'"
        rows="3"
        required
      />

      <v-textarea
        v-model="clinicalJustification"
        label="Clinical Justification (Detailed)"
        hint="Explain why immediate access is necessary for patient care"
        rows="4"
        required
      />

      <v-checkbox
        v-model="acknowledged"
        label="I acknowledge this access will be reviewed and I may be required to provide additional justification"
        required
      />
    </v-card-text>
    <v-card-actions>
      <v-btn @click="showBreakGlass = false">Cancel</v-btn>
      <v-btn
        color="error"
        @click="requestBreakGlass"
        :disabled="!canSubmit"
      >
        Request Emergency Access
      </v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

**Backend Logic**:
```python
@router.post("/api/v1/auth/break-glass")
async def request_break_glass_access(
    request: BreakGlassRequest,
    user: User = Depends(get_current_user)
):
    # Validate user has break-glass permission
    if not user.can_break_glass:
        raise HTTPException(403, "User not authorized for break-glass access")

    # Validate reason is provided and substantive
    if len(request.reason) < 20:
        raise HTTPException(400, "Reason must be detailed (min 20 characters)")

    # Find patient
    patient = await get_patient_by_identifier(request.patient_identifier)
    if not patient:
        raise HTTPException(404, "Patient not found")

    # Create break-glass event
    event = await create_break_glass_event(
        user_id=user.id,
        patient_id=patient.id,
        reason=request.reason,
        clinical_justification=request.clinical_justification,
        duration_minutes=60
    )

    # Audit log (high priority)
    await audit_log(
        user_id=user.id,
        action="BREAK_GLASS_ACCESS",
        resource_type="patient",
        resource_id=str(patient.id),
        details={
            "reason": request.reason,
            "clinical_justification": request.clinical_justification,
            "duration_minutes": 60
        }
    )

    # IMMEDIATE notifications
    await notify_security_team(event)  # Email + SMS
    await notify_clinical_governance_lead(event)

    # Grant temporary access (modify user permissions in-memory)
    # Return temporary token with patient access
    temp_token = create_temp_access_token(
        user_id=user.id,
        patient_id=patient.id,
        expires_in_minutes=60
    )

    return {
        "access_granted": True,
        "expires_at": event.access_expires_at,
        "temp_token": temp_token,
        "message": "Emergency access granted. Security team notified."
    }
```

**Auto-Revocation**:
```python
# Background task runs every 5 minutes
async def revoke_expired_break_glass_access():
    expired_events = await db.query(
        "SELECT * FROM break_glass_events WHERE access_expires_at < NOW() AND reviewed = FALSE"
    )

    for event in expired_events:
        # Revoke access (invalidate temp tokens)
        await revoke_temp_tokens(user_id=event.user_id, patient_id=event.patient_id)

        # Audit log
        await audit_log(
            user_id=event.user_id,
            action="BREAK_GLASS_EXPIRED",
            resource_type="patient",
            resource_id=str(event.patient_id)
        )
```

**Post-Access Review** (within 24 hours):
1. Clinical governance lead reviews all break-glass events
2. Contacts clinician for additional justification if needed
3. Marks review outcome (`justified`, `questionable`, `inappropriate`)
4. If `inappropriate` → Disciplinary process triggered

### Session Security Enhancements

#### Current Limitations

Basic JWT with 8-hour expiry is insufficient for healthcare security

#### Enhancements

**1. Session Binding**

```sql
-- Enhance sessions table
ALTER TABLE sessions
ADD COLUMN ip_address_hash VARCHAR(64) NOT NULL,  -- SHA-256 of IP
ADD COLUMN user_agent_hash VARCHAR(64) NOT NULL,  -- SHA-256 of user-agent
ADD COLUMN device_fingerprint VARCHAR(255) NULL,  -- Browser fingerprint
ADD COLUMN is_suspicious BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN suspicious_reason TEXT NULL;

-- Session validation now checks IP + user-agent match
```

**Validation Logic**:
```python
async def validate_session(token: str, request: Request):
    session = await get_session_by_token_hash(hash_token(token))

    if not session:
        raise HTTPException(401, "Invalid session")

    # Check expiry
    if session.expires_at < datetime.now():
        await delete_session(session.id)
        raise HTTPException(401, "Session expired")

    # Check IP binding (allow some variance for DHCP)
    current_ip_hash = hash_ip(request.client.host)
    if current_ip_hash != session.ip_address_hash:
        # Mark suspicious but don't reject (could be legitimate IP change)
        session.is_suspicious = True
        session.suspicious_reason = "IP address changed"
        await update_session(session)

        # Alert security team if multiple IP changes
        if session.suspicious_change_count > 3:
            await alert_security_team(session)

    # Check user-agent binding (strict)
    current_ua_hash = hash_user_agent(request.headers.get("User-Agent"))
    if current_ua_hash != session.user_agent_hash:
        # Immediate rejection (likely session hijack)
        await delete_session(session.id)
        await audit_log(
            user_id=session.user_id,
            action="SESSION_HIJACK_DETECTED",
            resource_type="session",
            resource_id=str(session.id),
            details={"reason": "User-Agent mismatch"}
        )
        raise HTTPException(401, "Session invalid - security violation")

    return session
```

**2. Concurrent Session Limits**

```python
# During login
async def create_session(user_id: UUID, ...):
    # Count active sessions for user
    active_sessions = await db.query(
        "SELECT COUNT(*) FROM sessions WHERE user_id = ? AND expires_at > NOW()",
        user_id
    )

    if active_sessions >= 2:  # Max 2 concurrent sessions
        # Terminate oldest session
        oldest_session = await db.query(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at ASC LIMIT 1",
            user_id
        )
        await delete_session(oldest_session.id)

        # Notify user (email)
        await notify_user(
            user_id=user_id,
            message="Previous session terminated due to new login from different device"
        )

    # Create new session
    # ...
```

**3. Idle Timeout (15 minutes)**

```python
# Middleware updates last_activity on every request
@app.middleware("http")
async def update_session_activity(request: Request, call_next):
    if "Authorization" in request.headers:
        token = extract_token(request.headers["Authorization"])
        session = await get_session_by_token_hash(hash_token(token))

        if session:
            # Check idle timeout
            if session.last_activity < datetime.now() - timedelta(minutes=15):
                # Session idle too long
                await delete_session(session.id)
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Session expired due to inactivity"}
                )

            # Update last activity
            session.last_activity = datetime.now()
            await update_session(session)

    response = await call_next(request)
    return response
```

**4. Admin Force Logout**

```sql
-- Add to sessions table
ALTER TABLE sessions
ADD COLUMN force_logout BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN force_logout_reason TEXT NULL,
ADD COLUMN force_logout_by UUID REFERENCES users(id);
```

**API Endpoint**:
```python
@router.post("/api/v1/admin/force-logout/{user_id}")
async def force_logout_user(
    user_id: UUID,
    reason: str,
    admin: User = Depends(require_permission("admin.force_logout"))
):
    # Mark all sessions for force logout
    await db.execute(
        """UPDATE sessions
           SET force_logout = TRUE,
               force_logout_reason = ?,
               force_logout_by = ?
           WHERE user_id = ?""",
        reason, admin.id, user_id
    )

    # Audit log
    await audit_log(
        user_id=admin.id,
        action="ADMIN_FORCE_LOGOUT",
        resource_type="user",
        resource_id=str(user_id),
        details={"reason": reason}
    )

    return {"message": f"All sessions for user {user_id} will be terminated"}
```

**Client-Side Check** (on every API call):
```python
# Middleware checks force_logout flag
if session.force_logout:
    await delete_session(session.id)
    return JSONResponse(
        status_code=401,
        content={
            "detail": "Your session has been terminated by an administrator",
            "reason": session.force_logout_reason
        }
    )
```

---

## Open Questions

### High Priority

1. **Q1**: MedCAT Model Storage
   - **Question**: Where are MedCAT models stored? Shared volume or per-user?
   - **Options**:
     - A) Shared volume (all users use same models) - **RECOMMENDED**
     - B) Per-user models (isolation but duplicated storage)
   - **Decision Needed By**: Before database schema finalized
   - **Owner**: Admin + Team Lead

2. **Q2**: Document Repository
   - **Question**: How are clinical documents stored? PostgreSQL or file system?
   - **Options**:
     - A) PostgreSQL BYTEA (encrypted, transactional) - **RECOMMENDED for <10MB docs**
     - B) File system (cheaper, larger files) - **RECOMMENDED for >10MB docs**
     - C) Hybrid (metadata in PostgreSQL, files on disk)
   - **Decision Needed By**: Before implementing document management
   - **Owner**: Backend Developer

3. **Q3**: Patient Data Storage
   - **Question**: Does this app store actual patient data (PHI) or just references (MRNs)?
   - **Options**:
     - A) Store PHI (names, DOB, MRN) - requires encryption, strict access controls
     - B) Store references only (MRN pointers to external EHR) - **RECOMMENDED**
   - **Decision Needed By**: Before database schema finalized
   - **Owner**: Compliance Officer + Team Lead
   - **Impact**: HIPAA compliance requirements, audit logging scope

4. **Q4**: Task Types
   - **Question**: What task types do we need beyond (annotation, search, review, validation)?
   - **Examples**: CDS rule configuration, cohort review, quality audit, etc.
   - **Decision Needed By**: Before task management implementation
   - **Owner**: Clinical SME + Product Manager

### Medium Priority

5. **Q5**: Email Notifications
   - **Question**: Should system send email notifications (task assignments, account lockouts)?
   - **Options**:
     - A) Yes, via SMTP (requires email server configuration)
     - B) No, users check dashboard manually - **RECOMMENDED for MVP**
   - **Decision Needed By**: Before user management implementation
   - **Owner**: Product Manager

6. **Q6**: Session Management
   - **Question**: Should system support multiple concurrent sessions per user?
   - **Options**:
     - A) Yes, multiple devices (desktop + tablet)
     - B) No, single session per user (logout on new login) - **RECOMMENDED**
   - **Decision Needed By**: Before authentication implementation
   - **Owner**: Security Lead

7. **Q7**: Database Backups
   - **Question**: Backup frequency and retention policy?
   - **Options**:
     - A) Daily backups, 30-day retention - **RECOMMENDED**
     - B) Hourly backups, 7-day retention (higher frequency, shorter retention)
   - **Decision Needed By**: Before deployment
   - **Owner**: IT Administrator

8. **Q8**: Module Installation
   - **Question**: How do admins install new modules? Upload .zip or pre-bundled?
   - **Options**:
     - A) Upload .zip via UI (dynamic installation) - **FUTURE FEATURE**
     - B) Pre-bundled in Docker image (rebuild image for new modules) - **RECOMMENDED for MVP**
   - **Decision Needed By**: Before module system implementation
   - **Owner**: DevOps Lead

### Low Priority

9. **Q9**: Internationalization (i18n)
   - **Question**: Support multiple languages (English, Spanish, etc.)?
   - **Decision**: Not for MVP, English only. Future consideration if requested.
   - **Owner**: Product Manager

10. **Q10**: Dark Mode
    - **Question**: Support dark mode UI theme?
    - **Decision**: Yes, Vuetify supports this easily. Low effort, high user satisfaction.
    - **Owner**: Frontend Developer

11. **Q11**: Mobile Responsiveness
    - **Question**: Should UI work on tablets/mobile devices?
    - **Decision**: Desktop first, responsive layout as nice-to-have (Vuetify handles this).
    - **Owner**: Frontend Developer

---

## Summary

This specification defines a **Clinical Care Tools Base Application** that:

1. **Runs on a single workstation** (Docker Compose deployment)
2. **Supports multiple users** (admin + clinicians via RDP)
3. **Isolates user work** (task-based assignment, project membership)
4. **Enables collaboration** (shared projects, resources, models)
5. **Provides comprehensive audit logging** (WHO, WHAT, WHEN, WHERE)
6. **Supports modular features** (patient search, timeline, CDS as pluggable modules)

**Key Architectural Decisions**:
- **Backend**: FastAPI (proven in MedCAT Service)
- **Frontend**: Vue 3 + Vuetify (proven in MedCAT Trainer)
- **Database**: PostgreSQL 17.6 (proven in MedCAT Trainer)
- **Authentication**: JWT-based (username/password, no OIDC)
- **Module System**: Dynamic loading with registration pattern

**Inspired by MedCAT Trainer**:
- Multi-user project membership pattern
- PostgreSQL database with relational integrity
- Django-style audit logging (adapted to FastAPI)
- Docker Compose deployment model
- User task assignment workflow

**Next Steps**:
1. Review this specification with stakeholders
2. Answer open questions (Q1-Q11)
3. Create technical plan (architecture diagrams, API design, data models)
4. Break down into tasks (Spec-Kit workflow)
5. Implement core infrastructure (auth, audit, module loader)
6. Implement first module (Patient Search as proof of concept)

---

**END OF SPECIFICATION**
