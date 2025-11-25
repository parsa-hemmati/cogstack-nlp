# De-identification System Training Checklist

**Version**: 1.0.0
**Last Updated**: 2025-11-22
**Purpose**: Ensure all users complete required training before accessing the de-identification system

---

## Training Overview

**Who**: All research coordinators, principal investigators, and authorized users

**Duration**:
- Pre-training: 30 minutes (prerequisites)
- Training session: 2 hours (user training)
- Compliance training: 1 hour (HIPAA)
- Hands-on practice: 1 hour (demo environment)
- **Total**: 4.5 hours

**Pass Rate**: 80% on training quiz (unlimited attempts)

**Validity**: 12 months (annual refresher required)

---

## Pre-Training Requirements

### ☐ 1. Prerequisites Completed

**Required Certifications**:
- [ ] **CITI Training**: Human Subjects Research certification (valid within 3 years)
  - URL: https://www.citiprogram.org/
  - Modules: Biomedical Research Investigators, Social & Behavioral Research
  - Certificate upload location: [Link to institutional portal]

- [ ] **HIPAA Training**: Privacy and security training (valid within 1 year)
  - Provider: [Institution-specific HIPAA training]
  - Duration: 2 hours
  - Topics: Privacy Rule, Security Rule, Breach Notification
  - Certificate upload location: [Link to institutional portal]

**Institutional Requirements**:
- [ ] **Background Check**: Cleared (for access to PHI systems)
- [ ] **Confidentiality Agreement**: Signed and on file
- [ ] **IRB Approval**: PI has active IRB protocol (provide protocol number)
- [ ] **PI Approval Letter**: PI authorizes user for de-identification access

**Technical Setup**:
- [ ] **Computer**: Institutional workstation or approved laptop (encrypted, antivirus)
- [ ] **Network**: Connected to institutional network or VPN
- [ ] **Browser**: Chrome 90+, Firefox 88+, Edge 90+, or Safari 14+ (latest version recommended)
- [ ] **MFA Device**: Smartphone with authenticator app (Google Authenticator, Authy) OR phone for SMS

---

### ☐ 2. Access Request Submitted

**Request Process**:
- [ ] **Email IT Administrator**: [it-admin@institution.edu]
- [ ] **Include Required Information**:
  - Full name
  - Email address
  - Department
  - PI name
  - IRB protocol number
  - Requested role (`research_coordinator` or `principal_investigator`)
  - Training completion certificates (CITI, HIPAA)

**Wait Time**: 1-2 business days for account creation

**Confirmation Email**: Account credentials and MFA setup instructions

---

### ☐ 3. Multi-Factor Authentication (MFA) Enabled

**Setup Steps**:
- [ ] **Login**: Navigate to https://[your-institution]/deidentify → Enter credentials
- [ ] **MFA Setup Page**: System prompts for MFA setup (first login only)
- [ ] **Scan QR Code**: Use authenticator app (Google Authenticator, Authy, Microsoft Authenticator)
- [ ] **Enter Test Code**: Verify MFA working (6-digit code from app)
- [ ] **Save Backup Codes**: Download and store securely (for account recovery)
- [ ] **Test Login**: Logout → Login again with MFA code (verify working)

**Backup Codes**:
- [ ] Backup codes saved in secure location (password manager, encrypted file)
- [ ] **DO NOT** share backup codes or screenshot them

---

## Training Session Checklist

### ☐ 4. Training Video Watched

**Training Video**: [Link to 20-minute training video]

**Topics Covered**:
1. **Introduction** (5 minutes):
   - What is de-identification?
   - HIPAA Safe Harbor method (18 identifiers)
   - Why automated de-identification?
   - System overview (workflow diagram)

2. **Uploading Notes** (5 minutes):
   - CSV upload (format requirements)
   - Database query (SQL examples)
   - Manual paste (small jobs)
   - Job configuration (method selection, options)

3. **Reviewing Results** (5 minutes):
   - Monitoring job progress
   - Side-by-side comparison view
   - Confidence scores (0.0-1.0 scale)
   - Approving/rejecting notes

4. **Manual Annotation** (3 minutes):
   - When to use manual annotation
   - Text selection (click and drag)
   - Entity type dropdown (18 HIPAA categories)
   - Keyboard shortcuts (N=NAME, D=DATE, etc.)

