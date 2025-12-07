# Skill: Specification to Technical Plan Converter

**Purpose**: Convert Spec-Kit specifications into detailed technical plans for healthcare NLP applications

**Domain**: Software Architecture, Healthcare NLP, FastAPI, Vue 3, PostgreSQL, Docker

**When to Use**:
- After specification approval
- Before implementation begins
- When creating architecture documentation
- When planning MedCAT integration

**Skill Type**: Planning & Architecture

---

## Core Expertise

This skill guides you in converting `.specify/specifications/*.md` files into comprehensive technical plans (`.specify/plans/*.md`) following the Spec-Kit framework.

### Technical Plan Structure

A complete technical plan includes:

1. **Architecture Overview** - High-level system design
2. **Technology Stack** - Choices with rationale
3. **API Design** - OpenAPI specification for all endpoints
4. **Database Schema** - Complete DDL with migrations
5. **Component Design** - Frontend components and backend services
6. **Security Architecture** - Authentication, authorization, encryption, audit
7. **MedCAT Integration** - How NLP processing integrates
8. **Testing Strategy** - Unit, integration, E2E test plans
9. **Deployment Architecture** - Docker Compose setup
10. **Performance Requirements** - Benchmarks and optimization strategy
11. **Risks & Mitigations** - Technical risks with mitigation plans
12. **Implementation Phases** - Ordered implementation sequence

---

## 1. Architecture Overview

### System Context Diagram

Use ASCII art or Mermaid for diagrams:

```
┌─────────────────────────────────────────────────────────┐
│  Clinical Care Tools Base Application                   │
│                                                          │
│  ┌──────────────┐       ┌──────────────┐               │
│  │   Frontend   │──────▶│   Backend    │               │
│  │  (Vue 3 +    │◀──────│  (FastAPI)   │               │
│  │   Vuetify)   │       │              │               │
│  └──────────────┘       └──────┬───────┘               │
│                                 │                        │
│                         ┌───────▼────────┐              │
│                         │   PostgreSQL   │              │
│                         │   (Database)   │              │
│                         └────────────────┘              │
│                                                          │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │  MedCAT Service      │
        │  (External NLP API)  │
        └──────────────────────┘
```

### Component Responsibilities

**Frontend (Vue 3 + TypeScript + Vuetify)**:
- User interface for clinical workflows
- Authentication (login, session management)
- Form validation and UX
- API communication (Axios)
- State management (Pinia)

**Backend (FastAPI + Python 3.11)**:
- REST API endpoints (OpenAPI documented)
- Business logic and validation
- MedCAT integration client
- Authentication (JWT tokens)
- Authorization (RBAC)
- Audit logging
- Background jobs (async processing)

**Database (PostgreSQL 15)**:
- Relational data storage
- JSONB for flexible fields
- Full-text search (for concept search)
- Audit trail (immutable logs)
- Encryption at rest

**MedCAT Service**:
- NLP entity extraction
- Meta-annotation classification
- De-identification (optional)
- Concept linking (SNOMED-CT, UMLS)

---

## 2. Technology Stack

### Backend Technologies

| Technology | Version | Rationale |
|------------|---------|-----------|
| **Python** | 3.11+ | MedCAT compatibility, async support, type hints |
| **FastAPI** | 0.115+ | Async, OpenAPI auto-generation, Pydantic validation |
| **Pydantic** | 2.0+ | Schema validation, serialization, type safety |
| **SQLAlchemy** | 2.0+ | ORM for PostgreSQL, async support |
| **Alembic** | 1.13+ | Database migration management |
| **python-jose** | 3.3+ | JWT token generation/validation |
| **passlib** | 1.7+ | Password hashing (bcrypt) |
| **httpx** | 0.27+ | Async HTTP client for MedCAT Service |
| **pytest** | 8.0+ | Testing framework |
| **pytest-asyncio** | 0.23+ | Async test support |

### Frontend Technologies

| Technology | Version | Rationale |
|------------|---------|-----------|
| **Vue** | 3.5+ | Composition API, TypeScript support, reactive |
| **TypeScript** | 5.0+ | Type safety, IDE autocomplete, maintainability |
| **Vuetify** | 3.7+ | Material Design, healthcare UI patterns |
| **Pinia** | 2.0+ | State management, TypeScript support |
| **Axios** | 1.7+ | HTTP client, interceptors for auth |
| **Vue Router** | 4.0+ | SPA routing, navigation guards |
| **Vitest** | 2.0+ | Fast unit testing, Vite-native |
| **Playwright** | 1.45+ | E2E testing, cross-browser |

