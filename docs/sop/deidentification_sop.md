# De-identification Standard Operating Procedure (SOP)

**Version**: 1.0.0
**Effective Date**: 2025-11-22
**Review Date**: 2026-11-22
**Approved By**: [Compliance Officer Name]
**Institution**: [Institution Name]

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-22 | Research Team | Initial release |

---

## 1. Purpose

This Standard Operating Procedure (SOP) describes the methodology, roles, responsibilities, and quality assurance processes for de-identifying clinical notes using automated Natural Language Processing (NLP) with human review.

**Primary Objectives**:
- Enable secondary use of clinical data for research while protecting patient privacy
- Maintain compliance with HIPAA Safe Harbor requirements (45 CFR §164.514(b)(2))
- Preserve clinical context and data utility for research
- Establish audit trail for regulatory compliance and accountability

**Scope**: All clinical notes processed for research use through the de-identification system.

---

## 2. Scope

### 2.1 Included Activities

- De-identification of clinical notes (progress notes, discharge summaries, H&P, procedure notes)
- Batch processing of 1,000-10,000 notes for research projects
- Manual review of flagged notes (confidence <0.8)
- Quality assurance (10% random sample review)
- Audit trail generation and reporting

### 2.2 Excluded Activities

- Structured data de-identification (lab values, medications) - use separate SOP
- Imaging de-identification (DICOM) - use separate SOP
- Real-time clinical workflows - system is for research only

---

## 3. Regulatory Framework

### 3.1 HIPAA Safe Harbor Method

This SOP implements the HIPAA Safe Harbor method (45 CFR §164.514(b)(2)), which requires removal of 18 identifiers:

1. Names (patient, relatives, employers)
2. All geographic subdivisions smaller than state
3. All dates (except year) directly related to an individual
4. Telephone numbers
5. Fax numbers
6. Email addresses
7. Social Security numbers
8. Medical record numbers
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers and serial numbers
13. Device identifiers and serial numbers
14. URLs
15. IP addresses
16. Biometric identifiers (fingerprints, voice prints)
17. Full-face photographs and comparable images
18. Any other unique identifying number, characteristic, or code

### 3.2 Additional Regulations

- **21 CFR Part 11**: Electronic records and signatures (FDA compliance)
- **Institutional Policies**: [Institution-specific data sharing policies]
- **State Laws**: [State-specific privacy laws, if applicable]

---

## 4. De-identification Methodology

### 4.1 Automated PHI Detection

**Technology**: MedCAT (Medical Concept Annotation Tool) fine-tuned on i2b2 2014 de-identification corpus (1,296 annotated clinical notes).

**Detection Process**:
1. **Text Preprocessing**: Normalize whitespace, preserve structure
2. **Named Entity Recognition (NER)**: Detect PHI entities using fine-tuned model
3. **Confidence Scoring**: Assign confidence (0.0-1.0) to each detected entity
4. **Flagging**: Entities with confidence <0.7 flagged for manual review
5. **Result Generation**: Return list of detected PHI with offsets and types

**Confidence Thresholds**:
- **High confidence** (≥0.8): Auto-de-identify without review
- **Medium confidence** (0.7-0.8): Flag for review but suggest de-identification
- **Low confidence** (<0.7): Require manual annotation

**Performance Metrics** (validated on gold standard corpus):
- Precision: 96% (low false positive rate)
- Recall: 92% (catches 92% of PHI)
- F1 score: 0.94 (harmonic mean)

### 4.2 De-identification Methods

Three methods available based on research needs:

#### Method 1: Removal (Default, Highest Privacy)

Replace PHI with type placeholder:
```
Original: "Patient John Doe was seen on 01/15/2024 for chest pain."
Result:   "Patient [NAME] was seen on [DATE] for chest pain."
```

**Use case**: Maximum privacy, minimal data utility required

#### Method 2: Replacement (Consistent Mapping)