5. **Downloading Results** (2 minutes):
   - Download formats (CSV, JSON, ZIP)
   - Audit log export (HIPAA compliance)
   - Secure storage best practices

**Video Completion**:
- [ ] Watched entire video (no skipping)
- [ ] Took notes on key points
- [ ] Questions noted for instructor (during live session)

---

### ☐ 5. User Guide Read

**User Guide**: `/docs/training/deidentification_user_guide.md` (15 pages)

**Required Reading**:
- [ ] **Section 1**: Quick Start Guide (5 minutes)
- [ ] **Section 2**: System Overview (10 minutes)
- [ ] **Section 3**: Detailed Workflow (20 minutes)
- [ ] **Section 4**: Manual Annotation Tool (15 minutes)
- [ ] **Section 5**: Downloading Results (10 minutes)
- [ ] **Section 6**: Troubleshooting (10 minutes)
- [ ] **Section 7**: FAQ (10 minutes)
- [ ] **Section 8**: Best Practices (10 minutes)

**Total Reading Time**: 90 minutes (can be done in multiple sessions)

**Comprehension Check**:
- [ ] Understand 3 de-identification methods (Removal, Replacement, Generalization)
- [ ] Know when to use manual annotation (PHI missed by automated system)
- [ ] Can identify 18 HIPAA entity types (NAME, DATE, LOCATION, etc.)
- [ ] Understand confidence scores and thresholds (0.7 default)

---

### ☐ 6. Live Training Session Attended

**Format**: 2-hour instructor-led session (in-person or virtual)

**Schedule**: [Link to training calendar]

**Agenda**:

**Hour 1: System Overview and Demo**
- [ ] **0:00-0:15**: Welcome and introductions
  - Instructor introduction
  - Participant introductions (name, department, research area)
  - Training objectives and schedule

- [ ] **0:15-0:30**: HIPAA Safe Harbor Review
  - 18 HIPAA identifiers (with examples)
  - Safe Harbor vs. Expert Determination
  - Institutional policies on de-identification

- [ ] **0:30-0:45**: System Architecture
  - MedCAT NLP model (fine-tuned on i2b2 2014 corpus)
  - Confidence scoring (0.0-1.0 scale)
  - Manual review workflow (flagged notes <0.8)
  - 10% sample review (compliance officer QA)

- [ ] **0:45-1:00**: Live Demo
  - Instructor demo: Upload CSV (10 sample notes)
  - Instructor demo: Monitor job progress
  - Instructor demo: Review flagged notes (side-by-side view)
  - Instructor demo: Manual annotation (text selection, entity types)
  - Instructor demo: Download results (CSV, JSON, audit log)

**Hour 2: Hands-On Practice**
- [ ] **1:00-1:15**: Practice Exercise 1 - Upload and Configure
  - Participant uploads sample dataset (10 notes provided)
  - Participant selects de-identification method (Replacement recommended)
  - Participant configures job (name, IRB number, email notification)
  - Participant starts job and monitors progress

- [ ] **1:15-1:30**: Practice Exercise 2 - Manual Review
  - Participant reviews flagged notes (2-3 notes with confidence <0.8)
  - Participant uses manual annotation tool (select text, choose entity type)
  - Participant approves/rejects notes
  - Participant finalizes review

- [ ] **1:30-1:45**: Practice Exercise 3 - Download and Verify
  - Participant downloads results (CSV format)
  - Participant spot-checks de-identified notes (10 random notes)
  - Participant exports audit log
  - Participant verifies no PHI in results

- [ ] **1:45-2:00**: Q&A and Troubleshooting
  - Instructor answers participant questions
  - Instructor demonstrates troubleshooting common errors
  - Instructor provides contact information (IT support, compliance officer)
  - Instructor schedules follow-up (1 week check-in)

**Attendance Verification**:
- [ ] Attended full 2-hour session (no early departure)
- [ ] Participated in all 3 practice exercises
- [ ] Asked questions or clarifications (if needed)
- [ ] Instructor signed attendance sheet

---

### ☐ 7. Hands-On Practice Completed

**Practice Environment**: https://[your-institution]/deidentify-demo

**Practice Dataset**: `/training/sample_notes.csv` (10 clinical notes)

**Practice Scenarios**:

**Scenario 1: Simple Batch (30 minutes)**
- [ ] Upload `sample_notes_simple.csv` (10 notes, no flagged notes)
- [ ] Select "Removal" method
- [ ] Monitor job progress (should complete in <1 minute)
- [ ] Download results and verify (all PHI replaced with placeholders)
- [ ] Export audit log and review (10 notes processed, 0 flagged)

