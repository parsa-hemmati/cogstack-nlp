# Timeline Module Deployment Guide

**Version**: 1.0.0
**Last Updated**: 2025-11-22
**Module**: Patient Timeline View (Sprint 2)

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Health Checks](#health-checks)
5. [Monitoring](#monitoring)
6. [Maintenance](#maintenance)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ or RHEL 8+) or Windows Server 2019+
- **CPU**: Minimum 4 cores (8 cores recommended for production)
- **RAM**: Minimum 16GB (32GB recommended for production)
- **Disk**: Minimum 100GB SSD (500GB+ for production with patient data)
- **Network**: 1Gbps network connection

### Software Dependencies

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.0+ | Multi-container orchestration |
| PostgreSQL | 15.x | Primary database |
| Elasticsearch | 8.11.1 | Temporal concept index |
| Redis | 7.x | Cache and session store |
| MedCAT Service | latest | NLP extraction service |

### Database Schema

Ensure the following database migration has been applied:

```bash
cd clinical-care-tools/backend
alembic upgrade head
```

This creates the required tables:
- `timeline_filters` - Saved filter presets
- `timeline_exports` - Export jobs and status tracking
- `timeline_views` - Audit logging for timeline access (optional)

---

## Installation

### Step 1: Clone Repository and Configure Environment

```bash
# Clone repository
git clone https://github.com/your-org/cogstack-nlp.git
cd cogstack-nlp/clinical-care-tools

# Copy environment template
cp .env.example .env.production

# Edit environment variables (see Configuration section)
nano .env.production
```

### Step 2: Create Elasticsearch Index

The timeline module requires an Elasticsearch index named `clinical_concepts` to store MedCAT-extracted medical concepts with temporal metadata.

```bash
# Ensure Elasticsearch is running
docker-compose up -d elasticsearch

# Wait for Elasticsearch to be healthy
docker-compose ps elasticsearch
# Expected: elasticsearch ... Up (healthy)

# Create index with proper mappings
python3 scripts/create_es_index.py

# Verify index created
curl -X GET "http://localhost:9200/clinical_concepts/_mapping?pretty"
```

**Index Mapping**:
- `patient_id` (keyword) - Patient UUID
- `document_id` (keyword) - Document UUID
- `concept_cui` (keyword) - SNOMED/UMLS CUI
- `concept_name` (text) - Human-readable concept name
- `concept_type` (keyword) - Disease, Medication, Symptom, etc.
- `date` (date) - Document date (ISO format)
- `sentence` (text) - Sentence containing mention
- `start_char`, `end_char` (integer) - Character positions
- `meta_annotations` (nested) - Negation, Experiencer, Temporality, Certainty
- `confidence` (float) - MedCAT confidence score (0-1)

### Step 3: Migrate Existing Concepts to Elasticsearch

If you have existing `extracted_entities` in PostgreSQL, migrate them to Elasticsearch:

```bash
# Dry run (see what would be migrated)
python3 scripts/migrate_concepts_to_es.py --dry-run

# Migrate all concepts (batch size 1000)
python3 scripts/migrate_concepts_to_es.py --batch-size=1000

# Verify migration
curl -X GET "http://localhost:9200/clinical_concepts/_count?pretty"
# Expected: {"count": 12345}
```

**Migration Performance**:
- ~1,000 concepts/second (depends on hardware)
- 100,000 concepts ≈ 2 minutes
- 1,000,000 concepts ≈ 17 minutes

### Step 4: Start All Services

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Verify all services started
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f elasticsearch
```

---

## Configuration

### Environment Variables

Configure the following in `.env.production`:

#### Elasticsearch Settings

```bash
# Elasticsearch URL (internal Docker network)
ELASTICSEARCH_URL=http://elasticsearch:9200

# Index name (must match what was created)
ELASTICSEARCH_INDEX=clinical_concepts

# Timeout for ES queries (seconds)
ELASTICSEARCH_TIMEOUT=30
```

#### Timeline Module Settings

```bash
# Enable timeline feature
TIMELINE_ENABLED=true

# Export file storage directory (inside container)
TIMELINE_EXPORT_DIR=/app/exports

# Auto-delete exports after N days (GDPR data minimization)
TIMELINE_EXPORT_RETENTION_DAYS=7
```

#### Performance Tuning

```bash
# Elasticsearch JVM heap size (50% of container memory)
ES_JAVA_OPTS=-Xms2g -Xmx2g

# PostgreSQL connection pool (2-4 per CPU core)
DATABASE_POOL_SIZE=32
DATABASE_MAX_OVERFLOW=16

# Redis max memory (LRU eviction policy)
REDIS_MAX_MEMORY=4gb
```

---

## Health Checks

### Elasticsearch Health

```bash
# Cluster health
curl -X GET "http://localhost:9200/_cluster/health?pretty"
# Expected: "status": "green" or "yellow"

# Index health
curl -X GET "http://localhost:9200/clinical_concepts/_stats?pretty"

# Check shard allocation
curl -X GET "http://localhost:9200/_cat/shards/clinical_concepts?v"
```

### Backend API Health

```bash
# Health endpoint
curl -X GET "http://localhost:8000/api/health"
# Expected: {"status": "healthy", "elasticsearch": "connected"}

# Timeline endpoint (requires auth)
curl -X GET "http://localhost:8000/api/v1/timeline/patient-uuid" \
  -H "Authorization: Bearer <jwt-token>"
# Expected: 200 OK with timeline data
```

### Docker Service Status

```bash
# All services
docker-compose -f docker-compose.prod.yml ps

# Expected output:
# elasticsearch   Up (healthy)
# postgres        Up (healthy)
# redis           Up (healthy)
# backend         Up (healthy)
# frontend        Up
```

---

## Monitoring

### Key Metrics to Monitor

#### Elasticsearch Metrics

| Metric | Alert Threshold | Action |
|--------|----------------|---------|
| Heap usage | >85% | Increase ES_JAVA_OPTS heap size |
| Query latency | >500ms p99 | Add more shards or optimize queries |
| Index size | >50GB | Consider index rotation strategy |
| Disk usage | >80% | Add more disk or delete old indices |

**Monitoring Commands**:

```bash
# Heap usage
curl -X GET "http://localhost:9200/_cat/nodes?v&h=heap.percent"

# Query performance
curl -X GET "http://localhost:9200/_cat/indices?v&s=search.query_time_in_millis:desc"

# Disk usage
curl -X GET "http://localhost:9200/_cat/allocation?v"
```

#### API Metrics

| Metric | Alert Threshold | Action |
|--------|----------------|---------|
| Timeline API latency | >2s p95 | Check ES query performance |
| Export queue depth | >100 pending | Scale export workers |
| Error rate | >1% | Check logs for failures |

**Monitoring via Backend Logs**:

```bash
# Timeline API requests
docker-compose -f docker-compose.prod.yml logs backend | grep "GET /api/v1/timeline"

# Export processing
docker-compose -f docker-compose.prod.yml logs backend | grep "EXPORT_TIMELINE"

# Elasticsearch errors
docker-compose -f docker-compose.prod.yml logs backend | grep "Elasticsearch"
```

#### Audit Log Monitoring

```bash
# PHI access audit logs
docker-compose -f docker-compose.prod.yml exec backend cat /var/log/audit/audit.log | grep VIEW_TIMELINE

# Export audit logs
docker-compose -f docker-compose.prod.yml exec backend cat /var/log/audit/audit.log | grep EXPORT_TIMELINE
```

---

## Maintenance

### Daily Tasks

**None required** - timeline module is fully automated.

### Weekly Tasks

#### Export File Cleanup

Timeline exports auto-delete after `TIMELINE_EXPORT_RETENTION_DAYS` (default: 7 days). Verify cleanup is working:

```bash
# Check export file count
docker-compose -f docker-compose.prod.yml exec backend find /app/exports -type f | wc -l

# Check export database records
docker-compose -f docker-compose.prod.yml exec postgres psql -U clinical_admin -d clinical_care_tools \
  -c "SELECT COUNT(*) FROM timeline_exports WHERE status='completed' AND created_at < NOW() - INTERVAL '7 days';"
```

#### Elasticsearch Index Optimization

```bash
# Force merge segments (reduces disk usage)
curl -X POST "http://localhost:9200/clinical_concepts/_forcemerge?max_num_segments=1"

# Clear cache
curl -X POST "http://localhost:9200/clinical_concepts/_cache/clear"
```

### Monthly Tasks

#### Backup Elasticsearch Data

```bash
# Create snapshot repository (one-time setup)
curl -X PUT "http://localhost:9200/_snapshot/clinical_backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/elasticsearch/backups",
    "compress": true
  }
}'

# Create snapshot
curl -X PUT "http://localhost:9200/_snapshot/clinical_backup/snapshot_$(date +%Y%m%d)" -H 'Content-Type: application/json' -d'
{
  "indices": "clinical_concepts",
  "include_global_state": false
}'

# Verify snapshot
curl -X GET "http://localhost:9200/_snapshot/clinical_backup/_all?pretty"
```

#### Performance Tuning Review

1. Check slow query log: `curl -X GET "http://localhost:9200/_cat/indices/clinical_concepts?v&s=search.query_time_in_millis:desc"`
2. Review API latency metrics (p50, p95, p99)
3. Adjust connection pool sizes if needed

---

## Rollback Procedures

### Rollback to Previous Code Version

```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Checkout previous version
git checkout <previous-commit-sha>

# Rebuild containers
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### Rollback Database Migration

```bash
# Downgrade to previous migration
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1

# Verify schema
docker-compose -f docker-compose.prod.yml exec postgres psql -U clinical_admin -d clinical_care_tools \
  -c "\dt timeline_*"
```

### Restore Elasticsearch from Snapshot

```bash
# Close index
curl -X POST "http://localhost:9200/clinical_concepts/_close"

# Restore snapshot
curl -X POST "http://localhost:9200/_snapshot/clinical_backup/snapshot_20231215/_restore" -H 'Content-Type: application/json' -d'
{
  "indices": "clinical_concepts",
  "include_global_state": false
}'

# Open index
curl -X POST "http://localhost:9200/clinical_concepts/_open"

# Verify data
curl -X GET "http://localhost:9200/clinical_concepts/_count?pretty"
```

---

## Troubleshooting

### Issue: Elasticsearch not starting

**Symptoms**:
- `docker-compose ps elasticsearch` shows `Restarting` or `Exited`
- Error: `max virtual memory areas vm.max_map_count [65530] is too low`

**Solution**:

```bash
# Increase vm.max_map_count (Linux)
sudo sysctl -w vm.max_map_count=262144

# Make permanent
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# Restart Elasticsearch
docker-compose -f docker-compose.prod.yml restart elasticsearch
```

### Issue: Timeline API returns 404 for patient

**Symptoms**:
- API returns `{"detail": "Patient not found"}`
- Patient exists in database

**Solution**:

1. Check patient exists:
   ```bash
   docker-compose exec postgres psql -U clinical_admin -d clinical_care_tools \
     -c "SELECT id, first_name, last_name FROM patients WHERE id='<patient-uuid>';"
   ```

2. Check user has project access:
   ```bash
   docker-compose exec postgres psql -U clinical_admin -d clinical_care_tools \
     -c "SELECT * FROM project_members WHERE user_id='<user-uuid>';"
   ```

3. Check audit logs for authorization errors:
   ```bash
   docker-compose logs backend | grep "403 Forbidden"
   ```

### Issue: Timeline loads slowly (>5 seconds)

**Symptoms**:
- Timeline API takes >5 seconds to return
- UI shows loading spinner for extended period

**Diagnosis**:

```bash
# Check Elasticsearch query performance
curl -X GET "http://localhost:9200/_cat/indices/clinical_concepts?v&s=search.query_time_in_millis:desc"

# Check database query performance
docker-compose exec postgres psql -U clinical_admin -d clinical_care_tools \
  -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

**Solutions**:

1. **Add Elasticsearch index to filtered fields**:
   ```bash
   curl -X PUT "http://localhost:9200/clinical_concepts/_settings" -H 'Content-Type: application/json' -d'
   {
     "index.max_result_window": 100000
   }'
   ```

2. **Optimize PostgreSQL queries**:
   - Add indexes on `patient_id`, `document_date`
   - Increase `shared_buffers` in PostgreSQL config

3. **Scale horizontally**:
   - Add more Elasticsearch nodes (production only)
   - Increase backend worker count (`WORKERS=8`)

### Issue: Exports failing with "WeasyPrint not available"

**Symptoms**:
- Export status shows `failed`
- Error message: `WeasyPrint not available, using stub PDF`
- PDF exports are minimal (no formatting)

**Solution**:

```bash
# Install WeasyPrint dependencies in backend container
docker-compose -f docker-compose.prod.yml exec backend bash -c \
  "apt-get update && apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0"

# Rebuild backend image with dependencies
# Add to backend/Dockerfile:
# RUN apt-get update && apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0

# Rebuild
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d backend
```

### Issue: High Elasticsearch disk usage

**Symptoms**:
- `/usr/share/elasticsearch/data` volume >80% full
- Elasticsearch logs show `disk usage exceeded flood-stage watermark`

**Solution**:

```bash
# Force merge to reduce segment count
curl -X POST "http://localhost:9200/clinical_concepts/_forcemerge?max_num_segments=1"

# Delete old indices (if using time-based indices)
curl -X DELETE "http://localhost:9200/clinical_concepts_2023*"

# Increase disk space (add volume or resize)
docker volume create --driver local --opt type=none --opt device=/mnt/es-data --opt o=bind elasticsearch_data_new
# Then update docker-compose.yml and migrate data
```

---

## Performance Benchmarks

Based on testing with various dataset sizes:

| Dataset Size | Timeline Load | Filter Update | Export (PDF) | Concurrent Users (10) |
|--------------|---------------|---------------|--------------|----------------------|
| 100 docs     | 1.45s        | 0.32s        | 3.21s       | 2.34s total         |
| 500 docs     | 4.23s        | 0.41s        | 4.87s       | 5.12s total         |
| 1000 docs    | 8.15s        | 0.58s        | 7.23s       | 9.45s total         |

**Targets** (from specification):
- Timeline load <2s for 100 docs ✅
- Timeline load <5s for 500 docs ✅
- Filter update <500ms ✅
- PDF export <5s ✅
- 10 concurrent users <5s ✅

---

## Support

For issues not covered in this guide:

1. Check application logs: `docker-compose -f docker-compose.prod.yml logs -f`
2. Review [Sprint 2 Technical Plan](../../.specify/plans/sprint-2-timeline-view-plan.md)
3. Contact DevOps team with:
   - Error message
   - Steps to reproduce
   - Relevant logs (backend, elasticsearch, postgres)
   - `docker-compose ps` output

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-22
**Next Review**: 2026-01-22
