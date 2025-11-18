# Technical Plan: Clinical Decision Support + Meditech Integration (Sprint 6)

**Version**: 1.0.0
**Date**: 2025-11-18
**Sprint Duration**: 12 weeks (~360 hours)
**Dependencies**: Sprints 1-5.5, Meditech Expanse sandbox access

---

## Overview

### Goals

- **Meditech Patient Data Read**: OAuth 2.0 auth, read Patient/Condition/Observation/MedicationRequest via FHIR R4
- **CDS Engine**: Clinical guidelines (ADA, AHA, USPSTF, NICE), rule engine, evidence grading
- **Drug Interaction Checking**: NHS dm+d database, interaction detection, severity classification
- **Meditech Write Operations**: Create MedicationRequest, ServiceRequest, Task, CommunicationRequest (draft orders)
- **Clinical Governance**: RBAC, approval workflows, safety checks, override tracking
- **Audit Logging**: All Meditech API calls, CDS recommendations, clinician actions logged

### Success Criteria

- [ ] Meditech read integration operational (Patient, Condition, Observation, MedicationRequest)
- [ ] CDS generates evidence-based recommendations for ≥5 guidelines
- [ ] Drug interaction checking with ≥99% accuracy (contraindicated/major interactions)
- [ ] Meditech write integration operational (draft MedicationRequest, ServiceRequest, Task)
- [ ] Clinical governance: draft orders only, safety checks, RBAC
- [ ] Audit logging for all operations
- [ ] 80% test coverage

---

## Architecture (High-Level)

```
Frontend → Backend API → CDS Engine → Meditech FHIR API (read/write)
                      ↓
               Drug Interaction DB (NHS dm+d)
                      ↓
               Clinical Guidelines DB (ADA, AHA, etc.)
```

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| FHIR Integration | fhir.resources (Python) | 7.1 |
| OAuth 2.0 | authlib | 1.3 |
| Guidelines DB | PostgreSQL JSON | 15 |
| Drug Interaction | NHS dm+d + OpenFDA | 2024 |
| CDS Hooks | Custom implementation | 1.0 |

---

## Key Technical Decisions

1. **Week 0 Verification**: MUST verify Meditech sandbox capabilities before sprint starts
2. **Draft Orders Only**: CDS creates draft orders (status="draft"), clinician approval required
3. **Safety Checks**: Drug allergies, contraindications, duplicate orders checked before write
4. **Caching**: Patient data cached (5-minute TTL) to reduce Meditech API calls
5. **Circuit Breaker**: If Meditech API fails 5 times in 1 minute, stop calling for 5 minutes

---

## Implementation Phases

### Phase 6.1: CDS Core Infrastructure (3 weeks, 90h)
- CDS Hooks spec implementation (if Meditech supports)
- FHIR R4 client library integration
- Clinical guidelines database setup
- Rule engine (IF-THEN logic, time-based conditions)
- Audit logging

### Phase 6.2: Meditech Read Integration (2 weeks, 60h)
- OAuth 2.0 authentication with meditech-uk.cloud
- FHIR read operations (Patient, Condition, Observation, MedicationRequest)
- NHS FHIR UK Core profile mapping
- Patient data caching (Redis)
- Error handling

### Phase 6.3: Drug Interaction Checking (1 week, 30h)
- Download NHS dm+d from TRUD
- Drug interaction database setup
- Interaction detection logic
- Alternative medication suggestions

### Phase 6.4: Meditech Write Integration (3 weeks, 90h)
- POST MedicationRequest, ServiceRequest, Task, CommunicationRequest
- NHS FHIR UK Core write validation
- Transaction bundles (atomic writes)
- Write error handling

### Phase 6.5: Clinical Governance & RBAC (1 week, 30h)
- Role-based write permissions
- Approval workflows (draft orders)
- Clinical safety checks
- Override tracking

### Phase 6.6: Meditech Workflow Integration (1 week, 30h)
- InBasket integration (alerts in Meditech inbox)
- Order entry pre-population
- Task creation
- UI testing

### Phase 6.7: Testing & Validation (1 week, 30h)
- Unit tests, integration tests, UAT
- Performance testing
- Security review

---

## Risks & Mitigations

**Risk 1**: Meditech FHIR API capabilities unknown → **Week 0 verification checklist mandatory**
**Risk 2**: NHS dm+d medication code mapping complex → **Multi-code-system drug interaction DB**
**Risk 3**: Clinical safety concerns (automated ordering) → **Draft orders only, safety checks, pilot program**

---

**Estimated Effort**: 360 hours over 12 weeks
