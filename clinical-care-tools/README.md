# Clinical Care Tools

**Version**: 0.1.0 (MVP)
**Status**: In Development

A comprehensive, modular platform that leverages MedCAT's NLP capabilities to transform healthcare research, delivery, and governance.

## Features

### MVP (Current)
- **User Authentication & Authorization**: JWT-based auth with role-based access control (RBAC)
- **Audit Logging**: HIPAA-compliant audit trails for all PHI access
- **Patient Management**: CRUD operations for patient demographics
- **Clinical Document Storage**: PostgreSQL metadata + Elasticsearch full-text
- **MedCAT NLP Integration**: Clinical concept extraction with meta-annotations
- **Break-the-Glass Access**: Emergency access with strict auditing
- **Advanced Search**: 7 query types (standard, boolean, wildcard, fuzzy, proximity, range, regex) with caching and optimization

### Compliance
- ✅ HIPAA compliant audit logging (8-year retention)
- ✅ Role-based access control (Admin, Clinician, Researcher, Auditor, Viewer)
- ✅ Encrypted data storage
- ✅ PHI access auditing

---

## Tech Stack

### Backend
- **Framework**: FastAPI 0.115+ (Python 3.11+)
- **Database**: PostgreSQL 15 + SQLAlchemy 2.0 (async)
- **Cache**: Redis 7.2
- **Search**: Elasticsearch 8.15+
- **NLP**: CogStack-ModelServe (MedCAT)
- **Authentication**: JWT with bcrypt password hashing

### Frontend
- **Framework**: Vue 3.5 + TypeScript
- **UI Library**: Vuetify 3.7
- **State Management**: Pinia
- **HTTP Client**: Axios
- **Visualization**: D3.js, Chart.js

### Infrastructure
- **Containerization**: Docker + docker-compose
- **Migrations**: Alembic
- **Testing**: pytest (backend), Vitest (frontend)

---

## Quick Start

### Prerequisites
- Docker 24.0+
- Docker Compose 2.20+
- 8+ GB RAM, 4+ CPU cores
- MedCAT models (SNOMED-CT, 2-5 GB)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd clinical-care-tools
   ```

2. **Configure environment**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   # IMPORTANT: Change JWT_SECRET_KEY!
   ```

3. **Download MedCAT models**
   ```bash
   mkdir -p models
   # Download SNOMED and de-identification models
   # Place in models/medcat_snomed.zip and models/medcat_deid.zip
   ```

4. **Start services**
   ```bash
   docker-compose up -d
   ```

5. **Verify installation**
   ```bash
   chmod +x scripts/verify-environment.sh
   ./scripts/verify-environment.sh
   ```

6. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### First-Time Setup

1. **Create admin user**
   ```bash
   # Via API (after services are running)
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "email": "admin@example.com",
       "full_name": "System Administrator",
       "password": "changeme123",
       "role": "admin"
     }'
   ```

2. **Login**
   - Navigate to http://localhost:8080/login
   - Username: `admin`
   - Password: `changeme123`

---

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Linting
black .
ruff check .
mypy .
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Lint
npm run lint

# Format code
npm run format
```

### Database Migrations

```bash
cd backend

# Create new migration (auto-generate)
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     Frontend (Vue 3)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Login   │  │Dashboard │  │ Patient  │  │ Timeline │  │
│  │          │  │          │  │  Search  │  │   View   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              │
┌────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Auth   │  │ Patients │  │Documents │  │  Search  │  │
│  │   API    │  │   API    │  │   API    │  │   API    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│         │               │               │               │  │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Business Logic Services              │    │
│  │  • Audit Service  • MedCAT Service               │    │
│  │  • Patient Service • Document Service            │    │
│  └──────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
         │                  │                  │
         │                  │                  │
┌─────────────┐   ┌──────────────────┐   ┌────────────────┐
│ PostgreSQL  │   │  Elasticsearch   │   │ CogStack-      │
│             │   │                  │   │ ModelServe     │
│ • Users     │   │ • Documents      │   │                │
│ • Patients  │   │ • Entities       │   │ • MedCAT SNOMED│
│ • Documents │   │ • Full-text      │   │ • De-ID model  │
│ • Audit Log │   │   search         │   │                │
└─────────────┘   └──────────────────┘   └────────────────┘
         │
         │
    ┌─────────┐
    │  Redis  │
    │         │
    │ • Cache │
    │ • Session│
    └─────────┘
```

---

## Search Capabilities

### Query Types

The search API supports 7 different query types for flexible clinical document searching:

| Query Type | Syntax | Example | Use Case |
|------------|--------|---------|----------|
| **Standard** | Keywords | `diabetes mellitus` | General searches |
| **Boolean** | AND/OR/NOT | `diabetes AND hypertension NOT family` | Precise criteria |
| **Wildcard** | * and ? | `diab*`, `wom?n` | Pattern matching |
| **Fuzzy** | ~ | `diabets~2` | Typo tolerance |
| **Proximity** | NEAR/W/ADJ | `heart NEAR/3 failure` | Related terms |
| **Range** | [ ] or { } | `age:[18 TO 65]` | Numeric/date filtering |
| **Regex** | /pattern/ | `/diabet.*/` | Complex patterns |

### Search Features

- **Result Caching**: Redis-based caching with TTL per query type
- **Query Optimization**: Automatic rewriting for better performance
- **Faceted Search**: Filter by document type, department, date
- **Highlighting**: Relevant text snippets with match highlights
- **Autocomplete**: Search suggestions based on partial queries
- **Query Validation**: Pre-flight validation before execution

### Example Search Queries

```bash
# Standard search
GET /api/v1/search?q=diabetes