**Scenario 2: Flagged Notes (30 minutes)**
- [ ] Upload `sample_notes_flagged.csv` (10 notes, 3 flagged notes <0.8)
- [ ] Select "Replacement" method
- [ ] Monitor job progress → Status: "Review Required"
- [ ] Review flagged notes (side-by-side comparison)
- [ ] Add manual annotation (instructor provides 1 missed PHI to find)
- [ ] Approve all notes and finalize review
- [ ] Download results and verify

**Scenario 3: Manual Annotation (30 minutes)**
- [ ] Upload `sample_notes_complex.csv` (10 notes, instructor hides 5 PHI entities)
- [ ] Select "Generalization" method
- [ ] Review all notes (even if not flagged)
- [ ] Find and annotate 5 hidden PHI entities (instructor provides answer key)
- [ ] Practice keyboard shortcuts (N=NAME, D=DATE, etc.)
- [ ] Download results and verify all PHI removed

**Practice Verification**:
- [ ] Completed all 3 scenarios
- [ ] Found all hidden PHI in Scenario 3 (5/5 correct)
- [ ] Comfortable with manual annotation tool
- [ ] Ready for production use

---

## Compliance Training Checklist

### ☐ 8. HIPAA Compliance Training Completed

**Training Module**: [Institution-specific HIPAA training]

**Topics Required**:
- [ ] **Privacy Rule** (45 minutes):
  - PHI definition (18 identifiers)
  - Permitted uses and disclosures
  - Minimum necessary standard
  - Patient rights (access, amendment, accounting)

- [ ] **Security Rule** (30 minutes):
  - Administrative safeguards (access control, audit logging)
  - Physical safeguards (workstation security, device encryption)
  - Technical safeguards (encryption, authentication, MFA)

- [ ] **Breach Notification Rule** (15 minutes):
  - Breach definition (unauthorized PHI disclosure)
  - Notification timelines (60 days to HHS/OCR)
  - Reporting procedures (institutional privacy officer)

- [ ] **De-identification Specifics** (30 minutes):
  - Safe Harbor method (remove 18 identifiers)
  - Expert Determination method (statistical disclosure risk)
  - Limited dataset (partial de-identification)
  - Re-identification prohibition

**Completion**:
- [ ] Passed HIPAA compliance quiz (80% required)
- [ ] Certificate uploaded to institutional portal
- [ ] Expiration date noted (annual renewal required)

---

### ☐ 9. Responsibilities Acknowledged

**User Responsibilities**:
- [ ] **Privacy**: I will protect patient privacy at all times
- [ ] **Accuracy**: I will carefully review flagged notes and annotate missed PHI
- [ ] **Security**: I will not share login credentials or MFA codes
- [ ] **Reporting**: I will report privacy incidents immediately (within 1 hour)
- [ ] **Compliance**: I will follow institutional policies and SOPs
- [ ] **Training**: I will complete annual refresher training
- [ ] **Data Handling**: I will store de-identified data securely and delete after research completes

**Acknowledgment**:
- [ ] Read and understood all responsibilities
- [ ] Signed responsibility acknowledgment form
- [ ] Form submitted to compliance officer

---

## Training Quiz

### ☐ 10. Training Quiz Passed

**Quiz Format**: 20 multiple-choice questions

**Pass Rate**: 80% (16/20 correct)

**Attempts**: Unlimited (can retake immediately if failed)

**Topics Covered**:
- HIPAA Safe Harbor identifiers (5 questions)
- De-identification methods (3 questions)
- Confidence scores and thresholds (3 questions)
- Manual annotation tool (4 questions)
- Audit logging and compliance (3 questions)
- Troubleshooting and best practices (2 questions)

**Sample Questions**:

**Q1**: Which of the following is NOT a HIPAA Safe Harbor identifier?
- A) Medical Record Number (MRN)
- B) Year of birth (e.g., 1985)
- C) Full date of birth (e.g., 01/15/1985)
- D) Social Security Number (SSN)
- **Answer**: B (Year is allowed, only month/day must be removed)

