---
name: modular-app-architect
description: Designs extensible modular architecture for clinical care tools platform. Use when planning base app structure with module/plugin extension points, separating core from features, designing shared infrastructure (auth, audit, config), or planning module communication. Integrates with existing MedCAT ecosystem (Trainer, Service, v2). Ensures modules can be developed and deployed independently.
---

# Modular App Architect Expert Skill

## When to use this skill

Activate when:
- Designing base app structure for clinical care tools
- Planning module/plugin system architecture
- Defining module extension points and APIs
- Separating core infrastructure from feature modules
- Planning independent module development and deployment
- Integrating with existing MedCAT components (Trainer, Service)
- Deciding on shared vs module-specific concerns

## Core Architectural Principles

### Principle 1: Core + Modules Pattern

**Core App** (minimal, stable):
- Authentication & authorization
- Audit logging
- Configuration management
- Module registry & loader
- Shared UI shell (header, sidebar, routing)
- API gateway (optional)

**Modules** (features, evolving):
- Patient Search Module
- Timeline View Module
- Clinical Decision Support Module
- Cohort Builder Module
- Concept Analytics Module
- (Future modules as needed)

**Benefits**:
- Modules developed independently (parallel work)
- Modules deployed independently (gradual rollout)
- Core remains stable (rarely changes)
- Easy to add/remove modules
- Clear ownership boundaries

### Principle 2: Module Independence

**Each module**:
- Has own codebase (separate directory)
- Has own routes (e.g., `/modules/patient-search/*`)
- Has own components (Vue)
- Has own API endpoints (e.g., `/api/v1/patient-search/*`)
- Can be disabled without affecting other modules
- Communicates with core via defined APIs

**Modules do NOT**:
- Import code from other modules (except via public APIs)
- Share database tables (except via core services)
- Depend on other modules being installed

### Principle 3: Shared Infrastructure

**Core provides**:
- Authentication service (OIDC/Keycloak)
- Authorization middleware (RBAC)
- Audit logging service
- Configuration store
- HTTP client (axios with auth interceptors)
- Database connections
- MedCAT Service client
- Elasticsearch client

**Modules consume via**:
- Dependency injection
- Environment variables
- Shared SDK/library

## Recommended Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Clinical Care Tools Platform                                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌──────────────────┐                  │
│  │  Core App       │  │  Shared Infra    │                  │
│  │  (Vue 3)        │  │                  │                  │
│  │  - Dashboard    │  │  - Auth (OIDC)   │                  │
│  │  - Module Loader│  │  - Audit Logger  │                  │
│  │  - Routing      │  │  - Config Store  │                  │
│  │  - Shell UI     │  │  - HTTP Client   │                  │
│  └─────────────────┘  └──────────────────┘                  │
│         │                       │                            │
│  ┌──────┴───────────────────────┴─────────────────┐         │
│  │          Module Registry                        │         │
│  │  {                                              │         │
│  │    "patient-search": { ... },                  │         │
│  │    "timeline-view": { ... },                   │         │
│  │    "clinical-decision-support": { ... }        │         │
│  │  }                                              │         │
│  └──────┬───────────────────────┬─────────────────┘         │
│         │                       │                            │
│  ┌──────▼───────┐  ┌───────────▼──────┐  ┌─────────────┐   │
│  │ Module 1     │  │ Module 2         │  │ Module N    │   │
│  │ Patient      │  │ Timeline         │  │ CDS         │   │
│  │ Search       │  │ View             │  │             │   │
│  └──────────────┘  └──────────────────┘  └─────────────┘   │
│         │                  │                     │           │
└─────────┼──────────────────┼─────────────────────┼───────────┘
          │                  │                     │
          ▼                  ▼                     ▼