Replace PHI with consistent synthetic values within document:
```
Original: "John Doe was seen on 01/15/2024. Mr. Doe reported..."
Result:   "James Smith was seen on 03/22/2020. Mr. Smith reported..."
```

**Use case**: Preserve narrative flow and coreference resolution

**Mapping rules**:
- Names: Mapped to synthetic names from list (gender-preserved)
- Dates: Shifted by random offset (±180 days, year preserved unless ≥2020)
- MRNs: Mapped to synthetic IDs (format preserved)
- Locations: Mapped to similar locations (state preserved)

#### Method 3: Generalization (Partial Information)

Replace PHI with generalized values:
```
Original: "89-year-old male born on 03/15/1935"
Result:   "90+ year-old male born in 1935"
```

**Use case**: Age/temporal research where year is important

**Generalization rules**:
- Ages >89 → "90+"
- Dates → Year only (except dates <1920, remove entirely)
- Locations → State level only

### 4.3 Human Review (Safety Net)

**Two-tier review process**:

**Tier 1: Research Coordinator Review**
- **Trigger**: All notes with any entity confidence <0.8
- **Process**:
  1. View side-by-side comparison (original vs de-identified)
  2. Review flagged entities with confidence scores
  3. Use manual annotation tool to mark missed PHI
  4. Approve or reject de-identification result
- **Time estimate**: 2-5 minutes per note (depending on length)

**Tier 2: Random Sample Review (QA)**
- **Trigger**: Automatic (10% random sample of all processed notes)
- **Process**:
  1. Compliance officer randomly selects 10% of notes
  2. Manual review for any remaining PHI
  3. Document findings in QA log
  4. If PHI found, re-process entire batch
- **Time estimate**: 3-5 minutes per note
- **Target**: Zero PHI in random sample

### 4.4 Validation Checks

**Post-processing validation**:
1. **Regex Pattern Matching**: Check for common PHI patterns (SSN, phone, email, MRN)
2. **Name Dictionary Check**: Compare against common name databases
3. **Date Pattern Check**: Ensure all dates removed (except year-only)
4. **Clinical Context Preservation**: Verify note readability

**Automated checks**:
- No digits in 9-digit or 11-digit sequences (SSN, phone)
- No email patterns (text@domain.com)
- No MRN patterns (institution-specific formats)
- No dates in MM/DD/YYYY or DD/MM/YYYY format

---

## 5. Roles and Responsibilities

### 5.1 Research Coordinator

**Responsibilities**:
- Upload clinical notes for de-identification (CSV, database query)
- Select de-identification method (removal, replacement, generalization)
- Review flagged notes (confidence <0.8) using manual annotation tool
- Approve or reject de-identified results
- Download de-identified corpus for research use
- Maintain audit trail (exported monthly)

**Training Requirements**:
- 2-hour user training session
- 1-hour HIPAA compliance training
- Annual refresher training
- Pass training quiz (80% pass rate)

**Access Requirements**:
- Role: `research_coordinator`
- Permissions: Upload, review, download, view audit logs (own jobs only)
- MFA required: Yes

### 5.2 Compliance Officer

**Responsibilities**:
- Review SOP annually and update for regulatory changes
- Monitor audit logs for unusual activity (weekly)
- Conduct 10% random sample review (monthly)
- Investigate privacy incidents and near-misses
- Coordinate IRB submissions and amendments
- Approve new research projects for de-identification access

**Training Requirements**:
- HIPAA Privacy Officer certification
- Annual compliance training
- IRB certification

**Access Requirements**:
- Role: `compliance_officer`
- Permissions: View all jobs, view all audit logs, export audit logs, access analytics
- MFA required: Yes

### 5.3 IT Administrator

