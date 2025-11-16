# NHS Windows Workstation RDP Deployment Guide

## Overview

Deploy MedCAT Trainer on a single Windows workstation for multi-user access via Remote Desktop Protocol (RDP). Multiple clinicians RDP to the workstation with their own Windows credentials and access the shared MedCAT Trainer instance.

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│  NHS Windows Workstation (Physical Machine)                 │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Docker Desktop (Shared Service)                       │ │
│  │                                                         │ │
│  │  ┌─────────────────┐  ┌──────────────┐  ┌───────────┐ │ │
│  │  │ MedCAT Trainer  │  │ PostgreSQL   │  │ Nginx     │ │ │
│  │  │ localhost:8000  │  │ localhost:   │  │ (optional)│ │ │
│  │  └─────────────────┘  └──────────────┘  └───────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ RDP Session 1│  │ RDP Session 2│  │ RDP Session 3│      │
│  │ (Admin)      │  │ (dr_smith)   │  │ (dr_jones)   │      │
│  │              │  │              │  │              │      │
│  │ Access:      │  │ Access:      │  │ Access:      │      │
│  │ localhost:   │  │ localhost:   │  │ localhost:   │      │
│  │ 8000         │  │ 8000         │  │ 8000         │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                         ▲                  ▲                 │
└─────────────────────────┼──────────────────┼─────────────────┘
                          │                  │
                    ┌─────┴──────┐     ┌─────┴──────┐
                    │ Clinician  │     │ Clinician  │
                    │ Laptop 1   │     │ Laptop 2   │
                    │ (RDP)      │     │ (RDP)      │
                    └────────────┘     └────────────┘
```

**Key Points**:
- Docker containers run **once** (shared across all RDP sessions)
- `localhost:8000` is accessible from **any RDP session**
- Each clinician uses **their own MedCAT Trainer credentials** (not Windows credentials)
- Workstation stays powered on 24/7 for continuous access

---

## Phase 1: Admin Workstation Preparation

### Step 1.1: Windows Configuration

**Requirements**:
- Windows 10 Pro/Enterprise or Windows Server (RDP multi-session support)
- Admin account with local administrator privileges
- Internet connection for Docker image downloads
- At least 16GB RAM, 100GB free disk space

**Enable Remote Desktop**:
1. Open **Settings** → **System** → **Remote Desktop**
2. Toggle **Enable Remote Desktop**: ON
3. Note the workstation's hostname or IP address (e.g., `NHS-WORKSTATION-01` or `192.168.1.100`)

**Configure Simultaneous RDP Sessions** (Windows Server only):
- Windows 10: Max 1 simultaneous RDP session (admin must disconnect before clinicians connect)
- Windows Server: Supports multiple simultaneous RDP sessions

**For Windows 10 multi-session**, use one of these workarounds:
- **Option A**: Admin installs/configures Docker, then **logs out**. Clinicians RDP in afterward.
- **Option B**: Use third-party tools (not recommended for NHS compliance)
- **Option C**: Upgrade to Windows Server 2019/2022 (recommended for production)

---

### Step 1.2: Install Docker Desktop for Windows

**Download Docker Desktop**:
1. Visit: https://www.docker.com/products/docker-desktop
2. Download: `Docker Desktop Installer.exe`
3. Run installer **as Administrator**

**Installation Options**:
```
✓ Use WSL 2 instead of Hyper-V (recommended)
✓ Add shortcut to desktop
✓ Start Docker Desktop when you log in
```

**Post-Installation Configuration**:

1. **Open Docker Desktop** → Settings → General
   - ✓ **Start Docker Desktop when you log in**
   - ✓ **Use the WSL 2 based engine**

2. **Resources** → Advanced:
   - CPUs: 4+ cores
   - Memory: 8GB+ RAM
   - Disk image size: 64GB+

3. **Resources** → File Sharing:
   - Add: `C:\MedCAT-Data` (for persistent data)

4. **Apply & Restart**

**Verify Installation**:
```powershell
# Open PowerShell as Administrator
docker --version
# Output: Docker version 24.0.x, build xxxxx

docker-compose --version
# Output: Docker Compose version v2.x.x
```

---

### Step 1.3: Configure Docker to Run as Windows Service

**⚠️ CRITICAL**: By default, Docker Desktop runs only when the user is logged in. For multi-user RDP access, configure Docker to run as a **Windows Service** that auto-starts on boot.

**Option A: Docker Desktop Auto-Start (Simpler)**

Docker Desktop **already auto-starts** if you enabled "Start Docker Desktop when you log in". However, it only runs while the admin user session is active.

**Workaround for RDP multi-user**:
1. Admin RDPs to workstation
2. Admin starts Docker Desktop (if not auto-started)
3. Admin runs `docker-compose up -d` (containers run in background)
4. Admin **stays logged in** (minimizes RDP window but doesn't log out)
5. Clinicians RDP to workstation using **their own accounts**
6. Clinicians access `http://localhost:8000` from their RDP sessions