┌──────────────────────────────────────────────────────────────┐
│  Backend Services (FastAPI)                                   │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────────┐  ┌─────────────┐     │
│  │ Core API    │  │ Module Endpoints │  │ Module N    │     │
│  │ /api/v1/    │  │ /api/v1/patients/│  │ /api/v1/cds/│     │
│  │   auth/     │  │   search         │  │   ...       │     │
│  │   audit/    │  │                  │  │             │     │
│  │   config/   │  │ /api/v1/timeline/│  │             │     │
│  └─────────────┘  └──────────────────┘  └─────────────┘     │
│         │                   │                    │            │
└─────────┼───────────────────┼────────────────────┼────────────┘
          │                   │                    │
          ▼                   ▼                    ▼
┌──────────────────────────────────────────────────────────────┐
│  Shared Services                                              │
├──────────────────────────────────────────────────────────────┤
│  - MedCAT Service (http://medcat-service:5555)               │
│  - Elasticsearch (patient index)                             │
│  - PostgreSQL (audit logs, users, module config)             │
│  - Redis (caching)                                            │
│  - Keycloak (authentication)                                  │
└──────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
cogstack-clinical-care-tools/
├── frontend/                    # Vue 3 frontend
│   ├── src/
│   │   ├── core/               # Core app
│   │   │   ├── App.vue         # Root component
│   │   │   ├── main.ts         # Entry point
│   │   │   ├── router.ts       # Core routes + module routes
│   │   │   ├── auth.ts         # OIDC auth setup
│   │   │   ├── components/     # Shared components
│   │   │   │   ├── AppShell.vue      # Header + sidebar + content
│   │   │   │   ├── NavBar.vue
│   │   │   │   ├── Sidebar.vue
│   │   │   │   └── Dashboard.vue
│   │   │   ├── services/       # Shared services
│   │   │   │   ├── api.ts      # HTTP client with auth
│   │   │   │   ├── audit.ts    # Audit logging
│   │   │   │   └── config.ts   # Config store
│   │   │   └── composables/    # Shared composables
│   │   │       ├── useAuth.ts
│   │   │       ├── useAudit.ts
│   │   │       └── useMedCAT.ts
│   │   │
│   │   ├── modules/            # Feature modules
│   │   │   ├── patient-search/
│   │   │   │   ├── index.ts    # Module entry (exports routes, components)
│   │   │   │   ├── routes.ts   # Module routes
│   │   │   │   ├── views/
│   │   │   │   │   └── PatientSearch.vue
│   │   │   │   ├── components/
│   │   │   │   │   ├── SearchFilters.vue
│   │   │   │   │   └── PatientList.vue
│   │   │   │   ├── services/
│   │   │   │   │   └── patientSearchAPI.ts
│   │   │   │   └── types.ts
│   │   │   │
│   │   │   ├── timeline-view/
│   │   │   │   ├── index.ts
│   │   │   │   ├── routes.ts
│   │   │   │   ├── views/
│   │   │   │   └── components/
│   │   │   │
│   │   │   └── clinical-decision-support/
│   │   │       └── ...
│   │   │
│   │   └── module-registry.ts  # Module registration
│   │
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app + module routers
│   │   ├── core/               # Core functionality
│   │   │   ├── config.py       # Pydantic settings
│   │   │   ├── auth.py         # OIDC JWT validation
│   │   │   ├── audit.py        # Audit logging
│   │   │   ├── database.py     # DB connections
│   │   │   └── dependencies.py # Shared dependencies
│   │   │
│   │   ├── modules/            # Module API endpoints
│   │   │   ├── patient_search/
│   │   │   │   ├── router.py   # FastAPI router
│   │   │   │   ├── service.py  # Business logic
│   │   │   │   ├── schemas.py  # Pydantic models
│   │   │   │   └── __init__.py
│   │   │   │
│   │   │   ├── timeline_view/
│   │   │   │   └── ...
│   │   │   │
│   │   │   └── clinical_decision_support/
│   │   │       └── ...
│   │   │
│   │   ├── clients/            # Shared clients
│   │   │   ├── medcat_client.py
│   │   │   ├── elasticsearch_client.py
│   │   │   └── cache_client.py
│   │   │
│   │   └── tests/
│   │
│   ├── alembic/                # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml          # Local development
├── .env.example
└── README.md
```

## Module Definition Pattern

### Frontend Module Structure

**Module Entry Point** (`modules/patient-search/index.ts`):
```typescript
import type { RouteRecordRaw } from 'vue-router'
import PatientSearch from './views/PatientSearch.vue'

export interface ModuleDefinition {
  name: string
  version: string
  displayName: string
  description: string
  icon: string                  // Material Design icon
  routes: RouteRecordRaw[]
  permissions: string[]         // Required permissions
  enabled: boolean
}

export const patientSearchModule: ModuleDefinition = {
  name: 'patient-search',
  version: '1.0.0',
  displayName: 'Patient Search',
  description: 'Search patients by medical concepts',
  icon: 'mdi-account-search',
  routes: [
    {
      path: '/patient-search',
      name: 'PatientSearch',
      component: PatientSearch,
      meta: {
        requiresAuth: true,
        requiredPermissions: ['patient:search']
      }
    }
  ],
  permissions: ['patient:search', 'patient:view'],
  enabled: true
}
```

**Module Registry** (`module-registry.ts`):
```typescript
import { patientSearchModule } from './modules/patient-search'
import { timelineViewModule } from './modules/timeline-view'
import { clinicalDecisionSupportModule } from './modules/clinical-decision-support'

export const modules = [
  patientSearchModule,
  timelineViewModule,
  clinicalDecisionSupportModule
]

// Filter enabled modules
export const enabledModules = modules.filter(m => m.enabled)

// Get all routes from enabled modules
export const moduleRoutes = enabledModules.flatMap(m => m.routes)

// Get all permissions from enabled modules
export const allPermissions = enabledModules.flatMap(m => m.permissions)
```

**Router Integration** (`core/router.ts`):
```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { moduleRoutes } from '../module-registry'
import Dashboard from './components/Dashboard.vue'

const coreRoutes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/settings', name: 'Settings', component: () => import('./views/Settings.vue') }
]

