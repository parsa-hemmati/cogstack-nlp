# Specification: Patient Search & Discovery

> ⚠️ **IMPORTANT: This document describes planned functionality for Phase 4 that is NOT YET IMPLEMENTED.**
>
> **Current State**: Specification complete, implementation pending.
>
> **Prerequisites Met**: Phase 3 (Document Management) provides the foundation (patients, documents, extracted_entities tables).
>
> **Next Step**: Implementation will begin with Task 4.1 (Database Indexes) - see [patient-search-tasks.md](../tasks/patient-search-tasks.md)

---

**Version**: 1.0.0
**Status**: Draft (PLANNED - Phase 4)
**Created**: 2025-11-18
**Phase**: 4 (Patient Search)
**Sprint**: 1 (Foundation)

---

## Context

Clinicians need to quickly find patients based on medical conditions, symptoms, or clinical concepts extracted from documents. Traditional keyword search is insufficient because:
- Medical terminology is complex (synonyms, abbreviations, misspellings)
- Context matters (current vs historical, patient vs family history, confirmed vs suspected)
- Manual document review is time-consuming and error-prone

**Problem**: Without intelligent search, clinicians:
- Miss relevant patients for care coordination
- Cannot identify cohorts for quality improvement
- Spend excessive time manually reviewing records
- Risk overlooking critical clinical information

**Opportunity**: Build a concept-based patient search that leverages Phase 3's NLP infrastructure:
1. Search by medical concepts (SNOMED-CT) instead of keywords
2. Filter by meta-annotations (current vs historical, negated, patient vs family)
3. Display concept highlights and source documents
4. Provide fast, accurate results (<500ms response time)
5. Maintain HIPAA compliance (audit logging, minimum necessary access)

**Foundation**: Phase 3 provides:
- PostgreSQL with patients, documents, extracted_entities tables
- MedCAT NLP integration (SNOMED-CT concept extraction)
- Meta-annotations (Negation, Temporality, Experiencer, Certainty)
- Encrypted document storage with PHI extraction
- Patient aggregation by NHS number

---

## Goals

### Primary Goals
1. **Concept-Based Search**: Find patients by medical concepts (SNOMED-CT CUIs or names)
2. **Meta-Annotation Filtering**: Filter by temporality (current/historical), negation (affirmed/negated), experiencer (patient/family)
3. **Fast Performance**: Return results within 500ms (P95)
4. **Accurate Results**: 90%+ precision using meta-annotation filters
5. **HIPAA Compliance**: Audit all searches, display minimum necessary information

### Secondary Goals
1. **Concept Highlights**: Show which documents/sentences contain the concept
2. **Patient Demographics**: Display name, NHS number, DOB, document count
3. **Pagination**: Support large result sets (100+ patients)
4. **Search History**: Track recent searches for quick re-run
5. **Export Results**: CSV export for care coordination

---

## Non-Goals

**Out of Scope for Phase 4**:
- Full-text search (not concept-based) - deferred to Phase 5
- Advanced analytics (concept co-occurrence, trends) - deferred to Phase 6
- Real-time document ingestion - uses existing Phase 3 background processing
- Multi-language support - English only (SNOMED-CT en_core_web_md)
- Elasticsearch integration - uses PostgreSQL (Elasticsearch in Phase 5 for performance)
- Fuzzy matching or spell correction - relies on MedCAT's built-in disambiguation

---

## User Stories

### US1: Search Patients by Concept (Clinician)
**As a** clinician
**I want to** search for patients by medical condition (e.g., "atrial flutter", "diabetes")
**So that** I can identify relevant patients for care coordination or quality improvement

**Acceptance Criteria**:
- Enter concept name or SNOMED-CT CUI
- Results show patients with that concept in their documents
- Results include patient demographics (name, NHS number, DOB)
- Results show document count with that concept
- Search completes within 500ms (P95)
- Audit log created for each search

---

### US2: Filter by Temporality (Clinician)
**As a** clinician
**I want to** filter search results to current conditions only
**So that** I don't get patients with historical mentions (e.g., "patient had diabetes 10 years ago")

**Acceptance Criteria**:
- Filter options: "Current" (default), "Historical", "Any"
- "Current" filters to Temporality IN ('Current', 'Recent')
- "Historical" filters to Temporality IN ('Historical', 'Past')
- Filter updates results immediately (no page reload)
- Filter state persisted in URL (shareable links)

