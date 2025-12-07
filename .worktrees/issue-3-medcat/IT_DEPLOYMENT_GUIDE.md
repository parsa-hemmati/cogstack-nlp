# CogStack NLP: IT Deployment Guide

A comprehensive step-by-step guide for deploying CogStack NLP services in production environments.

**Target Audience**: System Administrators, DevOps Engineers, IT Infrastructure Teams

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Deployment Options](#deployment-options)
5. [Step-by-Step Deployment](#step-by-step-deployment)
6. [Configuration](#configuration)
7. [Security](#security)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup & Recovery](#backup--recovery)
10. [Performance Tuning](#performance-tuning)
11. [Troubleshooting](#troubleshooting)
12. [Maintenance](#maintenance)

---

## Overview

### What You're Deploying

CogStack NLP is a suite of services for medical natural language processing:

- **MedCAT Service**: REST API for entity extraction (production NLP processing)
- **MedCAT Trainer**: Web application for model training and improvement
- **Demo Applications**: Testing and demonstration interfaces
- **Supporting Services**: Databases (PostgreSQL), search (Solr), web servers (Nginx)

### Deployment Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Planning | 1-2 weeks | Requirements, architecture design, security review |
| Infrastructure Setup | 1 week | Provision servers, networking, storage |
| Installation | 2-3 days | Deploy services, configure |
| Testing | 1 week | Integration testing, load testing |
| Production Rollout | 1 day | Go-live, monitoring setup |

---

## Architecture

### Service Architecture

```
┌─────────────────┐
│   Load Balancer │ (Optional: HAProxy, Nginx)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼────┐ ┌──▼─────────┐
│ MedCAT │ │  MedCAT    │
│ Service│ │  Trainer   │
│ (API)  │ │  (Web UI)  │
└───┬────┘ └──┬─────────┘
    │         │
    │    ┌────┴─────┐
    │    │          │
    │  ┌─▼───┐  ┌───▼──┐
    │  │Nginx│  │ Solr │
    │  └─────┘  └──────┘
    │         │
    │    ┌────▼──────┐
    │    │PostgreSQL │
    │    └───────────┘
    │
┌───▼────────────┐
│  Model Storage │
│  (Shared Vol.) │
└────────────────┘
```

### Network Ports

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| MedCAT Service | 5000 | HTTP | REST API |
| MedCAT Trainer | 8001 | HTTP | Web UI |
| Solr | 8983 | HTTP | Search index |
| PostgreSQL | 5432 | TCP | Database (internal) |
| Nginx | 80/443 | HTTP/HTTPS | Reverse proxy |

---

## Prerequisites

### Hardware Requirements

#### Minimum (Development/Testing)
- **CPU**: 4 cores
- **RAM**: 16 GB
- **Disk**: 50 GB SSD
- **Network**: 100 Mbps

#### Recommended (Production)
- **CPU**: 8-16 cores (or GPU: NVIDIA with CUDA support)
- **RAM**: 32-64 GB
- **Disk**: 200 GB SSD (for OS, services, models)
- **Storage**: 500 GB - 2 TB (for data, backups)
- **Network**: 1 Gbps

#### GPU Support (Optional, for high-throughput)
- **NVIDIA GPU**: Tesla T4, V100, A100, or RTX series
- **CUDA**: Version 11.8 or later
- **VRAM**: 16 GB minimum

### Software Requirements

#### Operating System
- **Linux**: Ubuntu 20.04/22.04 LTS (recommended), RHEL 8/9, CentOS 8+
- **Kernel**: 5.x or later (for Docker support)

#### Required Software
```bash
# Docker & Docker Compose
Docker Engine: 20.10+
Docker Compose: 2.x

# For GPU support
NVIDIA Driver: 525+
NVIDIA Container Toolkit: latest

# Optional
Git: 2.x
Python: 3.10+ (for local development)
```

### Network Requirements
- **Outbound Internet**: Required for Docker image pulls, model downloads
- **Inbound Access**: From clinical networks (configure firewall rules)
- **DNS**: Internal DNS resolution for service discovery

### Licensing & Access
- **UMLS License**: Free registration at [https://uts.nlm.nih.gov/uts/](https://uts.nlm.nih.gov/uts/)
- **NIH Account**: Required for model downloads
- **GitHub Access**: For source code and updates

---

## Deployment Options

### Option 1: Docker Compose (Recommended)

**Best for**: Single-server deployments, small-to-medium scale

**Pros**:
- Simple setup and maintenance
- All services in one configuration
- Easy backup and recovery

**Cons**:
- Limited horizontal scaling
- Single point of failure

### Option 2: Kubernetes

**Best for**: Large-scale, multi-tenant, high-availability deployments

**Pros**:
- Auto-scaling
- High availability
- Multi-node distribution

**Cons**:
- Complex setup
- Requires K8s expertise

### Option 3: Bare Metal / VM

**Best for**: Air-gapped environments, specific compliance requirements

**Pros**:
- Full control
- No containerization overhead

**Cons**:
- Complex dependency management
- Manual updates

---

## Step-by-Step Deployment

### Phase 1: Infrastructure Preparation

#### 1.1 Provision Server(s)

```bash
# For Ubuntu 22.04 LTS
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    ca-certificates \
    gnupg \
    lsb-release
```

#### 1.2 Install Docker

```bash
# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Add your user to docker group (optional, log out/in required)
sudo usermod -aG docker $USER
```

#### 1.3 Install GPU Support (Optional)

```bash
# Install NVIDIA drivers (if not already installed)
sudo apt install -y nvidia-driver-525

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update
sudo apt install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker

# Verify GPU is available to Docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

#### 1.4 Configure Storage

```bash
# Create directory structure
sudo mkdir -p /opt/cogstack/{models,data,backups,logs}
sudo mkdir -p /opt/cogstack/services/{medcat-service,medcat-trainer}

# Set permissions
sudo chown -R $USER:$USER /opt/cogstack

# For large model storage, consider mounting separate volume
# Example: Mount a 500GB volume to /opt/cogstack/models
```

#### 1.5 Configure Firewall

```bash
# Using UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5000/tcp  # MedCAT Service
sudo ufw allow 8001/tcp  # MedCAT Trainer
sudo ufw allow 443/tcp   # HTTPS (if using reverse proxy)

# Enable firewall
sudo ufw enable

# Verify rules
sudo ufw status
```

---

### Phase 2: Deploy MedCAT Service

#### 2.1 Clone Repository

```bash
cd /opt/cogstack
git clone https://github.com/CogStack/cogstack-nlp.git
cd cogstack-nlp
```

#### 2.2 Download Models

```bash
# Navigate to model directory
cd /opt/cogstack/models

# Option A: Manual download
# 1. Visit https://uts.nlm.nih.gov/uts/login?service=https://medcat.sites.er.kcl.ac.uk/auth-callback
# 2. Login with NIH credentials
# 3. Download model (e.g., medcat-snomed-2024.zip)
# 4. Upload to server

# Option B: Automated download via Python script
# (Requires UMLS API key)
cd /opt/cogstack/cogstack-nlp/medcat-scripts
pip install -e .
medcat-cli download --help  # Follow instructions

# Verify model file
ls -lh /opt/cogstack/models/
# Expected: medcat-snomed-2024.zip (or similar)
```

#### 2.3 Configure Environment Variables

```bash
cd /opt/cogstack/cogstack-nlp/medcat-service

# Copy example environment files
cp env/app.env env/app.prod.env
cp env/medcat.env env/medcat.prod.env
cp env/general.env env/general.prod.env

# Edit configuration
vim env/app.prod.env
```

**Key Configuration (`env/app.prod.env`)**:

```bash
# Application settings
APP_NAME=MedCAT
APP_MODEL_LANGUAGE=en
APP_MODEL_NAME=SNOMED-2024

# IMPORTANT: Use model pack path
APP_MEDCAT_MODEL_PACK=/cat/models/medcat-snomed-2024.zip

# Performance tuning
APP_BULK_NPROC=8          # Number of threads for bulk processing
APP_TORCH_THREADS=8       # PyTorch threads (CPU only)

# Server configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
SERVER_WORKERS=4          # Number of Gunicorn workers
SERVER_WORKER_TIMEOUT=300 # Timeout in seconds
SERVER_GUNICORN_MAX_REQUESTS=1000
SERVER_GUNICORN_MAX_REQUESTS_JITTER=50

# GPU settings (set to -1 for CPU)
APP_CUDA_DEVICE_COUNT=-1  # Set to 1 if using GPU

# Logging
APP_LOG_LEVEL=INFO
```

**MedCAT Configuration (`env/medcat.prod.env`)**:

```bash
# Logging
MEDCAT_LOG_LEVEL=40  # ERROR level

# Output format
MEDCAT_ANNOTATIONS_ENTITY_OUTPUT_MODE=dict

# De-identification (if needed)
MEDCAT_DEID_MODE=False
MEDCAT_DEID_REDACT=False
```

**General Configuration (`env/general.prod.env`)**:

```bash
# Docker shared memory size (CRITICAL for multi-processing)
DOCKER_SHM_SIZE=8g  # 8GB recommended for bulk processing

# CPU architecture (auto-detect)
DOCKER_DEFAULT_PLATFORM=linux/amd64

# Proxy settings (if behind corporate proxy)
# HTTP_PROXY=http://proxy.example.com:8080
# HTTPS_PROXY=http://proxy.example.com:8080
# no_proxy=localhost,127.0.0.1
```

#### 2.4 Create Docker Compose Configuration

```bash
cd /opt/cogstack/cogstack-nlp/medcat-service/docker

# For CPU deployment
cp docker-compose.example.yml docker-compose.prod.yml

# For GPU deployment
cp docker-compose-gpu.yml docker-compose.prod.yml

# Edit to reference production env files
vim docker-compose.prod.yml
```

**Production Docker Compose (`docker-compose.prod.yml`)**:

```yaml
services:
  medcat-service:
    image: cogstacksystems/medcat-service:latest
    container_name: medcat-service-prod
    restart: always
    env_file:
      - ../env/app.prod.env
      - ../env/medcat.prod.env
      - ../env/general.prod.env
    shm_size: "${DOCKER_SHM_SIZE:-8g}"
    volumes:
      - /opt/cogstack/models:/cat/models:ro
      - /opt/cogstack/logs/medcat-service:/cat/logs
    ports:
      - "5000:5000"
    networks:
      - cogstack-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/info"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s

networks:
  cogstack-net:
    driver: bridge
    name: cogstack-network
```

#### 2.5 Deploy Service

```bash
cd /opt/cogstack/cogstack-nlp/medcat-service/docker

# Pull latest image
docker compose -f docker-compose.prod.yml pull

# Start service
docker compose -f docker-compose.prod.yml up -d

# Verify service is running
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Wait for service to be ready (may take 2-5 minutes for model loading)
```

#### 2.6 Test Service

```bash
# Test health endpoint
curl http://localhost:5000/api/info

# Expected response:
# {
#   "app_name": "MedCAT",
#   "app_lang": "en",
#   "model_name": "SNOMED-2024",
#   ...
# }

# Test processing endpoint
curl -X POST http://localhost:5000/api/process \
  -H 'Content-Type: application/json' \
  -d '{
    "content": {
      "text": "Patient diagnosed with type 2 diabetes mellitus."
    }
  }'

# Expected: JSON response with extracted entities
```

---

### Phase 3: Deploy MedCAT Trainer

#### 3.1 Configure MedCAT Trainer

```bash
cd /opt/cogstack/cogstack-nlp/medcat-trainer

# Create environment file
cp envs/env envs/env.prod

# Edit configuration
vim envs/env.prod
```

**Trainer Configuration (`envs/env.prod`)**:

```bash
# Port configuration
MCTRAINER_PORT=8001
SOLR_PORT=8983

# Database configuration (uses SQLite by default, or configure PostgreSQL)
DATABASE_URL=sqlite:////home/api/db/trainer.db

# Security settings
SECRET_KEY=<generate-random-secret-key>  # Use: openssl rand -hex 32
ALLOWED_HOSTS=your-domain.com,localhost

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS=https://your-domain.com,http://localhost:8001

# Session settings
SESSION_COOKIE_SECURE=True  # Set to False for HTTP
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Strict

# User authentication
ENABLE_REGISTRATION=False  # Disable public registration in production

# Background task workers
WORKER_COUNT=2
```

#### 3.2 Deploy MedCAT Trainer

```bash
cd /opt/cogstack/cogstack-nlp/medcat-trainer

# Start services
docker compose -f docker-compose.yml --env-file envs/env.prod up -d

# Verify services
docker compose ps

# Expected services:
# - medcattrainer
# - nginx
# - solr

# Check logs
docker compose logs -f medcattrainer
```

#### 3.3 Create Admin User

```bash
# Access trainer container
docker compose exec medcattrainer bash

# Create superuser
python manage.py createsuperuser

# Follow prompts to set username, email, password
# Exit container
exit
```

#### 3.4 Test MedCAT Trainer

```bash
# Access web interface
# Open browser: http://your-server-ip:8001

# Login with admin credentials
# Verify you can:
# 1. Access admin panel
# 2. Create a project
# 3. Upload documents
```

---

### Phase 4: Production Hardening

#### 4.1 Set Up Reverse Proxy (Nginx)

```bash
# Install Nginx (if not using containerized version)
sudo apt install -y nginx

# Create Nginx configuration
sudo vim /etc/nginx/sites-available/cogstack-nlp
```

**Nginx Configuration**:

```nginx
# MedCAT Service
server {
    listen 443 ssl http2;
    server_name medcat-api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/medcat-api.crt;
    ssl_certificate_key /etc/ssl/private/medcat-api.key;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logging
    access_log /var/log/nginx/medcat-api-access.log;
    error_log /var/log/nginx/medcat-api-error.log;

    # Timeouts for long-running requests
    proxy_read_timeout 600s;
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;

    # Max request size
    client_max_body_size 50M;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# MedCAT Trainer
server {
    listen 443 ssl http2;
    server_name medcat-trainer.yourdomain.com;

    ssl_certificate /etc/ssl/certs/medcat-trainer.crt;
    ssl_certificate_key /etc/ssl/private/medcat-trainer.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    access_log /var/log/nginx/medcat-trainer-access.log;
    error_log /var/log/nginx/medcat-trainer-error.log;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name medcat-api.yourdomain.com medcat-trainer.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cogstack-nlp /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

#### 4.2 Set Up SSL Certificates

```bash
# Option A: Using Let's Encrypt (free)
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificates
sudo certbot --nginx -d medcat-api.yourdomain.com
sudo certbot --nginx -d medcat-trainer.yourdomain.com

# Auto-renewal is configured automatically

# Option B: Using organizational certificates
# Copy your certificates to /etc/ssl/certs/ and /etc/ssl/private/
```

#### 4.3 Configure Log Rotation

```bash
# Create logrotate configuration
sudo vim /etc/logrotate.d/cogstack-nlp
```

**Logrotate Configuration**:

```
/opt/cogstack/logs/medcat-service/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        docker compose -f /opt/cogstack/cogstack-nlp/medcat-service/docker/docker-compose.prod.yml restart > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/medcat-*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}
```

#### 4.4 Set Up Systemd Services

Create systemd service files for automatic startup on reboot.

```bash
# MedCAT Service
sudo vim /etc/systemd/system/medcat-service.service
```

**Systemd Service File**:

```ini
[Unit]
Description=MedCAT Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/cogstack/cogstack-nlp/medcat-service/docker
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
```

```bash
# MedCAT Trainer
sudo vim /etc/systemd/system/medcat-trainer.service
```

```ini
[Unit]
Description=MedCAT Trainer
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/cogstack/cogstack-nlp/medcat-trainer
ExecStart=/usr/bin/docker compose --env-file envs/env.prod up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
```

```bash
# Enable services
sudo systemctl daemon-reload
sudo systemctl enable medcat-service.service
sudo systemctl enable medcat-trainer.service

# Test services
sudo systemctl start medcat-service
sudo systemctl status medcat-service
```

---

## Configuration

### Environment Variables Reference

#### MedCAT Service (`env/app.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | MedCAT | Service name |
| `APP_MODEL_NAME` | - | Descriptive model name |
| `APP_MEDCAT_MODEL_PACK` | - | Path to model pack ZIP |
| `APP_BULK_NPROC` | 8 | Threads for bulk processing |
| `APP_TORCH_THREADS` | 8 | PyTorch CPU threads |
| `SERVER_WORKERS` | 1 | Gunicorn workers |
| `SERVER_WORKER_TIMEOUT` | 300 | Request timeout (seconds) |
| `SERVER_GUNICORN_MAX_REQUESTS` | 1000 | Max requests before worker restart |
| `APP_CUDA_DEVICE_COUNT` | -1 | GPU count (-1 for CPU) |
| `APP_LOG_LEVEL` | INFO | Log level |

#### MedCAT Library (`env/medcat.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `MEDCAT_LOG_LEVEL` | 40 | Log level (10=DEBUG, 40=ERROR) |
| `MEDCAT_SPACY_MODEL` | - | Override spaCy model |
| `MEDCAT_ANNOTATIONS_ENTITY_OUTPUT_MODE` | dict | Output format (dict/list) |
| `MEDCAT_DEID_MODE` | False | Enable de-identification |
| `MEDCAT_DEID_REDACT` | False | Redact identified entities |

#### Docker General (`env/general.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCKER_SHM_SIZE` | 1g | Shared memory size |
| `DOCKER_DEFAULT_PLATFORM` | linux/amd64 | Platform architecture |
| `HTTP_PROXY` | - | HTTP proxy |
| `HTTPS_PROXY` | - | HTTPS proxy |

---

## Security

### 1. Network Security

```bash
# Firewall rules (UFW example)
# Only allow specific IPs
sudo ufw allow from 10.0.0.0/8 to any port 5000 proto tcp
sudo ufw allow from 10.0.0.0/8 to any port 8001 proto tcp

# Deny all other access
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

### 2. API Authentication

MedCAT Service doesn't include built-in authentication. Implement at reverse proxy level:

**Nginx with Basic Auth**:

```bash
# Install apache2-utils
sudo apt install -y apache2-utils

# Create password file
sudo htpasswd -c /etc/nginx/.htpasswd medcat-user

# Add to Nginx config
```

```nginx
location / {
    auth_basic "MedCAT API";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:5000;
}
```

**Or use OAuth2 Proxy** for enterprise SSO integration.

### 3. Data Encryption

- **In-transit**: Use TLS/SSL for all external connections
- **At-rest**: Encrypt volumes using LUKS or cloud provider encryption
- **Backups**: Encrypt backup files before storage

```bash
# Example: Encrypt backup with GPG
tar -czf backup.tar.gz /opt/cogstack/data
gpg --symmetric --cipher-algo AES256 backup.tar.gz
```

### 4. Secrets Management

**Never commit secrets to version control.** Use environment variables or secrets management tools.

```bash
# Generate secure random keys
openssl rand -hex 32  # For SECRET_KEY
openssl rand -base64 32  # For API keys
```

### 5. Container Security

```bash
# Run containers as non-root user
# Add to docker-compose.yml:
services:
  medcat-service:
    user: "1000:1000"  # UID:GID
```

```bash
# Scan images for vulnerabilities
docker scan cogstacksystems/medcat-service:latest
```

### 6. Audit Logging

Enable comprehensive logging for security audits:

```python
# In application config (if extending)
LOGGING = {
    'handlers': {
        'audit': {
            'filename': '/cat/logs/audit.log',
            'formatter': 'json',
        }
    }
}
```

---

## Monitoring & Logging

### 1. Docker Logs

```bash
# View logs
docker compose logs -f medcat-service

# Last 100 lines
docker compose logs --tail=100 medcat-service

# Export logs
docker compose logs --no-color medcat-service > medcat-service.log
```

### 2. Health Checks

**Built-in Health Endpoint**:

```bash
# Check service health
curl http://localhost:5000/api/info

# Automated monitoring script
#!/bin/bash
# save as /usr/local/bin/check-medcat-health.sh

ENDPOINT="http://localhost:5000/api/info"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT)

if [ $RESPONSE -eq 200 ]; then
    echo "OK: MedCAT Service is healthy"
    exit 0
else
    echo "CRITICAL: MedCAT Service is down (HTTP $RESPONSE)"
    exit 2
fi
```

### 3. Resource Monitoring

```bash
# Monitor container resources
docker stats

# Continuous monitoring
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### 4. Prometheus Integration (Advanced)

**Docker Compose with Prometheus**:

```yaml
services:
  medcat-service:
    # ... existing config ...
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=5000"
      - "prometheus.path=/metrics"

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
```

### 5. Log Aggregation (ELK Stack)

For centralized logging, integrate with Elasticsearch/Logstash/Kibana or similar.

---

## Backup & Recovery

### 1. Backup Strategy

**What to Back Up**:
- Models: `/opt/cogstack/models`
- Trainer database: `/opt/cogstack/cogstack-nlp/medcat-trainer/api-db`
- Configuration files: `/opt/cogstack/cogstack-nlp/*/env/*.env`
- Custom models: Any user-trained models

**Backup Frequency**:
- Configuration: Daily
- Trainer database: Daily (after annotation sessions)
- Models: Weekly or after updates

### 2. Automated Backup Script

```bash
#!/bin/bash
# /usr/local/bin/backup-cogstack.sh

BACKUP_DIR="/opt/cogstack/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cogstack-backup-${TIMESTAMP}.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Stop services (optional, for consistency)
# systemctl stop medcat-trainer

# Backup files
tar -czf ${BACKUP_DIR}/${BACKUP_FILE} \
    /opt/cogstack/models \
    /opt/cogstack/cogstack-nlp/medcat-trainer/api-db \
    /opt/cogstack/cogstack-nlp/medcat-service/env \
    /opt/cogstack/cogstack-nlp/medcat-trainer/envs

# Restart services
# systemctl start medcat-trainer

# Encrypt backup (optional)
gpg --symmetric --cipher-algo AES256 ${BACKUP_DIR}/${BACKUP_FILE}
rm ${BACKUP_DIR}/${BACKUP_FILE}  # Remove unencrypted

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.gpg" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gpg"
```

```bash
# Make executable
chmod +x /usr/local/bin/backup-cogstack.sh

# Schedule with cron
crontab -e

# Add line (daily at 2 AM):
0 2 * * * /usr/local/bin/backup-cogstack.sh >> /var/log/cogstack-backup.log 2>&1
```

### 3. Restore Procedure

```bash
# Stop services
systemctl stop medcat-service medcat-trainer

# Decrypt backup
gpg --decrypt cogstack-backup-20250101_020000.tar.gz.gpg > backup.tar.gz

# Extract
tar -xzf backup.tar.gz -C /

# Restart services
systemctl start medcat-service medcat-trainer

# Verify
curl http://localhost:5000/api/info
```

### 4. Disaster Recovery Plan

**Recovery Time Objective (RTO)**: 4 hours
**Recovery Point Objective (RPO)**: 24 hours

**Steps**:
1. Provision new infrastructure (2 hours)
2. Restore from backup (1 hour)
3. Verify services (1 hour)

**Maintain**:
- Off-site backup copies
- Documented recovery procedures
- Regular DR testing (quarterly)

---

## Performance Tuning

### 1. CPU-Based Optimization

```bash
# env/app.env
APP_BULK_NPROC=16        # Set to number of CPU cores
APP_TORCH_THREADS=16     # Match NPROC
SERVER_WORKERS=4         # Usually 2-4x number of cores

# env/general.env
DOCKER_SHM_SIZE=16g      # 1-2GB per BULK_NPROC thread
```

### 2. GPU Optimization

```bash
# env/app.env
APP_CUDA_DEVICE_COUNT=1  # Number of GPUs
APP_TORCH_THREADS=0      # Disable CPU threading with GPU
SERVER_WORKERS=2         # Fewer workers needed with GPU
APP_BULK_NPROC=4         # Lower with GPU

# docker-compose.yml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### 3. Memory Management

```bash
# Check memory usage
docker stats medcat-service-prod

# If OOM errors occur:
# 1. Increase Docker memory limit
# 2. Reduce APP_BULK_NPROC
# 3. Reduce SERVER_WORKERS
# 4. Use smaller model
```

### 4. Network Optimization

```bash
# Increase Nginx worker processes
# /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 4096;

# Increase file descriptors
ulimit -n 65536
```

### 5. Database Optimization (MedCAT Trainer)

```bash
# For PostgreSQL (if using instead of SQLite)
# Tune postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
```

### 6. Caching

Implement Redis for caching frequent requests:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Service Won't Start

**Symptom**: Container exits immediately

```bash
# Check logs
docker compose logs medcat-service

# Common causes:
# - Missing model file
# - Incorrect model path in env file
# - Insufficient memory
```

**Solution**:
```bash
# Verify model exists
ls -lh /opt/cogstack/models/

# Check environment variable
docker compose config | grep APP_MEDCAT_MODEL_PACK

# Increase memory
# Edit docker-compose.yml, add:
    deploy:
      resources:
        limits:
          memory: 32G
```

#### Issue 2: Model Loading Timeout

**Symptom**: "Worker timeout" errors in logs

```bash
# Solution: Increase timeout
# env/app.env
SERVER_WORKER_TIMEOUT=600  # Increase to 10 minutes
```

#### Issue 3: OOM (Out of Memory) Errors

```bash
# Check memory usage
free -h
docker stats

# Solutions:
# 1. Reduce concurrent processing
APP_BULK_NPROC=4  # Lower value

# 2. Reduce number of workers
SERVER_WORKERS=1

# 3. Increase system swap
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Issue 4: Slow Processing

```bash
# Profile performance
# Check CPU/GPU usage
htop  # or nvidia-smi for GPU

# Solutions:
# 1. Enable GPU if available
# 2. Increase APP_BULK_NPROC
# 3. Scale horizontally (multiple instances + load balancer)
```

#### Issue 5: Network Connectivity Issues

```bash
# Check if service is listening
netstat -tuln | grep 5000

# Check Docker network
docker network inspect cogstack-network

# Test connectivity
curl -v http://localhost:5000/api/info

# Check firewall
sudo ufw status
```

#### Issue 6: SSL/Certificate Errors

```bash
# Verify certificates
openssl x509 -in /etc/ssl/certs/medcat-api.crt -text -noout

# Check Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Debug Mode

```bash
# Enable debug logging
# env/app.env
APP_LOG_LEVEL=DEBUG

# env/medcat.env
MEDCAT_LOG_LEVEL=10

# Restart service
docker compose restart medcat-service

# Monitor logs
docker compose logs -f medcat-service
```

### Getting Help

1. **Check logs first**: `docker compose logs`
2. **GitHub Issues**: [https://github.com/CogStack/cogstack-nlp/issues](https://github.com/CogStack/cogstack-nlp/issues)
3. **Discourse Forum**: [https://discourse.cogstack.org](https://discourse.cogstack.org)
4. **Documentation**: [https://docs.cogstack.org](https://docs.cogstack.org)

---

## Maintenance

### 1. Regular Updates

```bash
# Check for updates
cd /opt/cogstack/cogstack-nlp
git fetch origin
git log HEAD..origin/main --oneline

# Update code
git pull origin main

# Pull latest Docker images
docker compose pull

# Recreate containers with new images
docker compose up -d --force-recreate
```

### 2. Model Updates

```bash
# Download new model version
cd /opt/cogstack/models
# Follow download procedure

# Update environment variable
vim /opt/cogstack/cogstack-nlp/medcat-service/env/app.prod.env
# Change: APP_MEDCAT_MODEL_PACK=/cat/models/new-model.zip

# Restart service
docker compose restart medcat-service

# Verify new model
curl http://localhost:5000/api/info | jq .model_name
```

### 3. Database Maintenance (Trainer)

```bash
# Backup database
docker compose exec medcattrainer python manage.py dumpdata > backup.json

# Vacuum database (SQLite)
docker compose exec medcattrainer sqlite3 /home/api/db/trainer.db "VACUUM;"

# For PostgreSQL
docker compose exec postgres psql -U medcat -c "VACUUM ANALYZE;"
```

### 4. Log Cleanup

```bash
# Manual cleanup
find /opt/cogstack/logs -name "*.log" -mtime +30 -delete

# Docker logs cleanup
docker system prune -a --volumes --filter "until=720h"
```

### 5. Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker
sudo apt update
sudo apt install --only-upgrade docker-ce docker-ce-cli containerd.io

# Restart Docker
sudo systemctl restart docker

# Restart services
systemctl restart medcat-service medcat-trainer
```

### 6. Health Checks

Run weekly health checks:

```bash
#!/bin/bash
# /usr/local/bin/weekly-healthcheck.sh

echo "=== CogStack NLP Health Check ==="
echo "Date: $(date)"
echo

# Check services
echo "--- Service Status ---"
systemctl status medcat-service --no-pager
systemctl status medcat-trainer --no-pager

# Check disk space
echo "--- Disk Space ---"
df -h /opt/cogstack

# Check memory
echo "--- Memory ---"
free -h

# Check Docker
echo "--- Docker Containers ---"
docker ps

# Test API
echo "--- API Test ---"
curl -s http://localhost:5000/api/info | jq .

echo "=== End Health Check ==="
```

### 7. Capacity Planning

Monitor and plan for growth:

```bash
# Track request volumes
grep "POST /api/process" /var/log/nginx/medcat-api-access.log | wc -l

# Monitor response times
awk '{print $NF}' /var/log/nginx/medcat-api-access.log | \
    awk '{sum+=$1; count++} END {print "Avg:", sum/count "ms"}'

# Plan scaling when:
# - CPU usage consistently > 80%
# - Response times > 5 seconds
# - Request queue growing
```

---

## Appendix

### A. Deployment Checklist

Pre-Deployment:
- [ ] Hardware provisioned
- [ ] OS installed and updated
- [ ] Docker installed
- [ ] GPU drivers installed (if applicable)
- [ ] UMLS license obtained
- [ ] Models downloaded
- [ ] Firewall configured
- [ ] SSL certificates obtained
- [ ] Backup strategy defined

Deployment:
- [ ] Services deployed
- [ ] Environment variables configured
- [ ] Health checks passing
- [ ] API endpoints accessible
- [ ] Reverse proxy configured
- [ ] SSL working
- [ ] Logging configured
- [ ] Monitoring set up

Post-Deployment:
- [ ] Load testing completed
- [ ] Security scan completed
- [ ] Documentation updated
- [ ] Team trained
- [ ] Backup tested
- [ ] Runbook created

### B. Useful Commands Reference

```bash
# Docker Compose
docker compose up -d              # Start services
docker compose down               # Stop services
docker compose restart            # Restart services
docker compose logs -f            # Follow logs
docker compose ps                 # List containers
docker compose exec <service> bash # Shell into container

# Docker
docker ps                         # List running containers
docker stats                      # Resource usage
docker logs <container>           # View logs
docker inspect <container>        # Detailed info

# System
systemctl status <service>        # Service status
journalctl -u <service> -f        # Service logs
htop                              # Process monitor
df -h                             # Disk usage
free -h                           # Memory usage
netstat -tuln                     # Network ports

# Nginx
nginx -t                          # Test config
systemctl reload nginx            # Reload config
tail -f /var/log/nginx/access.log # Monitor access

# API Testing
curl http://localhost:5000/api/info
curl -X POST http://localhost:5000/api/process \
  -H 'Content-Type: application/json' \
  -d '{"content":{"text":"test"}}'
```

### C. Architecture Diagrams

#### Single Server Deployment
```
┌─────────────────────────────────────────┐
│            Server (Ubuntu)              │
│                                         │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │ MedCAT Svc   │  │ MedCAT Trainer  │ │
│  │ (Docker)     │  │ (Docker)        │ │
│  │              │  │                 │ │
│  │ Port: 5000   │  │ Port: 8001      │ │
│  └──────────────┘  └─────────────────┘ │
│                                         │
│  ┌─────────────────────────────────────│
│  │ Shared Volume: /opt/cogstack/models││
│  └─────────────────────────────────────│
│                                         │
└─────────────────────────────────────────┘
```

#### High-Availability Deployment
```
                ┌─────────────┐
                │Load Balancer│
                └──────┬──────┘
                       │
        ┏━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┓
        ▼                              ▼
┌───────────────┐              ┌───────────────┐
│   Server 1    │              │   Server 2    │
│               │              │               │
│ MedCAT Service│              │ MedCAT Service│
│               │              │               │
└───────┬───────┘              └───────┬───────┘
        │                              │
        └──────────┬───────────────────┘
                   ▼
           ┌───────────────┐
           │ Shared Storage│
           │   (NFS/S3)    │
           └───────────────┘
```

### D. Support Contacts

- **CogStack Team**: contact@cogstack.org
- **GitHub Issues**: https://github.com/CogStack/cogstack-nlp/issues
- **Community Forum**: https://discourse.cogstack.org
- **Documentation**: https://docs.cogstack.org

### E. Additional Resources

- **Docker Documentation**: https://docs.docker.com
- **Docker Compose Reference**: https://docs.docker.com/compose/compose-file/
- **NVIDIA Container Toolkit**: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/
- **Nginx Documentation**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/docs/

---

## Summary

This guide covered:
✅ Infrastructure setup and prerequisites
✅ Step-by-step deployment of MedCAT Service and Trainer
✅ Production hardening with SSL, reverse proxy, and systemd
✅ Comprehensive configuration reference
✅ Security best practices
✅ Monitoring and logging setup
✅ Backup and disaster recovery procedures
✅ Performance tuning guidelines
✅ Troubleshooting common issues
✅ Ongoing maintenance procedures

**For additional support**, consult the [CogStack Documentation](https://docs.cogstack.org) or post on the [Discourse Forum](https://discourse.cogstack.org).

**Next Steps**:
1. Review the [QUICK_START.md](QUICK_START.md) for a simplified overview
2. Check the [CLINICIAN_GUIDE.md](CLINICIAN_GUIDE.md) for clinical use cases
3. Explore the [tutorials](medcat-v2-tutorials/) for advanced usage

**Happy Deploying! 🚀**
