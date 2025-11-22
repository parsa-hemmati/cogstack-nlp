# Security & Compliance Guide

Comprehensive security model, best practices, and compliance requirements for Clinical Care Tools.

## Table of Contents

1. [Security Overview](#security-overview)
2. [Encryption & Data Protection](#encryption--data-protection)
3. [Authentication & Authorization](#authentication--authorization)
4. [Audit Logging](#audit-logging)
5. [Compliance Frameworks](#compliance-frameworks)
6. [Security Best Practices](#security-best-practices)
7. [Incident Response](#incident-response)
8. [Security Checklist](#security-checklist)

## Security Overview

The Clinical Care Tools application implements a defense-in-depth security model:

```
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL THREAT SURFACE                   │
├─────────────────────────────────────────────────────────────┤
│  TLS 1.3 Encryption │ API Authentication (JWT)             │
├─────────────────────────────────────────────────────────────┤
│         FastAPI Application                                 │
│  ├─ Input Validation (Pydantic)                            │
│  ├─ Rate Limiting                                          │
│  ├─ CORS Protection                                        │
│  └─ Security Headers (HSTS, CSP, X-Frame-Options)         │
├─────────────────────────────────────────────────────────────┤
│            Data Layer                                       │
│  ├─ Role-Based Access Control (RBAC)                      │
│  ├─ Row-Level Security (RLS)                              │
│  ├─ Query Parameterization (SQL Injection Prevention)      │
│  └─ Sensitive Data Masking                                │
├─────────────────────────────────────────────────────────────┤
│           Storage & Infrastructure                          │
│  ├─ Encryption at Rest (AES-256)                          │
│  ├─ Secure Key Management                                 │
│  ├─ Network Isolation (Private Networks)                  │
│  └─ Container Security (Signed Images)                    │
└─────────────────────────────────────────────────────────────┘
```

## Encryption & Data Protection

### In-Transit Encryption

**Protocol**: TLS 1.3 (minimum: TLS 1.2)

**Implementation**:

```python
# Development (.env):
SSL_ENABLED=false  # Self-signed, localhost only

# Production (.env):
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/clinical-care-tools.crt
SSL_KEY_PATH=/etc/ssl/private/clinical-care-tools.key
```

**Certificate Requirements**:
- Valid domain certificate (not self-signed)
- Minimum key length: 2048 bits RSA (4096 recommended)
- Must include wildcard or full domain
- Auto-renewal (Let's Encrypt recommended)

**Nginx Configuration**:

```nginx
server {
    listen 443 ssl http2;
    server_name clinical.healthcare.org;

    ssl_certificate /etc/ssl/certs/clinical.crt;
    ssl_certificate_key /etc/ssl/private/clinical.key;

    # Modern configuration
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS (force HTTPS)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

### At-Rest Encryption

**Database Encryption**:

```sql
-- PostgreSQL Full Disk Encryption
-- Use encrypted filesystem (LUKS on Linux)
sudo cryptsetup luksFormat /dev/sda1
sudo cryptsetup luksOpen /dev/sda1 encrypted_data
sudo mkfs.ext4 /dev/mapper/encrypted_data

-- Application-level encryption for sensitive fields
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,  -- Hashed, never plain text
    api_key_encrypted TEXT        -- Encrypted with KMS
);
```

**Sensitive Field Encryption** (AES-256):

```python
# backend/app/utils/encryption.py
from cryptography.fernet import Fernet

class FieldEncryption:
    def __init__(self, key: str):
        self.cipher = Fernet(key.encode())

    def encrypt(self, value: str) -> str:
        """Encrypt sensitive field"""
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        """Decrypt sensitive field"""
        return self.cipher.decrypt(encrypted.encode()).decode()

# Usage in models:
class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    key_encrypted = Column(String)  # Encrypted

    @property
    def key_decrypted(self) -> str:
        return encryption.decrypt(self.key_encrypted)
```

### Key Management

**Secret Management** (Use in Production):

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name clinical-care-tools/db-password \
  --secret-string "$(openssl rand -base64 32)"

# Docker Secrets (Swarm)
echo "secure-password" | docker secret create db_password -

# Environment Variables (Development Only)
# Use .env.development (git-ignored)
```

**Rotate Keys Regularly**:
- Database passwords: Every 90 days
- JWT signing key: Every 6 months (invalidate old tokens)
- TLS certificates: Before expiration (auto-renew)
- API keys: When compromised or on schedule

## Authentication & Authorization

### JWT Tokens

**Token Structure**:

```
Header.Payload.Signature

Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload:
{
  "sub": "user_id_uuid",
  "username": "admin",
  "role": "admin",
  "exp": 1641660000,
  "iat": 1641631200,
  "aud": "clinical-care-tools"
}

Signature:
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  secret_key
)
```

**Token Lifecycle**:

```
1. User logs in
   ├─ Credentials validated
   ├─ Issue access token (8 hours)
   └─ Issue refresh token (7 days)

2. User accesses protected resource
   ├─ Include access token in header
   ├─ Validate token signature
   ├─ Check expiration
   ├─ Check blacklist (revoked tokens)

3. Token expires
   ├─ Access denied
   ├─ Use refresh token to get new access token

4. User logs out
   ├─ Add tokens to blacklist (Redis TTL)
   ├─ Cannot be reused
```

**Implementation**:

```python
# backend/app/services/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

class AuthService:
    def create_tokens(self, user_id: str, username: str, role: str):
        """Create access and refresh tokens"""
        now = datetime.utcnow()

        # Access token (8 hours)
        access_payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": now + timedelta(hours=8),
            "iat": now,
            "type": "access"
        }
        access_token = jwt.encode(
            access_payload,
            settings.SECRET_KEY,
            algorithm="HS256"
        )

        # Refresh token (7 days)
        refresh_payload = {
            "sub": user_id,
            "exp": now + timedelta(days=7),
            "iat": now,
            "type": "refresh"
        }
        refresh_token = jwt.encode(
            refresh_payload,
            settings.SECRET_KEY,
            algorithm="HS256"
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 28800
        }

    def verify_token(self, token: str) -> dict:
        """Verify token validity"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )

            # Check if token is blacklisted (revoked)
            if redis_client.exists(f"blacklist:{token}"):
                raise JWTError("Token has been revoked")

            return payload

        except JWTError:
            raise JWTError("Invalid token")
```

### Role-Based Access Control (RBAC)

**Roles Defined**:

| Role | Permissions | Use Case |
|------|-------------|----------|
| `admin` | All operations | System administrators |
| `clinician` | Read/write patient data | Clinical staff |
| `researcher` | Read-only access | Research team |
| `analyst` | Analytics/reporting | Data analysts |
| `audit_viewer` | View audit logs only | Compliance team |

**Implementation**:

```python
# backend/app/models/user.py
class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True)
    username = Column(String, unique=True, index=True)
    role = Column(Enum(UserRole), default=UserRole.CLINICIAN)
    permissions = Column(JSON, default={})  # Custom permissions

# backend/app/dependencies.py
from fastapi import Depends, HTTPException

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get authenticated user from token"""
    payload = auth_service.verify_token(token)
    user = await db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def require_admin(
    user: User = Depends(get_current_user)
) -> User:
    """Require admin role"""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_clinician(
    user: User = Depends(get_current_user)
) -> User:
    """Require clinician or admin role"""
    if user.role not in [UserRole.ADMIN, UserRole.CLINICIAN]:
        raise HTTPException(status_code=403, detail="Clinician access required")
    return user

# Usage in endpoints:
@router.post("/api/patients")
async def create_patient(
    patient: PatientCreate,
    user: User = Depends(require_clinician)  # Require clinician role
):
    """Create new patient - clinician+ only"""
    # Implementation
    pass
```

### Password Security

**Requirements**:
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Not in common password list
- Enforce change on first login
- Prevent reuse of last 5 passwords

**Hashing**:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increase rounds for better security
)

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain, hashed)
```

## Audit Logging

**Complete Audit Trail** for all PHI access:

```python
# backend/app/models/audit_log.py
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    action = Column(String)  # VIEW, EXPORT, CREATE, DELETE, etc
    resource_type = Column(String)  # patient, document, entity
    resource_id = Column(UUID)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String)
    user_agent = Column(String)
    details = Column(JSON)  # Additional context
    status = Column(String)  # success, failure
    error_message = Column(String, nullable=True)

# Audit logging middleware
@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    """Log all requests to protected endpoints"""
    response = await call_next(request)

    # Log if accessing patient/document resources
    if "/api/patients" in request.url.path or "/api/documents" in request.url.path:
        user = request.state.user  # From auth middleware
        await audit_service.log(
            user_id=user.id,
            action=determine_action(request.method),
            resource_type=extract_resource_type(request.url.path),
            resource_id=extract_resource_id(request.url.path),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code
            },
            status="success" if response.status_code < 400 else "failure"
        )

    return response
```

**Audit Log Retention**:

```bash
# 7 years for clinical records (NHS requirement)
AUDIT_LOG_RETENTION_DAYS=2555

# PostgreSQL partitioning for performance
CREATE TABLE audit_logs_2025_01 PARTITION OF audit_logs
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

**Viewing Audit Logs**:

```bash
# API endpoint
GET /api/audit-logs?start_date=2025-01-01&end_date=2025-01-31

# Direct database query (admin only)
SELECT * FROM audit_logs
WHERE timestamp >= '2025-01-01'
  AND resource_type = 'patient'
ORDER BY timestamp DESC;
```

## Compliance Frameworks

### HIPAA (Health Insurance Portability and Accountability Act)

**Protected Health Information (PHI)**:
- Patient name, medical record number, date of birth
- Medical diagnoses, procedures, medications
- Lab results, imaging reports
- All must be encrypted and access logged

**HIPAA Requirements**:

```
✓ Encryption in Transit (TLS 1.2+)
✓ Encryption at Rest (AES-256)
✓ Access Controls (RBAC, MFA optional)
✓ Audit Logging (6 years minimum)
✓ Data Integrity Verification
✓ Risk Assessment (annual)
✓ Incident Response Plan
✓ Business Associate Agreements (BAAs)
✓ Workforce Training (annual)
```

**Compliance Checklist**:

```python
# HIPAA Compliance Checklist
hipaa_requirements = {
    "encryption": {
        "in_transit": "TLS 1.3 required",
        "at_rest": "AES-256 required",
        "key_management": "Secure key storage",
        "status": "IMPLEMENTED"
    },
    "access_control": {
        "authentication": "JWT + password hashing (bcrypt)",
        "authorization": "RBAC with 5 roles",
        "mfa": "Not required but recommended",
        "status": "IMPLEMENTED"
    },
    "audit_logging": {
        "coverage": "All PHI access logged",
        "retention": "7 years (2555 days)",
        "tamper_evident": "Database integrity checks",
        "status": "IMPLEMENTED"
    },
    "data_integrity": {
        "checksums": "MD5 for file integrity",
        "validation": "Input validation on all PHI",
        "status": "IMPLEMENTED"
    }
}
```

### GDPR (General Data Protection Regulation)

**Data Subject Rights**:

```python
# Right to Access
GET /api/data-subject/personal-data
→ Returns all personal data held

# Right to Erasure ("Right to be Forgotten")
DELETE /api/data-subject/{subject_id}/data
→ Securely delete all personal data

# Right to Data Portability
POST /api/data-subject/export
→ Export data in standard format (JSON)

# Right to Restrict Processing
POST /api/data-subject/{subject_id}/restrict
→ Stop processing personal data
```

**GDPR Requirements**:

```
✓ Lawful Basis for Processing (Consent or Legitimate Interest)
✓ Data Protection Impact Assessment (DPIA)
✓ Privacy by Design
✓ Data Minimization (collect only what's needed)
✓ Consent Management (explicit opt-in)
✓ Right to Access (within 30 days)
✓ Right to Erasure (reasonable effort)
✓ Breach Notification (within 72 hours)
✓ Data Protection Officer (for healthcare)
✓ Processor Agreements (with third parties)
```

### FDA 21 CFR Part 11

**Electronic Records Requirements**:

```
✓ System Validation & Documentation
✓ User Authentication & Audit Trails
✓ System Access Control & Authorization
✓ Secure Data Transmission
✓ Data Integrity & Accuracy
✓ Archive & Retrieval Capability
✓ System Documentation
✓ Change Control Procedures
```

**Implementation**:

```python
# backend/app/utils/validation.py
class CFRPart11Compliance:
    """Ensure FDA 21 CFR Part 11 compliance"""

    @staticmethod
    def validate_system():
        """System validation checklist"""
        return {
            "user_authentication": {
                "username_password": True,
                "uniqueness": True,
                "strength": "12+ chars, mixed case, symbols"
            },
            "audit_trail": {
                "coverage": "All data changes logged",
                "immutability": "Cannot be altered",
                "retention": "7 years"
            },
            "encryption": {
                "in_transit": "TLS 1.3",
                "at_rest": "AES-256"
            },
            "change_control": {
                "procedure": "Documented changes with review",
                "traceability": "Full change history"
            }
        }
```

## Security Best Practices

### Input Validation

```python
from pydantic import BaseModel, validator, constr

class PatientCreate(BaseModel):
    """Patient creation with validated input"""
    mrn: constr(regex=r"^[A-Z0-9]{6,12}$", min_length=6, max_length=12)
    first_name: constr(min_length=1, max_length=100)
    last_name: constr(min_length=1, max_length=100)
    dob: date

    @validator('dob')
    def validate_dob(cls, v):
        """Validate date of birth is reasonable"""
        if v > date.today():
            raise ValueError('DOB cannot be in the future')
        if (date.today() - v).days > 150 * 365:  # 150 years
            raise ValueError('DOB must be realistic')
        return v

# Pydantic automatically validates and sanitizes input
patient = PatientCreate(**request.data)
```

### SQL Injection Prevention

```python
# ✓ CORRECT: Use parameterized queries
patients = db.query(Patient).filter(
    Patient.mrn == mrn  # Parameter binding
).all()

# ✗ WRONG: String interpolation
patients = db.execute(f"SELECT * FROM patients WHERE mrn = '{mrn}'")
```

### XSS (Cross-Site Scripting) Prevention

```python
# Frontend: Vue 3 auto-escapes by default
<template>
  <!-- This is safe - Vue escapes -->
  <p>{{ patient.name }}</p>

  <!-- Use v-text for explicit escaping -->
  <p v-text="patient.name"></p>

  <!-- Avoid v-html unless sanitized -->
  <p v-html="sanitizeHTML(patient.notes)"></p>
</template>

# Backend: Return safe content types
@app.get("/api/patients/{id}")
async def get_patient(id: UUID):
    patient = await db.get(Patient, id)
    # FastAPI/Pydantic automatically escapes JSON
    return patient  # JSON-encoded response is safe
```

### CORS (Cross-Origin Resource Sharing)

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://clinical.healthcare.org",  # Production
        # NOT localhost in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-RateLimit-Remaining"],
    max_age=600  # Cache preflight 10 minutes
)
```

### Rate Limiting

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.util import get_remote_address

# Configure rate limiter
FastAPILimiter.init(redis_client)

# Apply to endpoints
@app.post("/api/auth/login")
@limiter.limit("5/minute")  # 5 login attempts per minute
async def login(credentials: LoginRequest):
    pass

@app.get("/api/patients/search")
@limiter.limit("10/minute")  # 10 searches per minute
async def search_patients(query: str):
    pass
```

### Security Headers

```python
# backend/app/main.py
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Enable XSS filtering
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self' https://"
    )

    # HSTS (HTTPS only)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains; preload"
    )

    return response
```

## Incident Response

**Incident Classification**:

1. **Level 1 (Critical)**: PHI breach, system compromise, ransomware
   - Response time: Immediate (within 1 hour)
   - Actions: Isolate system, notify stakeholders, preserve evidence

2. **Level 2 (High)**: Unauthorized access, failed login attempts, vulnerability
   - Response time: 4 hours
   - Actions: Investigate, patch, monitor

3. **Level 3 (Medium)**: Suspicious activity, configuration changes
   - Response time: 24 hours
   - Actions: Log, investigate, document

4. **Level 4 (Low)**: Policy violations, informational
   - Response time: 1 week
   - Actions: Document, communicate

**Incident Response Plan**:

```markdown
1. DETECTION
   - Monitor audit logs
   - Monitor system metrics
   - User reports

2. CONTAINMENT
   - Isolate affected system
   - Prevent further access
   - Preserve evidence

3. INVESTIGATION
   - Review audit logs
   - Analyze logs
   - Determine scope of breach

4. NOTIFICATION
   - Notify leadership (if PHI breach)
   - Notify regulators (if required)
   - Notify affected individuals (if required)

5. REMEDIATION
   - Close vulnerability
   - Deploy patch
   - Update security controls

6. POST-INCIDENT
   - Document lessons learned
   - Update procedures
   - Train staff
   - Improve monitoring
```

## Security Checklist

### Before Deployment

- [ ] SSL/TLS certificates valid and installed
- [ ] Database encrypted at rest
- [ ] All secrets in environment variables (not code)
- [ ] SQL injection prevention enabled
- [ ] XSS prevention enabled
- [ ] CORS configured for production domains only
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Audit logging enabled
- [ ] Access controls tested
- [ ] Passwords enforce complexity
- [ ] Admin credentials changed from defaults
- [ ] Backup encryption enabled
- [ ] Monitoring and alerting configured

### Regular Maintenance

- [ ] Monthly security patches applied
- [ ] Quarterly penetration testing
- [ ] Annual security audit
- [ ] Annual privacy assessment
- [ ] Regular password rotation (90 days)
- [ ] Regular certificate renewal
- [ ] Regular backup restoration test
- [ ] Security incident drills

### Compliance

- [ ] HIPAA compliance confirmed
- [ ] GDPR compliance confirmed
- [ ] FDA 21 CFR Part 11 compliance confirmed
- [ ] Business Associate Agreements signed
- [ ] Data Privacy Impact Assessment completed
- [ ] Incident response plan documented
- [ ] Staff training completed

---

**Last Updated**: 2025-01-08
**Version**: 1.0.0
**Classification**: Sensitive - Internal Use Only