const router = createRouter({
  history: createWebHistory(),
  routes: [
    ...coreRoutes,
    ...moduleRoutes  // Automatically include all module routes
  ]
})

// Auth guard
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !isAuthenticated()) {
    next('/login')
  } else if (to.meta.requiredPermissions) {
    const hasPermission = hasAllPermissions(to.meta.requiredPermissions)
    if (!hasPermission) {
      next('/unauthorized')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
```

### Backend Module Structure

**Module Router** (`modules/patient_search/router.py`):
```python
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user, require_permission
from app.core.audit import audit_log
from .service import PatientSearchService
from .schemas import PatientSearchQuery, PatientSearchResponse

router = APIRouter(
    prefix="/api/v1/patient-search",
    tags=["patient-search"]
)

@router.post("/search", response_model=PatientSearchResponse)
async def search_patients(
    query: PatientSearchQuery,
    user = Depends(get_current_user),
    _permission = Depends(require_permission("patient:search")),
    service: PatientSearchService = Depends()
):
    """Search patients by medical concept."""
    # Audit log
    await audit_log(
        user_id=user.id,
        action="PATIENT_SEARCH",
        resource_type="patient",
        query=query.dict()
    )

    # Execute search
    results = await service.search(query)

    return results
```

**Module Service** (`modules/patient_search/service.py`):
```python
from typing import List
from app.clients.medcat_client import MedCATClient
from app.clients.elasticsearch_client import ElasticsearchClient
from .schemas import PatientSearchQuery, PatientSearchResponse, Patient

class PatientSearchService:
    def __init__(
        self,
        medcat_client: MedCATClient,
        es_client: ElasticsearchClient
    ):
        self.medcat = medcat_client
        self.es = es_client

    async def search(self, query: PatientSearchQuery) -> PatientSearchResponse:
        # 1. Get CUIs from MedCAT
        concepts = await self.medcat.get_concepts_for_term(query.concept)
        cuis = [c.cui for c in concepts]

        # 2. Search Elasticsearch
        es_query = self._build_es_query(cuis, query.filters)
        results = await self.es.search(index="patients", query=es_query)

        # 3. Format response
        patients = [Patient(**hit["_source"]) for hit in results["hits"]["hits"]]

        return PatientSearchResponse(
            results=patients,
            total_results=results["hits"]["total"]["value"]
        )

    def _build_es_query(self, cuis: List[str], filters):
        # Build Elasticsearch query with meta-annotation filters
        # ...
```

**Main App Integration** (`main.py`):
```python
from fastapi import FastAPI
from app.core.config import settings
from app.modules.patient_search.router import router as patient_search_router
from app.modules.timeline_view.router import router as timeline_router
from app.modules.clinical_decision_support.router import router as cds_router

app = FastAPI(title="Clinical Care Tools Platform")

# Include module routers
app.include_router(patient_search_router)
app.include_router(timeline_router)
app.include_router(cds_router)

# Core endpoints
@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}

# Module registry endpoint (for frontend)
@app.get("/api/v1/modules")
async def get_modules():
    return {
        "modules": [
            {"name": "patient-search", "enabled": True},
            {"name": "timeline-view", "enabled": True},
            {"name": "clinical-decision-support", "enabled": False}
        ]
    }
```

## Shared Infrastructure Design

### Authentication (OIDC/Keycloak)

**Frontend** (`core/auth.ts`):
```typescript
import Keycloak from 'keycloak-js'

const keycloak = new Keycloak({
  url: import.meta.env.VITE_OIDC_URL,
  realm: import.meta.env.VITE_OIDC_REALM,
  clientId: import.meta.env.VITE_OIDC_CLIENT_ID
})

export async function initAuth() {
  await keycloak.init({ onLoad: 'login-required' })

  // Auto-refresh token
  setInterval(() => {
    keycloak.updateToken(70)
  }, 10000)

  return keycloak
}

export function getUserPermissions(): string[] {
  const tokenParsed = keycloak.tokenParsed
  return tokenParsed?.resource_access?.['clinical-care-tools']?.roles || []
}

export function hasPermission(permission: string): boolean {
  return getUserPermissions().includes(permission)
}

export function hasAllPermissions(permissions: string[]): boolean {
  const userPermissions = getUserPermissions()
  return permissions.every(p => userPermissions.includes(p))
}

export { keycloak }
```

**Backend** (`core/auth.py`):
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.config import settings

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Validate JWT token and return user info."""
    token = credentials.credentials

    try:
        # Verify JWT (OIDC public key from Keycloak)
        payload = jwt.decode(
            token,
            settings.OIDC_PUBLIC_KEY,
            algorithms=["RS256"],
            audience=settings.OIDC_CLIENT_ID
        )

        return {
            "id": payload.get("sub"),
            "username": payload.get("preferred_username"),
            "email": payload.get("email"),
            "roles": payload.get("resource_access", {})
                .get("clinical-care-tools", {})
                .get("roles", [])
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def require_permission(permission: str):
    """Dependency to check user has specific permission."""
    async def permission_checker(user = Depends(get_current_user)):
        if permission not in user["roles"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
    return Depends(permission_checker)
```

### Audit Logging

**Shared Service** (`core/audit.py`):
```python
from datetime import datetime
from app.core.database import get_db
from sqlalchemy.orm import Session

async def audit_log(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str = None,
    query: dict = None,
    ip_address: str = None
):
    """Log audit event to database."""
    db: Session = next(get_db())

    audit_entry = AuditLog(
        timestamp=datetime.utcnow(),
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        query_params=query,
        ip_address=ip_address
    )

    db.add(audit_entry)
    db.commit()
```

**Database Schema**:
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    query_params JSONB,
    ip_address VARCHAR(45)
);