---

### US3: Exclude Negated Mentions (Clinician)
**As a** clinician
**I want to** exclude negated mentions (e.g., "no evidence of diabetes")
**So that** I only find patients with confirmed conditions

**Acceptance Criteria**:
- Default filter: Negation = "Affirmed" (exclude negated)
- Filter options: "Affirmed" (default), "Negated", "Any"
- "Affirmed" filters to Negation = 'Affirmed'
- Results exclude statements like "denies chest pain", "no fever"
- Precision improves from 60% (no filter) to 90%+ (with filter)

---

### US4: Patient vs Family History (Clinician)
**As a** clinician
**I want to** exclude family history mentions (e.g., "mother has diabetes")
**So that** I only find patients with their own conditions

**Acceptance Criteria**:
- Default filter: Experiencer = "Patient" (exclude family)
- Filter options: "Patient" (default), "Family", "Other", "Any"
- "Patient" filters to Experiencer = 'Patient'
- Results exclude statements like "father had MI", "family history of cancer"
- Precision improves for patient identification

---

### US5: View Concept Highlights (Clinician)
**As a** clinician
**I want to** see which documents contain the concept
**So that** I can verify the NLP findings and understand context

**Acceptance Criteria**:
- Each result shows "X documents with concept"
- Click to expand and view document list
- Each document shows: title, date, highlight snippet
- Highlight snippet shows sentence with concept bolded
- Click document to open full text (modal or new tab)

---

### US6: Audit Trail for Compliance (Auditor)
**As a** compliance auditor
**I want** all patient searches logged
**So that** I can verify HIPAA compliance and investigate unauthorized access

**Acceptance Criteria**:
- Every search logged to audit_logs table
- Log includes: user_id, search_query, filters, result_count, timestamp
- Logs include IP address and user agent
- Logs immutable (cannot be modified/deleted)
- Logs retained for 8 years (NHS requirement)

---

## Requirements

### Functional Requirements

**FR1: Concept-Based Search**
- Accept free-text query (e.g., "atrial flutter", "diabetes mellitus")
- Use MedCAT to extract SNOMED-CT CUI from query (if not provided)
- Alternative: Accept SNOMED-CT CUI directly (e.g., "C0004238")
- Query extracted_entities table for matching CUI or pretty_name
- Return patients with at least one matching entity

**FR2: Meta-Annotation Filtering**
- Filter by Negation: Affirmed (default), Negated, Any
- Filter by Temporality: Current (default), Historical, Any
- Filter by Experiencer: Patient (default), Family, Other, Any
- Filter by Certainty: Confirmed (default), Suspected, Any
- Filters applied as AND conditions (all must match)
- Filters optional (user can disable for broader search)

**FR3: Result Ranking**
- Sort by relevance: document count with concept (descending)
- Alternative sort: patient name (alphabetical), last updated (recent first)
- Pagination: 20 results per page (configurable)
- Total result count displayed

**FR4: Patient Details**
- Display: full_name, nhs_number (masked: XXX-XXX-1234), date_of_birth, age
- Display: document_count (total), concept_document_count (matching)
- Display: last_updated (most recent document with concept)
- Click to navigate to patient detail page (future)

**FR5: Concept Highlights**
- Expandable section: "X documents with concept"
- List documents: title, date, snippet (sentence with concept)
- Snippet: 100 characters before + concept (bolded) + 100 characters after
- Click document to open full text
- Meta-annotations shown: Negation, Temporality, Experiencer, Certainty (color-coded badges)

**FR6: Search History**
- Track last 10 searches per user (stored in Redis)
- Display recent searches dropdown (autocomplete)
- Click recent search to re-run instantly
- Clear search history button

**FR7: Export Results**
- Export to CSV: patient list with demographics + concept count
- Export includes: nhs_number, full_name, date_of_birth, document_count
- Export limited to 1000 results (prevent large downloads)
- Audit log created for exports

**FR8: Audit Logging**
- Log every search: user_id, query, filters, result_count, timestamp, ip_address
- Log every export: user_id, result_count, timestamp
- Log every document view: user_id, document_id, patient_id, timestamp
- Logs written to audit_logs table (immutable)

---

### Non-Functional Requirements

