---
name: architecture-decision-helper
description: Guides backend architecture decisions for new features (FastAPI vs Django). Use when implementing new APIs, planning microservices, or extending existing systems. Analyzes requirements to recommend stateless FastAPI microservices for clinical care tools or stateful Django extensions for annotation workflows. Ensures consistency with dual-backend architecture (ADR-002).
---

# Architecture Decision Helper

## When to use this skill

Activate when:
- Planning new API endpoints or services
- Deciding between FastAPI vs Django for new features
- Architecting microservices vs monolith extensions
- Integrating new clinical care tools with existing infrastructure
- Reviewing architecture decisions in technical plans

## Dual Backend Architecture (ADR-002)

The repository uses **two backend frameworks** for different purposes:

### FastAPI (Stateless Microservices)
**Use for**:
- Clinical care tool APIs (patient search, timeline, CDS)
- Stateless NLP processing services
- External integrations (FHIR, EHR APIs)
- High-throughput, async operations
- Services that scale horizontally

**Pattern**:
```
New Feature API (FastAPI)
  ↓ async/await
MedCAT Service (FastAPI)
  ↓ async calls
External Services (Elasticsearch, FHIR)
```

**When to choose FastAPI**:
- ✅ No complex user sessions
- ✅ RESTful API only (no web UI)
- ✅ Async/await benefits (I/O-bound)
- ✅ Needs horizontal scaling
- ✅ Independent deployment
- ✅ Stateless operations

**Example use cases**:
- `/api/v1/patients/search` - Patient search API
- `/api/v1/timeline/{patient_id}` - Timeline data API
- `/api/v1/cds/alerts` - Clinical decision support alerts

### Django REST Framework (Stateful Web Apps)
**Use for**:
- Annotation workflows (extends MedCAT Trainer)
- User management and complex RBAC
- Stateful operations (sessions, wizards)
- Admin interfaces
- Full-stack web applications

**Pattern**:
```
MedCAT Trainer Extension (Django)
  ↓ Django ORM
PostgreSQL (95 migrations)
  ↓ Foreign keys
Existing Models (Project, User, Document)
```

**When to choose Django**:
- ✅ Extends MedCAT Trainer
- ✅ Needs Django ORM + migrations
- ✅ Uses existing User/Project models
- ✅ Web UI + API together
- ✅ Complex sessions/workflows
- ✅ Built-in admin interface

**Example use cases**:
- MedCAT Trainer new annotation modes
- Project management features
- User permission management

## Decision Tree

### Question 1: Does it extend MedCAT Trainer?
- **YES** → Use Django (easier to integrate with existing 95 migrations)
- **NO** → Continue to Question 2

### Question 2: Does it need user sessions or complex state?
- **YES** → Use Django (session management built-in)
- **NO** → Continue to Question 3

### Question 3: Is it a pure API (no web UI)?
- **YES** → Use FastAPI (async, lightweight)
- **NO** → Continue to Question 4

### Question 4: Does it need Django ORM models?
- **YES** → Use Django
- **NO** → Use FastAPI + SQLAlchemy (if database needed)

### Question 5: Will it scale independently?
- **YES** → Use FastAPI (easier horizontal scaling)
- **NO** → Either works, prefer simpler deployment

## Clinical Care Tools Recommendation

For **NEW clinical care tools** (patient search, timeline, CDS):

**Recommended**: **FastAPI + Vue 3 frontend**

**Rationale**:
- ✅ Stateless APIs for clinical queries
- ✅ Independent scaling from Trainer
- ✅ Async performance for Elasticsearch/MedCAT
- ✅ Vue 3 frontend reuses Trainer patterns (31 Vue files)
- ✅ Clean separation from annotation workflows
- ✅ Easier to deploy in different environments

**Architecture**:
```
Vue 3 Frontend (Clinical Care UI)
  ↓ HTTP
FastAPI Backend (Clinical Care APIs)
  ↓ HTTP (async)
MedCAT Service (NLP processing)
  ↓ Elasticsearch
Clinical Documents
```

**Authentication**: Shared OIDC provider (Keycloak) with both Trainer and new tools

## Anti-Patterns to Avoid

❌ **Don't**: Create Django app for stateless APIs
- Overhead of sessions, middleware, ORM when not needed

❌ **Don't**: Create FastAPI service that duplicates Django models
- Creates data sync issues, violates DRY

❌ **Don't**: Mix FastAPI and Django in same service
- Unnecessary complexity

✅ **Do**: Choose one framework per service
✅ **Do**: Communicate between services via REST APIs
✅ **Do**: Share authentication via OIDC

## Integration Patterns

### Pattern A: FastAPI calls Django API
```python
# FastAPI service
async def get_project_config(project_id: str):
    # Call MedCAT Trainer Django API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://trainer:8000/api/projects/{project_id}/",
            headers={"Authorization": f"Token {token}"}
        )
        return response.json()
```

### Pattern B: Django calls FastAPI service
```python
# Django view
import requests

def process_clinical_note(request):
    # Call MedCAT Service (FastAPI)
    response = requests.post(
        "http://medcat-service:5000/api/process",
        json={"text": request.data["text"]},
        timeout=5
    )
    return Response(response.json())
```

### Pattern C: Shared OIDC authentication
```yaml
# docker-compose.yml
services:
  keycloak:
    image: quay.io/keycloak/keycloak:latest

  trainer-django:
    environment:
      - OIDC_CLIENT_ID=medcat-trainer
      - OIDC_ISSUER=http://keycloak:8080/realms/cogstack

  clinical-tools-fastapi:
    environment:
      - OIDC_CLIENT_ID=clinical-tools
      - OIDC_ISSUER=http://keycloak:8080/realms/cogstack
```

## Checklist for Architecture Review

Before implementing, confirm:

**For FastAPI**:
- [ ] No complex Django ORM relationships needed
- [ ] Stateless operations (no sessions)
- [ ] Async I/O benefits (Elasticsearch, HTTP calls)
- [ ] Can deploy independently
- [ ] RESTful API only (or separate Vue frontend)

**For Django**:
- [ ] Extends MedCAT Trainer functionality
- [ ] Needs Django models + migrations
- [ ] Complex user workflows/sessions
- [ ] Built-in admin interface useful
- [ ] Web UI + API together

## Example Decisions

### ✅ CORRECT: Patient Search API (FastAPI)
```
Feature: /api/v1/patients/search
Decision: FastAPI
Rationale:
  ✓ Stateless search queries
  ✓ Async Elasticsearch calls
  ✓ Independent scaling
  ✓ No Django ORM needed
  ✓ High throughput required
```

### ✅ CORRECT: Annotation Mode Extension (Django)
```
Feature: New annotation workflow in Trainer
Decision: Django (extend MedCAT Trainer)
Rationale:
  ✓ Uses existing Project model
  ✓ Needs Django migrations
  ✓ Integrates with Trainer UI
  ✓ Uses Django auth/sessions
  ✓ Reuses 95 existing migrations
```

### ❌ INCORRECT: Patient Search in Django
```
Feature: /api/v1/patients/search
Decision: Django app in Trainer
Problem:
  ✗ Adds stateful overhead for stateless API
  ✗ Couples clinical tools to annotation platform
  ✗ Can't scale search independently
  ✗ Async Elasticsearch harder in Django
```

## References

- **ADR-002**: Technology Stack (dual backend rationale)
- **MedCAT Trainer**: `/medcat-trainer/` (Django example)
- **MedCAT Service**: `/medcat-service/` (FastAPI example)
- **Integration patterns**: `medcat-architecture` skill
