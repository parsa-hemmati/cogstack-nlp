# Clinical Care Tools - Full-Stack Healthcare NLP Application

A comprehensive, modular platform leveraging MedCAT's Natural Language Processing capabilities to transform healthcare research, delivery, and governance.

## Quick Overview

**Clinical Care Tools** is a full-stack application built with:
- **Backend**: FastAPI (Python) with PostgreSQL & Redis
- **Frontend**: Vue 3 with TypeScript and Vuetify
- **NLP Engine**: CogStack MedCAT for medical concept extraction
- **Infrastructure**: Docker Compose for containerized deployment

### Key Features

- **Patient Search & Discovery**: Find patients by medical concepts with semantic search
- **Timeline Visualization**: Interactive timeline of patient clinical events
- **Document Upload & Processing**: Automatically extract medical concepts from clinical documents
- **Cohort Identification**: Build patient cohorts based on clinical criteria
- **FHIR Integration**: Export findings to FHIR-compliant EHR systems
- **Audit Logging**: Complete audit trail for regulatory compliance (HIPAA/GDPR)
- **Multi-User Access Control**: Role-based access control (RBAC) with user management

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Vue 3 Frontend (Port 8080)                   │
│                  Patient Interface & Dashboard                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/HTTPS
┌─────────────────────────▼───────────────────────────────────────┐
│              FastAPI Backend API (Port 8000)                     │
│           Authentication, Business Logic, Orchestration          │
└──────────┬──────────────┬──────────────┬────────────────────────┘
           │              │              │
        NLP API        Database      Cache
           │              │              │
┌──────────▼──────┐ ┌─────▼──────┐ ┌───▼────────────────┐
│  MedCAT Service │ │ PostgreSQL  │ │   Redis Cache      │
│   (Port 8001)   │ │ (Port 5432) │ │   (Port 6379)      │
│  Medical NLP    │ │  Patient    │ │  Sessions, Cache   │
│  Extraction     │ │   Records   │ │                    │
└─────────────────┘ └────────────┘ └────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (v20.10+)
- 8GB RAM minimum (16GB recommended)
- 50GB disk space for models and data
- Linux/macOS/Windows with WSL2

### Development Setup (5 minutes)

```bash
# Clone and navigate
git clone https://github.com/CogStack/clinical-care-tools.git
cd clinical-care-tools

# Copy environment variables
cp .env.example .env.development

# Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Access the application
# Frontend:  http://localhost:8080
# Backend API: http://localhost:8000/api/docs (Swagger UI)
# MedCAT Service: http://localhost:8001/api/health
```

### First Login

Default credentials (change immediately in production):
- **Username**: admin
- **Password**: admin123

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [SETUP.md](docs/SETUP.md) | Development environment setup | Developers |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment guide | DevOps/IT Admins |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design & components | Architects/Developers |
| [API.md](docs/API.md) | RESTful API documentation | Backend Developers |
| [SECURITY.md](docs/SECURITY.md) | Security model & compliance | Security Officers |
| [USER_GUIDE.md](docs/USER_GUIDE.md) | Clinical user workflows | Clinicians/Researchers |
| [backend/README.md](backend/README.md) | Backend-specific documentation | Backend Developers |
| [frontend/README.md](frontend/README.md) | Frontend-specific documentation | Frontend Developers |

## 🏥 Clinical Features

### Patient Search
Search for patients by medical concepts with confidence scores and filtering:
```
Search: "Type 2 Diabetes"
Results: 324 patients found
├─ Filter by: Negation Status, Temporality, Experiencer
├─ Confidence: 85-100%
└─ Export: CSV, FHIR, JSON
```

### Document Processing
Automatically extract medical entities from clinical documents:
- PDF, RTF, TXT support
- Real-time concept extraction
- Confidence scoring
- Temporal relationship tracking

### Timeline Visualization
Interactive timeline showing:
- Clinical events chronologically
- Document milestones
- Medication timelines
- Lab result trends

### Cohort Builder
Create patient cohorts with inclusion/exclusion criteria:
- Medical concepts
- Lab values
- Demographics
- Temporal constraints

## 🔐 Security & Compliance

- **HIPAA Compliance**: Encrypted at-rest (AES-256) and in-transit (TLS 1.3)
- **GDPR Compliance**: Data minimization, right to be forgotten, audit trails
- **21 CFR Part 11**: Audit logging for FDA compliance
- **Authentication**: JWT with refresh tokens
- **Authorization**: Role-Based Access Control (RBAC)
- **Audit Logging**: Complete audit trail for all PHI access

