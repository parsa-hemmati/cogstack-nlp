# Clinical Care Tools: Complete Product Roadmap

**Version**: 2.0.0
**Date**: 2025-11-17
**Status**: Revised After Critical Analysis
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]

**Version History**:
- **1.0.0** (2025-11-17): Initial 47-week roadmap
- **2.0.0** (2025-11-17): **MAJOR UPDATE** - Revised to 69-week timeline after comprehensive critical analysis, Meditech Expanse bidirectional integration, added 20% buffer, Sprint 5.5 (Event Bus), Sprint 9.5 (Hardening)

---

## Executive Summary

**Vision**: Build a comprehensive, modular platform that leverages the full potential of CogStack NLP to transform healthcare research, delivery, and governance.

**Scope**: Complete CogStack product suite (all 6 products) over 9 sprints + 2 hardening sprints

**Timeline**: **69 weeks (~16 months)** from MVP to production-ready platform (**revised from 47 weeks**)

**Effort**: **2,130 hours** total development effort (**revised from 1,410 hours**)

**Budget**: **~$433,000** total project cost (**revised from $206,000**)

**Coverage**: 100% of CogStack products (vs 26% in original plan)

**Key Revisions in v2.0**:
- ✅ **Sprint 6 expanded**: 5 weeks → 12 weeks (Meditech Expanse bidirectional integration with NHS FHIR UK Core)
- ✅ **20% buffer added**: All sprints include contingency for rework, bug fixes, optimization
- ✅ **Sprint 5.5 added**: Event Bus Foundation (1 week, 30 hours) - enables module communication
- ✅ **Sprint 9.5 added**: Hardening Sprint (3 weeks, 110 hours) - monitoring, training, disaster recovery
- ✅ **Realistic timeline**: Based on critical analysis of healthcare project complexity

---

## CogStack Product Suite Coverage

| CogStack Product | Sprints | Status | Coverage |
|-----------------|---------|--------|----------|
| **Clinical Language AI** | MVP, All Sprints | ✅ PLANNED | 100% |
| **Enterprise-grade Search** | MVP, Sprint 1, 2, 3 | ✅ PLANNED | 100% |
| **EHR De-Identification** | Sprint 4 | ✅ PLANNED | 100% |
| **Clinical Coding** | Sprint 5 | ✅ PLANNED | 100% |
| **Automated Alerting** | Sprint 7 | ✅ PLANNED | 100% |
| **Population Health Dashboards** | Sprint 8, 9 | ✅ PLANNED | 100% |

**Total Coverage**: 100% (6/6 products)

---

## Roadmap Timeline (v2.0 - Revised)

```
Week 0 (CRITICAL): Meditech API Verification (1.5 weeks, parallel to MVP planning)

Week 1 ─────────────────────────────────────────────────────────────────────── Week 69

MVP (Base App + Patient Search)
├─ Phase 0-7: 14 weeks (revised from 11 weeks)
├─ ~388 hours (310h + 20% buffer + ModelServe verification)
└─ Week 1-14

Sprint 2 (Timeline View)
├─ 5 weeks (revised from 4 weeks)
├─ ~144 hours (120h + 20% buffer)
└─ Week 15-19

Sprint 3 (Full-Text Search)
├─ 6 weeks (revised from 4 weeks)
├─ ~168 hours (120h + 20% buffer + Elasticsearch optimization)
└─ Week 20-25

Sprint 4 (De-Identification)
├─ 5 weeks (revised from 4 weeks)
├─ ~144 hours (120h + 20% buffer)
└─ Week 26-30

Sprint 5 (Clinical Coding)
├─ 5 weeks (revised from 4 weeks)
├─ ~144 hours (120h + 20% buffer)
└─ Week 31-35

Sprint 5.5 (Event Bus Foundation) **[NEW in v2.0]**
├─ 1 week
├─ ~30 hours (Redis pub/sub for module communication)
└─ Week 36

Sprint 6 (Clinical Decision Support + Meditech Expanse) **[EXPANDED in v2.0]**
├─ 12 weeks (revised from 5 weeks) ⚠️ CRITICAL EXPANSION
├─ ~360 hours (bidirectional FHIR R4, NHS UK Core, dm+d codes, clinical governance)
└─ Week 37-48

Sprint 7 (Automated Alerting)
├─ 6 weeks (revised from 5 weeks)
├─ ~180 hours (150h + 20% buffer)
└─ Week 49-54

Sprint 8 (Population Health Dashboards)
├─ 6 weeks (revised from 5 weeks)
├─ ~180 hours (150h + 20% buffer)
└─ Week 55-60

Sprint 9 (Advanced Analytics)
├─ 6 weeks (revised from 5 weeks)
├─ ~180 hours (150h + 20% buffer)
└─ Week 61-66

Sprint 9.5 (Hardening Sprint) **[NEW in v2.0]**
├─ 3 weeks
├─ ~110 hours (monitoring, user training, disaster recovery, resilience patterns)
└─ Week 67-69

─────────────────────────────────────────────────────────────────────────────────
Total: 69 weeks (~16 months), ~2,130 hours

v1.0 → v2.0 Changes:
- Timeline: 47 weeks → 69 weeks (+22 weeks / +47% increase)
- Effort: 1,410 hours → 2,130 hours (+720 hours / +51% increase)
- Reason: Meditech bidirectional integration, 20% buffer, hardening sprint, realistic healthcare project timeline
```