### Infrastructure Technologies

| Technology | Version | Rationale |
|------------|---------|-----------|
| **Docker** | 24.0+ | Container runtime |
| **Docker Compose** | 2.20+ | Multi-container orchestration |
| **PostgreSQL** | 15+ | JSONB support, full-text search, ACID compliance |
| **Nginx** | 1.25+ | Reverse proxy, TLS termination, static file serving |

### Alternatives Considered

**Why not Django REST Framework?**
- FastAPI: Faster (async), auto OpenAPI docs, Pydantic validation built-in
- Django: Heavier, sync-first, requires DRF for REST

**Why not MongoDB?**
- PostgreSQL: ACID compliance required for healthcare, JSONB for flexibility
- MongoDB: Lacks transactional guarantees, harder audit trail

**Why not React?**
- Vue 3: Existing MedCAT Trainer uses Vue, team familiarity, simpler reactivity
- React: Steeper learning curve, more boilerplate

---

## 3. API Design

### OpenAPI Specification Template

Create OpenAPI 3.1 spec for all endpoints:

```yaml
openapi: 3.1.0
info:
  title: Clinical Care Tools API
  version: 1.0.0
  description: REST API for clinical care workflows with MedCAT NLP

servers:
  - url: http://localhost:8000
    description: Development server

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        username:
          type: string
        email:
          type: string
          format: email
        role:
          type: string
          enum: [admin, clinician, researcher, annotator]
        created_at:
          type: string
          format: date-time

    Error:
      type: object
      properties:
        detail:
          type: string
        error_code:
          type: string

security:
  - bearerAuth: []

paths:
  /api/v1/auth/login:
    post:
      summary: User login
      security: []  # No auth required
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                username:
                  type: string
                password:
                  type: string
              required: [username, password]
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  token_type:
                    type: string
                    example: bearer
                  expires_at:
                    type: string
                    format: date-time
        '401':
          description: Invalid credentials
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
```

### Endpoint Naming Conventions

**RESTful patterns**:
- `GET /api/v1/users` - List users (paginated)
- `GET /api/v1/users/{user_id}` - Get user details
- `POST /api/v1/users` - Create user
- `PUT /api/v1/users/{user_id}` - Update user (full)
- `PATCH /api/v1/users/{user_id}` - Update user (partial)
- `DELETE /api/v1/users/{user_id}` - Soft delete user

**Action-based patterns** (when RESTful doesn't fit):
- `POST /api/v1/documents/{doc_id}/process` - Trigger MedCAT processing
- `POST /api/v1/auth/logout` - Logout (invalidate token)
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/patients/search` - Search patients (complex query in body)

### Response Pagination

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "pages": 8,
  "has_next": true,
  "has_previous": false
}
```

### Error Response Format

```json
{
  "detail": "User-friendly error message",
  "error_code": "ENTITY_NOT_FOUND",
  "field_errors": {
    "email": ["Invalid email format"]
  },
  "request_id": "abc123def456"
}
```

---

## 4. Database Schema Design

### Schema Design Principles

1. **UUID Primary Keys**: Future-proof, distributed-system ready
2. **Soft Deletes**: `is_active`, `deleted` flags (not hard deletes)
3. **Audit Fields**: `created_at`, `created_by`, `updated_at`, `updated_by` on ALL tables
4. **JSONB for Flexibility**: Configuration, metadata, dynamic fields
5. **Foreign Key Constraints**: Enforce referential integrity
6. **Indexes**: On foreign keys, commonly queried fields, UUIDs
7. **Check Constraints**: Enum validation, value ranges

### Complete DDL Example

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'clinician', 'researcher', 'annotator')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    can_break_glass BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT username_min_length CHECK (LENGTH(username) >= 3),
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 of JWT
    ip_address_hash VARCHAR(64) NOT NULL,     -- SHA-256 of IP
    user_agent_hash VARCHAR(64) NOT NULL,     -- SHA-256 of user-agent
    is_suspicious BOOLEAN NOT NULL DEFAULT FALSE,
    suspicious_change_count INT NOT NULL DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    force_logout BOOLEAN NOT NULL DEFAULT FALSE,
    force_logout_reason TEXT,
    force_logout_by UUID REFERENCES users(id)
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- Audit logs table (immutable)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    ip_address VARCHAR(45),  -- IPv6 support
    user_agent TEXT,
    details JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Prevent updates/deletes on audit logs
