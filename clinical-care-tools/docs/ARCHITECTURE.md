# System Architecture

Complete overview of the Clinical Care Tools system design, component interactions, and data flows.

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Component Overview](#component-overview)
3. [Data Flows](#data-flows)
4. [Technology Stack](#technology-stack)
5. [Deployment Architecture](#deployment-architecture)
6. [Scalability Considerations](#scalability-considerations)
7. [Integration Points](#integration-points)

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER (Port 8080)                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │             Vue 3 Web Application (Vuetify)                  │  │
│  │  • Patient Search UI    • Document Upload UI                 │  │
│  │  • Timeline Visualization • Data Export                      │  │
│  │  • User Management      • Audit Log Viewer                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS/REST
┌──────────────────────────────▼──────────────────────────────────────┐
│                    API GATEWAY & ORCHESTRATION                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              FastAPI Application (Port 8000)                 │  │
│  │  • Authentication (JWT) • Authorization (RBAC)              │  │
│  │  • API Routing          • Request Validation                │  │
│  │  • Business Logic       • Error Handling                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────┬─────────────────┬──────────────────┬──────────────────────────┘
       │                 │                  │
       │                 │                  │
       ▼                 ▼                  ▼
┌────────────┐   ┌──────────────┐   ┌─────────────────┐
│ PostgreSQL │   │    Redis     │   │  MedCAT Service │
│   (5432)   │   │   (6379)     │   │    (Port 8001)  │
│            │   │              │   │                 │
│ • Patient  │   │ • Sessions   │   │ • NLP Engine    │
│   Records  │   │ • Cache      │   │ • Extractors    │
│ • Docs     │   │ • Jobs       │   │ • Models        │
│ • Audit    │   │              │   │ • Scoring       │
│   Logs     │   │              │   │                 │
└────────────┘   └──────────────┘   └─────────────────┘
```

### Architecture Principles

1. **Layered Architecture**
   - Separation of concerns (presentation, business, data)
   - Clear dependencies between layers
   - Testability at each layer

2. **Microservices-Ready**
   - NLP service is independent
   - Can scale independently
   - Clear API boundaries

3. **Security-First**
   - Encryption in transit (TLS)
   - Encryption at rest
   - Audit logging throughout

4. **Cloud-Native**
   - Container-based (Docker)
   - Stateless API servers
   - External state (PostgreSQL, Redis)

## Component Overview

### Frontend Layer

**Vue 3 Web Application**
- Framework: Vue 3 with Composition API
- UI Components: Vuetify (Material Design)
- State Management: Pinia
- HTTP Client: Axios with interceptors
- Build Tool: Vite

**Key Modules**:
```
frontend/src/
├── components/     # Reusable UI components
├── views/          # Page components
├── composables/    # Composition API logic
├── stores/         # Pinia state management
├── services/       # API clients
├── types/          # TypeScript interfaces
├── styles/         # Global styling
└── utils/          # Helper functions
```

**Responsibilities**:
- User authentication (login/logout)
- Patient search interface
- Document upload and visualization
- Timeline view and interactions
- Data export (CSV, FHIR)
- User profile and settings

### Backend API Layer

**FastAPI Application** (Python 3.9+)
- Framework: FastAPI with async support
- API Documentation: OpenAPI/Swagger
- Validation: Pydantic models
- Database ORM: SQLAlchemy
- Authentication: JWT tokens

**Key Modules**:
```
backend/app/
├── api/            # API route definitions
├── models/         # SQLAlchemy database models
├── schemas/        # Pydantic request/response models
├── services/       # Business logic
├── dependencies/   # Dependency injection
├── utils/          # Helper functions
├── middleware/     # Request/response middleware
└── config/         # Application configuration
```

**Responsibilities**:
- REST API endpoints
- Authentication and authorization
- Patient data management
- Document processing orchestration
- Entity extraction coordination
- Audit logging
- Cache management
- Error handling

### Data Layer

**PostgreSQL Database**
- Relational database for structured data
- ACID compliance for data integrity
- Full-text search capabilities
- JSON support for flexible fields

**Primary Tables**:
```
users
├── id (UUID)
├── username (unique)
├── password_hash
├── role (admin, clinician, researcher)
├── created_at, updated_at
└── is_active

patients
├── id (UUID)
├── mrn (medical record number)
├── first_name, last_name
├── dob (date of birth)
├── gender
├── created_at
└── metadata (JSON)

documents
├── id (UUID)
├── patient_id (FK)
├── filename
├── content (RTF/PDF stored as BYTEA)
├── uploaded_by (FK to users)
├── uploaded_at
├── document_type
└── metadata (JSON)

entities
├── id (UUID)
├── document_id (FK)
├── cui (SNOMED code)
├── name (concept name)
├── confidence_score (0-1)
├── char_span_start, char_span_end
├── meta_annotations (JSON)
└── created_at

audit_logs
├── id (bigint)
├── user_id (FK)
├── action (VIEW, EXPORT, CREATE, etc)
├── resource_type (patient, document, etc)
├── resource_id
├── ip_address
├── timestamp
└── details (JSON)
```

**Responsibilities**:
- Persistent data storage
- Patient records and demographics
- Clinical document storage
- Extracted medical entities
- User and audit information
- System configuration

### Cache Layer

**Redis**
- In-memory data structure store
- Session management
- Query result caching
- Job queue for async tasks

**Usage**:
```
sessions:{session_id}       # User sessions (TTL: 8 hours)
cache:patient:{patient_id}  # Patient data cache (TTL: 1 hour)
cache:entities:{doc_id}     # Extracted entities cache
jobs:pending                # Job queue for NLP extraction
rate_limit:{user_id}        # Rate limiting
```

**Responsibilities**:
- Session storage and validation
- Hot data caching
- Async job queue management
- Rate limiting enforcement
- Real-time notifications

### NLP Service

**MedCAT Service** (CogStack)
- REST API for medical NLP
- Concept extraction from text
- Meta-annotation extraction
- Confidence scoring
- Language support: English (extensible)

**Models**:
- Medical vocabulary (SNOMED-CT, UMLS)
- Concept annotations (pre-trained)
- Meta-annotation models

**API Endpoints**:
```
POST /api/extract
{
  "text": "clinical text",
  "model": "medcat-model"
}
→ Returns: entities, meta-annotations, scores

GET /api/health
→ Returns: service status, model info

GET /api/models
→ Returns: available models
```

**Responsibilities**:
- Medical concept extraction
- Meta-annotation prediction
- Confidence scoring
- Text processing and normalization

## Data Flows

### Authentication Flow

```
1. User submits login form
   ├─ POST /api/auth/login (username, password)

2. Backend validates credentials
   ├─ Hash password and compare with database
   ├─ Load user roles and permissions

3. Issue JWT token
   ├─ Create JWT with user claims
   ├─ Store session in Redis (for revocation)
   ├─ Return access + refresh tokens

4. Subsequent requests include JWT
   ├─ Authorization: Bearer {token}
   ├─ Validate token signature and expiry
   ├─ Extract user claims from token

5. Automatic refresh on expiry
   ├─ POST /api/auth/refresh (refresh_token)
   ├─ Issue new access token
```

### Patient Search Flow

```
1. User enters search criteria
   ├─ Frontend: POST /api/patients/search
   ├─ Criteria: medical concept, filters, limit

2. Backend processes search
   ├─ Validate user permissions
   ├─ Check Redis cache
   ├─ If cached: return cached results

3. Query database if not cached
   ├─ Build SQL query with filters
   ├─ Join with entities table
   ├─ Apply meta-annotation filters
   ├─ Limit results

4. Return paginated results
   ├─ Include confidence scores
   ├─ Include patient summaries
   ├─ Cache results in Redis (1 hour)
   ├─ Log search action to audit_logs

5. Frontend displays results
   ├─ Render patient list with scores
   ├─ Allow drill-down to documents
```

### Document Upload Flow

```
1. User selects document to upload
   ├─ Frontend: Validate file (RTF/PDF/TXT)
   ├─ Show progress bar

2. Upload document to backend
   ├─ POST /api/documents/upload
   ├─ Multipart form with file and patient_id
   ├─ Validate user permissions (can upload for this patient)
   ├─ Store document in PostgreSQL (BYTEA)

3. Queue NLP extraction job
   ├─ Create document record in database
   ├─ Queue async task in Redis
   ├─ Return document_id to frontend

4. Backend extracts entities (async)
   ├─ Read document from database
   ├─ Convert to plain text (PDF/RTF handling)
   ├─ Call MedCAT service: /api/extract
   ├─ Receive entities + meta-annotations + scores

5. Store extracted entities
   ├─ Save entities to database
   ├─ Store in Redis cache
   ├─ Create audit log entry
   ├─ Notify frontend (WebSocket or polling)

6. Frontend shows results
   ├─ Display extracted entities
   ├─ Show confidence scores
   ├─ Allow concept filtering
```

### Entity Extraction Pipeline

```
Document Text
    ↓
┌─────────────────────────────────────┐
│   MedCAT Service                    │
│  ┌──────────────────────────────┐  │
│  │ 1. Text Preprocessing        │  │
│  │    - Normalize whitespace    │  │
│  │    - Remove artifacts        │  │
│  └──────────────────────────────┘  │
│             ↓                       │
│  ┌──────────────────────────────┐  │
│  │ 2. Concept Extraction        │  │
│  │    - Dictionary matching     │  │
│  │    - Fuzzy matching          │  │
│  │    - Return CUI + name       │  │
│  └──────────────────────────────┘  │
│             ↓                       │
│  ┌──────────────────────────────┐  │
│  │ 3. Meta-Annotation Models    │  │
│  │    - Negation detection      │  │
│  │    - Temporality (past/recent/current) │
│  │    - Experiencer (patient/family/other) │
│  │    - Certainty (definite/probable) │  │
│  └──────────────────────────────┘  │
│             ↓                       │
│  ┌──────────────────────────────┐  │
│  │ 4. Confidence Scoring        │  │
│  │    - Model confidence (0-1)  │  │
│  │    - Contextual adjustments  │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
    ↓
Entities + Meta-Annotations + Scores
    ↓
Backend stores in PostgreSQL + Redis
    ↓
Frontend visualizes results
```

## Technology Stack

### Frontend
- **Framework**: Vue 3
- **Language**: TypeScript
- **UI Library**: Vuetify 3 (Material Design)
- **State Management**: Pinia
- **HTTP Client**: Axios
- **Build Tool**: Vite
- **Testing**: Vitest, Playwright
- **Code Quality**: ESLint, Prettier

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.9+
- **Database ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Authentication**: PyJWT
- **Database Driver**: psycopg2-binary
- **Cache**: Redis-py
- **Testing**: pytest, pytest-cov
- **Logging**: Python logging with structlog
- **API Documentation**: OpenAPI/Swagger

### Data Layer
- **Primary Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Search** (Optional): Elasticsearch 8 (for advanced search)
- **Queue**: Redis Streams or Celery (for async jobs)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Container Registry**: Docker Hub / GitHub Container Registry
- **Orchestration** (Prod): Kubernetes (optional)
- **Reverse Proxy**: Nginx (production)
- **Monitoring**: Prometheus + Grafana (optional)

### NLP
- **Library**: MedCAT (Medical Concept Annotation Tool)
- **Service**: CogStack MedCAT Service
- **Models**: SNOMED-CT, UMLS vocabulary

## Deployment Architecture

### Development Environment

```
Local Machine
├── Docker Engine
│   ├── PostgreSQL Container
│   ├── Redis Container
│   ├── MedCAT Service Container
│   ├── FastAPI Backend Container
│   └── Vue 3 Frontend Container
├── IDE/Editor
├── Git
└── Docker Compose CLI
```

### Production Environment

```
Production Server(s)
├── Docker Runtime
│   ├── Docker Compose OR Kubernetes
│   │   ├── PostgreSQL (with backups)
│   │   ├── Redis (with replication)
│   │   ├── MedCAT Service (scaled horizontally)
│   │   ├── FastAPI (multiple replicas, load balanced)
│   │   └── Nginx (reverse proxy)
│   └── Monitoring Stack (optional)
│       ├── Prometheus
│       └── Grafana
├── SSL/TLS Certificates
├── Backup Storage (off-site)
├── Log Aggregation (optional)
└── Monitoring & Alerting
```

### Scaling Architecture

```
Load Balancer
    │
    ├─ FastAPI Instance 1
    ├─ FastAPI Instance 2
    ├─ FastAPI Instance 3
    └─ FastAPI Instance N

    All instances share:
    ├─ PostgreSQL (with connection pooling)
    ├─ Redis (shared cache)
    └─ MedCAT Service(s)
```

## Scalability Considerations

### Horizontal Scaling

**Stateless API Servers**:
- Multiple FastAPI instances behind load balancer
- Session state in Redis (shared across instances)
- No local file storage

**Benefits**:
- Handle increased traffic
- Zero-downtime deployments
- Geographic distribution

**Configuration**:
```yaml
# docker-compose.yml with scaling
services:
  backend:
    deploy:
      replicas: 3  # Scale horizontally
    # Each instance shares PostgreSQL, Redis, MedCAT
```

### Vertical Scaling

**Increasing Single Instance Resources**:
- More CPU cores → Better parallelization
- More RAM → Larger caches
- Faster storage → Better database performance

**Resource Recommendations**:
- Small (dev): 4 CPU, 8GB RAM
- Medium (10 concurrent users): 8 CPU, 16GB RAM
- Large (50+ concurrent users): 16 CPU, 32GB RAM

### Database Optimization

**Indexing Strategy**:
```sql
-- Patient search optimization
CREATE INDEX idx_patient_mrn ON patients(mrn);
CREATE INDEX idx_entities_cui ON entities(cui);
CREATE INDEX idx_entities_confidence ON entities(confidence_score);

-- Audit log efficiency
CREATE INDEX idx_audit_user_date ON audit_logs(user_id, timestamp);

-- Foreign key optimization
CREATE INDEX idx_entities_doc_id ON entities(document_id);
```

**Query Optimization**:
- Connection pooling (20-30 connections)
- Query result caching in Redis
- Pagination for large result sets
- Async query processing

### Cache Strategy

**What to Cache**:
- Patient search results (1 hour TTL)
- User permissions (2 hour TTL)
- System configuration (24 hour TTL)
- NLP model responses (30 minute TTL)

**Cache Invalidation**:
- Time-based (TTL)
- Event-based (on updates)
- Manual (admin operations)

### NLP Service Scaling

**Single Instance** (sufficient for most):
- Handles ~100 extraction requests/second
- Process batch operations
- Memory: 2-4GB

**Multiple Instances**:
- Load balance across instances
- Shared model storage
- Independent processing

## Integration Points

### External Systems

**Electronic Health Records (EHR)**:
- FHIR R4 API integration
- CDS Hooks for clinical decision support
- Patient data synchronization

**Data Warehouse**:
- Extract aggregated clinical data
- Push cohort definitions
- Receive lab result feeds

**Authentication Service** (Optional):
- LDAP/Active Directory
- SAML SSO
- OAuth2 integration

### APIs Exposed

**Public APIs**:
```
GET /api/health              # Service health
POST /api/auth/login         # User authentication
GET /api/patients            # Patient search
POST /api/documents/upload   # Document upload
GET /api/documents/{id}      # Retrieve document
POST /api/export             # Data export
```

**Internal APIs** (Backend only):
```
MedCAT Service:
  POST /api/extract         # Extract entities
  GET /api/health           # Service status
  GET /api/models           # Available models
```

**Webhook Integrations** (Optional):
- Document processing status
- Entity extraction completion
- Audit log streaming

## Performance Characteristics

### Expected Response Times

| Operation | Time | Throughput |
|-----------|------|-----------|
| Patient search | <500ms | 100 req/s |
| Document upload (5MB) | <2s | 20 docs/s |
| Entity extraction (page) | <100ms | 500 pages/s |
| Timeline render | <200ms | 100 patients/s |
| Login | <200ms | 50 req/s |

### Resource Usage

| Component | Typical Usage |
|-----------|---------------|
| PostgreSQL | 100-500 connections |
| Redis | 500MB-2GB |
| MedCAT Service | 2-4GB RAM |
| FastAPI | 1-2GB per instance |
| Frontend | 200-500MB client-side |

## Security Architecture

### Network Security

```
Client
  ↓ HTTPS/TLS 1.3
Frontend (Port 8080)
  ↓ Internal Network (Docker Bridge)
FastAPI (Port 8000)
  ↓ Internal Network
PostgreSQL (Port 5432) - Not exposed
Redis (Port 6379) - Not exposed
MedCAT Service (Port 8001) - Not exposed
```

### Data Protection

- **In Transit**: TLS 1.3 encryption
- **At Rest**: AES-256 for sensitive data
- **In Memory**: Secure token handling

### Access Control

- **Authentication**: JWT tokens
- **Authorization**: Role-Based Access Control (RBAC)
- **API Keys**: For service-to-service communication

## Monitoring & Observability

### Metrics to Track

- API response times (p50, p95, p99)
- Database connection pool usage
- Cache hit rates
- NLP service latency
- Error rates by endpoint
- User activity metrics

### Logging Strategy

- Application logs (JSON format)
- Audit logs (all PHI access)
- Infrastructure logs (Docker, services)
- Query logs (slow queries)

### Health Checks

```bash
# Service health endpoints
GET /api/health

# Database connection
SELECT 1;

# Redis connectivity
PING

# NLP service availability
GET /api/health
```

---

**Last Updated**: 2025-01-08
**Version**: 1.0.0