**NFR1: Performance**
- Search response time: <500ms (P95)
- Pagination navigation: <200ms (P95)
- Document expansion: <300ms (P95)
- Concurrent searches: 10+ users simultaneously
- Database query optimization: indexes on cui, patient_id, meta_anns

**NFR2: Security**
- Authentication: JWT required for all endpoints
- Authorization: RBAC - Clinician, Researcher, Admin roles
- Input validation: Prevent SQL injection, XSS
- PHI minimization: Only return necessary fields
- Audit logging: All searches, exports, document views

**NFR3: Accuracy**
- Precision: 90%+ with meta-annotation filters
- Recall: 85%+ (may miss edge cases due to NLP limitations)
- False positive rate: <10% with filters
- False negative rate: <15% (acceptable for discovery tool)

**NFR4: Scalability**
- Support 10,000 patients (Phase 4 MVP)
- Support 100,000 patients (Phase 5 with Elasticsearch)
- Support 1,000,000 extracted entities
- PostgreSQL-based (Phase 4), Elasticsearch-based (Phase 5)

**NFR5: Usability**
- Search box autocomplete: Suggest concept names
- Filter presets: "Current Patient Conditions" (default), "Any Mention", "Historical Only"
- Keyboard navigation: Arrow keys, Enter to search
- Responsive design: Desktop + tablet (mobile deferred)

**NFR6: Compliance**
- HIPAA Security Rule 164.312(b): Audit controls ✓
- HIPAA Privacy Rule 164.502(b): Minimum necessary ✓
- GDPR Article 30: Records of processing activities ✓
- NHS Data Security Toolkit: Audit logs retained 8 years ✓

---

## Constraints

### Technical Constraints
- **Database**: PostgreSQL only (no Elasticsearch until Phase 5)
- **Performance**: Linear scan of extracted_entities table (no full-text search index)
- **NLP Model**: MedCAT SNOMED-CT model (medcat_snomed.zip)
- **Language**: English only (en_core_web_md)
- **Deployment**: Single workstation (16GB RAM, 8 CPU cores)

### Data Constraints
- **Phase 4 MVP**: 10,000 patients maximum
- **Document format**: RTF only (from Phase 3)
- **Concept vocabulary**: SNOMED-CT only (no UMLS, LOINC, ICD-10 yet)
- **Meta-annotations**: 4 types (Negation, Temporality, Experiencer, Certainty)

### Regulatory Constraints
- **HIPAA compliance**: All searches audited, PHI access logged
- **Minimum necessary**: Only return fields needed for care coordination
- **Patient consent**: Assume consent obtained (consent management in Phase 6)

### UI/UX Constraints
- **Design system**: Vuetify 3 Material Design
- **Browser support**: Chrome 90+, Firefox 88+, Edge 90+ (no IE11)
- **Accessibility**: WCAG 2.1 AA (deferred to Phase 5 for full compliance)

---

## Acceptance Criteria

### Search Functionality
- [ ] Search by concept name returns matching patients
- [ ] Search by SNOMED-CT CUI returns matching patients
- [ ] Empty query returns validation error (400)
- [ ] Invalid CUI returns empty results (not error)
- [ ] Search response time <500ms for 10,000 patients (P95)

### Meta-Annotation Filtering
- [ ] Negation filter excludes negated mentions
- [ ] Temporality filter excludes historical mentions (when set to "Current")
- [ ] Experiencer filter excludes family history (when set to "Patient")
- [ ] Multiple filters applied as AND conditions
- [ ] Precision improves from 60% to 90%+ with filters enabled

### Result Display
- [ ] Results show patient demographics (name, NHS number, DOB)
- [ ] Results show document count with concept
- [ ] Results paginated (20 per page)
- [ ] Total result count displayed
- [ ] Click patient navigates to detail page (stub in Phase 4)

### Concept Highlights
- [ ] Expandable section shows document list
- [ ] Each document shows title, date, snippet
- [ ] Snippet highlights concept (bolded)
- [ ] Meta-annotations displayed as color-coded badges
- [ ] Click document opens full text (modal)

### Audit Logging
- [ ] Every search logged to audit_logs
- [ ] Log includes user_id, query, filters, result_count, timestamp
- [ ] Logs immutable (cannot be modified/deleted)
- [ ] Audit logs queryable by admin users