CREATE RULE no_update_audit_logs AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE no_delete_audit_logs AS ON DELETE TO audit_logs DO INSTEAD NOTHING;
```

### Migration Strategy (Alembic)

```python
# alembic/versions/001_create_users_table.py
"""Create users table

Revision ID: 001
Revises:
Create Date: 2025-11-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_break_glass', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("role IN ('admin', 'clinician', 'researcher', 'annotator')", name='users_role_check'),
        sa.CheckConstraint("LENGTH(username) >= 3", name='users_username_min_length'),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_role', 'users', ['role'])

def downgrade():
    op.drop_index('idx_users_role')
    op.drop_index('idx_users_username')
    op.drop_index('idx_users_email')
    op.drop_table('users')
```

---

## 5. Component Design

### Backend Service Layer Pattern

```python
# app/services/document_service.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Document, User
from app.clients.medcat_client import MedCATClient
from app.services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)

class DocumentService:
    """Business logic for document processing and PHI extraction"""

    def __init__(
        self,
        db: AsyncSession,
        medcat_client: MedCATClient,
        audit_service: AuditService
    ):
        self.db = db
        self.medcat = medcat_client
        self.audit = audit_service

    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        user: User
    ) -> Document:
        """Upload and encrypt document, trigger MedCAT processing"""

        # Encrypt document
        encrypted_content = await self._encrypt_aes256(file_content)
        content_hash = hashlib.sha256(file_content).hexdigest()

        # Check for duplicates
        existing = await self._find_by_hash(content_hash)
        if existing:
            logger.warning(f"Duplicate document detected: {content_hash}")
            return existing

        # Create document record
        document = Document(
            filename=filename,
            content=encrypted_content,
            content_hash=content_hash,
            file_size=len(file_content),
            uploaded_by=user.id,
            medcat_status='pending'
        )
        self.db.add(document)
        await self.db.commit()

        # Audit log
        await self.audit.log(
            user_id=user.id,
            action='DOCUMENT_UPLOAD',
            resource_type='document',
            resource_id=str(document.id),
            details={'filename': filename, 'size': len(file_content)}
        )

        # Trigger async MedCAT processing (background task)
        await self._trigger_medcat_processing(document.id)

        return document

    async def _trigger_medcat_processing(self, document_id: str):
        """Queue document for MedCAT processing (async background job)"""
        # Use Celery, FastAPI BackgroundTasks, or similar
        pass
```

### Frontend Component Pattern (Vue 3 Composition API)

```vue
<!-- components/DocumentUpload.vue -->
<template>
  <v-card>
    <v-card-title>Upload Clinical Document</v-card-title>
    <v-card-text>
      <v-file-input
        v-model="file"
        label="Select RTF file"
        accept=".rtf"
        :rules="fileRules"
        @change="onFileSelected"
      />

      <v-alert v-if="error" type="error" dismissible>
        {{ error }}
      </v-alert>

      <v-progress-linear v-if="uploading" indeterminate color="primary" />
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn
        @click="uploadDocument"
        :disabled="!file || uploading"
        color="primary"
      >
        Upload
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDocumentStore } from '@/stores/document'
import type { VFileInput } from 'vuetify/components'

const documentStore = useDocumentStore()

const file = ref<File | null>(null)
const uploading = ref(false)
const error = ref<string | null>(null)

const fileRules = [
  (v: File | null) => !!v || 'File is required',
  (v: File | null) => !v || v.size < 1024 * 1024 || 'File must be less than 1MB',
  (v: File | null) => !v || v.name.endsWith('.rtf') || 'Only RTF files allowed'
]

const onFileSelected = (event: Event) => {
  error.value = null
}

const uploadDocument = async () => {
  if (!file.value) return

  uploading.value = true
  error.value = null

  try {
    await documentStore.uploadDocument(file.value)
    file.value = null
    // Success feedback
  } catch (err: any) {
    error.value = err.message || 'Upload failed'
  } finally {
    uploading.value = false
  }
}
</script>
```

---

## 6. Security Architecture

### Authentication Flow (JWT)

```
1. User submits credentials (username + password)
   ↓
2. Backend validates credentials (bcrypt verify)
   ↓
3. Backend creates JWT token (HS256, 8-hour expiry)
   ↓
4. Backend creates session record (token hash, IP hash, user-agent hash)
   ↓
5. Backend returns token to frontend
   ↓
6. Frontend stores token (sessionStorage, not localStorage)
   ↓
7. Frontend includes token in Authorization header (all requests)
   ↓
8. Backend validates token on each request:
   - Verify signature
   - Check expiry
   - Check session exists and not force_logout
   - Validate IP/user-agent binding (session hijack detection)
   - Update last_activity timestamp
   ↓
9. If token expired → 401 Unauthorized → Frontend redirects to login
```

### JWT Token Structure

```python
# app/security/jwt.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # 256-bit random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

def create_access_token(user_id: str, role: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    payload = {
        "sub": user_id,  # Subject (user ID)
        "role": role,
        "exp": expire,   # Expiration
        "iat": datetime.utcnow(),  # Issued at
        "jti": str(uuid.uuid4())   # JWT ID (unique token ID)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def verify_token(token: str, db: AsyncSession) -> Optional[User]:
    """Verify JWT and return user if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if not user_id:
            return None

        # Check session exists and not force_logout
        session = await db.execute(
            select(Session).where(
                Session.token_hash == hashlib.sha256(token.encode()).hexdigest(),
                Session.force_logout == False
            )
        )
        if not session.scalar_one_or_none():
            return None

        # Get user
        user = await db.get(User, user_id)
        return user if user and user.is_active else None

    except JWTError:
        return None
