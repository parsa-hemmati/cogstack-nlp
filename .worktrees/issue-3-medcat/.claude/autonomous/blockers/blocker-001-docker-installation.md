# Blocker 001: Docker Installation Required

**Mission ID**: mvp-phase-0-task-1
**Created**: 2025-11-17T00:00:00Z
**Status**: pending_human_input
**Priority**: P0 (Blocking all subsequent tasks)

---

## Issue

Autonomous execution cannot install Docker Desktop on the user's workstation. This requires manual installation by the user.

## Context

- **Spec file**: `.specify/specifications/clinical-care-tools-base-app.md`
- **Task section**: "Phase 0: Environment Setup - Task 0.1"
- **Estimated time**: 1 hour (manual)

**Requirements**:
- Workstation with 8+ GB RAM, 4+ CPU cores
- Windows or Linux OS
- Docker Desktop 24.0+
- Docker Compose 2.20+

## Question for Human

**Has Docker Desktop already been installed on this workstation?**

Please verify by running:
```bash
docker --version
docker-compose --version
docker run hello-world
```

## Action Required

### Option A: Docker Already Installed

If Docker is already installed and the commands above work:
1. Update mission status in `.claude/autonomous/progress.json`:
   ```json
   {
     "mission_id": "mvp-phase-0-task-1",
     "status": "completed"
   }
   ```
2. Remove this blocker file
3. Autonomous execution will continue with Mission 0.3

### Option B: Docker Not Installed

If Docker is not installed:

**Manual Steps**:
1. **Download Docker Desktop**
   - Visit: https://www.docker.com/products/docker-desktop
   - Download Docker Desktop 24.0+ for your OS (Windows/Linux)

2. **Install Docker Desktop**
   - Run installer with default settings
   - Restart machine if prompted

3. **Configure Resources**
   - Open Docker Desktop settings
   - Set RAM: **8 GB minimum**
   - Set CPUs: **4 cores minimum**
   - Set disk space: **50 GB minimum**
   - Save and restart Docker Desktop

4. **Verify Installation**
   ```bash
   # Check versions
   docker --version          # Should be >= 24.0
   docker-compose --version  # Should be >= 2.20

   # Test Docker
   docker run hello-world    # Should output success message
   ```

5. **Update Mission Status**
   Once verified, update `.claude/autonomous/progress.json`:
   ```json
   {
     "mission_id": "mvp-phase-0-task-1",
     "status": "completed",
     "completed_at": "<timestamp>",
     "actual_hours": 1.0,
     "notes": "Docker Desktop installed manually by user"
   }
   ```

6. **Resume Autonomous Execution**
   Autonomous execution will automatically continue with Mission 0.3.

## Acceptance Criteria

- [ ] `docker --version` shows version >= 24.0
- [ ] `docker-compose --version` shows version >= 2.20
- [ ] Docker Desktop shows 8GB RAM, 4 CPU cores allocated
- [ ] `docker run hello-world` executes successfully

## Impact if Not Resolved

**Blocks missions**:
- mvp-phase-0-task-2 (Download MedCAT Models)
- mvp-phase-0-task-3 (Create Docker Compose Configuration)
- mvp-phase-0-task-4 (Setup PostgreSQL Database)
- mvp-phase-0-task-5 (Setup Redis Cache)
- mvp-phase-0-task-6 (Setup CogStack-ModelServe)
- mvp-phase-0-task-7 (Create Environment Verification Script)
- **All subsequent MVP phases**

**Timeline impact**: +1 day (waiting for manual installation)

## Recommended Action

**Install Docker Desktop manually** using Option B steps above. This is a one-time setup that enables all subsequent autonomous execution.

---

**Next Blocker**: [blocker-002-medcat-models.md](blocker-002-medcat-models.md)