**Q2**: What does a confidence score of 0.65 mean?
- A) The entity is definitely PHI (de-identify automatically)
- B) The entity is probably PHI (flag for manual review)
- C) The entity is probably not PHI (ignore)
- D) The system is 65% sure it processed 65% of notes
- **Answer**: B (Scores <0.7 are flagged for manual review)

**Q3**: Which de-identification method preserves narrative flow and coreference?
- A) Removal (replace with "[NAME]")
- B) Replacement (consistent synthetic mapping)
- C) Generalization (partial information like "90+")
- D) None of the above
- **Answer**: B (Replacement maps "John Doe" to "James Smith" consistently)

**Quiz Completion**:
- [ ] Passed quiz with 80%+ score (16/20 correct)
- [ ] Reviewed incorrect answers (understand why wrong)
- [ ] Certificate generated and saved
- [ ] Certificate uploaded to institutional portal

---

## Production Access Authorization

### ☐ 11. Final Verification

**Before Production Access Granted**:
- [ ] All pre-training requirements completed (CITI, HIPAA, background check)
- [ ] MFA enabled and tested
- [ ] Training video watched (20 minutes)
- [ ] User guide read (90 minutes)
- [ ] Live training session attended (2 hours)
- [ ] Hands-on practice completed (3 scenarios, 90 minutes)
- [ ] HIPAA compliance training completed (90 minutes)
- [ ] Responsibilities acknowledged and signed
- [ ] Training quiz passed (80%+ score)

**IT Administrator Verification**:
- [ ] User account created
- [ ] Role assigned (`research_coordinator` or `principal_investigator`)
- [ ] MFA verified
- [ ] Training certificates reviewed
- [ ] Responsibility form on file
- [ ] Production access enabled

**Production Access Granted**:
- [ ] Email notification sent: "Production access granted"
- [ ] Demo environment access removed (no longer needed)
- [ ] Production URL: https://[your-institution]/deidentify
- [ ] Support contacts provided (IT, compliance, training)

---

### ☐ 12. Post-Training Follow-Up

**1-Week Check-In**:
- [ ] **Date**: [Scheduled date]
- [ ] **Trainer**: [Trainer name]
- [ ] **Format**: 15-minute phone call or video meeting
- [ ] **Agenda**:
  - Have you used the system since training?
  - Any questions or issues?
  - Any edge cases encountered?
  - Feedback on training (what worked, what didn't)

**1-Month Check-In**:
- [ ] **Date**: [Scheduled date]
- [ ] **Trainer**: [Trainer name]
- [ ] **Format**: Email survey
- [ ] **Questions**:
  - How many jobs have you completed? (0, 1-5, 6-10, 10+)
  - How confident do you feel using the system? (1-5 scale)
  - Have you found any PHI in de-identified results? (Yes/No, if yes report immediately)
  - What features would improve your workflow?

**Annual Refresher**:
- [ ] **Due Date**: [Training date + 12 months]
- [ ] **Format**: 1-hour online module + quiz (no live session required)
- [ ] **Topics**: System updates, new features, lessons learned, compliance review
- [ ] **Pass Rate**: 80% (same as initial training)

---

## Training Completion Certificate

**This certifies that**:

**User Name**: _______________________________

**User Email**: _______________________________

**Department**: _______________________________

**PI Name**: _______________________________

**IRB Protocol**: _______________________________

**Has successfully completed**:

- ✅ All pre-training requirements
- ✅ 2-hour user training session
- ✅ 1-hour HIPAA compliance training
- ✅ 1-hour hands-on practice
- ✅ Training quiz (score: ____%)
- ✅ Responsibility acknowledgment

**Training Date**: _______________________________

**Certificate Issued**: _______________________________

**Valid Until**: _______________________________ (12 months from training date)

**Instructor Signature**: _______________________________

**Compliance Officer Signature**: _______________________________

---

## Contact Information

**IT Support** (Technical issues, access requests):
- Email: [it-support@institution.edu]
- Phone: [555-123-4567]
- Hours: Mon-Fri 8am-5pm

**Compliance Officer** (Privacy incidents, audit logs):
- Email: [compliance@institution.edu]
- Phone: [555-123-4568]
- Hours: Mon-Fri 9am-5pm

**Training Coordinator** (Training materials, quiz resets):
- Email: [training@institution.edu]
- Phone: [555-123-4569]
- Hours: Mon-Fri 9am-5pm

---

**Training Checklist Version**: 1.0.0
**Last Updated**: 2025-11-22
**Next Review**: 2026-11-22