```

### Authorization (RBAC)

```python
# app/security/permissions.py
from enum import Enum
from functools import wraps
from fastapi import HTTPException, Depends

class Role(str, Enum):
    ADMIN = 'admin'
    CLINICIAN = 'clinician'
    RESEARCHER = 'researcher'
    ANNOTATOR = 'annotator'

class Permission(str, Enum):
    # User management
    USER_CREATE = 'user:create'
    USER_READ = 'user:read'
    USER_UPDATE = 'user:update'
    USER_DELETE = 'user:delete'

    # Document management
    DOCUMENT_UPLOAD = 'document:upload'
    DOCUMENT_READ = 'document:read'
    DOCUMENT_DELETE = 'document:delete'

    # Patient data
    PATIENT_SEARCH = 'patient:search'
    PATIENT_VIEW = 'patient:view'
    PATIENT_EXPORT = 'patient:export'

    # Admin
    AUDIT_VIEW = 'audit:view'
    SYSTEM_CONFIG = 'system:config'

# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_READ, Permission.DOCUMENT_DELETE,
        Permission.PATIENT_SEARCH, Permission.PATIENT_VIEW, Permission.PATIENT_EXPORT,
        Permission.AUDIT_VIEW, Permission.SYSTEM_CONFIG
    ],
    Role.CLINICIAN: [
        Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_READ,
        Permission.PATIENT_SEARCH, Permission.PATIENT_VIEW
    ],
    Role.RESEARCHER: [
        Permission.PATIENT_SEARCH, Permission.PATIENT_EXPORT
    ],
    Role.ANNOTATOR: [
        Permission.DOCUMENT_READ
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
@router.post("/api/v1/documents")
@require_permission(Permission.DOCUMENT_UPLOAD)
async def upload_document(file: UploadFile, user: User = Depends(get_current_user)):
    pass
```

### Encryption (AES-256)

```python
# app/security/encryption.py
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

# Load encryption key from environment (32 bytes for AES-256)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY").encode()  # Must be 32 bytes

def encrypt_aes256(plaintext: bytes) -> bytes:
    """Encrypt data with AES-256-CBC"""
    iv = os.urandom(16)  # Initialization vector
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad plaintext to 16-byte blocks
    padding_length = 16 - (len(plaintext) % 16)
    padded_plaintext = plaintext + bytes([padding_length] * padding_length)

    ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

    # Return IV + ciphertext (IV needed for decryption)
    return iv + ciphertext

def decrypt_aes256(ciphertext: bytes) -> bytes:
    """Decrypt AES-256-CBC encrypted data"""
    iv = ciphertext[:16]
    actual_ciphertext = ciphertext[16:]

    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    padded_plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()

    # Remove padding
    padding_length = padded_plaintext[-1]
    plaintext = padded_plaintext[:-padding_length]

    return plaintext
```

---

## 7. MedCAT Integration

### MedCAT Client Pattern

```python
# app/clients/medcat_client.py
import httpx
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class MedCATClient:
    """Async client for MedCAT Service REST API"""

    def __init__(self, base_url: str, timeout: int = 300):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def process_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Process text with MedCAT and return entities

        Returns:
            List of entities with structure:
            {
                "cui": "C0004238",
                "pretty_name": "Atrial Flutter",
                "start": 45,
                "end": 60,
                "type": "SNOMED-CT",
                "meta_anns": {
                    "Negation": "Affirmed",
                    "Experiencer": "Patient",
                    "Temporality": "Current",
                    "Certainty": "Definite"
                }
            }
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/process",
                json={"text": text}
            )
            response.raise_for_status()

            result = response.json()
            return result.get("entities", [])

        except httpx.HTTPError as e:
            logger.error(f"MedCAT API error: {e}")
            raise Exception(f"MedCAT processing failed: {e}")

    async def classify_entity_type(self, entity: Dict[str, Any]) -> str:
        """
        Classify entity as PHI or clinical concept

        Returns: 'phi_name', 'phi_nhs_number', 'phi_address', 'phi_dob', 'clinical'
        """
        cui = entity.get("cui", "")
        pretty_name = entity.get("pretty_name", "").lower()

        # Simple heuristic-based classification
        # In production, use trained classifier or CUI lookup

        if any(word in pretty_name for word in ["name", "surname", "forename"]):
            return "phi_name"
        elif "nhs number" in pretty_name or cui == "C1547728":
            return "phi_nhs_number"
        elif any(word in pretty_name for word in ["address", "postcode", "zip"]):
            return "phi_address"
        elif any(word in pretty_name for word in ["date of birth", "dob", "birthdate"]):
            return "phi_dob"
        else:
            return "clinical"
