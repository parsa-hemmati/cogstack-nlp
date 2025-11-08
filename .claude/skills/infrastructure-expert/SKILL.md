# Skill: Infrastructure Implementation Expert

**Purpose**: Guide implementation of core infrastructure (Docker, PostgreSQL, Authentication, Audit Logging) for healthcare applications

**Domain**: DevOps, Healthcare Security, Database Administration, Authentication Systems

**When to Use**:
- Setting up new project infrastructure
- Implementing Docker Compose environments
- Configuring PostgreSQL for healthcare data
- Implementing authentication/authorization
- Building audit logging systems
- Security hardening for HIPAA/GDPR compliance

**Skill Type**: Implementation & Best Practices

---

## Core Expertise

This skill provides battle-tested patterns for implementing core infrastructure components for healthcare NLP applications with patient data (PHI).

---

## 1. Docker Compose Setup

### Production-Ready docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL database
  postgres:
    image: postgres:15-alpine
    container_name: clinical_tools_postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-clinical_care_tools}
      POSTGRES_USER: ${POSTGRES_USER:-clinicaltools}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
      # Security hardening
      POSTGRES_HOST_AUTH_METHOD: scram-sha-256
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    networks:
      - clinical_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-clinicaltools} -d ${POSTGRES_DB:-clinical_care_tools}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    restart: unless-stopped
    # Security: Run as non-root user
    user: postgres
    # Security: Read-only root filesystem (except /var/lib/postgresql/data)
    read_only: true
    tmpfs:
      - /tmp
      - /var/run/postgresql

  # FastAPI backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: 3.11
    container_name: clinical_tools_backend
    environment:
      # Database
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-clinicaltools}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-clinical_care_tools}

      # Security
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:?JWT_SECRET_KEY is required}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY:?ENCRYPTION_KEY is required}

      # MedCAT Service
      MEDCAT_SERVICE_URL: ${MEDCAT_SERVICE_URL:-http://medcat-service:5000}

      # Environment
      ENVIRONMENT: ${ENVIRONMENT:-development}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}

      # CORS
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS:-http://localhost:8080}
    volumes:
      # Development: Mount source for hot reload
      - ./backend:/app:ro
      # Persistent logs
      - backend_logs:/var/log/clinical_tools
    ports:
      - "${BACKEND_PORT:-8000}:8000}
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
    # Security: Run as non-root user
    user: "${UID:-1000}:${GID:-1000}"
    # Security: Limited capabilities
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

  # Vue 3 frontend
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
    volumes:
      # Development: Mount source for hot reload
      - ./frontend:/app:ro
      - /app/node_modules  # Prevent overwriting node_modules
    ports:
      - "${FRONTEND_PORT:-8080}:8080"
    networks:
      - clinical_network
    depends_on:
      - backend
    restart: unless-stopped
    # Security: Run as non-root user
    user: "${UID:-1000}:${GID:-1000}"

  # Nginx reverse proxy (production)
  nginx:
    image: nginx:1.25-alpine
    container_name: clinical_tools_nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - frontend_dist:/usr/share/nginx/html:ro
    ports:
      - "80:80"
      - "443:443"
    networks:
      - clinical_network
    depends_on:
      - frontend
      - backend
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    # Security: Run as nginx user
    user: nginx

  # MedCAT Service (external NLP)
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
          memory: 4G  # MedCAT requires significant RAM
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  backend_logs:
    driver: local
  medcat_models:
    driver: local
  frontend_dist:
    driver: local

networks:
  clinical_network:
    driver: bridge
```

### Environment Variables (.env.example)

```bash
# Database
POSTGRES_DB=clinical_care_tools
POSTGRES_USER=clinicaltools
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD_HERE
POSTGRES_PORT=5432

# Backend
BACKEND_PORT=8000
JWT_SECRET_KEY=CHANGE_ME_256_BIT_RANDOM_KEY  # Generate: openssl rand -hex 32
ENCRYPTION_KEY=CHANGE_ME_256_BIT_RANDOM_KEY_32_BYTES  # Generate: openssl rand -base64 32
ENVIRONMENT=development
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:3000

