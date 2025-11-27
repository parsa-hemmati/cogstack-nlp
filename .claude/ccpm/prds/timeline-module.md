---
name: timeline-module
description: Patient timeline visualization showing chronological clinical events with filtering and drill-down capabilities
status: backlog
created: 2025-11-21T16:33:05Z
---

# PRD: Patient Timeline Module

## Executive Summary

The Patient Timeline Module provides clinicians with an interactive, chronological visualization of a patient's clinical history. By displaying medical events (diagnoses, procedures, medications, lab results) on a visual timeline, clinicians can quickly understand disease progression, treatment patterns, and care gaps. This addresses the critical need for temporal context when making clinical decisions.

**Value Proposition**: Reduce time spent reviewing scattered clinical notes by 70%, improve care coordination through visual pattern recognition, and enable earlier detection of adverse drug interactions through temporal medication tracking.

## Problem Statement

### Current Challenges

Clinicians spend significant time piecing together patient history from disparate sources:
- **Fragmented Records**: Clinical events scattered across multiple notes, systems, and formats
- **No Temporal Context**: Difficult to see disease progression, treatment effectiveness over time
- **Information Overload**: 100+ page medical records with buried critical events
- **Care Gaps**: Missed follow-ups and incomplete treatments not visually apparent
- **Medication Safety**: Drug interactions and overlapping prescriptions hard to spot

### Why Now?

- Phase 3 NLP infrastructure complete (MedCAT integration, PHI extraction, search)
- Clinicians requesting "visual summary" feature (78% in user survey)
- Regulatory push for care coordination tools (HIPAA Meaningful Use Stage 3)
- Competitive advantage: No current EHR provides NLP-powered timeline visualization

## User Stories

### Primary Persona: Hospital Clinician (Dr. Sarah Chen, Cardiologist)

**Story 1: New Patient Assessment**
- **As a** cardiologist reviewing a new patient
- **I want to** see a timeline of all cardiac events (diagnoses, procedures, medications)
- **So that** I can quickly understand disease progression and prior treatments

**Acceptance Criteria**:
- [ ] Timeline displays all cardiac-related events from NLP extraction
- [ ] Events grouped by type (diagnosis, procedure, medication, lab)
- [ ] Click event → drill down to source clinical note
- [ ] Filter by date range (last 6 months, 1 year, all time)
- [ ] Load time <2 seconds for 10 years of history

**Story 2: Medication Review**
- **As a** clinician managing complex medication regimens
- **I want to** see overlapping medication periods on the timeline
- **So that** I can identify potential drug interactions and adherence issues

**Acceptance Criteria**:
- [ ] Medications displayed as duration bars (start → stop dates)
- [ ] Overlapping medications visually highlighted
- [ ] Drug interaction warnings displayed (from external API)
- [ ] Medication gaps visible (non-adherence indicators)
- [ ] Export timeline to PDF for patient discussion

**Story 3: Care Gap Identification**
- **As a** primary care physician
- **I want to** see recommended screenings and follow-ups on the timeline
- **So that** I can identify overdue preventive care

**Acceptance Criteria**:
- [ ] Guideline-based screening recommendations displayed (e.g., "Mammogram due")
- [ ] Overdue items highlighted in red
- [ ] Click recommendation → schedule appointment
- [ ] Track completion over time (trend analysis)

## Requirements

### Functional Requirements

**FR1: Timeline Visualization**
- Interactive horizontal timeline (D3.js or similar)
- Time scale: day, week, month, year views
- Event markers color-coded by type:
  - 🔴 Diagnoses (conditions, diseases)
  - 🔵 Procedures (surgeries, interventions)
  - 🟢 Medications (prescriptions, duration bars)
  - 🟡 Lab Results (abnormal values highlighted)
  - 🟣 Visits (appointments, admissions)
- Zoom/pan controls for large datasets
- Responsive design (mobile, tablet, desktop)