```

---

## 8. Testing Strategy

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

### Unit Test Example (pytest)

```python
# tests/unit/services/test_document_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.document_service import DocumentService
from app.models import User, Document

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def mock_medcat():
    client = Mock()
    client.process_text = AsyncMock(return_value=[
        {"cui": "C0004238", "pretty_name": "Atrial Flutter"}
    ])
    return client

@pytest.fixture
def mock_audit():
    audit = Mock()
    audit.log = AsyncMock()
    return audit

@pytest.fixture
def document_service(mock_db, mock_medcat, mock_audit):
    return DocumentService(mock_db, mock_medcat, mock_audit)

@pytest.mark.asyncio
async def test_upload_document_creates_record(document_service, mock_db):
    """Test document upload creates database record"""
    # Arrange
    user = User(id="user-123", username="clinician1", role="clinician")
    file_content = b"Patient has atrial flutter."
    filename = "letter.rtf"

    # Act
    document = await document_service.upload_document(file_content, filename, user)

    # Assert
    assert document.filename == filename
    assert document.uploaded_by == user.id
    assert document.medcat_status == "pending"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_upload_document_detects_duplicates(document_service):
    """Test duplicate document detection via SHA-256 hash"""
    # Arrange
    user = User(id="user-123", username="clinician1", role="clinician")
    file_content = b"Patient has atrial flutter."

    # Mock existing document with same hash
    document_service._find_by_hash = AsyncMock(return_value=Document(id="doc-123"))

    # Act
    document = await document_service.upload_document(file_content, "letter.rtf", user)

    # Assert
    assert document.id == "doc-123"  # Returns existing document
```

### Integration Test Example

```python
# tests/integration/test_document_api.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.database import get_db

