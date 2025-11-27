## Deployment Guide - Clinical Care Tools

**Version**: 0.2.0
**Last Updated**: 2025-11-18

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+) or macOS
- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 16GB minimum (32GB+ recommended)
- **Disk**: 100GB+ SSD
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Required Services

1. PostgreSQL 15+
2. Redis 7+
3. Elasticsearch 8+
4. MedCAT Service (separate container)

---

## Quick Start (Development)

### 1. Clone Repository

```bash
git clone https://github.com/CogStack/cogstack-nlp.git
cd cogstack-nlp/clinical-care-tools
```

### 2. Create Environment File

```bash
cp .env.template .env
```

**Edit `.env` with your settings:**

```env
# Application
APP_NAME="Clinical Care Tools"
APP_VERSION="0.2.0"
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here-change-in-production
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/clinical_care_tools
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=clinical_care_tools

# Redis
REDIS_URL=redis://localhost:6379/0

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=clinical_documents

# MedCAT
MEDCAT_SERVICE_URL=http://localhost:5000

# Security
CORS_ORIGINS=["http://localhost:5173", "http://localhost:8080"]
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Features
ENABLE_FHIR_EXPORT=false
ENABLE_CLINICAL_DECISION_SUPPORT=false
ENABLE_BREAK_GLASS_ACCESS=true
```

### 3. Start Services

```bash
docker-compose up -d
```

**Services started:**
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Elasticsearch: `localhost:9200`
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`

### 4. Run Database Migrations

```bash
cd backend
docker-compose exec backend alembic upgrade head
```

### 5. Create Admin User

```bash
docker-compose exec backend python scripts/create_admin.py
```

**Default credentials** (change immediately):
- Email: `admin@example.com`
- Password: `Admin123!`

### 6. Verify Installation

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "environment": "development"
}
```

---

## Production Deployment

### Security Checklist

**Before deploying to production:**

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Update default admin password
- [ ] Configure HTTPS/TLS (nginx reverse proxy recommended)
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Configure firewall (only expose 80/443)
- [ ] Enable audit logging
- [ ] Configure backup strategy
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure CORS for production domain
- [ ] Review HIPAA/GDPR compliance checklist

### Database Backup

**Automated daily backups:**

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * /path/to/scripts/backup_database.sh
```

**Manual backup:**

```bash
docker-compose exec postgres pg_dump -U postgres clinical_care_tools > backup_$(date +%Y%m%d).sql
```

**Restore:**

```bash
docker-compose exec -T postgres psql -U postgres clinical_care_tools < backup_20251118.sql
```

### Data Retention

**Automated data retention runs daily at 2:00 AM** (configurable via APScheduler):

- Documents >8 years: Deleted (unless legal hold)
- Audit logs >7 years: Deleted
- Sessions >90 days: Cleared

**Manual trigger** (admin only):

```bash
curl -X POST http://localhost:8000/api/v1/admin/data-retention/purge \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Monitoring

**Health check endpoint:**

```bash
curl http://localhost:8000/health
```

**Application metrics** (if enabled):

```bash
curl http://localhost:8000/metrics
```

**Key metrics to monitor:**

- API response time (p50, p95, p99)
- Error rate (5xx responses)
- Database connection pool usage
- Elasticsearch query performance
- MedCAT NLP processing time
- Audit log volume
- Critical finding alert rate

---

## Testing

### Run All Tests

```bash
cd backend
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

**View coverage report:**

```bash
open htmlcov/index.html
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific module
pytest tests/unit/services/test_data_retention.py
```

---

## Troubleshooting

### Database Connection Issues

**Error**: `could not connect to server: Connection refused`

**Solution**:

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### MedCAT Service Not Responding

**Error**: `Failed to connect to MedCAT service`

**Solution**:

```bash
# Check MedCAT container
docker-compose ps medcat-service

# Check model is loaded
docker-compose logs medcat-service | grep "Model loaded"

# Restart with model download
docker-compose up -d --force-recreate medcat-service
```

### Migration Fails

**Error**: `Target database is not up to date`

**Solution**:

```bash
# Check current revision
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Upgrade to latest
docker-compose exec backend alembic upgrade head
```

### Scheduler Not Running

**Error**: Data retention not purging old records

**Solution**:

```bash
# Check scheduler logs
docker-compose logs backend | grep "scheduler"

# Manual trigger
curl -X POST http://localhost:8000/api/v1/admin/data-retention/purge \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Run migrations
docker-compose exec backend alembic upgrade head

# Restart services
docker-compose restart
```

### Clear Redis Cache

```bash
docker-compose exec redis redis-cli FLUSHDB
```

### Reindex Elasticsearch

```bash
# Delete index
curl -X DELETE http://localhost:9200/clinical_documents

# Recreate index
python scripts/create_es_index.py

# Reindex documents
python scripts/reindex_documents.py
```

---

## Support

**Issues**: https://github.com/CogStack/cogstack-nlp/issues
**Documentation**: See `README.md` and `CONTEXT.md`
**Compliance**: See `docs/compliance/healthcare-compliance-framework.md`