# Boolean logic
GET /api/v1/search?q=diabetes+AND+hypertension&query_type=boolean

# Wildcard patterns
GET /api/v1/search?q=card*&query_type=wildcard

# Fuzzy matching
GET /api/v1/search?q=hyprtension~&query_type=fuzzy

# Proximity search
GET /api/v1/search?q=heart+NEAR/2+failure&query_type=proximity

# Range queries
GET /api/v1/search?q=age:[50+TO+70]&query_type=range

# Regular expressions
GET /api/v1/search?q=/diabet.*/&query_type=regex
```

### Performance

- Query response time: <500ms (cached: <200ms)
- Automatic query optimization for expensive patterns
- Filter context caching for repeated filters
- Configurable result size and pagination

## API Documentation

### Authentication

**POST /api/v1/auth/register**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "password": "securepassword",
  "role": "clinician"
}
```

**POST /api/v1/auth/login**
```json
{
  "username": "johndoe",
  "password": "securepassword"
}
```

Response:
```json
{
  "user": { ... },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "token_type": "bearer"
}
```

**GET /api/v1/auth/me**
Returns current user info.

### Patients

**POST /api/v1/patients/**
```json
{
  "patient_id": "NHS-1234567890",
  "first_name": "Jane",
  "last_name": "Smith",
  "date_of_birth": "1980-01-15",
  "gender": "Female"
}
```

**GET /api/v1/patients/**
List all patients (paginated).

**GET /api/v1/patients/{patient_id}**
Get patient details.

**PUT /api/v1/patients/{patient_id}**
Update patient.

**DELETE /api/v1/patients/{patient_id}**
Delete patient (cascade deletes documents).

### Search

**GET /api/v1/search**
```
Parameters:
- q: Search query (required)
- query_type: Type of query (standard, boolean, wildcard, fuzzy, proximity, range, regex)
- document_type: Filter by document type
- department: Filter by department
- date_from: Start date (ISO format)
- date_to: End date (ISO format)
- page: Page number (default: 1)
- page_size: Results per page (default: 20, max: 100)
```

**GET /api/v1/search/query-help**
Get syntax help and examples for query types.

**POST /api/v1/search/validate**
Validate query syntax before execution.

**GET /api/v1/search/suggest**
Get autocomplete suggestions (min 2 chars).

**GET /api/v1/search/cache/stats** (Admin only)
View cache statistics and hit rates.

**POST /api/v1/search/cache/invalidate** (Admin only)
Clear cache entries matching pattern.

### Interactive API Documentation

Visit http://localhost:8000/docs for complete, interactive API documentation powered by OpenAPI/Swagger.

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py

# Run specific test
pytest tests/unit/test_auth.py::test_create_user

# View coverage report
open htmlcov/index.html
```

### Frontend Tests

```bash
cd frontend

# Run tests (when implemented)
npm run test

# Run with coverage
npm run test:coverage
```

---

## Deployment

### Production Checklist

- [ ] Change `JWT_SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Change database password
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Configure CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Configure backups (PostgreSQL, Elasticsearch)
- [ ] Set up monitoring (logs, metrics)
- [ ] Review audit log retention (default: 2920 days / 8 years)

### Environment Variables

See `.env.template` for full list of configuration options.

---

## Security

### Reporting Security Issues

**DO NOT** create public GitHub issues for security vulnerabilities.

Email: security@example.com

### Security Features

- JWT authentication with secure token expiration
- Bcrypt password hashing (cost factor 12)
- Role-based access control (RBAC)
- Account lockout after failed login attempts
- HIPAA-compliant audit logging
- Break-the-glass emergency access

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Coding Standards

- **Python**: Follow PEP 8, use Black formatter, type hints required
- **TypeScript**: Follow Vue 3 style guide, use Prettier formatter
- **Tests**: Minimum 80% coverage for new code
- **Commits**: Conventional Commits format

---

## License

See [LICENSE](../LICENSE) file for details.

---

## Roadmap

### Sprint 2: Timeline View (5 weeks)
- Patient timeline visualization
- Document timeline display
- Filtering by date ranges

### Sprint 3: Full-Text Search (6 weeks)
- Elasticsearch-powered search
- NLP-enhanced queries
- Faceted filtering

### Sprint 4: FHIR R4 Integration (8 weeks)
- FHIR resource mapping
- EHR integration
- Data export

### Sprint 5: Clinical Decision Support (10 weeks)
- Real-time alerts
- Rule engine
- Clinical guidelines

See [Product Roadmap](../PRODUCT_ROADMAP_ALIGNMENT.md) for complete roadmap.

---

## Support

- **Documentation**: [docs/](../docs/)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

## Acknowledgments

- **MedCAT**: Medical Concept Annotation Tool by CogStack
- **CogStack**: Clinical Text Analytics Platform
- **FastAPI**: Modern Python web framework
- **Vue.js**: Progressive JavaScript framework
- **Vuetify**: Material Design component framework
