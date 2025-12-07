# CogStack Product Suite vs Our Development Plan

**Date**: 2025-11-08
**Purpose**: Align our development roadmap with CogStack's complete product suite
**Status**: 🟡 PARTIAL COVERAGE - Significant gaps identified

---

## Executive Summary

**Our Current Plan**: Covers **2 of 6** CogStack products (33%)
- ✅ Enterprise-grade Search (partial - Patient Search only)
- ✅ Clinical Language AI (via CogStack-ModelServe)
- ❌ EHR De-Identification (not in plan)
- ❌ Clinical Coding (not in plan)
- ❌ Automated Alerting (not in plan)
- ❌ Population Health/Caseload Dashboards (not in plan)

**Recommendation**: Expand roadmap to cover all 6 products across multiple sprints

---

## 📊 Detailed Comparison

### CogStack Product #1: Enterprise-grade Search

**CogStack Offering**:
- Full-text search across millions of clinical records
- Simple search bar interface
- Structured field exploration
- Cohort identification
- Search results in seconds

**Our Current Plan**:
- ✅ **Patient Search Module** (Sprint 1 - planned)
  - Search by clinical concepts (SNOMED-CT)
  - Meta-annotation filtering (Negation, Temporality, Experiencer)
  - Elasticsearch integration
- ⚠️ **Gaps**:
  - No full-text search across all documents
  - No structured field exploration UI
  - Limited to patient-level search (not document-level)

**Status**: 🟡 **40% coverage** - Basic patient search only

---

### CogStack Product #2: Clinical Language AI

**CogStack Offering**:
- NLP models trained on millions of clinical records
- Condition identification and contextual analysis
- EHR conversion to interoperable codes (SNOMED-CT, UMLS, ICD-10)

**Our Current Plan**:
- ✅ **CogStack-ModelServe Integration** (Phase 0-1)
  - SNOMED-CT concept extraction
  - Meta-annotation classification (Negation, Temporality, Experiencer, Certainty)
  - PHI/PII detection (names, NHS numbers, dates, addresses)
- ✅ **Document Processing Pipeline** (Phase 3)
  - Upload RTF documents
  - Extract clinical entities
  - Store in structured format

**Status**: ✅ **80% coverage** - Good NLP foundation, missing ICD-10 coding

---

### CogStack Product #3: EHR De-Identification

**CogStack Offering**:
- Removes PII while preserving clinical meaning
- Enables research and quality improvement with de-identified data
- Maintains text structure and context

**Our Current Plan**:
- ✅ **PHI Detection** (Phase 3)
  - Detect names, NHS numbers, dates, addresses via CogStack-ModelServe DeID model
  - Classify entity types