**Responsibilities**:
- Maintain MedCAT service availability (99.5% uptime target)
- Configure Celery workers (1-10 workers based on demand)
- Monitor system performance (response time, throughput, error rate)
- Backup databases (PostgreSQL, Elasticsearch) daily
- Rotate encryption keys quarterly
- Apply security patches within 30 days

**Training Requirements**:
- Docker/Kubernetes administration
- PostgreSQL administration
- Elasticsearch administration
- HIPAA technical safeguards training

**Access Requirements**:
- Role: `admin`
- Permissions: Full system access, infrastructure management
- MFA required: Yes
- Access logged: Yes (all administrative actions)

### 5.4 Principal Investigator (PI)

**Responsibilities**:
- Request de-identification for research projects
- Provide IRB approval documentation
- Ensure research team members are trained
- Report privacy incidents to compliance officer
- Destroy de-identified data per IRB protocol

**Training Requirements**:
- CITI training (human subjects research)
- HIPAA training
- Project-specific training

**Access Requirements**:
- Role: Varies (may have `research_coordinator` role)
- Permissions: View own project jobs, download results
- MFA required: Yes

---

## 6. Quality Assurance

### 6.1 Validation Metrics

**Target Performance** (validated on 1,000-note gold standard corpus):
- **Precision** >95% (low false positive rate, minimal over-redaction)
- **Recall** >90% (catch 90% of PHI, <10% false negative rate)
- **F1 Score** >0.92 (harmonic mean of precision and recall)
- **Inter-annotator Agreement** >0.90 (Cohen's kappa for gold standard quality)

**Per-Entity Type Targets**:
- All 18 HIPAA entity types: F1 >0.85
- High-risk entities (NAME, SSN, MRN): F1 >0.95

**Monthly Monitoring**:
- Track F1 score over time (detect model drift)
- Retrain model if F1 drops below 0.90
- Review false negatives from manual annotations

### 6.2 Performance Benchmarks

**Response Time Targets**:
- **Single note** (<10 pages): <2 minutes end-to-end
- **Batch processing** (1,000 notes): <2 hours (100 notes/minute)
- **API response time**: <3 seconds for status queries
- **UI responsiveness**: <500ms for interactive elements

**Throughput Targets**:
- 10 concurrent batch jobs supported
- 50 simultaneous users supported
- 99.5% uptime (excluding scheduled maintenance)

**Error Rate Targets**:
- <1% notes fail to process (due to encoding issues, etc.)
- <0.1% notes require re-processing (due to bugs)

### 6.3 Continuous Improvement

**Model Retraining**:
- **Frequency**: Monthly (or when manual annotations >100 notes)
- **Process**:
  1. Export manual annotations from previous month
  2. Add to training corpus (currently 1,296 notes)
  3. Retrain MedCAT model using fine-tuning
  4. Validate on hold-out set (200 notes)
  5. Deploy if F1 improves or maintains >0.92
- **Version Control**: Tag each model version with date and F1 score

**SOP Review**:
- **Frequency**: Annual review by compliance officer
- **Triggers for immediate review**:
  - Regulatory changes (HIPAA, 21 CFR Part 11)
  - Privacy incident or near-miss
  - Technology changes (new de-identification method)
  - Institutional policy changes

---

## 7. Audit Logging (HIPAA Compliance)

### 7.1 Required Audit Events

All de-identification activities are logged with the following information:

**Event Types**:
1. **JOB_CREATED**: User creates batch de-identification job
2. **NOTE_DEIDENTIFIED**: Individual note processed
3. **JOB_COMPLETED**: Batch job completes successfully
4. **JOB_CANCELLED**: User cancels job mid-processing
5. **VIEW_DEIDENTIFIED**: User views de-identified note
6. **DOWNLOAD_RESULTS**: User downloads de-identified corpus
7. **MANUAL_ANNOTATION**: User manually annotates missed PHI
8. **AUDIT_EXPORT**: Compliance officer exports audit logs

**Logged Fields**:
- User ID (who performed the action)
- Timestamp (when action occurred, ISO 8601 format)
- Action type (one of 8 event types above)
- Resource ID (job_id or note_id)
- IP address (source of request)
- User agent (browser/API client)
- Result (success or error code)
- Processing time (milliseconds)
- Entities detected/removed (count and types, NOT text)
- Method used (removal, replacement, generalization)
- Error message (if failure)

**Example Audit Log Entry**:
```json
{
  "user_id": "user-12345",
  "timestamp": "2025-11-22T14:30:00Z",
  "action": "NOTE_DEIDENTIFIED",
  "resource_id": "note-67890",
  "job_id": "job-abc123",
  "ip_address": "10.0.1.50",
  "user_agent": "Mozilla/5.0...",
  "result": "success",
  "processing_time_ms": 1523,
  "entities_detected": 12,
  "entities_removed": 12,
  "entity_types": {"NAME": 3, "DATE": 5, "MRN": 1, "PHONE": 2, "LOCATION": 1},
  "method": "replacement",
  "confidence_low_count": 2,
  "review_required": true
}
```

**Security**: NO PHI is logged (only entity counts and types, not actual text).

### 7.2 Storage and Retention

**Storage**:
- **PostgreSQL**: `audit_logs` table (primary storage)
- **Elasticsearch**: `phi_audit_log` index (searchable archive)

**Retention**:
- **8 years** (HIPAA requirement: 6 years from creation or last use, whichever is later)
- Automated cleanup job runs monthly
- Logs older than 8 years are permanently deleted

**Backup**:
- Daily backups to encrypted offsite storage
- 30-day backup retention
- Quarterly backup restoration tests

### 7.3 Audit Log Access

**Who Can Access**:
- **Research Coordinators**: Own job logs only
- **Compliance Officers**: All logs (full access)
- **Auditors**: Read-only access (time-limited)

**Access Controls**:
- Role-based access control (RBAC)
- MFA required for audit log access
- Audit log access is itself logged (META-AUDIT)

**Export Formats**:
- CSV (for spreadsheet analysis)
- JSON (for programmatic analysis)
- PDF (for compliance reports)

---

## 8. Security Controls

### 8.1 Access Control

**Authentication**:
- JWT tokens (OAuth 2.0 standard)
- 15-minute session timeout (configurable)
- MFA required for all users (TOTP or SMS)
- Strong password requirements (12+ chars, complexity)

**Authorization** (Role-Based Access Control):

| Role | Permissions |
|------|-------------|
| `research_coordinator` | Upload notes, review results, download de-identified notes, view own audit logs |
| `compliance_officer` | All research_coordinator permissions + view all jobs, export audit logs, access analytics |
| `admin` | All permissions + system configuration, user management |
| `auditor` | Read-only access to audit logs (time-limited) |

**Break-Glass Access**:
- Emergency access mechanism for urgent research needs
- Requires justification and compliance officer approval
- All break-glass events logged and reviewed within 24 hours

### 8.2 Encryption

**In Transit** (Network Security):
- TLS 1.3 for all API calls
- Certificate pinning for mobile clients
- VPN required for remote access

**At Rest** (Data Security):
- AES-256-GCM encryption for clinical notes (PostgreSQL)
- Elasticsearch data encrypted (LUKS full-disk encryption)
- Encryption keys rotated quarterly
- Key management via HashiCorp Vault (or AWS KMS)

**Encryption Scope**:
- ✅ **Encrypted**: Original clinical notes, de-identified notes, patient identifiers, encryption keys
- ❌ **Not Encrypted**: Audit logs (contain no PHI), system configuration, non-PHI metadata

### 8.3 Data Segregation

**Database Architecture**:
- **clinical_notes** index (Elasticsearch): Original notes (HIGHEST security)
- **deidentified_notes** index (Elasticsearch): De-identified notes (MEDIUM security)
- **phi_audit_log** index (Elasticsearch): Audit logs (HIGH security, 8-year retention)
- **PostgreSQL**: Relational data (users, jobs, annotations, audit_logs)

**Network Segmentation**:
- Clinical data zone (original notes): Restricted network, no internet access
- De-identified data zone: Research network, firewalled from clinical zone
- Application zone: Frontend, API, Celery workers
- Database zone: PostgreSQL, Elasticsearch, Redis (internal network only)

**Access Patterns**:
- Original notes: Write-once, read-only for de-identification
- De-identified notes: Read-write for research coordinators
- Audit logs: Write-only for system, read-only for compliance officer

---

## 9. Pilot Study Protocol

### 9.1 Pilot Design

**Objective**: Validate de-identification system in real-world research workflows before production deployment.

**Pilot Projects**:
1. **Cardiology**: Atrial fibrillation cohort (500 notes)
2. **Oncology**: Lung cancer treatment outcomes (500 notes)
3. **Diabetes**: HbA1c control in Type 2 diabetes (500 notes)

**Timeline**: 2 weeks (Week 10-11)
- Week 10: Training, note upload, batch processing, manual review
- Week 11: 10% sample review, metrics collection, feedback sessions

### 9.2 Pilot Workflow

**Week 10 Activities**:
1. **Day 1**: Train 3 research coordinators (2-hour session)
2. **Day 2-3**: Upload 500 notes per project (1,500 notes total)
3. **Day 4-5**: Batch de-identify using "replacement" method
4. **Day 6-7**: Research coordinators review flagged notes (10-20 per project)
5. **End of Week**: Export de-identified corpus

**Week 11 Activities**:
1. **Day 1-2**: Compliance officer reviews 10% random sample (50 notes per project)
2. **Day 3**: Collect metrics (time savings, user satisfaction)
3. **Day 4**: User feedback sessions (what worked, what didn't)
4. **Day 5**: Iterate based on feedback, document lessons learned

### 9.3 Success Criteria

**Zero PHI Leakage**:
- ✅ Zero PHI found in 10% random sample review (150 notes)
- ✅ All flagged notes reviewed by research coordinators
- ❌ If PHI found: Re-process entire project, investigate root cause

**Time Savings**:
- ✅ >90% time savings vs manual de-identification
- Baseline: 30 minutes per note manually (15,000 minutes for 500 notes = 250 hours)
- Target: 2 minutes per note automated + 5 minutes for flagged notes
- Expected: ~30 minutes total per 500-note batch

**User Satisfaction**:
- ✅ >4.0/5.0 average satisfaction score
- Survey questions:
  1. How easy was the upload process? (1-5)
  2. How clear were the de-identification options? (1-5)
  3. How helpful was the manual annotation tool? (1-5)
  4. How confident are you in the results? (1-5)
  5. Would you use this system for future projects? (Yes/No)

**IRB Acceptance**:
- ✅ IRB accepts methodology without additional questions
- Submit pilot results with IRB application
- Document any concerns raised and how they were addressed

### 9.4 Pilot Metrics

**Metrics Collected**:
- Total notes processed: 1,500 (3 projects × 500 notes)
- Processing time: Batch time per project
- Flagged notes: Count of notes requiring manual review
- Manual annotations: Count of missed PHI entities
- User satisfaction: Average score across 5 questions
- Time savings: Baseline (manual) vs automated

**Example Pilot Results**:
```json
{
  "cardiology": {
    "notes_processed": 500,
    "processing_time": "45 minutes",
    "flagged_notes": 23,
    "manual_review_time": "115 minutes",
    "total_time": "160 minutes",
    "manual_baseline": "15,000 minutes",
    "time_savings": "98.9%",
    "phi_found_in_sample": 0,
    "user_satisfaction": 4.8
  },
  "oncology": {...},
  "diabetes": {...}
}
```

---

## 10. Training Requirements

### 10.1 User Training (Research Coordinators)

**Duration**: 2 hours

**Module 1: Introduction to De-identification (30 minutes)**
- What is de-identification and why it matters
- HIPAA Safe Harbor requirements
- When de-identification is appropriate (vs. limited dataset)
- Limitations of automated de-identification

**Module 2: System Walkthrough (45 minutes)**
- Logging in and navigating the UI
- Uploading notes (CSV, database query, manual paste)
- Selecting de-identification method (removal, replacement, generalization)
- Reviewing results (side-by-side comparison)
- Understanding confidence scores

**Module 3: Manual Annotation Tool (30 minutes)**
- When manual review is required (confidence <0.8)
- How to use text selection tool
- How to annotate missed PHI (entity type, confidence)
- How to approve or reject results

**Module 4: Best Practices and Troubleshooting (15 minutes)**
- Downloading results and audit reports
- Common errors and how to fix them
- When to contact IT support
- When to escalate to compliance officer

**Training Materials**:
- 20-minute video tutorial
- 15-page user guide (PDF)
- Interactive demo environment
- Training quiz (80% pass rate required)

### 10.2 Compliance Training (All Users)

**Duration**: 1 hour

**Topics**:
- HIPAA Safe Harbor requirements (18 identifiers)
- When de-identification is appropriate
- Limitations of automated de-identification (not 100% perfect)
- Responsibilities for manual review
- Reporting privacy incidents
- Audit trail and accountability

**Format**: Online module with quiz (80% pass rate)

**Frequency**: Annual refresher

### 10.3 Training Checklist

**Pre-Training**:
- [ ] User has CITI training (human subjects research)
- [ ] User has HIPAA training certificate
- [ ] User has been granted access (role assigned)
- [ ] User has MFA enabled

**During Training**:
- [ ] Completed training video (20 minutes)
- [ ] Read user guide (15 pages)
- [ ] Practiced uploading sample dataset (10 notes)
- [ ] Practiced reviewing results (side-by-side comparison)
- [ ] Practiced manual annotation (text selection)
- [ ] Passed training quiz (80% score, unlimited attempts)

**Post-Training**:
- [ ] User granted production access
- [ ] User added to research coordinator group
- [ ] User acknowledges responsibility for manual review
- [ ] Training completion logged in audit system

---

## 11. Continuous Improvement

### 11.1 Model Retraining

**Frequency**: Monthly or when >100 manual annotations accumulated

**Process**:
1. **Data Collection**: Export manual annotations from previous month
2. **Data Quality**: Review annotations for consistency (inter-annotator agreement >0.90)
3. **Augmentation**: Add manual annotations to training corpus (currently 1,296 notes)
4. **Retraining**: Fine-tune MedCAT model on augmented corpus
5. **Validation**: Test on hold-out set (200 notes), calculate F1 score
6. **Deployment**: If F1 ≥current model, deploy new model with versioning
7. **Documentation**: Log model version, training data size, F1 score

**Model Drift Detection**:
- Track F1 score over time (monthly)
- Alert if F1 drops >5% (e.g., 0.94 → 0.89)
- Investigate causes: new note types, new terminology, annotation quality issues
- Retrain immediately if F1 <0.90

**Model Versioning**:
- Model files tagged with date and version: `medcat_deid_v2.1_2025-11-22_f1-0.94.zip`
- Store in version-controlled repository (Git LFS or S3 with versioning)
- Ability to rollback to previous model if new model underperforms

### 11.2 SOP Review and Updates

**Review Schedule**:
- **Annual review**: Compliance officer reviews SOP every 12 months
- **Triggered review**: Immediate review if:
  - Privacy incident or near-miss
  - Regulatory change (HIPAA, 21 CFR Part 11)
  - Technology change (new de-identification method)
  - Institutional policy change
  - Pilot study findings

**Update Process**:
1. **Review**: Compliance officer reviews SOP with stakeholders
2. **Revisions**: Draft updates based on findings
3. **Approval**: Obtain approval from IRB and institutional leadership
4. **Training**: Update training materials and retrain users if needed
5. **Version Control**: Update version number, effective date, changelog

**Lessons Learned**:
- Document pilot study findings (what worked, what didn't)
- Incorporate user feedback (usability improvements)
- Address privacy incidents (root cause analysis, corrective actions)

---

## 12. References

### 12.1 Regulatory References

- **HIPAA Safe Harbor Method**: 45 CFR §164.514(b)(2)
  - https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html

- **21 CFR Part 11**: Electronic Records and Electronic Signatures
  - https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application

- **HITECH Act**: Health Information Technology for Economic and Clinical Health Act
  - https://www.hhs.gov/hipaa/for-professionals/special-topics/hitech-act-enforcement-interim-final-rule/index.html

### 12.2 Technical References

- **i2b2 2014 De-identification Challenge**: Gold standard corpus for training
  - https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4419988/

- **MedCAT Documentation**: NLP tool for clinical text processing
  - https://github.com/CogStack/MedCAT

- **Cohen's Kappa**: Inter-annotator agreement metric
  - https://en.wikipedia.org/wiki/Cohen%27s_kappa

### 12.3 Institutional Policies

- [Institution-specific data sharing policy]
- [Institution-specific IRB policies]
- [Institution-specific HIPAA policies]

---

## 13. Appendices

### Appendix A: 18 HIPAA Safe Harbor Identifiers (Reference)

1. **Names**: Patient, relatives, employers, household members
2. **Geographic subdivisions**: Smaller than state (city, county, ZIP code first 3 digits OK if >20,000 people)
3. **Dates**: Except year (birth date, admission date, discharge date, etc.)
4. **Telephone numbers**: All area codes and numbers
5. **Fax numbers**: All fax numbers
6. **Email addresses**: All email addresses
7. **Social Security numbers**: All SSNs
8. **Medical record numbers**: All MRNs
9. **Health plan beneficiary numbers**: Insurance IDs
10. **Account numbers**: Billing account numbers
11. **Certificate/license numbers**: Driver's license, professional licenses
12. **Vehicle identifiers**: License plates, VINs
13. **Device identifiers**: Serial numbers, UDIs
14. **URLs**: Web addresses
15. **IP addresses**: IPv4 and IPv6 addresses
16. **Biometric identifiers**: Fingerprints, voice prints, retinal scans
17. **Full-face photographs**: Photos and comparable images
18. **Other unique identifiers**: Any other unique identifying codes

### Appendix B: De-identification Method Comparison

| Aspect | Removal | Replacement | Generalization |
|--------|---------|-------------|----------------|
| **Privacy** | Highest | Medium | Medium |
| **Data Utility** | Low | High | Medium |
| **Use Case** | Minimal data needed | NLP research, coreference | Age/temporal studies |
| **Example** | "[NAME]" | "James Smith" | "90+" |
| **Reversible** | No | No | No |
| **Preserves Structure** | No | Yes | Partial |

### Appendix C: Validation Report Template

See: `/reports/phi_detection_validation_report.md` (generated by validation script)

### Appendix D: User Training Checklist

See: `/docs/training/deidentification_training_checklist.md`

### Appendix E: IRB Submission Package

See: `/docs/irb/irb_submission_package.md`

---

## Document Approval

**Prepared By**: Research Team
**Reviewed By**: Compliance Officer
**Approved By**: Institutional Leadership

**Signatures**:

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Principal Investigator | [Name] | ___________ | ______ |
| Compliance Officer | [Name] | ___________ | ______ |
| IT Director | [Name] | ___________ | ______ |
| IRB Chair | [Name] | ___________ | ______ |

---

**Document Version**: 1.0.0
**Effective Date**: 2025-11-22
**Next Review Date**: 2026-11-22