---

## Sprint Breakdown

### MVP: Base Application + Patient Search (Weeks 1-11)

**Duration**: 11 weeks | **Effort**: ~310 hours

**Deliverables**:
- ✅ Base application infrastructure (auth, audit, module system)
- ✅ Patient Search module (SNOMED-CT concepts, meta-annotation filtering)
- ✅ CogStack-ModelServe integration (SNOMED, De-ID models)
- ✅ Docker Compose deployment
- ✅ HIPAA/GDPR compliance (audit logging, session security, data retention)

**Dependencies**: None (foundational)

**CogStack Products**: Clinical Language AI (80%), Enterprise-grade Search (40%)

**Specification**: `.specify/specifications/clinical-care-tools-base-app.md`
**Plan**: `.specify/plans/clinical-care-tools-base-plan.md`
**Tasks**: `.specify/tasks/clinical-care-tools-base-tasks.md`

---

### Sprint 2: Timeline View Module (Weeks 12-15)

**Duration**: 4 weeks | **Effort**: ~120 hours

**Deliverables**:
- ✅ Chronological document timeline visualization (D3.js)
- ✅ Clinical concept timeline (events on timeline)
- ✅ Temporal pattern detection (first mention vs recurring)
- ✅ Export to PDF, FHIR R4, JSON

**Dependencies**: MVP (Patient Search, CogStack-ModelServe)

**CogStack Products**: Enterprise-grade Search (visualization component)

**Specification**: `.specify/specifications/sprint-2-timeline-view.md`

---

### Sprint 3: Full-Text Search Enhancement (Weeks 16-19)

**Duration**: 4 weeks | **Effort**: ~120 hours

**Deliverables**:
- ✅ Document-level full-text search (Elasticsearch)
- ✅ Structured field exploration (filter by type, author, date, department)
- ✅ Advanced query builder (Boolean operators, field-specific search)
- ✅ Relevance ranking (BM25 scoring, field boosting)
- ✅ Saved searches, search analytics

**Dependencies**: MVP (documents indexed in Elasticsearch)

**CogStack Products**: Enterprise-grade Search (full-text search across millions of records)

**Specification**: `.specify/specifications/sprint-3-full-text-search.md`

---

### Sprint 4: EHR De-Identification Module (Weeks 20-23)

**Duration**: 4 weeks | **Effort**: ~120 hours

**Deliverables**:
- ✅ Automated PHI detection (CogStack-ModelServe `medcat_deid` model)
- ✅ De-identification strategies (Redaction, Safe Harbor, Masking, Generalization, Pseudonymization)
- ✅ Batch processing (Celery workers)
- ✅ Export de-identified corpus (Text, JSON, FHIR)
- ✅ Quality assurance (manual review workflow)

**Dependencies**: MVP (CogStack-ModelServe DeID model)

**CogStack Products**: EHR De-Identification

**Specification**: `.specify/specifications/sprint-4-ehr-deidentification.md`

---

### Sprint 5: Clinical Coding Module (Weeks 24-27)

**Duration**: 4 weeks | **Effort**: ~120 hours

**Deliverables**:
- ✅ Automated ICD-10 extraction (CogStack-ModelServe `medcat_icd10` model)
- ✅ Clinical coder assistance UI (review AI suggestions, add codes)
- ✅ Code validation (format, existence, combinations)
- ✅ Coding quality metrics (precision, recall, productivity)
- ✅ Bulk coding workflow