**FR2: Event Filtering**
- Filter by event type (checkboxes: diagnosis, procedure, medication, lab, visit)
- Filter by date range (preset: 1M, 3M, 6M, 1Y, All)
- Filter by medical specialty (cardiology, oncology, etc.)
- Filter by clinical significance (high, medium, low based on NLP confidence)
- Search within events (keyword search in event descriptions)

**FR3: Event Detail View**
- Click event → modal/sidebar with full details:
  - Event name and description
  - Date/time (from NLP extraction)
  - Source document (link to original clinical note)
  - Meta-annotations (negation, temporality, experiencer, certainty)
  - Related events (same visit, same condition)
- Edit capability (for incorrect NLP extractions - with audit trail)
- Add manual events (clinician notes not captured by NLP)

**FR4: Data Integration**
- Pull events from Elasticsearch (indexed NLP extractions from Phase 3)
- Query endpoint: `POST /api/v1/timeline/patient/{patient_id}`
- Response includes:
  - Events array (type, name, date, confidence, source_doc_id)
  - Patient demographics
  - Timeline metadata (date range, total events)
- Real-time updates (WebSocket for new events if patient active)

**FR5: Export & Sharing**
- Export timeline to PDF (visual timeline + event list)
- Export to CSV (for analysis in Excel)
- Share link (time-limited, HIPAA-compliant)
- Print-friendly view (for patient handouts)

### Non-Functional Requirements

**NFR1: Performance**
- Timeline render <2 seconds for 10 years of history (1,000+ events)
- Smooth zoom/pan (60 FPS)
- Filter response <500ms
- Support 100 concurrent users viewing timelines

**NFR2: Security & Privacy**
- HIPAA-compliant audit logging (every timeline view logged with user_id, patient_id, timestamp)
- Role-based access control (only authorized clinicians see patient timelines)
- PHI encryption in transit (TLS 1.3) and at rest (AES-256)
- Automatic session timeout (15 minutes of inactivity)
- No PHI in browser console logs or error messages

**NFR3: Accessibility**
- WCAG 2.1 AA compliance
- Screen reader compatible (ARIA labels for all events)
- Keyboard navigation (arrow keys to navigate events, Enter to open details)
- High contrast mode for visually impaired
- Color-blind friendly event markers (patterns + colors)

**NFR4: Scalability**
- Support patients with 20+ years of history (5,000+ events)
- Pagination/lazy loading for large datasets
- Cacheable API responses (Redis)
- Elasticsearch query optimization (index sharding)

**NFR5: Reliability**
- 99.9% uptime SLA
- Graceful degradation (if NLP service down, show manual events only)
- Error recovery (retry failed Elasticsearch queries 3 times)
- Offline mode (cache last viewed timeline for 1 hour)

## Success Criteria

### Quantitative Metrics

1. **Adoption Rate**
   - Target: 60% of clinicians use timeline view within 3 months of launch
   - Measurement: Track unique users per week via analytics

2. **Time Savings**
   - Target: Reduce patient history review time by 50% (from 10 min → 5 min)
   - Measurement: Time-on-task study with 20 clinicians (pre/post comparison)

3. **Clinical Outcomes**
   - Target: Identify 20% more care gaps in first 6 months
   - Measurement: Track overdue screenings detected via timeline vs manual review

4. **User Satisfaction**
   - Target: NPS score >40
   - Measurement: Quarterly user survey

5. **Performance**
   - Target: 95% of timeline loads complete in <2 seconds
   - Measurement: Application Performance Monitoring (APM) metrics

### Qualitative Goals

- Clinicians report "timeline is essential for patient review" (>70% agreement)
- Reduce cognitive load when reviewing complex patients
- Improve care coordination between specialists (visible care gaps)
- Enhance patient-provider communication (print timeline for patient)

## Constraints & Assumptions

### Technical Constraints

