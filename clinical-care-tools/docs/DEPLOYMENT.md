# Production Deployment Guide

Complete guide for deploying Clinical Care Tools to production environments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Service Deployment](#service-deployment)
5. [Reverse Proxy Configuration](#reverse-proxy-configuration)
6. [SSL/TLS Setup](#ssltls-setup)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [Backup & Recovery](#backup--recovery)
9. [Performance Tuning](#performance-tuning)
10. [Health Checks](#health-checks)
11. [Scaling](#scaling)
12. [Troubleshooting](#troubleshooting)

## Pre-Deployment Checklist

### System Requirements

- [ ] Server with 16GB+ RAM
- [ ] 200GB+ disk space (models: 50GB, data: growth)
- [ ] 8+ CPU cores
- [ ] Linux (Ubuntu 20.04+ or CentOS 8+)
- [ ] Docker 20.10+, Docker Compose 1.29+
- [ ] Git installed

### Security Review

- [ ] Reviewed [SECURITY.md](SECURITY.md)
- [ ] SSL/TLS certificates obtained
- [ ] Firewall rules configured
- [ ] Admin credentials changed
- [ ] Database backups tested
- [ ] Incident response plan documented

### Application Configuration

- [ ] All environment variables reviewed
- [ ] Database password changed
- [ ] JWT secret key changed
- [ ] CORS origins configured
- [ ] Audit logging verified
- [ ] Rate limiting configured

### Testing

- [ ] Unit tests passing (backend & frontend)
- [ ] Integration tests passing
- [ ] Load test (./scripts/load-test.sh)
- [ ] Backup/restore tested
- [ ] Failover tested

## Environment Setup

### 1. Prepare Server

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/v2.0.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Add user to docker group (optional, for sudo-less access)
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Create Application User

```bash
# Create dedicated application user
sudo useradd -m -s /bin/bash clinical-care
sudo usermod -aG docker clinical-care

# Create application directories
sudo mkdir -p /opt/clinical-care-tools
sudo mkdir -p /opt/clinical-care-tools/models
sudo mkdir -p /opt/clinical-care-tools/backups
sudo mkdir -p /var/log/clinical-care-tools

# Set permissions
sudo chown -R clinical-care:clinical-care /opt/clinical-care-tools
sudo chown -R clinical-care:clinical-care /var/log/clinical-care-tools
```

### 3. Clone Repository

```bash
cd /opt/clinical-care-tools
sudo -u clinical-care git clone https://github.com/CogStack/clinical-care-tools.git .
sudo -u clinical-care git checkout main  # or specific tag
```

### 4. Configure Environment

```bash
# Create production .env file
sudo -u clinical-care cp .env.production.example .env.production

# Edit with production values
sudo -u clinical-care nano .env.production

# Example production values:
# DATABASE_URL=postgresql://clinical_admin:$(openssl rand -base64 32)@postgres:5432/clinical_care_tools
# SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
# ENVIRONMENT=production
# LOG_LEVEL=info
```

## Database Setup

### PostgreSQL Initialization

```bash
# Create data directory with proper permissions
sudo mkdir -p /var/lib/postgresql/data
sudo chown -R 999:999 /var/lib/postgresql/data
sudo chmod 700 /var/lib/postgresql/data

# Use provided initialization script
sudo -u clinical-care ./scripts/init-db.sql
```

### Database Migrations

```bash
# Run migrations on first deployment
docker-compose exec backend alembic upgrade head
```

### Verify Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U clinical_admin -d clinical_care_tools -c "\dt"

# Output should show tables:
# audit_logs, documents, entities, patients, users, sessions
```

### Backup Database

```bash
# Create initial backup
docker-compose exec postgres pg_dump -U clinical_admin clinical_care_tools > /opt/clinical-care-tools/backups/initial-backup.sql

# Test restore
pg_restore -U clinical_admin -d test_db /opt/clinical-care-tools/backups/initial-backup.sql
```

## Service Deployment

### Production Docker Compose

Use `docker-compose.yml` with production overrides:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    restart: always
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - /var/lib/postgresql/data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U clinical_admin"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - /var/lib/redis/data:/data

  backend:
    restart: always
    deploy:
      replicas: 3  # Horizontal scaling
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    environment:
      - ENVIRONMENT=production
      - WORKERS=8
      - LOG_LEVEL=info

  frontend:
    restart: always
    environment:
      - ENVIRONMENT=production
      - VITE_API_BASE_URL=https://clinical.healthcare.org/api
```

### Deploy Services

```bash
# Deploy with production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify all services started
docker-compose ps

# Check logs
docker-compose logs -f backend
```

## Reverse Proxy Configuration

### Nginx Setup

```nginx
# /etc/nginx/sites-available/clinical-care-tools

upstream backend {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=30s;
    server backend:8000 max_fails=3 fail_timeout=30s;  # Multiple replicas
    server backend:8000 max_fails=3 fail_timeout=30s;
}

upstream frontend {
    server frontend:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name clinical.healthcare.org;

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name clinical.healthcare.org;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/clinical.crt;
    ssl_certificate_key /etc/ssl/private/clinical.key;
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/clinical-care-tools-access.log;
    error_log /var/log/nginx/clinical-care-tools-error.log;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;

        # CORS headers (already handled by FastAPI)
        proxy_pass_header Access-Control-Allow-Origin;
        proxy_pass_header Access-Control-Allow-Methods;
        proxy_pass_header Access-Control-Allow-Headers;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://backend/api/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

### Enable Nginx Configuration

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/clinical-care-tools \
           /etc/nginx/sites-enabled/clinical-care-tools

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Verify it's running
sudo systemctl status nginx
```

## SSL/TLS Setup

### Obtain Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --nginx -d clinical.healthcare.org

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Manual Certificate Installation

```bash
# Copy certificate files
sudo cp clinical.crt /etc/ssl/certs/
sudo cp clinical.key /etc/ssl/private/
sudo chmod 644 /etc/ssl/certs/clinical.crt
sudo chmod 600 /etc/ssl/private/clinical.key

# Update Nginx configuration to use paths
sudo nano /etc/nginx/sites-available/clinical-care-tools
# ssl_certificate /etc/ssl/certs/clinical.crt;
# ssl_certificate_key /etc/ssl/private/clinical.key;
```

## Monitoring & Alerting

### Container Monitoring

```bash
# View resource usage
docker stats

# Example output:
# CONTAINER       CPU %   MEM USAGE / LIMIT
# backend         2.5%    512MiB / 2GiB
# postgres        1.2%    768MiB / 4GiB
# redis           0.5%    256MiB / 2GiB
```

### Log Aggregation

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f postgres

# Save logs to file
docker-compose logs > /var/log/clinical-care-tools/docker-logs-$(date +%Y%m%d).log
```

### Prometheus Monitoring (Optional)

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
```

## Backup & Recovery

### Automated Backup Script

```bash
#!/bin/bash
# /opt/clinical-care-tools/scripts/backup-production.sh

BACKUP_DIR="/opt/clinical-care-tools/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/clinical-care-tools_$DATE.sql.gz"

# Backup database
docker-compose exec -T postgres pg_dump -U clinical_admin clinical_care_tools | gzip > $BACKUP_FILE

# Backup docker volumes
tar -czf "$BACKUP_DIR/volumes_$DATE.tar.gz" \
  /var/lib/docker/volumes/clinical-care-tools_postgres_data \
  /var/lib/docker/volumes/clinical-care-tools_redis_data

# Keep only last 30 days of backups
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

### Scheduled Backups (Cron)

```bash
# Edit crontab
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/clinical-care-tools/scripts/backup-production.sh

# Add weekly full backup on Sundays
0 3 * * 0 /opt/clinical-care-tools/scripts/full-backup.sh

# Verify cron jobs
sudo crontab -l
```

### Database Restore

```bash
# Restore from backup
docker-compose exec -T postgres psql -U clinical_admin -d clinical_care_tools < /path/to/backup.sql

# Or if gzipped
gunzip -c /path/to/backup.sql.gz | docker-compose exec -T postgres psql -U clinical_admin
```

## Performance Tuning

### PostgreSQL Optimization

```sql
-- Increase shared_buffers (25% of system RAM)
-- In docker-compose.yml environment:
-- POSTGRES_INITDB_ARGS="-c shared_buffers=4GB"

-- Create indexes for common queries
CREATE INDEX idx_patient_mrn ON patients(mrn);
CREATE INDEX idx_entities_cui ON entities(cui);
CREATE INDEX idx_entities_confidence ON entities(confidence_score);
CREATE INDEX idx_audit_user_date ON audit_logs(user_id, timestamp);

-- Enable query logging for slow queries
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1 second
```

### Redis Optimization

```yaml
# In docker-compose.yml
redis:
  command: >
    redis-server
    --maxmemory 4gb
    --maxmemory-policy allkeys-lru
    --appendonly yes
    --appendfsync everysec
    --slowlog-log-slower-than 10000
```

### FastAPI Optimization

```python
# backend/app/main.py
# Increase number of workers
# In docker-compose.yml:
# WORKERS=8  (2-4 per CPU core)

# Connection pooling
# DATABASE_POOL_SIZE=20
# DATABASE_MAX_OVERFLOW=10

# Cache strategy
REDIS_CACHE_TTL=3600  # 1 hour
```

## Health Checks

### Automated Health Check Script

```bash
#!/bin/bash
# /opt/clinical-care-tools/scripts/health-check.sh

echo "Clinical Care Tools Health Check"
echo "=================================="

# Check Docker
echo "1. Docker Services:"
docker-compose ps

# Check API
echo -e "\n2. API Health:"
curl -s http://localhost:8000/api/health | jq .

# Check Database
echo -e "\n3. Database Health:"
docker-compose exec -T postgres pg_isready -U clinical_admin

# Check Redis
echo -e "\n4. Redis Health:"
docker-compose exec -T redis redis-cli ping

# Check Disk Space
echo -e "\n5. Disk Usage:"
df -h /opt/clinical-care-tools

# Check Process Memory
echo -e "\n6. Memory Usage:"
docker stats --no-stream

# Check Recent Errors
echo -e "\n7. Recent Errors:"
docker-compose logs --tail=20 | grep -i error
```

### Monitoring Endpoints

```bash
# API health check
curl http://localhost:8000/api/health

# Database connection
curl http://localhost:8000/api/health | jq '.services.database'

# Redis connection
curl http://localhost:8000/api/health | jq '.services.redis'

# NLP service
curl http://localhost:8001/api/health
```

## Scaling

### Horizontal Scaling (Multiple Instances)

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 3  # Scale to 3 instances
    labels:
      - "com.example.description=Clinical Care Tools Backend"
```

### Load Balancing

Nginx handles load balancing across backend replicas:

```nginx
upstream backend {
    least_conn;  # Use least connections algorithm
    server backend:8000 max_fails=3 fail_timeout=30s;
    server backend:8000 max_fails=3 fail_timeout=30s;
    server backend:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

### Database Connection Pooling

```python
# Adjust pool size based on replicas
# If 3 backends × 10 connections = 30 pool size
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=10
```

## Troubleshooting

### Services Won't Start

```bash
# Check Docker daemon
sudo systemctl status docker

# View container logs
docker-compose logs -f <service>

# Example: Backend startup error
docker-compose logs backend | tail -50
```

### Database Connection Errors

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check credentials
cat .env.production | grep POSTGRES

# Test connection manually
docker-compose exec postgres psql -U clinical_admin -c "SELECT 1;"
```

### High Memory Usage

```bash
# Check memory by container
docker stats --no-stream

# Limit container memory
docker update --memory 2g --memory-swap 2g <container_id>

# Or in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
```

### API Timeouts

```bash
# Increase proxy timeout in Nginx
proxy_read_timeout 300s;
proxy_connect_timeout 75s;

# Or increase in docker-compose
COGSTACK_TIMEOUT=60
```

### Disk Space Full

```bash
# Check disk usage
df -h /opt/clinical-care-tools

# Clean up old backups
find /opt/clinical-care-tools/backups -type f -mtime +30 -delete

# Clean Docker cache
docker system prune -a

# Increase volume size (if using cloud infrastructure)
```

## Rollback Procedure

### Rollback to Previous Version

```bash
# 1. Stop current version
docker-compose down

# 2. Revert to previous commit
git checkout <previous-commit-sha>

# 3. Start previous version
docker-compose up -d

# 4. Verify health
./scripts/health-check.sh
```

### Rollback Database Migrations

```bash
# Downgrade to previous version
docker-compose exec backend alembic downgrade -1

# Or specific revision
docker-compose exec backend alembic downgrade <revision>
```

---

**Last Updated**: 2025-01-08
**Version**: 1.0.0
**Deployment Environments**: Development, Staging, Production