**Dependencies**: MVP (CogStack-ModelServe ICD-10 model)

**CogStack Products**: Clinical Coding

**Specification**: `.specify/specifications/sprint-5-clinical-coding.md`

---

### Sprint 5.5: Event Bus Foundation (Week 36) **[NEW in v2.0]**

**Duration**: 1 week | **Effort**: ~30 hours

**Deliverables**:
- ✅ Redis pub/sub for module events (ICD10_CODES_UPDATED, PATIENT_DATA_CHANGED)
- ✅ Event schema standardization (event type, patient_id, payload)
- ✅ Module subscription patterns (Sprint 7 Alerting, Sprint 8 Dashboards subscribe to events)
- ✅ Event logging for debugging

**Dependencies**: MVP (Redis already deployed)

**Why Added**: Prevents tight coupling between modules. Sprint 5 (ICD-10 coding) feeds Sprint 6-8, but no event bus → modules query each other's tables directly (brittle). Event bus enables loose coupling.

**Specification**: To be created before Sprint 5.5 starts

---

### Sprint 6: Clinical Decision Support + Meditech Expanse Integration (Weeks 37-48) **[EXPANDED in v2.0]**

**Duration**: 12 weeks (revised from 5 weeks) | **Effort**: ~360 hours (revised from 150 hours)

**⚠️ CRITICAL EXPANSION**: Bidirectional Meditech Expanse integration (read + write) vs original read-only CDS

**Deliverables**:
- ✅ **Meditech Read Integration**: OAuth 2.0 with meditech-uk.cloud, read Patient/Condition/Observation/MedicationRequest via FHIR R4 API
- ✅ **Clinical Decision Support Engine**: Clinical guidelines database (ADA, AHA, USPSTF, NICE), rule engine, evidence grading (A/B/C)
- ✅ **Drug Interaction Checking**: NHS dm+d medication database, interaction detection, alternative suggestions
- ✅ **Meditech Write Integration** (NEW): Create draft MedicationRequest, ServiceRequest, Task, CommunicationRequest in Meditech
- ✅ **Clinical Governance** (NEW): RBAC for write permissions, approval workflows (draft orders), clinical safety checks (allergies, contraindications)
- ✅ **Meditech Workflow Integration** (NEW): InBasket integration, order entry pre-population, task creation
- ✅ **NHS FHIR UK Core Compliance** (NEW): NHS numbers, ODS codes, dm+d codes, SNOMED CT UK edition
- ✅ **Comprehensive Audit Logging**: All Meditech API calls (read + write), CDS recommendations, clinician actions

**Dependencies**:
- MVP
- Sprint 5 (ICD-10 codes for guideline matching)
- **Week 0 Meditech API Verification** (MUST complete before Sprint 6 starts - see `.specify/week-0-meditech-verification-checklist.md`)

**CogStack Products**: Clinical Decision Support (though not explicitly in CogStack suite, fills critical gap)

**EHR Platform**: Meditech Expanse on meditech-uk.cloud (sandbox + test + production environments)

**Integration Type**: Bidirectional FHIR R4 (read patient data from Meditech, write draft orders to Meditech)

**Specification**: `.specify/specifications/sprint-6-clinical-decision-support.md` (v2.0 - updated for Meditech bidirectional integration)

**Risks**:
- 🔴 **HIGH**: Meditech API write permissions may not be granted (contingency: reduce to read-only CDS, 6 weeks instead of 12 weeks)
- 🟡 **MEDIUM**: NHS dm+d medication code mapping complexity if Meditech uses RxNorm instead
- 🟡 **MEDIUM**: Clinical governance may reject automated ordering (contingency: draft orders only with clinician approval)

**Critical Success Factors**:
- ✅ Complete Week 0 Meditech API verification BEFORE Sprint 6 starts
- ✅ Obtain Meditech write permissions for MedicationRequest, ServiceRequest, Task
- ✅ Engage NHS trust clinical safety officer early (Week 4-6)

---

### Sprint 7: Automated Alerting Module (Weeks 33-37)

**Duration**: 5 weeks | **Effort**: ~150 hours

**Deliverables**:
- ✅ Real-time event detection engine (drug combos, comorbidities, demographics)
- ✅ Automated notification infrastructure (Email, SMS, in-app)
- ✅ Alert management UI (inbox, acknowledge, dismiss, snooze)
- ✅ Alert rules engine (admin configures rules)
- ✅ Escalation workflows (unacknowledged alerts escalate)

