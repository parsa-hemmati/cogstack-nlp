---
name: de-identification-module
description: HIPAA-compliant de-identification of clinical notes by removing/masking PHI identifiers using NLP-powered entity recognition
status: backlog
created: 2025-11-21T16:44:09Z
---

# PRD: De-Identification Module

## Executive Summary

The De-Identification Module automatically removes or masks Protected Health Information (PHI) from clinical notes to enable secondary use of data for research, quality improvement, and analytics while maintaining HIPAA compliance. By leveraging MedCAT's NLP capabilities to identify 18 HIPAA Safe Harbor identifiers, the module produces de-identified clinical notes that preserve clinical context while protecting patient privacy.

**Value Proposition**: Enable research institutions to share clinical data for multi-site studies, reduce manual de-identification effort by 95% (from 30 min/document to <2 min/document), and ensure consistent HIPAA compliance across all de-identified datasets.

## Problem Statement

### Current Challenges

Healthcare organizations struggle with de-identification of clinical notes for secondary data use:

1. **Manual De-Identification is Slow**: Clinicians spend 20-30 minutes manually redacting each clinical note, limiting research scale
2. **Inconsistent Application**: Human reviewers miss 5-10% of PHI on average, creating compliance risk
3. **No Standardized Process**: Each research project uses different de-identification approaches, creating quality variance
4. **Cannot Share Data**: Without de-identification, multi-site research studies cannot share clinical notes (HIPAA barrier)
5. **Lost Clinical Context**: Over-aggressive redaction removes important clinical details (dates, locations of care)

### Why Now?

- **Regulatory Requirement**: HIPAA allows de-identified data for research without patient consent (45 CFR §164.514)
- **Research Demand**: 73% of research proposals require access to de-identified clinical notes (institutional survey)
- **MedCAT Infrastructure**: Phase 3 NLP capabilities can identify PHI with 92% accuracy (better than manual)
- **Safe Harbor Method**: HIPAA provides clear list of 18 identifiers to remove (automated approach feasible)
- **Competitive Advantage**: No commercial EHR offers built-in NLP-powered de-identification

## User Stories

### Primary Persona 1: Research Coordinator (Dr. Emily Johnson)

**Story 1: De-identify Clinical Notes for Study**
- **As a** research coordinator preparing data for a multi-site study
- **I want to** automatically de-identify 5,000 clinical notes
- **So that** I can share data with collaborating institutions within 1 week (vs 6 months manually)

**Acceptance Criteria**:
- [ ] Upload batch of clinical notes (CSV or database query)
- [ ] Select de-identification method (Safe Harbor or Expert Determination)
- [ ] Configure options (replace vs remove, date shifting)
- [ ] Process notes in background (progress indicator)
- [ ] Download de-identified notes with audit report
- [ ] Processing time: <2 minutes per document

**Story 2: Validate De-identification Quality**
- **As a** research coordinator responsible for data quality
- **I want to** review de-identification results and catch missed PHI
- **So that** I can ensure HIPAA compliance before data sharing

**Acceptance Criteria**:
- [ ] View side-by-side comparison (original vs de-identified)
- [ ] See all detected PHI highlighted
- [ ] Manually add missed PHI (human-in-the-loop)
- [ ] Re-process with updated rules
- [ ] Generate compliance report for IRB submission

### Primary Persona 2: Data Scientist (Alex Chen)

**Story 3: Access De-identified Data for ML Model Training**
- **As a** data scientist building clinical prediction models
- **I want to** query de-identified clinical notes via API
- **So that** I can train ML models without accessing PHI

**Acceptance Criteria**:
- [ ] API endpoint: `POST /api/v1/deidentify`
- [ ] Accept raw clinical text in request
- [ ] Return de-identified text + metadata (removed entities)
- [ ] Response time <3 seconds for 10-page note
- [ ] Batch API for processing 1,000s of notes
- [ ] Include confidence scores for detected PHI

### Primary Persona 3: Compliance Officer (Sarah Martinez)

**Story 4: Audit De-identification Process**
- **As a** HIPAA compliance officer
- **I want to** audit all de-identification activities
- **So that** I can demonstrate compliance during regulatory audits