### Security
- [ ] Authentication required (401 if not logged in)
- [ ] Authorization enforced (403 if insufficient permissions)
- [ ] Input validation prevents SQL injection
- [ ] No PHI in application logs (only audit logs)

### Performance
- [ ] Search <500ms for 10,000 patients (P95)
- [ ] Pagination <200ms (P95)
- [ ] Concurrent searches: 10 users simultaneously
- [ ] Database indexes optimize query performance

---

## Alignment with Constitution

### 1. Patient Safety First ✅
- Meta-annotation filtering prevents false positives (e.g., family history, negated conditions)
- Precision threshold: 90%+ with filters enabled
- Manual verification encouraged (concept highlights with source documents)

### 2. Privacy by Design ✅
- Audit logging for all searches (HIPAA requirement)
- Minimum necessary information displayed (name, NHS number, DOB only)
- PHI masked in UI (NHS number: XXX-XXX-1234)
- No PHI in application logs

### 3. Evidence-Based Development ✅
- Meta-annotation filtering based on published research (MedCAT paper, JAMIA studies)
- Performance targets based on clinical workflow studies (<500ms acceptable)
- Test coverage: 85%+ required

### 4. Modularity and Composability ✅
- PatientSearchService reusable for other features (timeline view, cohort builder)
- Meta-annotation filters reusable for all concept-based features
- API-first design (frontend consumes REST API)

### 5. Open Standards and Interoperability ✅
- SNOMED-CT concepts (international standard)
- NHS numbers (UK national patient identifier)
- FHIR-ready (entities mappable to FHIR Observations/Conditions)

### 6. Transparency and Explainability ✅
- Concept highlights show source documents
- Meta-annotations visible to user (color-coded badges)
- Search filters explicit and user-controlled

### 7. Performance and Scalability ✅
- <500ms response time (clinical workflow acceptable)
- Pagination for large result sets
- Database indexes optimize queries
- Elasticsearch migration path (Phase 5) for 100k+ patients

### 8. Developer Experience ✅
- Clear API documentation (OpenAPI spec)
- Reusable service layer (PatientSearchService)
- Comprehensive tests (unit + integration)

### 9. Clinical Workflow Integration ✅
- Fast search (<500ms) doesn't interrupt workflow
- Recent searches for quick re-run
- Keyboard navigation for power users

### 10. Continuous Improvement ✅
- Search history tracked for usage analytics
- Performance metrics monitored (response time, result count)
- User feedback collected for iterative improvement

---

## Implementation Status

**Status**: Draft (Phase 4 not started)

**Dependencies**:
- ✅ Phase 3 complete (patients, documents, extracted_entities tables)
- ✅ MedCAT service operational (medcat_snomed.zip)
- ✅ Meta-annotations enabled (Negation, Temporality, Experiencer, Certainty)
- ⏳ Test data: Need 1,000+ test documents with diverse concepts
- ⏳ Frontend components: Vue 3 + Vuetify base structure exists

**Risks**:
- PostgreSQL performance may degrade beyond 10,000 patients (mitigate with indexes)
- MedCAT concept extraction quality depends on model training data
- Meta-annotation accuracy varies by concept type (negation ~95%, temporality ~85%)

---

## Future Enhancements (Out of Scope for Phase 4)

1. **Elasticsearch Integration** (Phase 5): Full-text search, fuzzy matching, 100k+ patients
2. **Advanced Filters** (Phase 5): Date range, document type, concept co-occurrence
3. **Saved Searches** (Phase 5): Persistent search queries, scheduled email alerts
4. **Concept Synonyms** (Phase 5): "MI" = "myocardial infarction" = "heart attack"
5. **Multi-Language** (Phase 6): Support non-English clinical notes
6. **Real-Time Updates** (Phase 6): WebSocket notifications for new patient matches

---

## References

- **MedCAT Documentation**: https://github.com/CogStack/MedCAT
- **Meta-Annotations Guide**: docs/advanced/meta-annotations-guide.md
- **PROJECT_PLAN.md**: Sprint 1 - Patient Search & Discovery
- **Phase 3 Implementation**: .specify/specifications/document-management.md
- **Skills**: .claude/skills/medcat-meta-annotations/

---

**Specification Approved**: Pending
**Next Steps**: Create technical plan, task breakdown
**Review Date**: 2025-11-19