- ❌ **Gaps**:
  - No de-identification/redaction functionality (we detect but don't anonymize)
  - No pseudonymization support
  - No de-identified export feature
  - No research dataset generation

**Status**: 🔴 **20% coverage** - Detection only, no anonymization

---

### CogStack Product #4: Clinical Coding (Automated ICD-10)

**CogStack Offering**:
- Automated ICD-10 coding with AI augmentation
- Assists clinical coders
- Reduces manual coding burden

**Our Current Plan**:
- ❌ **Not in current plan**
- ⚠️ **Partial infrastructure**:
  - CogStack-ModelServe supports `medcat_icd10` model
  - Could add ICD-10 extraction alongside SNOMED

**Status**: 🔴 **0% coverage** - Not planned

---

### CogStack Product #5: Automated Alerting

**CogStack Offering**:
- Real-time clinical event detection
- Continuous scanning for specific conditions:
  - Drug combinations
  - Comorbidity patterns
  - Demographic risk factors
- Automated notifications
- Patient safety monitoring

**Our Current Plan**:
- ⚠️ **Partial foundation** (Phase 6)
  - Critical findings alerts (planned)
  - Clinical override tracking (planned)
- ❌ **Gaps**:
  - No real-time event detection
  - No automated alerting system
  - No drug interaction monitoring
  - No comorbidity pattern detection
  - No notification infrastructure

**Status**: 🔴 **10% coverage** - Only manual critical findings, no automation

---

### CogStack Product #6: Population Health/Caseload Dashboards

**CogStack Offering**:
- Analytics and visualization tools
- Population health management
- Service planning dashboards
- Clinical audit views
- Registry support
- Cohort deep phenotyping

**Our Current Plan**:
- ❌ **Not in current plan**
- ⚠️ **Related features**:
  - Timeline View (planned) - individual patient, not population
  - Patient Search (planned) - could support cohort identification

**Status**: 🔴 **5% coverage** - No dashboards or population analytics

---

## 📋 Our Current Development Plan Location

### Primary Documents

1. **Technical Plan v1.2.0** (Architecture & Implementation)
   - **File**: `.specify/plans/clinical-care-tools-base-plan.md`
   - **Lines**: ~3,700 lines
   - **Covers**: 8 phases, 310 hours (11 weeks)
   - **Focus**: Base application infrastructure + Patient Search module

2. **Specification v1.1.0** (Requirements)
   - **File**: `.specify/specifications/clinical-care-tools-base-app.md`
   - **Covers**: Base app requirements, PHI extraction, module system

3. **Task Breakdown** (Implementation Tasks)
   - **File**: `.specify/tasks/clinical-care-tools-base-tasks.md`
   - **Covers**: ~90 tasks across 8 phases

### Current Phases (Base Application Only)

```
Phase 0: Environment Setup         - 7 tasks,  20 hours ✅ Ready
Phase 1: Core Infrastructure       - 12 tasks, 60 hours
Phase 2: User & Project Management - 7 tasks,  30 hours
Phase 3: Document Upload & PHI     - 12 tasks, 40 hours
Phase 4: Module System & Patient Search - 4+ tasks, 50 hours
Phase 5: Session Security          - 6 tasks,  30 hours
Phase 6: Data Retention & Safety   - 5 tasks,  30 hours
Phase 7: Testing & Deployment      - 10 tasks, 50 hours
────────────────────────────────────────────────────────────
Total: ~90 tasks, ~310 hours (11 weeks)
```

**Scope**: Base application + ONE module (Patient Search)

---

## 🎯 Recommended Expanded Roadmap

### Current Scope (MVP - 11 weeks)
✅ Base Application Infrastructure
✅ Patient Search Module

### Sprint 2-3 (8 weeks) - Search & Visualization
- **Sprint 2**: Timeline View Module
  - Chronological patient event visualization
  - Document timeline
  - Clinical concept timeline
  - Export timeline to PDF/FHIR

- **Sprint 3**: Full-Text Search Enhancement
  - Document-level search (not just patient-level)
  - Structured field exploration UI
  - Advanced query builder
  - Search results relevance ranking

### Sprint 4-5 (8 weeks) - De-Identification & Coding
- **Sprint 4**: EHR De-Identification Module
  - Automated PII redaction
  - Pseudonymization support
  - De-identified dataset export
  - Research data generator
  - Maintain clinical meaning (context preservation)

- **Sprint 5**: Clinical Coding Module
  - Automated ICD-10 extraction (using CogStack-ModelServe `medcat_icd10` model)
  - Clinical coder assistance UI
  - Code suggestion and validation
  - Bulk coding workflow
  - Coding quality metrics

### Sprint 6-7 (10 weeks) - Alerting & Decision Support
- **Sprint 6**: Clinical Decision Support Module
  - CDS Hooks integration
  - FHIR R4 interoperability
  - EHR integration (Epic, Cerner)
  - Evidence-based recommendations

- **Sprint 7**: Automated Alerting Module
  - Real-time event detection engine
  - Drug interaction monitoring
  - Comorbidity pattern detection
  - Demographic risk factor alerts
  - Notification infrastructure (email, SMS, in-app)
  - Alert management UI
  - Alert escalation workflows

### Sprint 8-9 (10 weeks) - Analytics & Dashboards
- **Sprint 8**: Population Health Dashboards Module
  - Cohort analytics
  - Service planning dashboards
  - Clinical audit views
  - Performance metrics
  - Trend analysis

- **Sprint 9**: Advanced Analytics Module
  - Registry support
  - Cohort deep phenotyping
  - Custom report builder
  - Data export (CSV, Excel, FHIR)
  - Predictive analytics (optional)

### Total Expanded Roadmap
- **Duration**: ~58 weeks (~14 months)
- **Sprints**: 9 sprints (MVP + 8 additional)
- **Coverage**: All 6 CogStack products

---

## 🚀 Phased Approach Recommendation

### Option 1: Expand Now (Comprehensive Planning)
**Pros**:
- Complete vision documented upfront
- Easier to secure resources/funding
- Clear product roadmap for stakeholders

**Cons**:
- Significant upfront planning effort (~2-3 weeks)
- May change based on MVP feedback
- Risk of over-planning

### Option 2: MVP First, Expand Later (Agile)
**Pros**:
- Faster time to first value (MVP in 11 weeks)
- Learn from user feedback before committing to full roadmap
- Adapt based on real-world usage

**Cons**:
- Piecemeal specifications (more overhead per sprint)
- May miss architectural decisions that affect multiple modules

### Option 3: Hybrid (Recommended)
**Pros**:
- Plan MVP + Sprints 2-3 now (Search & Visualization)
- Defer detailed planning for Sprints 4-9 until MVP feedback
- Balance between vision and agility

**Timeline**:
1. **Now**: Complete MVP (Phase 0-7)
2. **Week 8**: Plan Sprints 2-3 (based on MVP progress)
3. **Week 16**: Plan Sprints 4-5 (based on user feedback)
4. **Week 24**: Plan Sprints 6-9 (based on adoption)

---

## 📝 Action Items

### Immediate (Before Phase 0)
1. ✅ **Review this gap analysis** with user
2. ⏳ **Decide on roadmap approach** (Option 1, 2, or 3)
3. ⏳ **Update project documentation** if expanding scope

### If Expanding Scope (Option 1 or 3)
1. Create specifications for additional modules:
   - `.specify/specifications/de-identification-module.md`
   - `.specify/specifications/clinical-coding-module.md`
   - `.specify/specifications/automated-alerting-module.md`
   - `.specify/specifications/population-health-dashboards.md`

2. Create Sprint PRDs (Product Requirement Documents):
   - `.specify/sprints/sprint-2-timeline-view.md`
   - `.specify/sprints/sprint-3-full-text-search.md`
   - etc.

3. Update CONTEXT.md with expanded roadmap

### If MVP First (Option 2)
1. Proceed with Phase 0 (Environment Setup)
2. Complete MVP (Phases 1-7)
3. Gather user feedback
4. Plan next sprint based on priorities

---

## 🎯 Current Status

**Base Application**: ✅ Fully planned (Technical Plan v1.2.0, Task Breakdown ready)

**CogStack Product Coverage**:
- Clinical Language AI: 80% ✅
- Enterprise-grade Search: 40% 🟡
- EHR De-Identification: 20% 🔴
- Clinical Coding: 0% 🔴
- Automated Alerting: 10% 🔴
- Population Health Dashboards: 5% 🔴

**Overall Coverage**: **~26%** of full CogStack product suite

---

## 💡 Recommendation

**Adopt Option 3 (Hybrid Approach)**:

1. **Complete MVP** (11 weeks) - Base application + Patient Search
2. **Plan Sprints 2-3** during MVP implementation - Timeline View + Full-Text Search
3. **Gather user feedback** after MVP deployment
4. **Prioritize remaining modules** based on user needs:
   - High priority: De-Identification (research enablement)
   - High priority: Clinical Coding (operational efficiency)
   - Medium priority: Automated Alerting (patient safety)
   - Medium priority: Population Health (service planning)

**Rationale**:
- ✅ Fast time to value (MVP in 11 weeks)
- ✅ Learn from real usage before committing resources
- ✅ Maintain alignment with CogStack product vision
- ✅ Flexibility to adapt priorities based on feedback

---

**Next Step**: Discuss with stakeholders which approach to take before beginning Phase 0 implementation.