CREATE INDEX idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

## Module Communication Patterns

### Pattern 1: Event Bus (Frontend)

**Shared Event Bus** (`core/event-bus.ts`):
```typescript
import mitt, { type Emitter } from 'mitt'

type Events = {
  'patient:selected': { mrn: string }
  'concept:selected': { cui: string, name: string }
  'search:completed': { results: any[] }
}

export const eventBus: Emitter<Events> = mitt<Events>()
```

**Module A emits**:
```typescript
import { eventBus } from '@/core/event-bus'

function onPatientSelected(mrn: string) {
  eventBus.emit('patient:selected', { mrn })
}
```

**Module B listens**:
```typescript
import { eventBus } from '@/core/event-bus'
import { onMounted, onUnmounted } from 'vue'

onMounted(() => {
  eventBus.on('patient:selected', (data) => {
    loadPatientTimeline(data.mrn)
  })
})

onUnmounted(() => {
  eventBus.off('patient:selected')
})
```

### Pattern 2: Shared State (Pinia Store)

**Shared Store** (`core/stores/patient.ts`):
```typescript
import { defineStore } from 'pinia'

export const usePatientStore = defineStore('patient', {
  state: () => ({
    selectedMRN: null as string | null,
    patientCache: new Map()
  }),

  actions: {
    selectPatient(mrn: string) {
      this.selectedMRN = mrn
    },

    async loadPatient(mrn: string) {
      if (this.patientCache.has(mrn)) {
        return this.patientCache.get(mrn)
      }

      const patient = await api.get(`/api/v1/patients/${mrn}`)
      this.patientCache.set(mrn, patient)
      return patient
    }
  }
})
```