**Important**: On Windows 10, only **one RDP session** can be active at a time. The admin must **disconnect** (not log out) their RDP session before clinicians connect.

**Option B: Run Docker as Windows Service (Advanced, requires Linux containers on Windows)**

For true multi-user support where admin doesn't need to stay logged in:

```powershell
# This requires Docker Enterprise or manual Docker Engine (not Docker Desktop)
# Not recommended for initial deployment
```

**Recommendation**: Use **Option A** for initial NHS deployment. Upgrade to Windows Server for production multi-user support.

---

## Phase 2: MedCAT Trainer Installation

### Step 2.1: Clone Repository

```powershell
# Open PowerShell as Administrator
cd C:\
git clone https://github.com/CogStack/MedCAT-Trainer.git
cd MedCAT-Trainer
```

### Step 2.2: Create Data Directories

```powershell
# Create directories for persistent data (outside Docker)
New-Item -ItemType Directory -Path C:\MedCAT-Data\postgres
New-Item -ItemType Directory -Path C:\MedCAT-Data\media
New-Item -ItemType Directory -Path C:\MedCAT-Data\models
New-Item -ItemType Directory -Path C:\MedCAT-Data\rtf_files
```

### Step 2.3: Configure Environment

```powershell
# Copy example environment file
Copy-Item envs\env -Destination .\medcat-trainer\.env

# Edit environment file
notepad .\medcat-trainer\.env
```

**Required `.env` settings**:
```env
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=medcat_trainer
DB_USER=medcat
DB_PASS=NHS_Secure_P@ssw0rd_2025  # CHANGE THIS!

# Django Configuration
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=NHS_Admin_P@ssw0rd_2025  # CHANGE THIS!
DJANGO_SUPERUSER_EMAIL=admin@nhs.uk

# Security
SECRET_KEY=GENERATE_RANDOM_50_CHAR_STRING_HERE  # CRITICAL: Generate unique key!

# OIDC (Optional - for NHS Active Directory integration)
OIDC_ENABLED=False

# File Storage (map to Windows directories)
MEDIA_ROOT=/app/media
STATIC_ROOT=/app/static
```

**Generate SECRET_KEY**:
```powershell
# Generate random secret key (Python)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 2.4: Update docker-compose.yml for Windows Paths

Edit `docker-compose.yml` to mount Windows directories:

```yaml
services:
  medcat-trainer:
    volumes:
      - C:/MedCAT-Data/media:/app/media
      - C:/MedCAT-Data/models:/app/models

  postgres:
    volumes:
      - C:/MedCAT-Data/postgres:/var/lib/postgresql/data
```

**Note**: Use forward slashes (`/`) even on Windows in Docker paths.

### Step 2.5: Start Services

```powershell
# Start containers in detached mode (background)
docker-compose up -d

# Verify containers are running
docker-compose ps

# Expected output:
# NAME                    STATE      PORTS
# medcat-trainer          running    0.0.0.0:8000->8000/tcp
# medcat-trainer-postgres running    5432/tcp
```

### Step 2.6: Verify Deployment

**From Admin RDP Session**:
1. Open browser (Chrome/Edge)
2. Navigate to: `http://localhost:8000`
3. Verify MedCAT Trainer login page appears

**Check logs**:
```powershell
# View container logs
docker-compose logs -f medcat-trainer

# Wait for this message:
# "Django version X.X, using settings 'core.settings'"
# "Starting development server at http://0.0.0.0:8000/"
```

---

## Phase 3: Multi-User RDP Access Configuration

### Step 3.1: Test RDP Access from Another Account

**From another computer (or same workstation)**:

1. **Disconnect** admin RDP session (don't log out - **Disconnect** only)
   - On RDP window: X button → Choose **Disconnect**
   - Docker containers **keep running** after disconnect

2. **RDP as clinician**:
   ```
   Computer: NHS-WORKSTATION-01 (or IP: 192.168.1.100)
   Username: NHS\dr_smith (or workstation-name\dr_smith)
   Password: {dr_smith's Windows password}
   ```

3. **Inside clinician RDP session**:
   - Open browser (Chrome/Edge)
   - Navigate to: `http://localhost:8000`
   - **Expected**: MedCAT Trainer login page appears
   - Login with **MedCAT Trainer credentials** (not Windows credentials):
     - Username: `dr_smith` (created by admin in MedCAT Trainer)
     - Password: {password set by admin}

**✅ Success Indicator**: MedCAT Trainer loads and shows clinician's projects.

### Step 3.2: Troubleshooting Multi-User Access

#### Issue: "This site can't be reached" (localhost:8000)

**Possible Causes**:
1. Docker containers not running
2. Admin logged out (instead of disconnected) and Docker stopped

**Fix**:
```powershell
# RDP as admin
# Check Docker Desktop status (system tray icon)
# If Docker is stopped, start Docker Desktop

# Check containers
docker-compose ps

# If containers stopped, restart them
cd C:\MedCAT-Trainer
docker-compose up -d
```

#### Issue: "Multiple users can't RDP at the same time"

**Cause**: Windows 10 limitation (only 1 RDP session + 1 console session)

**Fix**:
- **Short-term**: Admin disconnects before clinicians connect
- **Long-term**: Upgrade to Windows Server 2019/2022 (supports 2-10+ simultaneous RDP sessions)

#### Issue: "Clinician can RDP but MedCAT Trainer loads slowly"

**Cause**: Insufficient RAM/CPU resources

**Fix**:
```powershell
# Check resource usage
docker stats

# Increase Docker Desktop resources:
# Docker Desktop → Settings → Resources → Advanced
# - Memory: Increase to 12GB+ if available
# - CPUs: Increase to 6+ if available
```

---

## Phase 4: RTF Clinical Document Upload

### Step 4.1: Convert RTF to CSV (Preprocessing)

Since MedCAT Trainer doesn't support RTF natively, preprocess RTF files:

**From Admin RDP Session**:

```powershell
# Install Python (if not already installed)
# Download: https://www.python.org/downloads/

# Install RTF converter dependencies
cd C:\MedCAT-Trainer\scripts
pip install -r requirements-rtf.txt

# Place RTF files in directory
# Example: C:\MedCAT-Data\rtf_files\batch_1\

# Convert RTF → CSV
python rtf_to_csv_converter.py C:\MedCAT-Data\rtf_files\batch_1 C:\MedCAT-Data\clinical_notes.csv

# Output:
# Found 150 RTF files
# Processing: Patient-001.rtf
# ...
# ✅ Conversion complete: C:\MedCAT-Data\clinical_notes.csv
```

### Step 4.2: Upload CSV to MedCAT Trainer

1. Navigate to: `http://localhost:8000/admin/`
2. Login as admin
3. **Datasets** → **Add Dataset**
4. **Name**: "NHS Cardiology Batch 1"
5. **Original File**: Upload `C:\MedCAT-Data\clinical_notes.csv`
6. **Save**

**Verify**:
- Dataset shows **150 documents**
- Click dataset → View documents list
- Check: Document names match RTF filenames

---

## Phase 5: Auto-Start Configuration (Production)

### Step 5.1: Auto-Start Docker on Windows Boot

**Configure Docker Desktop**:
1. Docker Desktop → Settings → General
2. ✓ **Start Docker Desktop when you log in**
3. Apply & Restart

**Configure Auto-Login (Optional - for unattended restarts)**:

**⚠️ Security Warning**: Auto-login bypasses Windows login. Only use on physically secured workstations.

```powershell
# Run as Administrator
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v AutoAdminLogon /t REG_SZ /d 1 /f
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultUserName /t REG_SZ /d "admin_username" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultPassword /t REG_SZ /d "admin_password" /f
```

**Recommendation**: **DO NOT** use auto-login for NHS workstations. Instead, ensure admin RDPs after reboots.

### Step 5.2: Auto-Start MedCAT Trainer Containers

Create a Windows Task Scheduler task to start containers on boot:

```powershell
# Create startup script
New-Item -ItemType File -Path C:\MedCAT-Trainer\startup.bat

# Edit startup.bat
notepad C:\MedCAT-Trainer\startup.bat
```

**startup.bat contents**:
```batch
@echo off
cd C:\MedCAT-Trainer
docker-compose up -d
```

**Create Scheduled Task**:
1. Open **Task Scheduler** (taskschd.msc)
2. **Create Basic Task**:
   - Name: "MedCAT Trainer Auto-Start"
   - Trigger: **At startup**
   - Action: **Start a program**
   - Program: `C:\MedCAT-Trainer\startup.bat`
3. **Conditions**:
   - Uncheck "Start the task only if the computer is on AC power"
4. **Settings**:
   - ✓ Run task as soon as possible after a scheduled start is missed

**Test**:
```powershell
# Reboot workstation
Restart-Computer

# After reboot, verify containers auto-started
docker-compose ps
```

---

## Phase 6: Network Access (Optional - Access from Clinician Laptops)

**Current setup**: Clinicians **RDP to workstation** then access `http://localhost:8000`

**Alternative**: Clinicians access MedCAT Trainer **directly from their laptops** without RDP.

### Configuration:

**Step 6.1: Open Windows Firewall**

```powershell
# Allow port 8000 through firewall
New-NetFirewallRule -DisplayName "MedCAT Trainer" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

**Step 6.2: Update docker-compose.yml**

Change port binding from `127.0.0.1:8000` to `0.0.0.0:8000`:

```yaml
services:
  medcat-trainer:
    ports:
      - "0.0.0.0:8000:8000"  # Accessible from network
```

**Step 6.3: Restart Containers**

```powershell
docker-compose down
docker-compose up -d
```

**Step 6.4: Access from Clinician Laptop**

From clinician laptop on same NHS network:
```
http://192.168.1.100:8000  # Replace with workstation IP
```

**⚠️ Security Warning**: This exposes MedCAT Trainer to the entire NHS network. Ensure:
- Network segmentation (only cardiology department subnet)
- HTTPS/TLS encryption (add Nginx reverse proxy)
- VPN access only
- Regular security audits

**Recommendation**: **Use RDP access only** for initial NHS deployment. Network access requires additional security hardening.

---

## Troubleshooting

### Issue: Docker Desktop won't start after reboot

**Cause**: WSL2 not running

**Fix**:
```powershell
# Start WSL
wsl --update
wsl --set-default-version 2

# Restart Docker Desktop
```

### Issue: Containers fail to start with "port already in use"

**Cause**: Another service using port 8000

**Fix**:
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process by PID
taskkill /PID <PID> /F

# Restart containers
docker-compose up -d
```

### Issue: Database data lost after container restart

**Cause**: Volume mapping incorrect

**Fix**:
```powershell
# Verify volume mounts
docker-compose config

# Ensure postgres volume points to Windows directory:
# volumes:
#   - C:/MedCAT-Data/postgres:/var/lib/postgresql/data
```

---

## Production Checklist

**Before NHS Go-Live**:

- [ ] Windows Server 2019/2022 (not Windows 10) for multi-user RDP
- [ ] 16GB+ RAM, 8+ CPU cores, 256GB+ SSD
- [ ] Docker Desktop configured to auto-start
- [ ] MedCAT Trainer containers auto-start on boot (Task Scheduler)
- [ ] Admin account password changed from default
- [ ] SECRET_KEY generated (50+ random characters)
- [ ] PostgreSQL password changed from default
- [ ] HTTPS/TLS enabled (Nginx reverse proxy)
- [ ] Firewall configured (port 8000 blocked externally, allow only RDP)
- [ ] Backup strategy for PostgreSQL data (C:\MedCAT-Data\postgres)
- [ ] Backup strategy for uploaded models (C:\MedCAT-Data\models)
- [ ] Backup strategy for RTF files (C:\MedCAT-Data\rtf_files)
- [ ] UPS (Uninterruptible Power Supply) for workstation
- [ ] Physical security (locked server room)
- [ ] Audit logging enabled (Django admin logs)
- [ ] OIDC integration with NHS Active Directory (if required)
- [ ] Test RDP access from 3+ simultaneous clinician sessions
- [ ] Test failover (reboot workstation, verify auto-start)
- [ ] Document admin credentials in secure NHS password vault

---

## Summary: RDP Multi-User Access

**How it works**:

1. **Admin** installs Docker Desktop on Windows workstation
2. **Admin** runs `docker-compose up -d` (containers run in background)
3. **Admin disconnects** RDP session (containers keep running)
4. **Clinician 1** RDPs to workstation → Opens browser → `http://localhost:8000` → Logs into MedCAT Trainer
5. **Clinician 1 disconnects**, **Clinician 2** RDPs → Same process
6. **All clinicians** share the same MedCAT Trainer instance running on `localhost:8000`

**Key Insight**: `localhost` is the **physical workstation**, not the RDP session. All RDP users access the same localhost.

**Limitations**:
- Windows 10: Only 1 RDP session at a time (clinicians take turns)
- Windows Server: 2-10+ simultaneous RDP sessions (clinicians work in parallel)

**Recommendation**: **Windows Server 2019/2022** for production NHS deployment with multiple simultaneous clinicians.