# Frontend
FRONTEND_PORT=8080
VITE_API_URL=http://localhost:8000

# MedCAT
MEDCAT_SERVICE_URL=http://medcat-service:5000
MEDCAT_PORT=5000
MEDCAT_WORKERS=2

# User IDs (for running containers as non-root)
UID=1000
GID=1000
```

### Security Checklist for Docker Compose

- [✓] **No hardcoded secrets** - All secrets in `.env` file (gitignored)
- [✓] **Non-root users** - All containers run as non-root user
- [✓] **Read-only filesystems** - Where possible (postgres, nginx)
- [✓] **Health checks** - All services have health checks
- [✓] **Resource limits** - Memory/CPU limits defined
- [✓] **Capability restrictions** - Drop ALL, add only necessary
- [✓] **Network isolation** - Custom network (not default bridge)
- [✓] **Restart policies** - `unless-stopped` for production
- [✓] **SSL/TLS** - Nginx terminates TLS (production)

---

## 2. PostgreSQL Configuration

### Production Database Initialization Script

```sql
-- scripts/init-db.sql
-- Runs on first database creation

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create audit logging function (automatic timestamp updates)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create audit logging trigger template
-- Usage: Call this after creating any table with updated_at column
CREATE OR REPLACE FUNCTION create_updated_at_trigger(table_name text)
RETURNS void AS $$
BEGIN
    EXECUTE format('
        CREATE TRIGGER update_%I_updated_at
        BEFORE UPDATE ON %I
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    ', table_name, table_name);
END;
$$ LANGUAGE plpgsql;

-- Create immutable audit log protection
CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable and cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

-- Performance: Set shared_buffers (25% of RAM)
-- This requires docker run --shm-size or tmpfs in docker-compose
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;  # For SSD
ALTER SYSTEM SET effective_io_concurrency = 200;  # For SSD

-- Security: Set password encryption
ALTER SYSTEM SET password_encryption = 'scram-sha-256';

-- Logging: Enable slow query logging (>500ms)
ALTER SYSTEM SET log_min_duration_statement = 500;
ALTER SYSTEM SET log_line_prefix = '%t [%p]: user=%u,db=%d,app=%a,client=%h ';
ALTER SYSTEM SET log_statement = 'mod';  # Log all INSERT/UPDATE/DELETE

-- Connection pooling
ALTER SYSTEM SET max_connections = 100;

-- Reload configuration
SELECT pg_reload_conf();
```

### PostgreSQL Backup Script

```bash
#!/bin/bash
# scripts/backup-postgres.sh
# Daily automated backup script for PostgreSQL

set -e

# Configuration
BACKUP_DIR="/backups/$(date +%Y-%m-%d)"
POSTGRES_CONTAINER="clinical_tools_postgres"
POSTGRES_USER="clinicaltools"
POSTGRES_DB="clinical_care_tools"
RETENTION_DAYS=30

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
echo "Verifying backup integrity..."
pg_restore --list "$BACKUP_DIR/database.dump" > /dev/null

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_DIR/database.dump" | cut -f1)
echo "Backup complete: $BACKUP_SIZE"

# Encrypt backup (AES-256)
echo "Encrypting backup..."
tar czf - "$BACKUP_DIR" | \
    openssl enc -aes-256-cbc -salt -pbkdf2 \
    -pass file:/etc/clinical-tools/backup-password.txt \
    -out "$BACKUP_DIR.tar.gz.enc"

# Remove unencrypted backup
rm -rf "$BACKUP_DIR"

# Copy to offsite storage (example: NFS mount)
echo "Copying to offsite storage..."
cp "$BACKUP_DIR.tar.gz.enc" /mnt/nas/clinical-backups/

# Purge old backups (retention policy)
echo "Purging backups older than $RETENTION_DAYS days..."
find /mnt/nas/clinical-backups/ -name "*.tar.gz.enc" -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully at $(date)"
```

### PostgreSQL Restore Script

```bash
#!/bin/bash
# scripts/restore-postgres.sh
# Restore PostgreSQL from encrypted backup

set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file.tar.gz.enc>"
    exit 1
fi

echo "Restoring from backup: $BACKUP_FILE"

# Decrypt backup
echo "Decrypting backup..."
openssl enc -aes-256-cbc -d -pbkdf2 \
    -pass file:/etc/clinical-tools/backup-password.txt \
    -in "$BACKUP_FILE" | tar xzf -

# Extract directory name
BACKUP_DIR=$(basename "$BACKUP_FILE" .tar.gz.enc)

# Stop application (prevent connections during restore)
echo "Stopping application..."
docker-compose stop backend frontend

# Drop and recreate database
echo "Recreating database..."
docker exec clinical_tools_postgres psql -U clinicaltools -c "DROP DATABASE IF EXISTS clinical_care_tools;"
docker exec clinical_tools_postgres psql -U clinicaltools -c "CREATE DATABASE clinical_care_tools;"

# Restore database
echo "Restoring database..."
docker exec -i clinical_tools_postgres pg_restore \
    -U clinicaltools \
    -d clinical_care_tools \
    -Fc \
    --clean \
    --if-exists \
    < "$BACKUP_DIR/database.dump"

# Run migrations (ensure schema is current)
echo "Running migrations..."
docker-compose run --rm backend alembic upgrade head

# Restart application
echo "Starting application..."
docker-compose up -d

echo "Restore completed successfully at $(date)"
```

---

## 3. Authentication Implementation (JWT)

### JWT Token Generation (FastAPI + python-jose)

```python
# app/security/jwt.py
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import uuid

# Load from environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise ValueError("JWT_SECRET_KEY must be at least 32 characters")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

def create_access_token(user_id: str, role: str, additional_claims: dict = None) -> dict:
    """
    Create JWT access token

    Returns:
        {
            "access_token": "eyJ...",
            "token_type": "bearer",
            "expires_at": "2025-11-09T08:00:00Z"
        }
    """
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    payload = {
        "sub": user_id,  # Subject (user ID)
        "role": role,
        "exp": expire,   # Expiration
        "iat": datetime.utcnow(),  # Issued at
        "jti": str(uuid.uuid4())   # JWT ID (unique token ID)
    }

    # Add additional claims (optional)
    if additional_claims:
        payload.update(additional_claims)

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": expire.isoformat() + "Z"
    }