**Module Usage**:
```typescript
import { usePatientStore } from '@/core/stores/patient'

const patientStore = usePatientStore()

// Module A: Select patient
patientStore.selectPatient('MRN123')

// Module B: React to selection
watch(() => patientStore.selectedMRN, async (mrn) => {
  if (mrn) {
    const patient = await patientStore.loadPatient(mrn)
    // ...
  }
})
```

## Configuration Management

**Environment Variables** (`.env`):
```bash
# OIDC Authentication
VITE_OIDC_URL=http://keycloak:8080
VITE_OIDC_REALM=clinical-care-tools
VITE_OIDC_CLIENT_ID=clinical-care-tools-frontend

# Backend API
VITE_API_BASE_URL=http://localhost:8000/api/v1

# MedCAT Service
VITE_MEDCAT_SERVICE_URL=http://medcat-service:5555

# Elasticsearch
VITE_ELASTICSEARCH_URL=http://elasticsearch:9200

# Module Configuration
VITE_ENABLE_PATIENT_SEARCH=true
VITE_ENABLE_TIMELINE_VIEW=true
VITE_ENABLE_CDS=false
```

**Backend** (`core/config.py`):
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OIDC
    OIDC_URL: str
    OIDC_REALM: str
    OIDC_CLIENT_ID: str
    OIDC_PUBLIC_KEY: str

    # Database
    DATABASE_URL: str = "postgresql://user:pass@db:5432/clinical_care_tools"

    # MedCAT Service
    MEDCAT_SERVICE_URL: str = "http://medcat-service:5555"

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://elasticsearch:9200"

    # Module Config
    ENABLE_PATIENT_SEARCH: bool = True
    ENABLE_TIMELINE_VIEW: bool = True
    ENABLE_CDS: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

## Next Steps

After designing modular architecture:
1. **Create base app specification** using `prd-to-spec` skill
2. **Implement core infrastructure** (auth, audit, config, module loader)
3. **Implement first module** (patient search) following module pattern
4. **Test module independence** (disable module, app still works)
5. **Document module API** (for future module developers)
6. **Update CONTEXT.md** with architecture decisions (ADR)
