# Clinical Care Tools Backend

A FastAPI-based backend for the Clinical Care Tools application, providing APIs for healthcare NLP workflows powered by MedCAT.

## Architecture

### Technology Stack
- **Framework**: FastAPI 0.115.2
- **Database**: PostgreSQL 15 + SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT + Passlib
- **Caching**: Redis
- **Validation**: Pydantic v2

### Project Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── env.py                 # Alembic configuration (async SQLAlchemy)
│   ├── script.py.mako         # Migration template
│   └── versions/
│       ├── 001_initial_schema.py
│       └── 002_module_tables.py
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration from environment variables
│   ├── database.py            # Database engine and session management
│   └── models/
│       ├── __init__.py
│       ├── user.py            # User authentication model
│       ├── session.py         # Session management model
│       ├── audit_log.py       # Immutable audit trail (HIPAA/GDPR)
│       ├── project.py         # Project, ProjectMember, Task models
│       ├── document.py        # Encrypted clinical document model
│       ├── extracted_entity.py # NLP extraction results
│       ├── patient.py         # Aggregated patient records
│       ├── module.py          # Installed modules
│       ├── patient_search.py  # Patient search module models
│       └── timeline.py        # Timeline module models
├── pyproject.toml             # Project metadata and dependencies
├── requirements.txt           # Pinned dependencies
├── alembic.ini               # Alembic configuration
└── .env.example              # Environment variable template
```

## Database Models

### Core Models (9)

1. **User** - User accounts with authentication and role-based access control
2. **Session** - Active user sessions with token management
3. **AuditLog** - Immutable audit trail for HIPAA/GDPR compliance
4. **Project** - Shared workspaces for collaborative work
5. **ProjectMember** - Project membership and role assignments
6. **Task** - User assignments and task management
7. **Document** - Encrypted clinical documents (RTF/PDF)
8. **ExtractedEntity** - NLP extraction results from MedCAT
9. **Patient** - Aggregated patient records from extracted entities

### Module-Specific Models (2)

10. **PatientSearchResult** - Patient Search module
11. **TimelineView** - Timeline module

### Additional Models

12. **Module** - Installed system modules registry

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15
- Redis 7

### Installation

1. **Create virtual environment**:
   ```bash
   cd clinical-care-tools/backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # Or for development:
   pip install -e ".[dev]"
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and settings
   ```

4. **Initialize database**:
   ```bash
   # Apply all migrations
   alembic upgrade head
   ```

## Running the Application

```bash
# Development with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

## Database Migrations

### Creating a new migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Or manually create a migration
alembic revision -m "description of changes"
```

### Running migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# View current migration
alembic current
```

## Security & Compliance

### HIPAA/GDPR Features

- **Audit Logging**: All PHI access logged to immutable audit_logs table (7-year retention)
- **Encryption**: Documents encrypted at rest (AES-256)
- **Access Control**: RBAC with user roles (admin, clinician, researcher)
- **Session Management**: JWT tokens with expiration
- **PHI Tracking**: Automatic detection and classification of identifiable information

### Key Constraints

- **Users**: Email and username must be unique, role must be one of {admin, clinician, researcher}
- **Documents**: Maximum 10MB file size, encrypted content storage
- **Patients**: Must have either NHS number (10 digits) or MRN identifier
- **ExtractedEntities**: Confidence score must be 0.0 - 1.0
- **AuditLogs**: Immutable (no updates or deletes via database rules)

## Model Relationships

```
User
  ├── sessions (1:N) → Session
  ├── audit_logs (1:N) → AuditLog
  ├── projects_created (1:N) → Project
  ├── project_members (1:N) → ProjectMember
  ├── tasks_assigned (1:N) → Task
  └── documents_uploaded (1:N) → Document

Project
  ├── members (1:N) → ProjectMember
  ├── tasks (1:N) → Task
  ├── documents (1:N) → Document
  └── extracted_entities (1:N) → ExtractedEntity

Document
  └── extracted_entities (1:N) → ExtractedEntity

Patient
  (aggregates data from ExtractedEntity)
```

## API Endpoints (To be implemented)

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/users/me` - Current user profile
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/{id}` - Get document
- `GET /api/v1/extracted-entities/search` - Search entities
- `GET /api/v1/patients/search` - Patient search

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::test_user_creation
```

## Development Guidelines

### Code Style
- Follow PEP 8 with Black formatter (line length: 120)
- Use isort for import sorting
- Type hints required for all functions
- Use async/await for database operations

### Type Hints
```python
from typing import Optional, List
from uuid import UUID
from datetime import datetime

async def get_user(user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    pass
```

### Database Models
- All models inherit from `Base` in `app.models`
- Use `mapped_column()` for SQLAlchemy 2.0 syntax
- Add docstrings explaining purpose and relationships
- Include `__repr__()` for debugging

### Relationships
```python
# In parent model
children: Mapped[List["Child"]] = relationship(
    "Child",
    back_populates="parent",
    cascade="all, delete-orphan"
)

# In child model
parent: Mapped["Parent"] = relationship(
    "Parent",
    back_populates="children"
)
```

## Troubleshooting

### Database connection errors
- Verify PostgreSQL is running: `psql --version`
- Check DATABASE_URL in .env
- Ensure database exists: `createdb clinical_care_tools`

### Migration errors
- Check current migration: `alembic current`
- View migration history: `alembic history`
- Check database schema: `\dt` in psql

### Async issues
- Ensure all I/O operations use `async`/`await`
- Use `async_session_factory()` for database access
- Don't block the event loop

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