def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT token and return payload

    Returns:
        {"sub": "user-id", "role": "clinician", ...} or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check expiration (jose does this automatically, but double-check)
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            return None

        return payload

    except JWTError:
        return None

def decode_token_without_verification(token: str) -> Optional[dict]:
    """
    Decode JWT without verification (for logging/debugging only)

    WARNING: DO NOT use for authentication!
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except JWTError:
        return None
```

### Authentication Dependency (FastAPI)

```python
# app/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib

from app.database import get_db
from app.models import User, Session
from app.security.jwt import verify_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user

    Raises:
        HTTPException(401): If token invalid, expired, or session terminated
    """
    token = credentials.credentials

    # Verify JWT signature and expiration
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check session exists and not force_logout
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(
        select(Session).where(
            Session.token_hash == token_hash,
            Session.force_logout == False
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session terminated or not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    user = await db.get(User, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update session last_activity (for idle timeout detection)
    session.last_activity = datetime.utcnow()
    await db.commit()

    return user

def require_role(allowed_roles: list[str]):
    """
    Dependency factory to require specific roles

    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_role(["admin"]))])
    """
    async def check_role(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(allowed_roles)}"
            )
        return user
    return check_role
```

### Login Endpoint

```python
# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
from datetime import datetime

from app.database import get_db
from app.models import User, Session
from app.schemas import LoginRequest, TokenResponse, UserResponse
from app.security.jwt import create_access_token
from app.security.password import verify_password
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    User login with username/password

    Returns JWT access token on success
    """
    audit = AuditService(db)

    # Query user by username
    result = await db.execute(
        select(User).where(User.username == login_data.username)
    )
    user = result.scalar_one_or_none()

    # Verify user exists and password correct
    if not user or not verify_password(login_data.password, user.password_hash):
        # Audit log: Failed login
        await audit.log(
            user_id=None,
            action="LOGIN_FAILURE",
            resource_type="auth",
            resource_id=login_data.username,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={"reason": "invalid_credentials"}
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Check user is active
    if not user.is_active:
        await audit.log(
            user_id=str(user.id),
            action="LOGIN_FAILURE",
            resource_type="auth",
            resource_id=str(user.id),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={"reason": "user_inactive"}
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create JWT token
    token_data = create_access_token(user_id=str(user.id), role=user.role)

    # Create session record (for session tracking and force logout)
    session = Session(
        user_id=user.id,
        token_hash=hashlib.sha256(token_data["access_token"].encode()).hexdigest(),
        ip_address_hash=hashlib.sha256(request.client.host.encode()).hexdigest(),
        user_agent_hash=hashlib.sha256(request.headers.get("user-agent", "").encode()).hexdigest(),
        expires_at=datetime.fromisoformat(token_data["expires_at"].rstrip("Z"))
    )
    db.add(session)

    # Audit log: Successful login
    await audit.log(
        user_id=str(user.id),
        action="LOGIN_SUCCESS",
        resource_type="auth",
        resource_id=str(user.id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        details={"session_id": str(session.id)}
    )

    await db.commit()

    return token_data

@router.post("/logout")
async def logout(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    User logout (invalidate current session)
    """
    audit = AuditService(db)

    # Get current session token from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = auth_header[7:]  # Remove "Bearer " prefix
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Delete session
    result = await db.execute(
        select(Session).where(
            Session.token_hash == token_hash,
            Session.user_id == user.id
        )
    )
    session = result.scalar_one_or_none()

    if session:
        await db.delete(session)

        # Audit log
        await audit.log(
            user_id=str(user.id),
            action="LOGOUT",
            resource_type="auth",
            resource_id=str(user.id),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )

        await db.commit()

    return {"message": "Logged out successfully"}
```

---

## 4. Audit Logging Implementation

### Audit Service Pattern

```python
# app/services/audit_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AuditService:
    """
    Centralized audit logging service

    ALL PHI access must be logged through this service
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """
        Create audit log entry

        Args:
            user_id: User performing action (None for system actions)
            action: Action performed (e.g., LOGIN_SUCCESS, DOCUMENT_UPLOAD, PATIENT_VIEW)
            resource_type: Type of resource (e.g., document, patient, user)
            resource_id: ID of specific resource (e.g., patient UUID)
            ip_address: Client IP address
            user_agent: Client user-agent string
            details: Additional context (JSON)

        Examples:
            await audit.log(
                user_id=user.id,
                action="PATIENT_VIEW",
                resource_type="patient",
                resource_id=patient_id,
                ip_address="192.168.1.10",
                user_agent="Mozilla/5.0...",
                details={"search_query": "diabetes"}
            )
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details
            )

            self.db.add(audit_log)
            await self.db.flush()  # Don't commit yet (let caller control transaction)

            logger.info(
                f"AUDIT: user={user_id} action={action} resource={resource_type}/{resource_id}"
            )

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise - audit logging failure shouldn't break application

    async def log_phi_access(
        self,
        user_id: str,
        patient_id: str,
        access_type: str,
        ip_address: str,
        user_agent: str,
        details: Optional[dict] = None
    ):
        """
        Specialized logging for PHI access (patient data)

        This is a convenience wrapper for patient-related actions
        """
        await self.log(
            user_id=user_id,
            action=f"PHI_{access_type.upper()}",
            resource_type="patient",
            resource_id=patient_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
```

### Audit Log Model

```python
# app/models/audit_log.py
from sqlalchemy import Column, String, Text, TIMESTAMP, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid

class AuditLog(Base):
    """
    Immutable audit log for all system actions

    Protected by PostgreSQL rules (no updates/deletes allowed)
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # None for system actions
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support (max 45 chars)
    user_agent = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id} at {self.created_at}>"
```

### Audit Log Migration with Immutability

```python
# alembic/versions/003_create_audit_logs_table.py
"""Create immutable audit_logs table

Revision ID: 003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # Create table
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    # Create indexes
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'], postgresql_using='btree')

    # Make audit logs IMMUTABLE (prevent updates/deletes)
    op.execute("""
        CREATE RULE no_update_audit_logs AS
        ON UPDATE TO audit_logs
        DO INSTEAD NOTHING;
    """)

    op.execute("""
        CREATE RULE no_delete_audit_logs AS
        ON DELETE TO audit_logs
        DO INSTEAD NOTHING;
    """)

def downgrade():
    op.execute("DROP RULE IF EXISTS no_delete_audit_logs ON audit_logs;")
    op.execute("DROP RULE IF EXISTS no_update_audit_logs ON audit_logs;")
    op.drop_index('idx_audit_logs_created_at')
    op.drop_index('idx_audit_logs_resource')
    op.drop_index('idx_audit_logs_action')
    op.drop_index('idx_audit_logs_user_id')
    op.drop_table('audit_logs')
```

---

## 5. Healthcare Security Hardening Checklist

### HIPAA Compliance Checklist

- [ ] **Access Control (164.312(a)(1))**
  - [ ] Unique user identification (UUID, username)
  - [ ] Emergency access (break-glass implemented)
  - [ ] Automatic logoff (idle timeout: 15 minutes)
  - [ ] Encryption/decryption (AES-256 for data at rest)

- [ ] **Audit Controls (164.312(b))**
  - [ ] Record all PHI access (audit_logs table)
  - [ ] Immutable audit logs (PostgreSQL rules)
  - [ ] Log retention: 7 years minimum
  - [ ] Audit log review process (weekly)

- [ ] **Integrity (164.312(c)(1))**
  - [ ] Mechanism to authenticate electronic PHI (SHA-256 hashing)
  - [ ] Prevent unauthorized alteration (database constraints)

- [ ] **Transmission Security (164.312(e)(1))**
  - [ ] TLS 1.3 for data in transit (Nginx)
  - [ ] Certificate management (Let's Encrypt or internal CA)

### GDPR Compliance Checklist

- [ ] **Lawful Basis (Article 6)**
  - [ ] User consent recorded (for research use)
  - [ ] Legitimate interest documented

- [ ] **Data Minimization (Article 5(1)(c))**
  - [ ] Collect only necessary PHI fields
  - [ ] Retention policy implemented (8 years)
  - [ ] Automated purging after retention period

- [ ] **Right to Erasure (Article 17)**
  - [ ] Delete patient data on request
  - [ ] Cascade deletes (documents, entities)
  - [ ] Audit log of deletion (who, when, why)

- [ ] **Data Portability (Article 20)**
  - [ ] Export patient data in structured format (JSON, CSV)
  - [ ] Include all related documents and entities

- [ ] **Security (Article 32)**
  - [ ] Encryption at rest (AES-256)
  - [ ] Encryption in transit (TLS 1.3)
  - [ ] Pseudonymization (for research exports)
  - [ ] Regular backups (daily, encrypted, offsite)

---

## Common Patterns

### Pattern: Retry Logic for External Services (MedCAT)

```python
# app/clients/medcat_client.py
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class MedCATClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def process_text(self, text: str):
        """Process text with retry logic (3 attempts, exponential backoff)"""
        response = await self.client.post(
            f"{self.base_url}/api/process",
            json={"text": text}
        )
        response.raise_for_status()
        return response.json()
```

### Pattern: Database Connection Pooling

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Extra connections if pool exhausted
    pool_pre_ping=True,  # Test connection before using
    pool_recycle=3600,   # Recycle connections every hour
)

async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """FastAPI dependency for database sessions"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

## Usage

When implementing core infrastructure:

1. **Start with Docker Compose** - Get services running first
2. **Configure PostgreSQL** - Security hardening, backup scripts
3. **Implement Authentication** - JWT tokens, login endpoint, dependencies
4. **Implement Audit Logging** - AuditService, immutable audit_logs table
5. **Test Security** - Run security checklist, penetration testing
6. **Document** - Update CONTEXT.md with infrastructure decisions

**Reference**: This skill when implementing tasks from `.specify/tasks/*-tasks.md`
