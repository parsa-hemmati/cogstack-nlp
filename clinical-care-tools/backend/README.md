# Clinical Care Tools - Backend

FastAPI-based backend for Clinical Care Tools application with HIPAA-compliant audit logging, RBAC authorization, and JWT authentication.

## Tech Stack

- **Python 3.11** - Backend language
- **FastAPI 0.104+** - Async web framework with automatic OpenAPI docs
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL 16** - Database
- **Alembic** - Database migrations
- **pytest** - Testing framework
- **bcrypt** - Password hashing

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings management
│   │   ├── database.py   # Database connection
│   │   └── security.py   # JWT token handling
│   ├── models/           # SQLAlchemy models
│   │   ├── user.py       # User model
│   │   ├── session.py    # Session model
│   │   └── audit_log.py  # Audit log model
│   ├── schemas/          # Pydantic schemas
│   │   ├── auth.py       # Auth request/response schemas
│   │   └── session.py    # Session schemas
│   ├── services/         # Business logic
│   │   ├── auth_service.py   # Authentication service
│   │   └── audit_service.py  # Audit logging service
│   └── main.py           # FastAPI application
├── alembic/              # Database migrations
├── scripts/              # Utility scripts
│   └── first-time-setup.py  # Initial setup script
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- virtualenv or similar

### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Environment
ENVIRONMENT=development
DEBUG=true
APP_VERSION=0.1.0

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/clinical_care_tools

# Security
SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Admin Setup (for first-time-setup.py)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password-here
ADMIN_FULL_NAME=System Administrator
```

**⚠️ IMPORTANT**: Change `SECRET_KEY` and `ADMIN_PASSWORD` in production!

### Installation

1. **Create virtual environment**:
   ```bash
   cd /home/user/cogstack-nlp/clinical-care-tools/backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Run first-time setup** (creates admin user):
   ```bash
   python scripts/first-time-setup.py
   ```

   This script:
   - ✅ Creates admin user (if not exists)
   - ✅ Is idempotent (safe to run multiple times)
   - ✅ Uses environment variables for credentials
   - ✅ Provides clear success/error messages

   **Output example**:
   ```
   ======================================================================
   Clinical Care Tools - First-Time Setup
   ======================================================================

   Step 1: Verifying database connection...
   ✅ Database connection successful

   Step 2: Checking database migrations...
   ✅ Database tables exist (migrations applied)

   Step 3: Creating admin user...
   ✅ Created admin user 'admin' (ID: 550e8400-e29b-41d4-a716-446655440000)
      Full Name: System Administrator
      Role: admin
      Password: ************

   ======================================================================
   ✅ First-time setup complete!

   Next steps:
   1. Start the backend server:
      cd /home/user/cogstack-nlp/clinical-care-tools/backend
      uvicorn app.main:app --reload --port 8000

   2. Login with admin credentials:
      Username: admin
      Password: your-password

   3. Access API docs:
      http://localhost:8000/docs
   ======================================================================
   ```

5. **Start development server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   Server will be available at:
   - API: http://localhost:8000
   - OpenAPI docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /api/v1/auth/login` - Login with username/password, returns JWT access token
- `POST /api/v1/auth/refresh` - Refresh access token using refresh token
- `POST /api/v1/auth/logout` - Logout (invalidates session)
- `GET /api/v1/auth/me` - Get current user info

### Session Management

- `GET /api/v1/sessions/my-sessions` - Get current user's active sessions
- `DELETE /api/v1/sessions/{session_id}` - Revoke specific session
- `DELETE /api/v1/sessions/all` - Revoke all sessions for current user

### Health Check

- `GET /health` - Health check endpoint (returns 200 if healthy, 503 if unhealthy)

## Authentication Flow

1. **Login**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
   ```

   Response:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIs...",
     "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
     "token_type": "bearer",
     "expires_in": 28800,
     "user": {
       "id": "550e8400-e29b-41d4-a716-446655440000",
       "username": "admin",
       "full_name": "System Administrator",
       "role": "admin"
     }
   }
   ```

2. **Use access token**:
   ```bash
   curl http://localhost:8000/api/v1/auth/me \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
   ```

3. **Refresh token** (when access token expires):
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/refresh \
     -H "Authorization: Bearer <refresh_token>"
   ```

## Authorization (RBAC)

The system uses Role-Based Access Control with 4 roles:

| Role | Permissions |
|------|-------------|
| **admin** | All permissions (user management, configuration, PHI access) |
| **clinician** | PHI access, patient search, timeline view, annotation |
| **researcher** | De-identified data only, cohort identification, statistics |
| **viewer** | Read-only access to non-PHI data |

Example endpoint requiring admin role:
```python
from app.core.security import get_current_user_with_permission

@router.get("/admin-only")
async def admin_only_endpoint(
    user: User = Depends(get_current_user_with_permission("admin"))
):
    return {"message": "Admin access granted"}
```

## Audit Logging

All PHI access and critical operations are logged to the `audit_logs` table:

- **WHO**: user_id, username
- **WHAT**: action, resource_type, resource_id
- **WHEN**: timestamp (UTC)
- **WHERE**: ip_address, user_agent

**Common Actions**:
- `LOGIN`, `LOGOUT`, `REFRESH_TOKEN`
- `VIEW_PATIENT`, `UPDATE_PATIENT`, `DELETE_PATIENT`
- `VIEW_DOCUMENT`, `CREATE_DOCUMENT`, `UPDATE_DOCUMENT`
- `BREAK_GLASS_ACCESS` (emergency PHI access)

**Example**:
```python
from app.services.audit_service import log_action

await log_action(
    db=db,
    user_id=user.id,
    username=user.username,
    action="VIEW_PATIENT",
    resource_type="patient",
    resource_id="patient-123",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent", ""),
    details={"search_query": "diabetes", "results_count": 15}
)
```

## Testing

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file:
```bash
pytest tests/unit/test_auth_service.py
```

### Run integration tests only:
```bash
pytest tests/integration/
```

**Current Test Coverage**: 85%+ across all modules

**Test Structure**:
- `tests/unit/` - Unit tests for services, models, utilities
- `tests/integration/` - API endpoint tests with test database
- `tests/conftest.py` - Shared fixtures and test configuration

## Database Migrations

### Create new migration:
```bash
alembic revision --autogenerate -m "Add new table"
```

### Apply migrations:
```bash
alembic upgrade head
```

### Rollback migration:
```bash
alembic downgrade -1
```

### View migration history:
```bash
alembic history
```

## Security Best Practices

1. **Password Hashing**: bcrypt with automatic salt generation
2. **JWT Tokens**: HS256 algorithm, 8-hour expiry, refresh tokens supported
3. **Session Management**: IP/UA binding, max 2 concurrent sessions per user
4. **Audit Logging**: Immutable logs (UPDATE/DELETE blocked at database level)
5. **RBAC**: Permission checks on all sensitive endpoints
6. **Input Validation**: Pydantic schemas validate all request data
7. **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

## HIPAA Compliance Features

- ✅ **Audit Trail**: All PHI access logged with WHO/WHAT/WHEN/WHERE
- ✅ **Encryption**: TLS 1.3 in transit (configure in production proxy)
- ✅ **Access Control**: RBAC with principle of least privilege
- ✅ **Authentication**: Strong password hashing, JWT tokens, session management
- ✅ **Data Integrity**: Database constraints, immutable audit logs
- ✅ **Accountability**: User attribution for all actions

## Development Workflow

1. **Create feature branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Write tests first** (TDD):
   ```bash
   # Create test file
   vim tests/unit/test_my_feature.py

   # Run tests (should fail)
   pytest tests/unit/test_my_feature.py
   ```

3. **Implement feature**:
   ```bash
   # Implement code
   vim app/services/my_feature.py

   # Run tests (should pass)
   pytest tests/unit/test_my_feature.py
   ```

4. **Run all tests**:
   ```bash
   pytest --cov=app
   ```

5. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat(my-feature): add feature description"
   git push origin feature/my-feature
   ```

## Troubleshooting

### Database connection refused
```
Error: [Errno 111] Connect call failed ('127.0.0.1', 5432)
```

**Solution**:
1. Ensure PostgreSQL is running: `sudo systemctl start postgresql`
2. Check `DATABASE_URL` in `.env` file
3. Verify database exists: `psql -U postgres -c "SELECT 1;"`

### Import errors
```
ImportError: cannot import name 'X' from 'app.core'
```

**Solution**:
1. Ensure virtual environment is activated: `source venv/bin/activate`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python path: `echo $PYTHONPATH`

### Migration errors
```
ERROR [alembic.util.messaging] Target database is not up to date.
```

**Solution**:
1. Apply all migrations: `alembic upgrade head`
2. If conflicts, manually resolve or reset: `alembic downgrade base && alembic upgrade head`

## Production Deployment

### Environment Setup
1. Set production environment variables
2. Use PostgreSQL with connection pooling (not NullPool)
3. Enable HTTPS (TLS 1.3) via reverse proxy (nginx, Caddy)
4. Set strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
5. Change default admin password immediately

### Recommended Stack
- **Web Server**: uvicorn with multiple workers
- **Reverse Proxy**: nginx or Caddy (handles HTTPS, static files)
- **Database**: PostgreSQL 16 with regular backups
- **Process Manager**: systemd or supervisor

### Example systemd service
```ini
[Unit]
Description=Clinical Care Tools API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/clinical-care-tools/backend
Environment="PATH=/opt/clinical-care-tools/backend/venv/bin"
ExecStart=/opt/clinical-care-tools/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target
```

## License

[Your License Here]

## Contributing

1. Follow TDD workflow (tests first)
2. Maintain 80%+ test coverage
3. Use conventional commits (feat, fix, docs, etc.)
4. Update CONTEXT.md with all changes
5. Follow HIPAA compliance guidelines

## Support

For issues or questions, contact [Your Contact Info]