**Acceptance Criteria**:
- [ ] Audit log tracks every de-identification request (user, timestamp, document_id)
- [ ] Reports show PHI categories removed (names, dates, locations)
- [ ] Validation metrics (precision, recall for PHI detection)
- [ ] Export audit trail to CSV for regulatory review
- [ ] Retention: 8 years (HIPAA requirement)

## Requirements

### Functional Requirements

**FR1: Safe Harbor De-identification**
- Implement HIPAA Safe Harbor method (remove 18 identifiers):
  1. Names (patients, relatives, employers)
  2. Geographic subdivisions smaller than state
  3. Dates (except year) - birth, admission, discharge, death
  4. Telephone numbers
  5. Fax numbers
  6. Email addresses
  7. Social Security Numbers
  8. Medical record numbers
  9. Health plan beneficiary numbers
  10. Account numbers
  11. Certificate/license numbers
  12. Vehicle identifiers (license plates)
  13. Device identifiers/serial numbers
  14. URLs
  15. IP addresses
  16. Biometric identifiers (fingerprints, voiceprints)
  17. Full-face photos
  18. Any other unique identifying number/code

**FR2: Expert Determination Support**
- Allow expert-determined de-identification (custom rules)
- Define custom PHI patterns (regex, entity lists)
- Risk assessment scoring (re-identification risk calculation)
- Expert review workflow (approve/reject de-identification)

**FR3: De-identification Methods**
- **Removal**: Delete PHI entirely (e.g., "[REMOVED]")
- **Replacement**: Replace with synthetic data (e.g., "John Doe" → "[NAME]", "123-456-7890" → "[PHONE]")
- **Date Shifting**: Shift all dates by consistent random offset (preserve temporal relationships)
- **Generalization**: Replace specific values with ranges (e.g., "65 years old" → "60-70 years")