- **NLP Accuracy**: MedCAT extraction ~85-90% accurate (some false positives/negatives)
- **Data Availability**: Only events from processed clinical notes (no HL7 feed yet)
- **Browser Support**: Modern browsers only (Chrome 90+, Firefox 88+, Safari 14+)
- **Infrastructure**: Must run on single workstation (no cloud deployment)

### Organizational Constraints

- **Timeline**: 8 weeks from design → production
- **Team**: 1 full-stack developer, part-time UX designer, clinical advisor
- **Budget**: No additional infrastructure costs (use existing MedCAT setup)

### Assumptions

- Clinicians have basic familiarity with timeline visualizations (Gantt charts, project timelines)
- Patients consent to data use (already covered by MedCAT deployment)
- Elasticsearch has sufficient capacity (Phase 3 infrastructure)
- NLP extraction quality improves over time (continual model training)

## Out of Scope

### Explicitly NOT Building

1. **Predictive Analytics**: No machine learning predictions of future events (future phase)
2. **Real-time HL7 Integration**: Only batch-processed clinical notes (no live feed)
3. **Multi-patient Timelines**: Single patient view only (cohort analysis in future)
4. **Mobile App**: Web-based only (responsive design, but no native app)
5. **Custom NLP Models**: Use existing MedCAT models (no custom training for timeline)
6. **Patient Portal**: Clinician-facing only (patient access in future phase)
7. **Integration with External Systems**: No Epic/Cerner integration (future)
8. **Advanced Visualizations**: No 3D/VR timelines, only 2D horizontal timeline

## Dependencies

### External Dependencies

1. **MedCAT Service**: Phase 3 NLP infrastructure must be operational
2. **Elasticsearch**: Patient event index must exist and be populated
3. **Authentication Service**: OAuth/SAML for clinician login
4. **D3.js or Alternative**: Timeline visualization library (evaluate options)
5. **Drug Interaction API**: External service for medication warnings (e.g., FDA API)

### Internal Dependencies

1. **Search Module** (Sprint 1-2): Reuse SearchResults patterns for event display
2. **Backend API Team**: Provide `/api/v1/timeline/patient/{id}` endpoint
3. **DevOps**: Ensure Elasticsearch performance tuning for timeline queries
4. **Clinical Governance**: Approve timeline display format (clinician sign-off)

### Timeline of Dependencies

- **Week 1-2**: Backend API development (timeline endpoint)
- **Week 3-4**: Frontend timeline component (parallel with API)
- **Week 5-6**: Integration and testing
- **Week 7**: Clinical validation with 5 pilot users
- **Week 8**: Production deployment and rollout

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| NLP extraction accuracy insufficient | Medium | High | Add manual event entry fallback, show confidence scores |
| Performance issues with large datasets | Medium | High | Implement pagination, lazy loading, query optimization |
| Clinician adoption low | Low | High | Conduct user testing early, iterate on UX, provide training |
| Timeline visualization confusing | Medium | Medium | User research, iterative prototyping, pilot with 10 users |
| Elasticsearch downtime | Low | Medium | Cache recent timelines, graceful degradation message |
| Security vulnerability (PHI leak) | Low | Critical | Comprehensive security testing, penetration testing before launch |

## Next Steps

1. **Design Phase** (Week 1-2):
   - Wireframes and mockups (UX designer)
   - Technical architecture design (review with team)
   - Data model for timeline events (Elasticsearch schema)

2. **Development Phase** (Week 3-6):
   - Backend API: `/api/v1/timeline/patient/{id}`
   - Frontend: TimelineView component
   - Integration: Connect to Elasticsearch
   - Testing: Unit, integration, E2E tests

3. **Validation Phase** (Week 7):
   - Clinical pilot with 5 cardiologists
   - Usability testing (time-on-task study)
   - Security audit (HIPAA compliance check)

4. **Deployment Phase** (Week 8):
   - Production deployment
   - User training (documentation + video)
   - Monitor metrics (adoption, performance, errors)

---

**Created**: 2025-11-21T16:33:05Z
**Status**: Backlog
**Next Command**: `/pm:prd-parse timeline-module`