@pytest.mark.asyncio
async def test_upload_document_endpoint(async_client: AsyncClient, auth_headers):
    """Test document upload API endpoint"""
    # Arrange
    file_content = b"Patient has atrial flutter."
    files = {"file": ("letter.rtf", file_content, "application/rtf")}

    # Act
    response = await async_client.post(
        "/api/v1/documents",
        files=files,
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "letter.rtf"
    assert data["medcat_status"] == "pending"
    assert "id" in data

@pytest.mark.asyncio
async def test_upload_document_requires_auth(async_client: AsyncClient):
    """Test document upload requires authentication"""
    # Arrange
    files = {"file": ("letter.rtf", b"content", "application/rtf")}

    # Act
    response = await async_client.post("/api/v1/documents", files=files)

    # Assert
    assert response.status_code == 401
```

### E2E Test Example (Playwright)

```typescript
// tests/e2e/document-upload.spec.ts
import { test, expect } from '@playwright/test'

test('clinician can upload and view document', async ({ page }) => {
  // Login
  await page.goto('http://localhost:8080/login')
  await page.fill('input[name="username"]', 'clinician1')
  await page.fill('input[name="password"]', 'password123')
  await page.click('button[type="submit"]')

  // Wait for redirect to dashboard
  await expect(page).toHaveURL('http://localhost:8080/dashboard')

  // Navigate to document upload
  await page.click('text=Upload Document')

  // Upload file
  const fileInput = await page.locator('input[type="file"]')
  await fileInput.setInputFiles('tests/fixtures/test-letter.rtf')
  await page.click('button:has-text("Upload")')

  // Verify success message
  await expect(page.locator('.v-alert--type-success')).toContainText('Document uploaded successfully')

  // Verify document appears in list
  await page.goto('http://localhost:8080/documents')
  await expect(page.locator('text=test-letter.rtf')).toBeVisible()
})
```

---

## 9. Deployment Architecture

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: clinical_care_tools
      POSTGRES_USER: clinicaltools
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U clinicaltools"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://clinicaltools:${DB_PASSWORD}@postgres:5432/clinical_care_tools
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      MEDCAT_SERVICE_URL: ${MEDCAT_SERVICE_URL}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  medcat_models:  # Shared MedCAT models volume
```

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run database migrations on startup
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json .
RUN npm ci

# Copy application code
COPY . .

# Build for production
RUN npm run build

# Serve with nginx
FROM nginx:1.25-alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 10. Performance Requirements

### Response Time Targets

| Endpoint | Target | Max Acceptable |
|----------|--------|----------------|
| User login | <200ms | 500ms |
| Patient search | <500ms | 1000ms |
| Document upload | <1s | 3s |
| MedCAT processing | <30s | 60s |
| Timeline view | <800ms | 1500ms |

### Optimization Strategies

**Database**:
- Connection pooling (SQLAlchemy async pool, min=5, max=20)
- Query optimization (eager loading, select only needed columns)
- Indexes on foreign keys and frequently queried fields
- JSONB GIN indexes for concept search

**API**:
- Response compression (gzip)
- Pagination (limit large result sets to 20-50 items)
- Caching (Redis for frequently accessed data)
- Async I/O (FastAPI async endpoints, httpx async client)

**Frontend**:
- Lazy loading (components, routes)
- Virtual scrolling (long lists)
- Debounced search inputs (300ms delay)
- Image optimization (WebP, lazy loading)

---

## 11. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| MedCAT Service downtime | High | Medium | Retry logic, circuit breaker, offline mode |
| Database migration failure | High | Low | Backup before migration, rollback scripts, test in staging |
| JWT secret leak | Critical | Low | Rotate keys, use environment variables, never commit secrets |
| Session hijacking | High | Medium | IP/user-agent binding, suspicious activity detection |
| Slow MedCAT processing | Medium | High | Background jobs, progress tracking, user feedback |
| Document storage overflow | Medium | Medium | Retention policy, automated purging, compression |

---

## 12. Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- Docker Compose setup
- PostgreSQL database + migrations
- JWT authentication
- Audit logging
- User management API

### Phase 2: Document Management (Week 3)
- Document upload endpoint
- AES-256 encryption
- MedCAT client integration
- Background job processing

### Phase 3: PHI Extraction (Week 4)
- Entity extraction workflow
- Patient aggregation logic
- NHS number matching

### Phase 4: First Module - Patient Search (Week 5-6)
- Search API with meta-annotation filters
- Frontend search interface
- Results display with confidence scores

### Phase 5: Testing & Hardening (Week 7-8)
- Unit test coverage >80%
- Integration tests for critical paths
- E2E tests for user journeys
- Security audit
- Performance testing

---

## Usage

When creating a technical plan:

1. **Read the specification completely**
2. **Extract requirements** (functional + non-functional)
3. **Design architecture** (components, data flows)
4. **Define API contracts** (OpenAPI spec)
5. **Design database schema** (DDL + migrations)
6. **Plan security** (auth, authz, encryption, audit)
7. **Plan testing** (unit, integration, E2E strategies)
8. **Define deployment** (Docker Compose, environment config)
9. **Identify risks** (technical, timeline, security)
10. **Create implementation phases** (ordered by dependency)

**Output**: Save to `.specify/plans/{feature-name}-plan.md`

**Review**: Get user approval before proceeding to task breakdown