**Dependencies**: MVP, Patient data integration

**CogStack Products**: Automated Alerting

**Specification**: `.specify/specifications/sprint-7-automated-alerting.md`

---

### Sprint 8: Population Health Dashboards (Weeks 38-42)

**Duration**: 5 weeks | **Effort**: ~150 hours

**Deliverables**:
- ✅ Cohort analytics dashboard (disease prevalence, demographics, trends)
- ✅ Quality metrics dashboard (HbA1c control, BP control, screening rates)
- ✅ Service planning dashboard (patient volumes, clinic capacity, wait times)
- ✅ Clinical audit dashboard (guideline adherence, outcome trends)
- ✅ Data export (CSV, Excel, PDF, API access)

**Dependencies**: MVP, ICD-10 codes, quality metrics definitions

**CogStack Products**: Population Health/Caseload Dashboards

**Specification**: `.specify/specifications/sprint-8-population-health-dashboards.md`

---

### Sprint 9: Advanced Analytics Module (Weeks 43-47)

**Duration**: 5 weeks | **Effort**: ~150 hours

**Deliverables**:
- ✅ Registry support (diabetes, cancer, chronic disease registries)
- ✅ Cohort deep phenotyping (comprehensive characterization)
- ✅ Custom report builder (visual query builder, no SQL required)
- ✅ Data export for statistical analysis (R, Python, SAS)
- ✅ Predictive analytics (optional: risk stratification, survival analysis)

**Dependencies**: MVP, Registries infrastructure

**CogStack Products**: Population Health/Caseload Dashboards (advanced features)

**Specification**: `.specify/specifications/sprint-9-advanced-analytics.md`

---

### Sprint 9.5: Hardening & Production Readiness (Weeks 67-69) **[NEW in v2.0]**

**Duration**: 3 weeks | **Effort**: ~110 hours

**Why Added**: v1.0 roadmap had NO time for monitoring, user training, disaster recovery, or resilience patterns. These are CRITICAL for production healthcare systems.

**Deliverables**:
- ✅ **Monitoring Stack** (30 hours):
  - Prometheus metrics for FastAPI, Elasticsearch, PostgreSQL, Meditech API
  - Grafana dashboards (response times, error rates, resource usage)
  - Alerting (email/SMS if service down >5 minutes)

- ✅ **User Onboarding & Training** (40 hours):
  - Video tutorials (5-10 minutes per module: Patient Search, Timeline, CDS, etc.)
  - In-app help tooltips and guided tours
  - User guide PDF (20-30 pages)
  - Admin training session (2 hours live)

- ✅ **Disaster Recovery** (20 hours):
  - Test backup restore (PostgreSQL, Elasticsearch)
  - Document rollback procedures (database migration, code deployment)
  - Practice disaster recovery scenario (simulate server failure)

- ✅ **Resilience Patterns** (20 hours):
  - Circuit breaker for CogStack-ModelServe, Meditech API, Elasticsearch
  - Fallback logic (if ModelServe down, show cached concepts or warning message)
  - Retry with exponential backoff

**Dependencies**: Sprints 1-9 complete