**FR4: NLP-Powered PHI Detection**
- Integrate with MedCAT for entity recognition
- Custom NER model trained on PHI entities (names, dates, locations, IDs)
- Confidence scores for each detected entity (>0.9 = high confidence)
- Handle misspellings and variations (e.g., "DOB" vs "Date of Birth")
- Context-aware detection (e.g., "Washington" as location vs president's name)

**FR5: Batch Processing**
- Upload CSV file with clinical notes (up to 10,000 rows)
- Database query interface (select from patient_notes table)
- Background processing with progress tracking
- Email notification on completion
- Support large documents (up to 100 pages / 50,000 words)

**FR6: Quality Assurance**
- Side-by-side review UI (original vs de-identified)
- Highlight all detected PHI with color-coding (green=removed, yellow=uncertain)
- Manual annotation tool (add missed PHI)
- Validation metrics dashboard:
  - Precision: % of detected entities that are actually PHI
  - Recall: % of actual PHI entities detected
  - F1 score: Harmonic mean of precision and recall
- Generate compliance report (PDF) for IRB submission

**FR7: API Access**
- REST API endpoint: `POST /api/v1/deidentify`
- Request: `{"text": "Patient John Doe...", "method": "safe_harbor", "options": {...}}`
- Response: `{"deidentified_text": "Patient [NAME]...", "entities_removed": [...], "confidence": 0.95}`
- Batch endpoint: `POST /api/v1/deidentify/batch`
- Rate limiting: 100 requests/minute per user
- API authentication: JWT tokens

**FR8: Audit Logging**
- Log every de-identification request:
  - User ID, timestamp, document ID
  - Method used (Safe Harbor / Expert Determination)
  - Number of entities removed (by type)
  - Confidence scores (mean, min, max)
- Searchable audit log UI
- Export to CSV for compliance audits
- Retention: 8 years (HIPAA requirement)

### Non-Functional Requirements

**NFR1: Performance**
- Process clinical note (10 pages) in <2 minutes
- Batch processing: 1,000 notes in <2 hours
- API response time: <3 seconds for single note
- Support 50 concurrent de-identification jobs
- Elasticsearch indexing: <1 second per document

**NFR2: Accuracy**
- PHI detection precision: >95% (low false positive rate)
- PHI detection recall: >90% (catch 90% of actual PHI)
- Human review required for confidence <0.8
- Validation against gold standard corpus (1,000 manually annotated notes)
- Monthly model retraining with new annotations

**NFR3: Security & Privacy**
- All PHI access logged for audit trail
- Role-based access control (only authorized users can de-identify)
- Original notes encrypted at rest (AES-256)
- De-identified notes stored separately (lower security tier)
- No PHI in application logs or error messages
- Secure deletion of original notes after de-identification (if requested)

**NFR4: Compliance**
- HIPAA Safe Harbor compliance (45 CFR §164.514(b)(2))
- Expert Determination support (45 CFR §164.514(b)(1))
- IRB-ready compliance reports (PDF with methodology, validation metrics)
- Annual compliance audit by external auditor
- Documentation: De-identification Standard Operating Procedure (SOP)

**NFR5: Usability**
- One-click de-identification for single notes
- Batch upload via CSV or database query
- Progress indicator for long-running jobs
- Email notifications on completion
- Downloadable results (CSV, JSON, TXT)
- Training materials (video tutorials, user guide)

**NFR6: Scalability**
- Support 100,000 notes per month
- Horizontal scaling (add more workers for batch processing)
- Queue-based architecture (Redis/Celery)
- Caching frequent PHI patterns (Redis)
- Database sharding for large audit logs

## Success Criteria

### Quantitative Metrics

1. **Adoption Rate**
   - Target: 80% of research projects use de-identification module within 6 months
   - Measurement: Track unique users per month, notes processed per project

2. **Time Savings**
   - Target: Reduce de-identification time by 95% (30 min → 2 min per document)
   - Measurement: Time-on-task study with 10 research coordinators (pre/post)

3. **Accuracy**
   - Target: Precision >95%, Recall >90% (F1 score >0.92)
   - Measurement: Validation against gold standard corpus (1,000 annotated notes)

4. **Data Sharing**
   - Target: Enable 5 multi-site research collaborations in first year
   - Measurement: Track number of IRB-approved data sharing agreements citing module

5. **Compliance**
   - Target: Zero HIPAA violations related to de-identified data
   - Measurement: Annual compliance audit, incident tracking

### Qualitative Goals

- Research coordinators report "de-identification is no longer a bottleneck" (>80% agreement)
- IRB reviewers accept de-identification methodology without additional questions
- Data scientists trust de-identified data for ML model training
- Compliance officers confident in audit trail completeness

## Constraints & Assumptions

### Technical Constraints

- **NLP Accuracy**: MedCAT PHI detection ~92% recall (8% of PHI may be missed without human review)
- **Data Format**: Only supports unstructured clinical text (not structured EHR data)
- **Language**: English only (no multilingual support in Phase 1)
- **Infrastructure**: Must run on single workstation (no cloud deployment)

### Organizational Constraints

- **Timeline**: 12 weeks from design → production
- **Team**: 1 full-stack developer, 1 ML engineer (part-time), clinical advisor, compliance officer
- **Budget**: No additional infrastructure costs (use existing MedCAT setup)
- **Regulatory**: Requires IRB review of de-identification methodology

### Assumptions

- IRB will accept Safe Harbor method for most studies (no custom expert determination needed initially)
- Research coordinators willing to do human-in-the-loop review (catch missed PHI)
- MedCAT model can be fine-tuned for PHI detection (transfer learning)
- 8% false negative rate acceptable with human review safety net

## Out of Scope

### Explicitly NOT Building

1. **Structured Data De-identification**: Only clinical notes (text), not EHR structured data (lab values, vital signs)
2. **Image De-identification**: No face detection or X-ray de-identification
3. **Real-time De-identification**: Batch processing only (not streaming)
4. **Multi-language Support**: English only (Spanish, Mandarin in future phases)
5. **Re-identification Risk Analysis**: Simple confidence scores, not statistical disclosure control
6. **Data Synthesis**: No synthetic data generation (only removal/masking)
7. **Custom NER Training UI**: Use existing MedCAT models (no model training interface)
8. **Blockchain Audit Trail**: Standard database audit log (not blockchain-based)

## Dependencies

### External Dependencies

1. **MedCAT Service**: Phase 3 NLP infrastructure for entity recognition
2. **PHI NER Model**: Pre-trained or fine-tuned NER model for PHI detection (may need to train)
3. **Elasticsearch**: Store original and de-identified notes with audit metadata
4. **Celery + Redis**: Background job processing for batch de-identification
5. **IRB Approval**: Institutional Review Board must approve de-identification methodology

### Internal Dependencies

1. **Search Module** (Sprint 1-2): Reuse entity highlighting patterns for PHI visualization
2. **Timeline Module** (Sprint 4-5): De-identified notes feed into timeline view
3. **Backend API Team**: Provide `/api/v1/deidentify` endpoint
4. **Compliance Team**: Review and approve de-identification SOP
5. **DevOps**: Set up secure storage for de-identified notes (separate from PHI)

### Timeline of Dependencies

- **Week 1-2**: Fine-tune MedCAT model for PHI detection (ML engineer)
- **Week 3-4**: Backend API development (developer)
- **Week 5-6**: Frontend UI for batch processing and review (developer)
- **Week 7-8**: Integration testing and IRB documentation (all team)
- **Week 9**: IRB review and approval (compliance officer)
- **Week 10-11**: Pilot with 3 research projects (clinical advisor)
- **Week 12**: Production rollout and training (all team)

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PHI detection recall <90% | Medium | Critical | Human-in-the-loop review, continuous model improvement |
| IRB rejects methodology | Low | High | Early engagement with IRB, pilot study validation |
| Re-identification possible | Low | Critical | Red team testing (attempt re-identification), expert consultation |
| Performance too slow for large batches | Medium | Medium | Optimize NLP pipeline, parallel processing, caching |
| User adoption low (prefer manual) | Low | Medium | Demonstrate time savings, make UI intuitive, provide training |
| Compliance audit failure | Low | Critical | External audit before production, document everything |
| MedCAT model drift over time | Medium | Medium | Monthly retraining, validation dataset monitoring |

## Validation Plan

### Phase 1: Technical Validation (Week 8)

**Gold Standard Corpus**:
- 1,000 clinical notes manually annotated by 2 clinical annotators
- Inter-annotator agreement >0.90 (Cohen's kappa)
- Cover diverse note types (H&P, discharge summaries, progress notes)

**Metrics**:
- Precision, Recall, F1 score per PHI category
- Confusion matrix (which PHI types are missed)
- Processing time per document (performance)

### Phase 2: Clinical Validation (Week 10-11)

**Pilot Studies**:
- 3 research projects (cardiology, oncology, diabetes)
- 500 notes de-identified per project
- Research coordinators review 10% sample
- Measure time savings and user satisfaction

**Success Criteria**:
- Zero PHI found in 10% sample review
- Time savings >90% vs manual
- User satisfaction score >4/5

### Phase 3: Compliance Validation (Week 9)

**IRB Review**:
- Submit de-identification methodology SOP to IRB
- Include validation metrics from Phase 1
- Request approval for secondary data use

**Compliance Audit**:
- External HIPAA compliance expert reviews:
  - De-identification process
  - Audit trail completeness
  - Security controls
- Aim for zero findings

## Next Steps

1. **Model Development** (Week 1-2):
   - Acquire or create annotated PHI dataset (1,000 notes)
   - Fine-tune MedCAT NER model for 18 HIPAA identifiers
   - Validate on held-out test set (target: F1 >0.92)

2. **Backend Development** (Week 3-6):
   - Implement de-identification API endpoint
   - Build batch processing pipeline (Celery + Redis)
   - Create audit logging system
   - Write comprehensive tests

3. **Frontend Development** (Week 5-8):
   - Build batch upload UI
   - Create side-by-side review interface
   - Implement manual annotation tool
   - Add audit log viewer

4. **IRB Preparation** (Week 7-9):
   - Write de-identification SOP document
   - Compile validation metrics
   - Submit to IRB for review
   - Address IRB questions/concerns

5. **Pilot & Rollout** (Week 10-12):
   - Pilot with 3 research projects
   - Incorporate feedback
   - Train research coordinators
   - Production deployment

---

**Created**: 2025-11-21T16:44:09Z
**Status**: Backlog
**Next Command**: `/pm:prd-parse de-identification-module`
