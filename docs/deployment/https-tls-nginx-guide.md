# HTTPS/TLS Configuration with Nginx Reverse Proxy

## Overview

This guide covers securing MedCAT Trainer with HTTPS/TLS using Nginx as a reverse proxy. **HTTPS is mandatory for HIPAA/GDPR compliance** when handling patient health information (PHI).

**What you'll learn**:
- Why HTTPS/TLS is critical for healthcare applications
- How Nginx reverse proxy works
- Certificate options (self-signed, Let's Encrypt, enterprise CA)
- Step-by-step configuration for Windows/Linux deployment
- Testing, troubleshooting, and renewal

**Target audience**: Administrators deploying MedCAT Trainer in NHS hospitals or healthcare organizations

---

## 📚 Part 1: Understanding HTTPS/TLS

### What is HTTPS?

**HTTPS** = HTTP + TLS (Transport Layer Security)

**Without HTTPS** (HTTP only):
```
Clinician Browser                        MedCAT Trainer
     ↓                                          ↑
     |  http://localhost:8000                   |
     |  GET /api/patients/search                |
     |  Authorization: Bearer abc123            |  ← READABLE by anyone on network
     |  Body: { "query": "diabetes" }           |  ← PHI exposed!
     |                                           |
     └──────────────────────────────────────────┘
          Unencrypted traffic (plaintext)
```

**⚠️ Security Risks**:
- Passwords sent in plaintext
- PHI (patient data) readable by network sniffers
- Session tokens can be stolen
- Man-in-the-middle attacks possible
- **HIPAA/GDPR violation** (unencrypted PHI)

**With HTTPS** (TLS encryption):
```
Clinician Browser                        MedCAT Trainer
     ↓                                          ↑
     |  https://medcat.nhs.uk                   |
     |  TLS Handshake (establish encryption)    |
     |  ✓ Certificate verified                  |
     |                                           |
     |  GET /api/patients/search                |  ← ENCRYPTED
     |  Authorization: Bearer abc123            |  ← ENCRYPTED
     |  Body: { "query": "diabetes" }           |  ← ENCRYPTED
     |                                           |
     └──────────────────────────────────────────┘
          Encrypted traffic (AES-256-GCM)
```

**✅ Security Benefits**:
- All traffic encrypted (TLS 1.3: AES-256-GCM cipher)
- Passwords protected
- PHI encrypted in transit
- Session tokens protected
- Server identity verified (certificate)
- **HIPAA/GDPR compliant**

---

### What is TLS?

**TLS** (Transport Layer Security) is a cryptographic protocol that:
1. **Encrypts** data in transit (confidentiality)
2. **Authenticates** the server (identity verification)
3. **Ensures integrity** (data not tampered with)

**TLS Versions** (use latest only):
- ❌ **TLS 1.0, 1.1** - Deprecated (insecure)
- ⚠️ **TLS 1.2** - Acceptable (minimum for HIPAA)
- ✅ **TLS 1.3** - Recommended (faster, more secure)

**TLS Handshake** (simplified):
```
1. Client Hello
   Browser → Server: "I support TLS 1.3, here are my cipher suites"

2. Server Hello
   Server → Browser: "I choose TLS 1.3 + AES-256-GCM cipher"
   Server sends: SSL certificate (contains public key)

3. Certificate Verification
   Browser verifies:
   ✓ Certificate signed by trusted CA (Certificate Authority)
   ✓ Certificate not expired
   ✓ Certificate matches domain name (medcat.nhs.uk)

4. Key Exchange
   Browser + Server: Agree on symmetric encryption key using Diffie-Hellman

5. Encrypted Communication
   All subsequent traffic encrypted with AES-256-GCM
```

---

### What is an SSL Certificate?

**SSL Certificate** contains:
- **Public Key**: Used to establish encrypted connection
- **Domain Name**: e.g., `medcat.nhs.uk`
- **Issuer**: Certificate Authority (CA) that verified identity
- **Expiration Date**: Typically 90 days (Let's Encrypt) or 1-2 years (enterprise CA)
- **Digital Signature**: Proves certificate is authentic

**Certificate Authorities** (who signs certificates):
- **Self-Signed**: You create and sign it yourself (⚠️ browser warnings)
- **Let's Encrypt**: Free, automated CA (✅ trusted by browsers, 90-day expiry)
- **Enterprise CA**: NHS-internal CA or commercial (DigiCert, GlobalSign)

---

### What is a Reverse Proxy?

**Reverse Proxy** sits between clients and your application server:

**Without Reverse Proxy**:
```
Clinician Browser
     ↓
     | http://localhost:8000
     ↓
MedCAT Trainer (Django/Gunicorn)
```

**With Nginx Reverse Proxy**:
```
Clinician Browser
     ↓
     | https://medcat.nhs.uk (port 443)
     ↓
Nginx Reverse Proxy
  ├── Handles: HTTPS/TLS termination
  ├── Handles: SSL certificate
  ├── Handles: Static file serving (CSS, JS, images)
  ├── Handles: Rate limiting, caching, compression
  └── Forwards requests to:
        ↓
        | http://localhost:8000 (internal network only)
        ↓
   MedCAT Trainer (Django/Gunicorn)
```

**Benefits**:
- ✅ **TLS termination**: Nginx handles encryption/decryption (faster than Python)
- ✅ **Load balancing**: Distribute requests across multiple backends
- ✅ **Static files**: Serve CSS/JS directly (don't hit Django)
- ✅ **Caching**: Cache responses for faster loading
- ✅ **Security**: Hide backend servers, rate limiting, WAF
- ✅ **Centralized config**: One place to manage TLS settings

---

## 📋 Part 2: Certificate Options

### Option 1: Self-Signed Certificate

**Use case**: Internal testing, isolated networks, PoC deployments

**Pros**:
- ✅ Free
- ✅ Instant (no CA approval needed)
- ✅ Works offline

**Cons**:
- ❌ Browser warnings ("Your connection is not private")
- ❌ Users must manually accept security exception
- ❌ Not suitable for production (poor user experience)
- ⚠️ May violate NHS security policies

**When to use**: Development/testing only, NOT production

---

### Option 2: Let's Encrypt (Free CA)

**Use case**: Internet-accessible deployments with public domain names

**Pros**:
- ✅ Free
- ✅ Automated renewal (certbot)
- ✅ Trusted by all browsers
- ✅ 90-day certificates (forces regular renewal = good security practice)

**Cons**:
- ❌ Requires public domain name (e.g., medcat.nhs.uk)
- ❌ Requires port 80/443 open to internet (for validation)
- ❌ Not suitable for internal-only deployments (localhost, 192.168.x.x)
- ⚠️ 90-day expiry (must automate renewal)

**When to use**: Production deployments accessible from internet

---

### Option 3: NHS Enterprise CA

**Use case**: NHS hospital internal deployments

**Pros**:
- ✅ Trusted by NHS computers (pre-installed CA certificate)
- ✅ Works on internal networks (no internet required)
- ✅ Longer validity (1-2 years)
- ✅ Aligned with NHS security policies
- ✅ No browser warnings for NHS users

**Cons**:
- ⚠️ Requires NHS IT approval and certificate request process
- ⚠️ Manual renewal (less convenient than Let's Encrypt)
- ❌ Not trusted outside NHS (external users see warnings)

**When to use**: Internal NHS deployments (recommended for your use case)

---

### Option 4: Commercial CA (DigiCert, GlobalSign, etc.)

**Use case**: Public-facing production deployments

**Pros**:
- ✅ Trusted by all browsers
- ✅ 1-2 year validity
- ✅ Support for Extended Validation (EV) certificates
- ✅ Insurance coverage (certificate warranty)

**Cons**:
- ❌ Expensive (£50-500/year)
- ⚠️ Manual approval process

**When to use**: Public-facing commercial deployments

---

## 🔧 Part 3: Implementation Guide

### Scenario 1: Self-Signed Certificate (Testing)

**Step 1: Generate Self-Signed Certificate**

On **Windows** (PowerShell):
```powershell
# Create certificate directory
New-Item -ItemType Directory -Path C:\MedCAT-Trainer\ssl

# Generate private key and certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
  -keyout C:\MedCAT-Trainer\ssl\nginx-selfsigned.key `
  -out C:\MedCAT-Trainer\ssl\nginx-selfsigned.crt `
  -subj "/C=GB/ST=England/L=London/O=NHS/OU=Cardiology/CN=localhost"
```

On **Linux**:
```bash
# Create certificate directory
mkdir -p /etc/nginx/ssl

# Generate private key and certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/nginx-selfsigned.key \
  -out /etc/nginx/ssl/nginx-selfsigned.crt \
  -subj "/C=GB/ST=England/L=London/O=NHS/OU=Cardiology/CN=localhost"
```

**Output**:
- `nginx-selfsigned.key` - Private key (keep secure!)
- `nginx-selfsigned.crt` - Public certificate

**Step 2: Create Nginx Configuration**

Create `nginx.conf`:
```nginx
# nginx.conf - Self-Signed Certificate Configuration

events {
    worker_connections 1024;
}

http {
    # Rate limiting (protect against brute-force)
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    # Upstream MedCAT Trainer
    upstream medcat_trainer {
        server localhost:8000;
    }

    # HTTP → HTTPS redirect
    server {
        listen 80;
        server_name localhost;

        # Redirect all HTTP to HTTPS
        return 301 https://$host$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name localhost;

        # SSL Certificate and Key
        ssl_certificate     C:/MedCAT-Trainer/ssl/nginx-selfsigned.crt;
        ssl_certificate_key C:/MedCAT-Trainer/ssl/nginx-selfsigned.key;

        # TLS Configuration (TLS 1.2+ only)
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Client body size (for large dataset uploads)
        client_max_body_size 500M;

        # Proxy settings
        location / {
            proxy_pass http://medcat_trainer;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support (if needed)
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Rate limiting for login endpoint
        location /api/api-token-auth/ {
            limit_req zone=login burst=5;
            proxy_pass http://medcat_trainer;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files (optional - if serving from Nginx)
        location /static/ {
            alias C:/MedCAT-Trainer/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Media files (uploaded datasets, models)
        location /media/ {
            alias C:/MedCAT-Trainer/media/;
            expires 1h;
            add_header Cache-Control "private";
        }
    }
}
```

**Step 3: Add Nginx to Docker Compose**

Edit `docker-compose.yml`:
```yaml
version: '3.8'

services:
  medcat-trainer:
    image: cogstacksystems/medcat-trainer:latest
    ports:
      - "127.0.0.1:8000:8000"  # Only accessible via localhost (Nginx forwards here)
    environment:
      - DB_HOST=postgres
      # ... other env vars
    volumes:
      - C:/MedCAT-Data/media:/app/media
      - C:/MedCAT-Data/models:/app/models

  postgres:
    image: postgres:14
    # ... postgres config

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"    # HTTP (redirects to HTTPS)
      - "443:443"  # HTTPS
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - C:/MedCAT-Trainer/ssl:/etc/nginx/ssl:ro
      - C:/MedCAT-Trainer/static:/static:ro
      - C:/MedCAT-Data/media:/media:ro
    depends_on:
      - medcat-trainer
```

**Step 4: Start Services**

```powershell
# Restart containers with Nginx
docker-compose down
docker-compose up -d

# Verify Nginx is running
docker-compose ps

# Expected:
# nginx                 running   0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
# medcat-trainer        running   127.0.0.1:8000->8000/tcp
```

**Step 5: Test HTTPS**

1. Open browser → `https://localhost`
2. **Expected**: Browser security warning ("Your connection is not private")
3. Click **Advanced** → **Proceed to localhost (unsafe)**
4. **Result**: MedCAT Trainer loads via HTTPS

**Why the warning?**
- Self-signed certificates are not trusted by browsers
- Browser doesn't know who signed the certificate
- **Safe for testing**, but NOT for production

---

### Scenario 2: Let's Encrypt (Public Deployment)

**Prerequisites**:
- Public domain name (e.g., `medcat.nhs.uk`)
- DNS A record pointing to your server's public IP
- Ports 80 and 443 open to internet

**Step 1: Install Certbot**

On **Linux** (Ubuntu/Debian):
```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Verify installation
certbot --version
```

On **Windows**:
```powershell
# Install via Chocolatey
choco install certbot

# Or download: https://github.com/certbot/certbot/releases
```

**Step 2: Obtain Certificate**

```bash
# Obtain certificate (automatic Nginx configuration)
sudo certbot --nginx -d medcat.nhs.uk

# Prompts:
# Email: admin@nhs.uk (for renewal notifications)
# Agree to ToS: Yes
# Redirect HTTP to HTTPS: Yes (recommended)
```

**Output**:
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/medcat.nhs.uk/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/medcat.nhs.uk/privkey.pem
This certificate expires on 2025-02-14.
```

**Step 3: Verify Nginx Configuration**

Certbot automatically updates `/etc/nginx/sites-available/default`:

```nginx
server {
    listen 80;
    server_name medcat.nhs.uk;

    # Certbot-managed redirect
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name medcat.nhs.uk;

    # Certbot-managed certificates
    ssl_certificate /etc/letsencrypt/live/medcat.nhs.uk/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/medcat.nhs.uk/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Your application configuration
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Step 4: Test HTTPS**

```bash
# Reload Nginx
sudo nginx -t  # Test configuration
sudo systemctl reload nginx

# Test in browser
https://medcat.nhs.uk

# Expected: ✅ Secure connection (no warnings)
```

**Step 5: Automate Renewal**

Let's Encrypt certificates expire every **90 days**. Certbot installs a cron job for automatic renewal:

```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# Output: "Congratulations, all renewals succeeded"

# View cron job
sudo systemctl list-timers | grep certbot
# Output: certbot.timer runs twice daily
```

**Manual renewal** (if needed):
```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

### Scenario 3: NHS Enterprise CA (Internal Deployment)

**Use case**: NHS hospital internal network deployment (recommended for your RDP scenario)

**Step 1: Request Certificate from NHS IT**

Contact your NHS IT department's Certificate Services team:

**Request details**:
```
Subject: SSL Certificate Request for MedCAT Trainer Deployment

Server: NHS-WORKSTATION-01 (or hostname)
FQDN: medcat.cardiology.nhs.uk (internal DNS name)
Purpose: MedCAT clinical annotation platform
Department: Cardiology
Contact: [Your name and email]

Certificate Requirements:
- Key length: 2048-bit RSA or 256-bit ECC
- Validity: 1-2 years
- Subject Alternative Names (SANs):
  - medcat.cardiology.nhs.uk
  - medcat.cardiology.internal
  - NHS-WORKSTATION-01.nhs.uk
```

**Step 2: Generate Certificate Signing Request (CSR)**

```powershell
# On Windows workstation
openssl req -new -newkey rsa:2048 -nodes `
  -keyout C:\MedCAT-Trainer\ssl\nhs-medcat.key `
  -out C:\MedCAT-Trainer\ssl\nhs-medcat.csr `
  -subj "/C=GB/ST=England/L=London/O=NHS/OU=Cardiology/CN=medcat.cardiology.nhs.uk"
```

**Output**:
- `nhs-medcat.key` - Private key (**keep secure, never share**)
- `nhs-medcat.csr` - Certificate Signing Request (send to NHS IT)

**Step 3: Submit CSR to NHS IT**

- Email `nhs-medcat.csr` to NHS Certificate Services
- Wait for approval (typically 1-3 days)

**Step 4: Install Certificate**

NHS IT will provide:
- `nhs-medcat.crt` - Your signed certificate
- `nhs-root-ca.crt` - NHS Root CA certificate
- `nhs-intermediate-ca.crt` - Intermediate CA certificate (if applicable)

**Create certificate chain**:
```powershell
# Combine certificate + intermediate + root
Get-Content nhs-medcat.crt, nhs-intermediate-ca.crt, nhs-root-ca.crt | `
  Set-Content C:\MedCAT-Trainer\ssl\nhs-medcat-fullchain.crt
```

**Step 5: Configure Nginx**

```nginx
server {
    listen 443 ssl http2;
    server_name medcat.cardiology.nhs.uk;

    # NHS Enterprise CA certificates
    ssl_certificate     C:/MedCAT-Trainer/ssl/nhs-medcat-fullchain.crt;
    ssl_certificate_key C:/MedCAT-Trainer/ssl/nhs-medcat.key;

    # TLS 1.2+ only (NHS requirement)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';
    ssl_prefer_server_ciphers off;

    # ... rest of configuration
}
```

**Step 6: Test from NHS Computer**

From any NHS-domain computer:
```
https://medcat.cardiology.nhs.uk

Expected: ✅ Secure connection (no warnings)
         NHS CA certificate pre-trusted on NHS devices
```

---

## 🔐 Part 4: Security Hardening

### TLS Best Practices

**Use Mozilla SSL Configuration Generator**: https://ssl-config.mozilla.org/

**Modern Configuration** (TLS 1.3 only):
```nginx
ssl_protocols TLSv1.3;
```

**Intermediate Configuration** (TLS 1.2+, recommended for NHS):
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;
```

**HSTS (HTTP Strict Transport Security)**:
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```
- Forces browsers to use HTTPS for 1 year
- Prevents downgrade attacks

**OCSP Stapling** (certificate revocation checking):
```nginx
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/nginx/ssl/chain.pem;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

**Diffie-Hellman Parameters** (stronger key exchange):
```bash
# Generate DH parameters (takes ~5 minutes)
openssl dhparam -out /etc/nginx/ssl/dhparam.pem 2048

# Add to Nginx config
ssl_dhparam /etc/nginx/ssl/dhparam.pem;
```

---

### Security Headers

```nginx
# Prevent clickjacking (don't allow embedding in iframes)
add_header X-Frame-Options "SAMEORIGIN" always;

# Prevent MIME type sniffing
add_header X-Content-Type-Options "nosniff" always;

# XSS protection (legacy, but still good practice)
add_header X-XSS-Protection "1; mode=block" always;

# Referrer policy (don't leak URLs)
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Content Security Policy (advanced - test before deploying)
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

---

### Rate Limiting

Protect against brute-force login attacks:

```nginx
http {
    # Define rate limit zones
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;  # 5 requests per minute
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s; # 100 requests per second

    server {
        # Login endpoint (strict rate limit)
        location /api/api-token-auth/ {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://medcat_trainer;
        }

        # API endpoints (moderate rate limit)
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://medcat_trainer;
        }
    }
}
```

---

## 🧪 Part 5: Testing and Validation

### Test 1: SSL Labs Test (Online)

**For internet-accessible deployments**:

1. Visit: https://www.ssllabs.com/ssltest/
2. Enter your domain: `medcat.nhs.uk`
3. Click **Submit**
4. **Target Grade**: A or A+

**Common issues**:
- Grade B: TLS 1.0/1.1 enabled (disable them)
- Grade C: Weak ciphers (use Mozilla config)
- Grade F: Certificate expired or invalid

---

### Test 2: OpenSSL Command-Line Test

```bash
# Test TLS connection
openssl s_client -connect medcat.nhs.uk:443 -tls1_3

# Expected output:
# SSL-Session:
#     Protocol  : TLSv1.3
#     Cipher    : TLS_AES_256_GCM_SHA384
#     Session-ID: ...
#     Master-Key: ...
# Verify return code: 0 (ok)  ← Success!
```

**Test specific TLS version**:
```bash
# Test TLS 1.2
openssl s_client -connect medcat.nhs.uk:443 -tls1_2

# Test TLS 1.1 (should fail)
openssl s_client -connect medcat.nhs.uk:443 -tls1_1
# Expected: "no protocols available"
```

---

### Test 3: Certificate Validation

```bash
# View certificate details
openssl s_client -connect medcat.nhs.uk:443 -showcerts

# Check expiration date
echo | openssl s_client -connect medcat.nhs.uk:443 2>/dev/null | \
  openssl x509 -noout -dates

# Output:
# notBefore=Nov 16 00:00:00 2024 GMT
# notAfter=Feb 14 23:59:59 2025 GMT
```

---

### Test 4: Browser Testing

**Test in multiple browsers**:
- ✅ Chrome/Edge: Check for green padlock icon
- ✅ Firefox: Check certificate details
- ✅ Safari: Check for "Secure" indicator

**Check certificate details**:
1. Click padlock icon → Certificate
2. Verify:
   - ✓ Issued to: `medcat.nhs.uk` (matches domain)
   - ✓ Issued by: `Let's Encrypt` or `NHS Root CA`
   - ✓ Valid from: Recent date
   - ✓ Valid until: Future date (not expired)

---

## 🔧 Part 6: Troubleshooting

### Issue 1: "NET::ERR_CERT_AUTHORITY_INVALID"

**Cause**: Self-signed certificate or untrusted CA

**Solutions**:

**For self-signed (testing only)**:
```
1. Click "Advanced"
2. Click "Proceed to localhost (unsafe)"
```

**For NHS CA (production)**:
```
1. Verify NHS Root CA is installed on client computer
2. Windows: certmgr.msc → Trusted Root Certification Authorities
3. If missing, contact NHS IT to push CA certificate via Group Policy
```

---

### Issue 2: "ERR_SSL_PROTOCOL_ERROR"

**Cause**: Nginx SSL configuration error

**Debugging**:
```bash
# Test Nginx configuration
nginx -t

# View Nginx error logs
docker-compose logs nginx

# Common errors:
# - Certificate file not found (check paths)
# - Private key doesn't match certificate
# - TLS protocol mismatch
```

**Verify certificate/key match**:
```bash
# Certificate modulus
openssl x509 -noout -modulus -in certificate.crt | openssl md5

# Key modulus
openssl rsa -noout -modulus -in private.key | openssl md5

# If MD5 hashes match → certificate and key are paired ✓
```

---

### Issue 3: Certificate Expired

**Check expiration**:
```bash
openssl x509 -noout -dates -in certificate.crt

# Output:
# notAfter=Nov 16 23:59:59 2024 GMT  ← EXPIRED if past this date
```

**Fix**:

**For Let's Encrypt**:
```bash
sudo certbot renew
sudo systemctl reload nginx
```

**For NHS CA**:
```
1. Request new certificate from NHS IT (1-2 weeks before expiry)
2. Generate new CSR (same process as initial request)
3. Install new certificate when received
```

---

### Issue 4: "Mixed Content" Warnings

**Cause**: HTTPS page loading HTTP resources (insecure)

**Example**:
```html
<!-- ❌ Bad: HTTP resource on HTTPS page -->
<img src="http://example.com/image.jpg">

<!-- ✅ Good: HTTPS resource -->
<img src="https://example.com/image.jpg">

<!-- ✅ Better: Protocol-relative URL -->
<img src="//example.com/image.jpg">
```

**Fix in MedCAT Trainer**:
```python
# Django settings.py
SECURE_SSL_REDIRECT = True  # Force HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 📊 Part 7: Monitoring and Maintenance

### Certificate Expiration Monitoring

**Script to check expiration** (run daily via cron):

```bash
#!/bin/bash
# check-cert-expiry.sh

DOMAIN="medcat.nhs.uk"
THRESHOLD_DAYS=30

# Get expiration date
EXPIRY=$(echo | openssl s_client -connect ${DOMAIN}:443 2>/dev/null | \
         openssl x509 -noout -enddate | cut -d= -f2)

# Calculate days until expiry
EXPIRY_EPOCH=$(date -d "${EXPIRY}" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

# Alert if expiring soon
if [ $DAYS_LEFT -lt $THRESHOLD_DAYS ]; then
    echo "⚠️ WARNING: SSL certificate expires in ${DAYS_LEFT} days!"
    # Send email alert
    echo "Certificate for ${DOMAIN} expires on ${EXPIRY}" | \
      mail -s "SSL Certificate Expiring Soon" admin@nhs.uk
else
    echo "✅ Certificate valid for ${DAYS_LEFT} more days"
fi
```

**Add to cron**:
```bash
# Run daily at 9 AM
0 9 * * * /usr/local/bin/check-cert-expiry.sh
```

---

### Log Monitoring

**Monitor Nginx access logs for suspicious activity**:

```bash
# View access log
docker-compose logs nginx | grep "GET"

# Count requests by IP (detect brute-force)
docker-compose logs nginx | grep "POST /api/api-token-auth" | \
  awk '{print $1}' | sort | uniq -c | sort -rn

# Output:
#  150 192.168.1.50  ← Normal (clinician)
#  500 203.0.113.10  ← ⚠️ Suspicious (many login attempts)
```

**Alert on excessive requests**:
```bash
# If > 100 login attempts from single IP in 1 hour
docker-compose logs nginx --since 1h | grep "POST /api/api-token-auth" | \
  awk '{print $1}' | sort | uniq -c | \
  awk '$1 > 100 {print "⚠️ Brute-force from", $2}'
```

---

## 📝 Part 8: NHS Production Checklist

**Before deploying HTTPS in NHS hospital**:

- [ ] **Certificate type chosen**: Self-signed (testing) / Let's Encrypt (internet) / NHS CA (internal)
- [ ] **Certificate obtained**: CSR generated, certificate received from CA
- [ ] **Certificate installed**: fullchain.pem + privkey.pem in `/etc/nginx/ssl/`
- [ ] **Nginx configured**: SSL directives added, TLS 1.2+ enabled, weak ciphers disabled
- [ ] **Security headers added**: HSTS, X-Frame-Options, CSP
- [ ] **Rate limiting configured**: Login endpoint limited to 5 requests/minute
- [ ] **HTTP → HTTPS redirect**: All HTTP traffic redirected to HTTPS
- [ ] **Browser testing**: Chrome, Firefox, Edge all show secure connection
- [ ] **SSL Labs test**: Grade A or A+ (if internet-accessible)
- [ ] **Certificate expiration monitoring**: Daily cron job alerts 30 days before expiry
- [ ] **Auto-renewal configured**: Certbot timer (Let's Encrypt) or calendar reminder (NHS CA)
- [ ] **Firewall configured**: Ports 80, 443 open; port 8000 blocked externally
- [ ] **Django settings updated**: `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`
- [ ] **Backup private key**: Encrypted backup stored in secure NHS password vault
- [ ] **Documentation updated**: Certificate location, renewal process documented
- [ ] **NHS IT notified**: Certificate deployment registered with NHS Security team

---

## 🎓 Part 9: Key Concepts Summary

### What You Learned

**HTTPS/TLS**:
- HTTPS = HTTP + TLS encryption
- Protects PHI in transit (HIPAA/GDPR requirement)
- TLS 1.3 recommended, TLS 1.2 minimum
- Cipher suites determine encryption strength

**SSL Certificates**:
- Contain public key + domain name + CA signature
- Self-signed: Free, browser warnings (testing only)
- Let's Encrypt: Free, automated, 90-day expiry (internet deployments)
- NHS CA: Internal, trusted by NHS devices (recommended for RDP scenario)

**Nginx Reverse Proxy**:
- Sits between clients and MedCAT Trainer
- Handles TLS termination (encryption/decryption)
- Serves static files, caching, rate limiting
- Hides backend servers (security)

**Security Hardening**:
- Disable TLS 1.0/1.1 (weak protocols)
- Use strong ciphers (AES-256-GCM)
- Add security headers (HSTS, X-Frame-Options)
- Implement rate limiting (brute-force protection)

**Monitoring**:
- Monitor certificate expiration (30-day threshold)
- Monitor access logs (detect brute-force)
- Test SSL configuration regularly (SSL Labs)

---

## 📚 Additional Resources

**TLS/SSL**:
- Mozilla SSL Configuration Generator: https://ssl-config.mozilla.org/
- SSL Labs: https://www.ssllabs.com/ssltest/
- Let's Encrypt: https://letsencrypt.org/

**Nginx**:
- Official Docs: https://nginx.org/en/docs/
- Nginx HTTPS Guide: https://nginx.org/en/docs/http/configuring_https_servers.html

**Healthcare Security**:
- HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/
- NIST TLS Guidelines: https://csrc.nist.gov/publications/detail/sp/800-52/rev-2/final

---

## ❓ FAQs

**Q: Can I use HTTP for testing?**
A: Yes, but NEVER in production with real PHI. Always use HTTPS for production.

**Q: How often should I renew certificates?**
A: Let's Encrypt: 90 days (auto-renew). NHS CA: 1-2 years (manual). Commercial: 1-2 years.

**Q: What if NHS IT takes weeks to issue a certificate?**
A: Use self-signed for initial testing. Replace with NHS CA cert once received.

**Q: Can I use the same certificate for multiple servers?**
A: Yes, use Subject Alternative Names (SANs) in CSR. Or use wildcard cert (*.nhs.uk).

**Q: What happens if private key is compromised?**
A: Immediately revoke certificate (contact NHS IT or CA), generate new key pair, request new certificate.

---

**Ready to deploy?** Follow Scenario 3 (NHS Enterprise CA) for your RDP deployment!