**Why Critical**: Production healthcare systems CANNOT be deployed without:
- Monitoring (how do you know if services are down?)
- Training (clinicians won't use unfamiliar tools)
- Disaster recovery (what if database corrupts?)
- Resilience (what if Meditech API is temporarily unavailable?)

**Specification**: To be created before Sprint 9.5 starts

---

## Dependency Graph

```
MVP (Base App + Patient Search)
  ↓
  ├─→ Sprint 2 (Timeline View)
  ├─→ Sprint 3 (Full-Text Search)
  ├─→ Sprint 4 (De-Identification)
  ├─→ Sprint 5 (Clinical Coding)
  ├─→ Sprint 6 (Clinical Decision Support)
  ├─→ Sprint 7 (Automated Alerting)
  ├─→ Sprint 8 (Population Health Dashboards)
  └─→ Sprint 9 (Advanced Analytics)

All sprints depend on MVP. Sprints 2-9 are independent of each other (can be parallelized if resources available).
```

---

## Resource Allocation

### Development Team Composition (Recommended)

**For Sequential Execution** (1 sprint at a time):
- **1 Full-Stack Developer** (Backend + Frontend)
- **1 DevOps Engineer** (part-time, for deployment/infrastructure)
- **1 Clinical SME** (part-time, for requirements/testing)

**For Parallel Execution** (2-3 sprints at a time):
- **2-3 Full-Stack Developers**
- **1 DevOps Engineer** (full-time)
- **1 Clinical SME** (full-time)
- **1 Project Manager** (coordinate parallel work)

### Effort Breakdown by Sprint

| Sprint | Effort (hours) | Weeks | Team Size | Parallel? |
|--------|---------------|-------|-----------|-----------|
| MVP | 310 | 11 | 1 dev | No (foundational) |
| Sprint 2 | 120 | 4 | 1 dev | Yes (after MVP) |
| Sprint 3 | 120 | 4 | 1 dev | Yes (after MVP) |
| Sprint 4 | 120 | 4 | 1 dev | Yes (after MVP) |
| Sprint 5 | 120 | 4 | 1 dev | Yes (after MVP) |
| Sprint 6 | 150 | 5 | 1 dev | Yes (after MVP) |
| Sprint 7 | 150 | 5 | 1 dev | Yes (after MVP) |
| Sprint 8 | 150 | 5 | 1 dev | Yes (after MVP) |
| Sprint 9 | 150 | 5 | 1 dev | Yes (after MVP) |
| **Total** | **1,410** | **47** | - | - |

**Sequential Timeline**: 47 weeks (~11 months)
**Parallel Timeline** (3 devs after MVP): ~25 weeks (~6 months)

---

## Milestones & Deliverables

### Milestone 1: MVP Complete (Week 11)
**Deliverable**: Base application + Patient Search deployed
**Success Criteria**:
- [ ] Users can search for patients by clinical concepts
- [ ] Meta-annotation filtering works (95% precision)
- [ ] Audit logging functional
- [ ] Docker Compose deployment successful

### Milestone 2: Search & Visualization Complete (Week 19)
**Deliverable**: Timeline View + Full-Text Search deployed
**Success Criteria**:
- [ ] Clinicians can view patient timeline
- [ ] Full-text search across documents functional
- [ ] Export to PDF/FHIR working

### Milestone 3: Research Enablement Complete (Week 27)
**Deliverable**: De-Identification + Clinical Coding deployed
**Success Criteria**:
- [ ] Researchers can de-identify datasets
- [ ] Clinical coders can review AI-suggested codes
- [ ] De-identified exports available

### Milestone 4: Decision Support Complete (Week 37)
**Deliverable**: CDS + Automated Alerting deployed
**Success Criteria**:
- [ ] CDS Hooks integrated with EHR
- [ ] Alerts triggered for critical events
- [ ] Clinicians receive notifications

### Milestone 5: Analytics Complete (Week 47)
**Deliverable**: Population Health Dashboards + Advanced Analytics deployed
**Success Criteria**:
- [ ] Population health dashboards functional
- [ ] Registries created and populated
- [ ] Custom reports working

---

## Risk Management

### High-Risk Items

**Risk 1: CogStack-ModelServe Model Availability**
- **Impact**: High (blocks multiple sprints)
- **Mitigation**: Verify models available before starting sprints (medcat_snomed, medcat_deid, medcat_icd10)
- **Contingency**: Use MedCAT v2 library directly if ModelServe unavailable

**Risk 2: EHR Integration Complexity (Sprint 6)**
- **Impact**: Medium (may delay Sprint 6)
- **Mitigation**: Start EHR integration discussions early, use sandbox environments for testing
- **Contingency**: MVP: Standalone CDS (no EHR integration), Phase 2: EHR integration

**Risk 3: Alert Fatigue (Sprint 7)**
- **Impact**: Medium (low adoption if too many false positives)
- **Mitigation**: Start with conservative alert thresholds, iterate based on clinician feedback
- **Contingency**: Admin configurable alert sensitivity

**Risk 4: Performance at Scale (Sprints 8-9)**
- **Impact**: Medium (dashboards slow for large datasets)
- **Mitigation**: Performance testing early, optimize queries, use Elasticsearch aggregations
- **Contingency**: Implement caching, pagination, background jobs for slow queries

---

## Success Metrics

### MVP Success Metrics
- [ ] 10 concurrent users supported
- [ ] Patient search response time <500ms
- [ ] 95% precision for concept extraction (with meta-annotations)
- [ ] Zero PHI exposure incidents (audit logs reviewed)

### Sprint 2 Success Metrics
- [ ] Timeline loads <2 seconds for <100 documents
- [ ] 90% clinician satisfaction (timeline useful for clinical decisions)
- [ ] PDF exports used (>50% of clinicians export timelines)

### Sprint 3 Success Metrics
- [ ] Search response time <1 second for simple queries
- [ ] 80% of searches successful (not zero results)
- [ ] Saved searches used (>30% of users save complex queries)

### Sprint 4 Success Metrics
- [ ] PHI detection recall ≥95%, precision ≥90%
- [ ] De-identified datasets used for research (>10 exports per month)
- [ ] Zero re-identification incidents (manual reviews show no PHI remaining)

### Sprint 5 Success Metrics
- [ ] ICD-10 extraction precision ≥90%, recall ≥85%
- [ ] Coder productivity increase (30% faster than manual coding)
- [ ] Coding accuracy maintained (≥95% accuracy)

### Sprint 6 Success Metrics
- [ ] CDS Hooks response time <2 seconds
- [ ] Alert acceptance rate >50% (clinicians act on CDS suggestions)
- [ ] Drug interaction alerts reduce adverse events (measured via incident reporting)

### Sprint 7 Success Metrics
- [ ] Alert delivery success rate ≥99.9%
- [ ] Alert response time <15 minutes (median)
- [ ] False positive rate <20%

### Sprint 8 Success Metrics
- [ ] Dashboard load time <3 seconds
- [ ] Quality metrics used for service improvement (documented use cases)
- [ ] Scheduled reports delivered (>80% success rate)

### Sprint 9 Success Metrics
- [ ] Registries populated and maintained (>3 active registries)
- [ ] Custom reports created (>50 reports saved)
- [ ] Data exports used for research (>10 publications citing platform)

---

## Stakeholder Communication

### Weekly Updates
- **Audience**: Development team, project sponsor
- **Content**: Progress, blockers, upcoming work
- **Format**: Standup notes, email summary

### Sprint Demo (End of Each Sprint)
- **Audience**: Clinicians, researchers, admin, sponsors
- **Content**: Demo new features, gather feedback
- **Format**: Live demo + Q&A session (30-60 minutes)

### Monthly Steering Committee
- **Audience**: Executive sponsors, clinical leadership
- **Content**: Overall progress, budget, timeline, risks
- **Format**: Executive summary + discussion (1 hour)

---

## Budget Estimate (v2.0 - Revised)

### Development Costs (Estimated)

**Assumptions**:
- Full-stack developer: $100/hour
- DevOps engineer: $120/hour
- Clinical SME: $150/hour (increased from 10% → 20% time)
- QA Engineer: $80/hour (NEW - 20% time)
- Security Auditor: $150/hour (NEW - consulting, 80 hours total)
- FHIR/NHS UK Expert: $150/hour (NEW - consulting, 120 hours for Sprint 6 only)
- Project manager: $90/hour (for parallel execution only)

**Sequential Execution (v2.0)**:
- Development: **2,130 hours** × $100 = $213,000 (**revised from 1,410 hours**)
- DevOps (30% of dev time): 639 hours × $120 = $76,680
- Clinical SME (20% of dev time): 426 hours × $150 = $63,900
- QA Engineer (NEW, 20% of dev time): 426 hours × $80 = $34,080
- Security Auditor (NEW, 80 hours): 80 hours × $150 = $12,000
- FHIR/NHS UK Expert (NEW, 120 hours Sprint 6): 120 hours × $150 = $18,000
- **Total Labor**: ~$417,660 (**revised from $196,000**)

**Parallel Execution (v2.0)** (3 devs after MVP):
- Development: 2,130 hours × $100 = $213,000
- DevOps (40% of dev time): 852 hours × $120 = $102,240
- Clinical SME (25% of dev time): 533 hours × $150 = $79,950
- QA Engineer (NEW, 25% of dev time): 533 hours × $80 = $42,640
- Security Auditor (NEW, 100 hours): 100 hours × $150 = $15,000
- FHIR/NHS UK Expert (NEW, 120 hours Sprint 6): 120 hours × $150 = $18,000
- Project manager (30% of dev time): 639 hours × $90 = $57,510
- **Total Labor**: ~$528,340 (**revised from $255,000**)

**Infrastructure Costs** (Annual):
- Servers (workstation): $5,000/year (**upgraded hardware: 32-64GB RAM, 8-16 cores, 500GB SSD**)
- Docker/infrastructure: $2,000/year
- CogStack-ModelServe hosting: $3,000/year
- NHS dm+d database: Free (NHS TRUD)
- Drug interaction database: $5,000/year (commercial: Lexicomp/Micromedex) OR $0 (open-source: OpenFDA)
- **Total**: ~$15,000/year (**revised from $10,000/year**)

**Total Project Cost (v2.0)**:
- Sequential: **~$432,660** (**revised from $206,000**)
- Parallel: **~$543,340** (**revised from $265,000**)

**Budget Increase Breakdown**:
- +$72,000: Sprint 6 expansion (Meditech bidirectional integration: 150h → 360h)
- +$60,000: 20% buffer across all sprints (rework, bug fixes, optimization)
- +$34,080: QA Engineer (NEW role - 20% time for testing)
- +$12,000: Security Auditor (NEW role - HIPAA/GDPR compliance review)
- +$18,000: FHIR/NHS UK Expert (NEW role - Sprint 6 Meditech integration)
- +$30,000: Event Bus (Sprint 5.5) + Hardening (Sprint 9.5)

---

## Next Steps

### Immediate (Week 0)
1. ✅ Review and approve this roadmap
2. ⏳ Allocate development team
3. ⏳ Set up project tracking (Jira, GitHub Projects)
4. ⏳ Confirm CogStack-ModelServe model availability
5. ⏳ Begin MVP Phase 0 (Environment Setup)

### Short-Term (Weeks 1-11)
1. ⏳ Execute MVP (Phases 0-7)
2. ⏳ Conduct Sprint 2-3 planning (during MVP weeks 8-10)
3. ⏳ Gather user feedback on MVP

### Medium-Term (Weeks 12-27)
1. ⏳ Execute Sprints 2-5
2. ⏳ Gather user feedback and iterate
3. ⏳ Plan Sprints 6-7 based on feedback

### Long-Term (Weeks 28-47)
1. ⏳ Execute Sprints 6-9
2. ⏳ Prepare for production deployment
3. ⏳ Plan future enhancements (machine learning, mobile apps, etc.)

---

## Appendices

### Appendix A: Specification File Locations

All sprint specifications are located in `.specify/specifications/`:

- MVP: `clinical-care-tools-base-app.md`
- Sprint 2: `sprint-2-timeline-view.md`
- Sprint 3: `sprint-3-full-text-search.md`
- Sprint 4: `sprint-4-ehr-deidentification.md`
- Sprint 5: `sprint-5-clinical-coding.md`
- Sprint 6: `sprint-6-clinical-decision-support.md`
- Sprint 7: `sprint-7-automated-alerting.md`
- Sprint 8: `sprint-8-population-health-dashboards.md`
- Sprint 9: `sprint-9-advanced-analytics.md`

### Appendix B: Technology Stack

**Frontend**:
- Vue 3.5+ (Composition API, TypeScript)
- Vuetify 3.7+ (Material Design components)
- D3.js (Timeline visualization)
- Chart.js or ECharts (Dashboards)

**Backend**:
- FastAPI 0.115+ (Python 3.10+)
- PostgreSQL 15+ (Relational data)
- Elasticsearch 8+ (Full-text search, analytics)
- Redis 7.2+ (Caching, Celery broker)
- Celery (Background jobs)

**NLP**:
- CogStack-ModelServe (NLP model serving)
- Models: medcat_snomed, medcat_deid, medcat_icd10

**Infrastructure**:
- Docker 24.0+ (Containerization)
- Docker Compose (Orchestration)

**Compliance**:
- HIPAA, GDPR, 21 CFR Part 11

### Appendix C: CogStack Product Mapping

| CogStack Product | Our Modules | Coverage |
|-----------------|-------------|----------|
| **Enterprise-grade Search** | Patient Search (Sprint 1), Timeline View (Sprint 2), Full-Text Search (Sprint 3) | 100% |
| **Clinical Language AI** | CogStack-ModelServe integration (all sprints) | 100% |
| **EHR De-Identification** | De-Identification Module (Sprint 4) | 100% |
| **Clinical Coding** | Clinical Coding Module (Sprint 5) | 100% |
| **Automated Alerting** | Automated Alerting Module (Sprint 7) | 100% |
| **Population Health Dashboards** | Population Health Dashboards (Sprint 8), Advanced Analytics (Sprint 9) | 100% |

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-17
**Status**: ✅ Ready for Implementation
**Approval**: Pending stakeholder sign-off