See [SECURITY.md](docs/SECURITY.md) for detailed security model.

## 📦 Services

### Core Services

| Service | Port | Purpose | Resource Limits |
|---------|------|---------|-----------------|
| PostgreSQL | 5432 | Patient data, audit logs | 4GB RAM |
| Redis | 6379 | Session cache, job queue | 2GB RAM, LRU eviction |
| MedCAT Service | 8001 | Medical NLP processing | 2-4GB RAM (configurable) |
| FastAPI Backend | 8000 | REST API, business logic | Auto-scaling (4-8 workers) |
| Vue 3 Frontend | 8080 | Web UI | 512MB RAM |

### Health Checks

All services include health checks:
```bash
# Check all services
docker-compose ps

# Manual health check
curl http://localhost:8000/api/health
curl http://localhost:8001/api/health
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/clinical_care_tools

# Redis
REDIS_URL=redis://redis:6379/0

# NLP Service
COGSTACK_MODELSERVE_URL=http://cogstack-modelserve:8001

# Security
SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_HOURS=8
JWT_REFRESH_DAYS=7

# Compliance
AUDIT_LOG_RETENTION_DAYS=2555  # 7 years for NHS
ENVIRONMENT=development|production
```

## 📊 Database Schema

The application uses PostgreSQL with the following main tables:

- `users` - User accounts and authentication
- `patients` - Patient demographic data
- `documents` - Clinical documents (RTF/PDF/TXT)
- `entities` - Extracted medical entities
- `audit_logs` - Complete audit trail
- `sessions` - User sessions (TTL)

See [DEPLOYMENT.md](docs/DEPLOYMENT.md#database-schema) for detailed schema.

## 🧪 Testing

```bash
# Backend tests (pytest)
cd backend
pytest tests/ -v --cov

# Frontend tests (Vitest)
cd frontend
npm run test

# E2E tests (Playwright)
cd frontend
npm run test:e2e

# Load testing
./scripts/load-test.sh
```

## 📈 Performance

Typical performance metrics:

| Operation | Response Time | Throughput |
|-----------|---------------|-----------|
| Patient search | <500ms | 100 req/s |
| Document upload (5MB) | <2s | 20 docs/s |
| Entity extraction | <100ms/page | 500 pages/s |
| Timeline rendering | <200ms | 100 patients/s |

See [DEPLOYMENT.md](docs/DEPLOYMENT.md#performance-tuning) for optimization guide.

## 🚀 Deployment

### Development
```bash
docker-compose up -d
# Access: http://localhost:8080
```

### Staging
```bash
./scripts/setup-dev.sh
```

### Production
```bash
./scripts/deploy-prod.sh
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## 🔄 Updates & Maintenance

### Backup Database
```bash
./scripts/backup-db.sh
```

### Restore Database
```bash
./scripts/restore-db.sh /path/to/backup.sql.gz
```

### Health Check
```bash
./scripts/health-check.sh
```

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs -f backend
docker-compose logs -f postgres

# Verify health
./scripts/health-check.sh
```

### Database Connection Errors
```bash
# Check PostgreSQL is running and healthy
docker-compose ps postgres

# Check credentials in .env
cat .env | grep DATABASE
```

### MedCAT Service Errors
```bash
# Check service logs
docker-compose logs -f cogstack-modelserve

# Verify models are mounted
docker-compose exec cogstack-modelserve ls -la /models
```

### Frontend Not Loading
```bash
# Check API connectivity
curl http://localhost:8000/api/health

# Check CORS settings
# Update CORS_ORIGINS in .env if needed
```

## 📞 Support & Contribution

- **Issues**: Report on [GitHub Issues](https://github.com/CogStack/clinical-care-tools/issues)
- **Discussions**: Join [GitHub Discussions](https://github.com/CogStack/clinical-care-tools/discussions)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [MedCAT](https://github.com/CogStack/MedCAT) - Medical Concept Annotation Tool
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Vue 3](https://vuejs.org/) - Progressive JavaScript framework
- [Vuetify](https://vuetifyjs.com/) - Vue component framework
- [PostgreSQL](https://www.postgresql.org/) - Reliable database
- [Redis](https://redis.io/) - High-performance caching
- [Docker](https://www.docker.com/) - Containerization

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

**Version**: 1.0.0
**Last Updated**: 2025-01-08
**Status**: Production Ready
