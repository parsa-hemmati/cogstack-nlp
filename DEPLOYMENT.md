# Production Deployment Guide

This guide covers deploying CogStack NLP platform to production environments.

**Target Audience**: DevOps engineers, system administrators, IT operations teams

**Version**: 1.0.0
**Last Updated**: 2025-11-22

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Database Setup](#database-setup)
5. [Application Deployment](#application-deployment)
6. [Configuration](#configuration)
7. [Security Hardening](#security-hardening)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup & Disaster Recovery](#backup--disaster-recovery)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance](#maintenance)

---

## System Requirements

### Hardware

**Minimum Configuration**:
- **CPU**: 8 cores (2.0 GHz or faster)
- **RAM**: 32 GB
- **Storage**: 500 GB SSD (initial), scales with document volume
- **Network**: 1 Gbps connection

**Recommended Configuration** (for production):
- **CPU**: 16+ cores (2.5 GHz or faster)
- **RAM**: 64 GB
- **Storage**: 2 TB+ SSD with RAID-1 mirroring
- **Network**: 10 Gbps redundant connections

### Software

**Operating System**:
- Ubuntu 22.04 LTS or later
- RHEL 9+ / CentOS 9+
- Debian 12+

**Container Runtime**:
- Docker CE 24.0+
- Docker Compose 2.20+
- (Optional) Kubernetes 1.26+

**Required Services**:
- PostgreSQL 15.0+
- Redis 7.0+
- Elasticsearch 8.10+
- MedCAT Service 2.2.0+

---

## Pre-Deployment Checklist

### Security
- [ ] SSL/TLS certificates obtained and validated
- [ ] Network security groups configured (firewall rules)
- [ ] VPN access to production environment established
- [ ] SSH key pairs generated for server access
- [ ] Secrets management solution ready (Vault, AWS Secrets Manager, etc.)

### Compliance
- [ ] HIPAA compliance validation completed
- [ ] GDPR data processing agreement signed
- [ ] 21 CFR Part 11 audit trail requirements verified
- [ ] Data residency requirements confirmed
- [ ] Encryption algorithm approval documented

### Infrastructure
- [ ] Load balancer configured (nginx/HAProxy)
- [ ] Database backup solution tested
- [ ] Monitoring and logging infrastructure ready
- [ ] CDN configured for static assets (optional)
- [ ] DNS records created and verified

### Documentation
- [ ] Network topology documented
- [ ] Database schema backed up
- [ ] API documentation reviewed
- [ ] Incident response procedures documented
- [ ] On-call rotation established

### Testing
- [ ] Load testing completed (100+ concurrent users)
- [ ] Failover testing successful
- [ ] Database recovery tested
- [ ] Backup restoration tested
- [ ] Security scanning completed (OWASP, dependency scanning)

---

## Infrastructure Setup

### Docker Compose Deployment (Single Server)

**Best for**: Dev/staging environments or small production deployments

1. **Install Dependencies**:
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

2. **Clone Repository**:
```bash
git clone https://github.com/CogStack/cogstack-nlp.git
cd cogstack-nlp
```

3. **Create Environment File**:
```bash
cp .env.example .env
# Edit .env with production values (see Configuration section)
```

4. **Start Services**:
```bash
# Build images
docker-compose build

# Start services in background
docker-compose up -d

# Verify services running
docker-compose ps
```

5. **Initialize Database**:
```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.scripts.create_indexes
```

### Kubernetes Deployment (Scalable)

**Best for**: High-availability production environments

1. **Prerequisites**:
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

2. **Add Helm Repository**:
```bash
helm repo add cogstack https://charts.cogstack.org
helm repo update
```

3. **Create Namespace**:
```bash
kubectl create namespace cogstack-nlp
```

4. **Deploy Using Helm**:
```bash
helm install cogstack-nlp cogstack/cogstack-nlp \
  --namespace cogstack-nlp \
  --values production-values.yaml
```

5. **Verify Deployment**:
```bash
# Check pod status
kubectl get pods -n cogstack-nlp

# Check services
kubectl get svc -n cogstack-nlp

# Check logs
kubectl logs -n cogstack-nlp deployment/cogstack-nlp-backend
```

---

## Database Setup

### PostgreSQL Configuration

1. **Create Database**:
```bash
createdb cogstack_nlp
```

2. **Run Migrations**:
```bash
cd backend
alembic upgrade head
```

3. **Create Indexes**:
```bash
# The following indexes are created during migrations:
# - users (username, email)
# - audit_logs (user_id, resource_type, created_at)
# - documents (patient_id, created_at)
# - entities (document_id, cui, confidence)
# - patients (nhs_number, created_at)
```

4. **Performance Tuning**:
```sql
-- Update PostgreSQL configuration for production
ALTER SYSTEM SET shared_buffers = '16GB';
ALTER SYSTEM SET effective_cache_size = '48GB';
ALTER SYSTEM SET maintenance_work_mem = '4GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
SELECT pg_reload_conf();
```

5. **Backup Configuration**:
```bash
# Create backup user
createuser backup_user;

# Configure daily backups in cron
0 2 * * * pg_dump -h localhost -U postgres -d cogstack_nlp | gzip > /backups/cogstack_nlp_$(date +\%Y\%m\%d).sql.gz
```

### Elasticsearch Configuration

1. **Create Indexes**:
```bash
python backend/scripts/create_indexes.py
```

2. **Index Mappings**:
```python
# Backend creates 4 indexes:
# - documents (full-text clinical documents)
# - entities (extracted medical concepts)
# - audit_logs (HIPAA-compliant audit trail)
# - deidentified_notes (de-identified text)
```

3. **Performance Settings**:
```bash
# Configure Elasticsearch heap size
export ES_JAVA_OPTS="-Xms16g -Xmx16g"

# Update JVM settings for production
# In /etc/elasticsearch/jvm.options:
# -Xms16g
# -Xmx16g
```

4. **Backup Configuration**:
```bash
# Register snapshot repository
curl -X PUT "localhost:9200/_snapshot/daily_backups" \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/var/backups/elasticsearch"
    }
  }'

# Create daily snapshots
0 3 * * * curl -X PUT "localhost:9200/_snapshot/daily_backups/daily_$(date +\%Y\%m\%d)?wait_for_completion=true"
```

### Redis Configuration

1. **Configure Redis**:
```bash
# Edit /etc/redis/redis.conf
requirepass production_password_here
maxmemory 8gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
```

2. **Start Redis**:
```bash
sudo systemctl restart redis-server
```

3. **Verify**:
```bash
redis-cli ping
# Should return: PONG
```

---

## Application Deployment

### Backend Deployment

1. **Install Python Dependencies**:
```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install gunicorn uvicorn
```

2. **Run Migrations**:
```bash
cd backend
alembic upgrade head
```

3. **Create Systemd Service** (`/etc/systemd/system/cogstack-nlp-backend.service`):
```ini
[Unit]
Description=CogStack NLP Backend API
After=network.target postgresql.service

[Service]
Type=notify
User=cogstack
WorkingDirectory=/opt/cogstack-nlp/backend
Environment="PATH=/opt/cogstack-nlp/venv/bin"
Environment="PYTHONPATH=/opt/cogstack-nlp/backend"
ExecStart=/opt/cogstack-nlp/venv/bin/gunicorn \
  --workers 8 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/cogstack-nlp/access.log \
  --error-logfile /var/log/cogstack-nlp/error.log \
  app.main:app

Restart=always
RestartSec=10s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

4. **Start Service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cogstack-nlp-backend
sudo systemctl start cogstack-nlp-backend
```

### Frontend Deployment

1. **Build Production Bundle**:
```bash
cd frontend
npm install
npm run build
# Creates dist/ directory
```

2. **Configure nginx** (`/etc/nginx/sites-available/cogstack-nlp`):
```nginx
server {
    listen 80;
    server_name api.cogstack.org;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.cogstack.org;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/api.cogstack.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.cogstack.org/privkey.pem;
    ssl_protocols TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # Frontend
    location / {
        root /var/www/cogstack-nlp;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API reverse proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

3. **Deploy Frontend**:
```bash
sudo cp -r dist/* /var/www/cogstack-nlp/
sudo chown -R www-data:www-data /var/www/cogstack-nlp
```

4. **Enable nginx**:
```bash
sudo ln -s /etc/nginx/sites-available/cogstack-nlp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Configuration

### Environment Variables

Create `.env` file with the following configuration:

```bash
# === Database ===
DATABASE_URL=postgresql://user:password@localhost:5432/cogstack_nlp
SQLALCHEMY_ECHO=false

# === Redis ===
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# === Elasticsearch ===
ELASTICSEARCH_URL=http://localhost:9200
ES_INDEX_PREFIX=cogstack

# === Security ===
SECRET_KEY=generate_strong_random_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# === CORS ===
CORS_ORIGINS=["https://api.cogstack.org"]
CORS_CREDENTIALS=true
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]

# === MedCAT Service ===
MEDCAT_SERVICE_URL=http://localhost:5000
MEDCAT_API_KEY=your_medcat_api_key

# === Celery ===
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379

# === Logging ===
LOG_LEVEL=INFO
LOG_FORMAT=json

# === Email ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@cogstack.org

# === Sentry (Error Tracking) ===
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0

# === Feature Flags ===
FEATURE_TIMELINE=true
FEATURE_SEARCH=true
FEATURE_DEIDENTIFICATION=true
FEATURE_ANALYTICS=false

# === HIPAA Compliance ===
AUDIT_LOG_RETENTION_YEARS=8
ENCRYPT_AT_REST=true
ENCRYPTION_ALGORITHM=AES-256-GCM
```

### Database Migrations

```bash
# View current schema version
cd backend && alembic current

# Apply all pending migrations
alembic upgrade head

# Rollback to previous version (emergency only)
alembic downgrade -1
```

---

## Security Hardening

### Network Security

1. **Firewall Rules**:
```bash
# Allow only necessary ports
sudo ufw enable
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 5432/tcp   # PostgreSQL (from local only)
sudo ufw allow 6379/tcp   # Redis (from local only)
sudo ufw allow 9200/tcp   # Elasticsearch (from local only)
```

2. **SSL/TLS Configuration**:
```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Or use Let's Encrypt (recommended for production)
sudo apt-get install certbot
sudo certbot certonly --standalone -d api.cogstack.org
```

3. **VPN Configuration**:
   - Configure bastion host for SSH access
   - Use VPN for database and cache layer access
   - Implement network segmentation (DMZ, internal networks)

### Application Security

1. **Secrets Management**:
```bash
# Never commit secrets to git
echo ".env" >> .gitignore

# Use HashiCorp Vault for secret management
vault kv put secret/cogstack-nlp \
  DATABASE_URL="postgresql://..." \
  SECRET_KEY="..." \
  MEDCAT_API_KEY="..."
```

2. **HIPAA Compliance**:
```bash
# Enable encryption at rest
# Configure AES-256-GCM for all sensitive fields

# Enable audit logging
# All PHI access must be logged with user, timestamp, action

# Configure 8-year retention
# Ensure audit logs retained per HIPAA requirements
```

3. **Input Validation**:
   - All user inputs validated server-side
   - SQL injection prevention via parameterized queries
   - XSS protection via output encoding
   - CSRF tokens for state-changing operations

4. **Authentication & Authorization**:
```bash
# JWT token configuration
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password requirements
# Minimum 12 characters
# Require special characters, numbers, uppercase

# MFA (optional but recommended)
# Configure 2FA for admin accounts
```

---

## Monitoring & Logging

### Application Monitoring

1. **Health Checks**:
```bash
curl http://localhost:8000/api/v1/health

# Response
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "services": {
    "database": "connected",
    "redis": "connected",
    "elasticsearch": "connected"
  }
}
```

2. **Prometheus Metrics**:
```bash
# Endpoint: /metrics
curl http://localhost:8000/metrics

# Metrics include:
# - HTTP request latency (p50, p95, p99)
# - Database query count and latency
# - Celery task queue depth
# - Cache hit rate
```

3. **APM (Application Performance Monitoring)**:
```bash
# Configure Datadog (or Sentry, NewRelic)
DD_TRACE_ENABLED=true
DD_SERVICE=cogstack-nlp
DD_ENVIRONMENT=production
```

### Logging Configuration

1. **Structured Logging** (JSON format):
```json
{
  "timestamp": "2025-11-22T15:30:00Z",
  "level": "INFO",
  "logger": "app.api.endpoints.search",
  "message": "Patient search executed",
  "user_id": "user-123",
  "patient_id": "pat-456",
  "query": "diabetes",
  "result_count": 42,
  "duration_ms": 150
}
```

2. **Centralized Logging** (ELK Stack):
```bash
# Configure Elasticsearch for log storage
# Configure Kibana for log visualization
# Configure Filebeat for log shipping

# Query logs in Kibana
GET /logs-cogstack-nlp-*/_search
{
  "query": {
    "match": {
      "level": "ERROR"
    }
  }
}
```

3. **Log Retention**:
```bash
# Application logs: 30 days
# Audit logs: 8 years (HIPAA requirement)
# Access logs: 90 days
```

### Alerting

1. **Critical Alerts**:
```yaml
- Alert: Database Connection Failed
  Condition: postgres.connection_pool.available == 0
  Action: Page on-call engineer

- Alert: Elasticsearch Cluster Red
  Condition: elasticsearch.cluster.health.status == "red"
  Action: Page on-call engineer

- Alert: High Error Rate
  Condition: http_request_error_rate > 0.05 (5%)
  Action: Warn in Slack #oncall

- Alert: High Latency
  Condition: http_request_p95_latency > 5000ms
  Action: Warn in Slack #oncall
```

2. **Monitoring Dashboard** (Grafana):
   - Request rate and latency
   - Error rate and types
   - Database pool utilization
   - Redis memory usage
   - Elasticsearch cluster health
   - Application uptime
   - User activity patterns

---

## Backup & Disaster Recovery

### Backup Strategy

1. **Database Backups**:
```bash
# Daily full backups
0 2 * * * pg_dump -h localhost -U postgres -d cogstack_nlp | \
  gzip > /backups/db/cogstack_nlp_$(date +\%Y\%m\%d).sql.gz

# Weekly backup to S3
0 3 * * 0 aws s3 cp /backups/db/cogstack_nlp_$(date +\%Y\%m\%d).sql.gz \
  s3://cogstack-backups/db/

# Retention: Keep 30 days local, 1 year in S3
```

2. **Document Backup**:
```bash
# Daily backup of documents stored in PostgreSQL
# BYTEA fields automatically included in database backup

# Optional: Export to S3 for archival
0 4 * * * aws s3 sync /var/data/documents/ \
  s3://cogstack-backups/documents/
```

3. **Configuration Backup**:
```bash
# Backup environment and configuration files
0 1 * * * tar -czf /backups/config/cogstack_config_$(date +\%Y\%m\%d).tar.gz \
  /opt/cogstack-nlp/.env \
  /etc/nginx/sites-available/cogstack-nlp \
  /etc/systemd/system/cogstack-nlp-*.service
```

### Disaster Recovery

1. **RTO & RPO**:
```
Recovery Time Objective (RTO): 4 hours
Recovery Point Objective (RPO): 1 hour
```

2. **Database Recovery**:
```bash
# Step 1: Stop application
sudo systemctl stop cogstack-nlp-backend

# Step 2: Restore database from backup
psql < /backups/db/cogstack_nlp_20251122.sql

# Step 3: Run migrations to ensure schema is current
cd backend && alembic upgrade head

# Step 4: Verify data integrity
python backend/scripts/validate_data.py

# Step 5: Start application
sudo systemctl start cogstack-nlp-backend
```

3. **Testing Recovery**:
```bash
# Monthly disaster recovery drill
# 1. Restore to test database
# 2. Verify all data integrity
# 3. Document recovery time
# 4. Update runbook as needed
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Test connection
psql -h localhost -U cogstack_user -d cogstack_nlp -c "SELECT 1"

# Check connection pool
# In pgAdmin or psql:
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

# Solution: Increase max_connections in postgresql.conf
max_connections = 200
shared_preload_libraries = 'pg_stat_statements'
```

#### 2. Elasticsearch Not Indexing

```bash
# Check Elasticsearch health
curl -X GET "localhost:9200/_cluster/health"

# Check index status
curl -X GET "localhost:9200/_cat/indices"

# Reindex documents
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' \
  -d '{
    "source": { "index": "documents_old" },
    "dest": { "index": "documents_new" }
  }'
```

#### 3. High Memory Usage

```bash
# Check process memory
top -p $(pgrep -f "gunicorn")
ps aux | grep cogstack

# Check cache size
redis-cli INFO memory

# Clear old cache entries
redis-cli FLUSHDB

# Check Elasticsearch heap
curl -X GET "localhost:9200/_nodes/stats/jvm"
```

#### 4. Slow Queries

```bash
# Check PostgreSQL slow query log
SELECT * FROM pg_stat_statements
ORDER BY total_time DESC LIMIT 10;

# Explain query plan
EXPLAIN ANALYZE
SELECT * FROM documents WHERE patient_id = 'pat-123';

# Add missing indexes
CREATE INDEX idx_documents_patient_id ON documents(patient_id);
```

#### 5. High Error Rate

```bash
# Check application logs
journalctl -u cogstack-nlp-backend -n 100 --no-pager

# Check error rate in Kibana
GET /logs-*/_search
{
  "query": { "match": { "level": "ERROR" } }
}

# Check system resources
free -h
df -h
uptime
```

### Log Files

- **Application**: `/var/log/cogstack-nlp/app.log`
- **nginx**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **PostgreSQL**: `/var/log/postgresql/postgresql.log`
- **Elasticsearch**: `/var/log/elasticsearch/elasticsearch.log`
- **Systemd**: `journalctl -u cogstack-nlp-backend`

---

## Maintenance

### Regular Tasks

**Daily**:
- Monitor error rate and latency
- Check database replication lag (if applicable)
- Verify backup completion

**Weekly**:
- Review security logs for suspicious activity
- Check disk usage and clean up old logs
- Verify database integrity

**Monthly**:
- Run disaster recovery drill
- Review and update monitoring alerts
- Analyze performance metrics and optimize
- Update dependency packages

### Scaling

1. **Horizontal Scaling** (Add more servers):
```bash
# Configure load balancer (nginx/HAProxy)
upstream cogstack_backend {
    server app1.internal:8000 weight=1;
    server app2.internal:8000 weight=1;
    server app3.internal:8000 weight=1;
}

# Use session affinity or distributed cache (Redis)
# for session state across servers
```

2. **Vertical Scaling** (Upgrade server):
   - Increase CPU and RAM
   - Upgrade database hardware
   - Use SSD with RAID for reliability

3. **Database Scaling**:
   - Implement read replicas for query scaling
   - Use connection pooling (PgBouncer)
   - Implement caching layer (Redis)
   - Consider sharding for very large datasets

### Performance Optimization

1. **Database**:
```bash
# Analyze query performance
EXPLAIN ANALYZE <slow_query>;

# Add indexes for frequently queried fields
CREATE INDEX idx_entities_cui ON entities(cui);

# Vacuum to reclaim space
VACUUM ANALYZE;
```

2. **Caching**:
```bash
# Configure Redis for:
# - Session storage
# - Search history
# - Timeline data caching
# - Query result caching

# Monitor cache hit rate
redis-cli INFO stats
```

3. **Search Performance**:
```bash
# Enable Elasticsearch sharding for parallelism
# Tune refresh interval for bulk operations
# Use filter context for faster queries
```

---

## Support

For deployment issues:
1. Check logs: `journalctl -u cogstack-nlp-backend`
2. Consult troubleshooting section above
3. Review monitoring dashboard for health status
4. Contact support: support@cogstack.org
5. GitHub Issues: https://github.com/CogStack/cogstack-nlp/issues

---

**Last Updated**: 2025-11-22
**Version**: 1.0.0
