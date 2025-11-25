# De-identification System User Guide

**Version**: 1.0.0
**Last Updated**: 2025-11-22
**Audience**: Research Coordinators, Principal Investigators
**Training Time**: 30 minutes (reading) + 30 minutes (hands-on practice)

---

## Table of Contents

1. [Quick Start Guide](#1-quick-start-guide)
2. [System Overview](#2-system-overview)
3. [Detailed Workflow](#3-detailed-workflow)
4. [Manual Annotation Tool](#4-manual-annotation-tool)
5. [Downloading Results](#5-downloading-results)
6. [Troubleshooting](#6-troubleshooting)
7. [FAQ](#7-faq)
8. [Best Practices](#8-best-practices)

---

## 1. Quick Start Guide

### 1.1 Five-Minute Workflow

**Goal**: De-identify 100 clinical notes for research

**Steps**:
1. **Login**: Navigate to https://[your-institution]/deidentify → Enter credentials → MFA code
2. **Upload**: Click "New Job" → Select "Upload CSV" → Choose file → Click "Upload" (2 minutes)
3. **Configure**: Select de-identification method (Removal, Replacement, Generalization) → Click "Start Job"
4. **Wait**: Batch processes automatically (1-2 minutes for 100 notes)
5. **Review**: Check flagged notes (if any) → Approve results
6. **Download**: Click "Download Results" → Select format (CSV, JSON, ZIP) → Export

**Total Time**: 5-10 minutes (vs. 50 hours manually at 30 min/note)

---

### 1.2 System Requirements

**Browser**: Chrome 90+, Firefox 88+, Edge 90+, Safari 14+ (latest versions recommended)

**Network**: Institutional network or VPN (de-identification service not internet-accessible)

**Permissions**: `research_coordinator` role (request from IT administrator)

**Training**: Complete 2-hour user training + 1-hour HIPAA compliance training

**MFA**: Multi-factor authentication enabled (TOTP app or SMS)

---

### 1.3 First-Time Setup

**1. Request Access**:
- Email IT administrator: [it-admin@institution.edu]
- Include: Name, email, department, PI name, IRB protocol number
- Wait for account creation notification (1-2 business days)

**2. Enable MFA**:
- Login to https://[your-institution]/deidentify
- Click "Enable MFA" → Scan QR code with authenticator app (Google Authenticator, Authy)
- Save backup codes in secure location

**3. Complete Training**:
- Watch 20-minute training video: [link to video]
- Read this user guide (15 pages)
- Practice on demo dataset (10 sample notes)
- Pass training quiz (80% required, unlimited attempts)

**4. Test System**:
- Upload 10-note sample dataset (provided in training)
- De-identify using "Replacement" method
- Review results and download
- Verify de-identified notes look correct

---

## 2. System Overview

### 2.1 What is De-identification?

**Definition**: Removal of Protected Health Information (PHI) from clinical notes to enable secondary use in research while protecting patient privacy.

**HIPAA Safe Harbor**: Requires removal of 18 identifiers (names, dates, locations, MRNs, SSNs, phone numbers, etc.)

**Why Automated?**:
- **Fast**: 100 notes in 2 minutes (vs. 50 hours manually)
- **Accurate**: 96% precision, 92% recall (validated on 1,000-note gold standard)
- **Consistent**: Same entity types detected every time
- **Auditable**: Every action logged for HIPAA compliance

---

### 2.2 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                   De-identification Workflow                │
└─────────────────────────────────────────────────────────────┘

1. UPLOAD                      2. DETECT PHI               3. REVIEW
   ┌─────────┐                    ┌─────────┐                ┌─────────┐
   │ Clinical│                    │ MedCAT  │                │ Flagged │
   │  Notes  │ ──────────────────>│  NLP    │───────────────>│  Notes  │
   │ (CSV)   │                    │  Model  │                │ (<0.8)  │
   └─────────┘                    └─────────┘                └─────────┘
                                       │                          │
                                       ▼                          ▼
                                  ┌─────────┐              ┌──────────┐
                                  │18 PHI   │              │ Manual   │
                                  │Types    │              │ Review   │
                                  │Detected │              │ (You!)   │
                                  └─────────┘              └──────────┘
                                       │                          │
                                       ▼                          ▼
4. DE-IDENTIFY                 5. VALIDATE                6. DOWNLOAD
   ┌─────────┐                    ┌─────────┐                ┌─────────┐
   │ Remove/ │                    │ Regex   │                │ De-id   │
   │ Replace/│<───────────────────│ Check   │<───────────────│ Notes   │
   │Generalize│                   │ (QA)    │                │ (CSV)   │
   └─────────┘                    └─────────┘                └─────────┘
```

**Key Components**:
- **MedCAT**: Medical NLP model (trained on 1,296 clinical notes)
- **Confidence Scores**: 0.0-1.0 (how sure the model is that text is PHI)
- **Manual Review**: You review notes with confidence <0.8 (safety net)
- **10% Sample Review**: Compliance officer reviews random 10% (quality check)

---

### 2.3 De-identification Methods

**Choose the method that best fits your research needs:**

#### Method 1: Removal (Highest Privacy, Lowest Utility)

**What it does**: Replaces PHI with type placeholder

**Example**:
```
Original: "Patient John Doe was seen on 01/15/2024 for chest pain."
Result:   "Patient [NAME] was seen on [DATE] for chest pain."
```

**Best for**:
- Maximum privacy required
- Minimal data utility needed
- Aggregate statistics (no individual patient tracking)

**Pros**: Highest privacy, no re-identification risk
**Cons**: Loses narrative flow, can't track patients across notes

---

#### Method 2: Replacement (Balanced Privacy and Utility)

**What it does**: Replaces PHI with consistent synthetic values within document

**Example**:
```
Original: "John Doe was seen on 01/15/2024. Mr. Doe reported..."
Result:   "James Smith was seen on 03/22/2020. Mr. Smith reported..."
```

**Mapping Rules**:
- **Names**: Synthetic names (gender-preserved, e.g., "John" → "James")
- **Dates**: Shifted by random offset (±180 days, year preserved unless ≥2020)
- **MRNs**: Synthetic IDs (format preserved, e.g., "MR12345" → "MR67890")
- **Locations**: Similar locations (state preserved, e.g., "Boston" → "Worcester")

**Best for**:
- NLP research (entity extraction, relationship extraction)
- Coreference resolution (track "John Doe" across sentences)
- Temporal analysis (date relationships preserved)

**Pros**: Preserves narrative flow, enables advanced NLP
**Cons**: Slightly lower privacy (synthetic mapping could theoretically be reversed if original notes leaked)

---

#### Method 3: Generalization (Partial Information)

**What it does**: Replaces PHI with generalized values

**Example**:
```
Original: "89-year-old male born on 03/15/1935"
Result:   "90+ year-old male born in 1935"
```

**Generalization Rules**:
- **Ages >89**: Replace with "90+" (HIPAA requirement)
- **Dates**: Year only (e.g., "01/15/2024" → "2024")
- **Locations**: State level only (e.g., "Boston, MA" → "Massachusetts")

**Best for**:
- Age-related research (geriatrics, longevity)
- Temporal studies (trends over time)
- Geographic studies (state-level analysis)

**Pros**: Preserves partial information, useful for temporal/age analysis
**Cons**: Lower privacy (year retained), not always HIPAA-compliant (depends on population size)

---

### 2.4 Confidence Scores

**What they mean**:
- **0.9-1.0**: Very confident (likely PHI, auto-de-identify)
- **0.8-0.9**: Confident (likely PHI, auto-de-identify)
- **0.7-0.8**: Somewhat confident (flag for review, suggest de-identification)
- **<0.7**: Low confidence (flag for review, manual decision required)

**How to use them**:
- Focus manual review on notes with entities <0.7 first (highest risk of missed PHI)
- Then review 0.7-0.8 (medium risk)
- Skip >0.8 unless flagged by colleague or compliance officer

**Example**:
```
Entity: "John Doe"
Type: NAME
Confidence: 0.95
Action: Auto-de-identify (no review needed)

Entity: "Normal"
Type: NAME (false positive)
Confidence: 0.65
Action: Manual review → User marks as "NOT PHI" → Whitelisted
```

---

## 3. Detailed Workflow

### 3.1 Creating a New Job

**Step 1: Navigate to De-identification System**
- Open browser → https://[your-institution]/deidentify
- Login with credentials → Enter MFA code
- Dashboard loads (shows recent jobs, system status)

**Step 2: Click "New Job"**
- Click "New Job" button (top-right corner)
- Modal opens with job configuration options

**Step 3: Upload Notes**

**Option A: CSV Upload** (Most Common)
- Click "Upload CSV" → Select file from computer
- CSV format required:
  ```csv
  note_id,patient_id,note_text,note_type,note_date
  N001,P12345,"Patient presents with...",progress_note,2024-01-15
  N002,P12345,"Discharge summary...",discharge_summary,2024-01-20
  ```
- Required columns: `note_id`, `note_text`
- Optional columns: `patient_id`, `note_type`, `note_date` (helpful for organizing results)
- File size limit: 100 MB (approx. 10,000 notes)

**Option B: Database Query** (Advanced)
- Click "Database Query" → Enter SQL query
- Example:
  ```sql
  SELECT note_id, patient_id, note_text, note_type, note_date
  FROM clinical_notes
  WHERE note_date >= '2020-01-01'
    AND note_type IN ('progress_note', 'discharge_summary')
  LIMIT 1000
  ```
- Query must return: `note_id`, `note_text` (minimum)
- Result limit: 10,000 rows (adjust LIMIT if needed)

**Option C: Manual Paste** (Small Jobs)
- Click "Manual Paste" → Paste text into text area
- Good for: 1-10 notes, testing, quick de-identification
- Click "Add Note" to add multiple notes

**Step 4: Select De-identification Method**
- **Removal**: Maximum privacy (placeholder like "[NAME]")
- **Replacement**: Balanced (synthetic mapping, preserves narrative)
- **Generalization**: Partial information (year-only dates, 90+ ages)

**Step 5: Configure Options** (Optional)
- **Confidence Threshold**: 0.7 (default), 0.6 (more aggressive), 0.8 (less aggressive)
- **Notify Email**: Enter email to receive notification when batch completes
- **Job Name**: Descriptive name (e.g., "AF-2024 Cardiology Study")
- **IRB Protocol**: IRB number for audit trail (optional but recommended)

**Step 6: Review and Submit**
- Review: Number of notes, method, options
- Click "Start Job" → Job queued for processing
- Modal closes → Redirected to job details page

---

### 3.2 Monitoring Job Progress

**Job Details Page**:
- **Status**: Pending → Processing → Review Required → Completed
- **Progress Bar**: Shows percentage complete (updates every 10 seconds)
- **Estimated Completion**: Time remaining (based on 100 notes/minute)
- **Entities Detected**: Count of PHI entities found
- **Flagged Notes**: Count of notes requiring manual review (<0.8 confidence)

**Example**:
```
Job: AF-2024 Cardiology Study (Job ID: job-abc123)
Status: Processing (45% complete)
Progress: 225 / 500 notes processed
Estimated Completion: 3 minutes remaining
Entities Detected: 1,234 PHI entities (NAME: 456, DATE: 389, MRN: 123, ...)
Flagged Notes: 18 notes require manual review
```

**Refresh**: Page auto-refreshes every 10 seconds (or click "Refresh" button)

---

### 3.3 Reviewing Flagged Notes

**When**: After job status changes to "Review Required"

**Step 1: Navigate to Review Page**
- Click "Review Flagged Notes" button on job details page
- Review page loads with list of flagged notes (sorted by confidence, lowest first)

**Step 2: Review Each Flagged Note**
- Click note to expand side-by-side comparison:
  - **Left**: Original note (PHI highlighted in yellow)
  - **Right**: De-identified note (placeholders/replacements in blue)
- Check each highlighted entity:
  - **Green checkmark**: Correct (PHI detected and de-identified)
  - **Red X**: Incorrect (false positive, not PHI)
  - **Yellow warning**: Uncertain (manual decision needed)

**Step 3: Manual Annotation** (If PHI Missed)
- If you see PHI that wasn't detected (not highlighted):
  - **Select text** with mouse (click and drag)
  - **Entity type dropdown** appears → Select type (NAME, DATE, MRN, etc.)
  - **Confidence slider** (optional) → Adjust confidence (default: 1.0 for manual annotations)
  - **Click "Save Annotation"** → Entity added to de-identification list
- Repeat for all missed PHI in the note

**Step 4: Approve or Reject**
- **Approve**: Click "Approve" button → Note marked as reviewed
- **Reject**: Click "Reject" button → Note excluded from results (if too messy to de-identify)

**Step 5: Move to Next Note**
- Click "Next Note" button → Repeat Step 2-4 for remaining flagged notes
- Progress bar shows: "Reviewed 12 / 18 notes"

**Step 6: Finalize Review**
- After reviewing all flagged notes, click "Finalize Review"
- Job status changes to "Completed"
- Download results button appears

---

## 4. Manual Annotation Tool

### 4.1 When to Use Manual Annotation

**Scenario 1: PHI Missed by Automated System**
- Example: "John Doe" detected, but "Dr. Smith" (physician name) missed
- Action: Select "Dr. Smith" → Choose "NAME" → Save

**Scenario 2: False Positive (Not PHI)**
- Example: "Normal" flagged as NAME (false positive)
- Action: Click "Not PHI" button → Entity removed from de-identification list

**Scenario 3: Uncertain Entity Type**
- Example: "MGH" (hospital name) - could be LOCATION or OTHER
- Action: Select "MGH" → Choose "LOCATION" → Save (institutional guidance: hospital names are LOCATION)

---

### 4.2 Text Selection

**How to Select**:
1. Click and hold at start of text
2. Drag to end of text
3. Release mouse button
4. Entity type dropdown appears

**Tips**:
- Select full entity (e.g., "John Doe", not just "John")
- Don't include punctuation (e.g., "John Doe", not "John Doe,")
- For multi-word entities, select entire phrase (e.g., "Massachusetts General Hospital")

**Keyboard Shortcuts** (After text selected):
- `N` = NAME
- `D` = DATE
- `L` = LOCATION
- `P` = PHONE
- `M` = MRN
- `S` = SSN
- `Esc` = Cancel selection

---

### 4.3 Entity Types (18 HIPAA Categories)

| Type | Examples | Keyboard Shortcut |
|------|----------|-------------------|
| **NAME** | John Doe, Dr. Smith, Jane Johnson | `N` |
| **DATE** | 01/15/2024, January 15, 2024 | `D` |
| **LOCATION** | Boston, MGH, 123 Main St | `L` |
| **AGE** | 89, 90, 95 (ages >89 only) | `A` |
| **PHONE** | 617-555-1234, (617) 555-1234 | `P` |
| **FAX** | 617-555-5678 | `F` |
| **EMAIL** | john.doe@example.com | `E` |
| **SSN** | 123-45-6789 | `S` |
| **MRN** | MR12345, 000-11-2222 | `M` |
| **ACCOUNT** | ACCT-98765 | `C` (account) |
| **LICENSE** | DL A1234567 | `I` (ID/license) |
| **VEHICLE** | MA 123ABC, VIN 1HGBH41JXMN109186 | `V` |
| **DEVICE** | Serial# 98765, UDI (01)00614141000036 | `X` (device) |
| **URL** | https://example.com, www.hospital.org | `U` |
| **IP** | 192.168.1.1, 2001:0db8::1 | `Y` (IP) |
| **BIOMETRIC** | Fingerprint, voice print, retinal scan | `B` |
| **PHOTO** | [PHOTO], full-face photo | `H` (photo) |
| **OTHER** | Other unique identifier | `O` |

**Tip**: Focus on most common types first (NAME, DATE, LOCATION, PHONE, MRN) - these account for 90% of PHI.

---

### 4.4 Confidence Slider

**Purpose**: Indicate how confident you are that the text is PHI

**Scale**: 0.0 (not PHI) to 1.0 (definitely PHI)

**Default**: 1.0 (manual annotations are high-confidence)

**When to adjust**:
- **0.9-1.0**: Definite PHI (e.g., "Social Security number: 123-45-6789")
- **0.7-0.9**: Probably PHI (e.g., "Dr. Smith" in physician signature)
- **0.5-0.7**: Uncertain (e.g., "Normal" could be name or medical term)
- **<0.5**: Probably not PHI (don't annotate, click "Not PHI" instead)

**Impact**: Low-confidence manual annotations (<0.7) will be flagged for compliance officer review.

---

## 5. Downloading Results

### 5.1 Download Options

**Format Options**:
1. **CSV**: De-identified notes in CSV format (same structure as input)
2. **JSON**: De-identified notes in JSON format (includes metadata)
3. **ZIP**: All files zipped (CSV + audit log + summary report)

**Download Steps**:
1. Navigate to job details page (Jobs → Select job)
2. Verify status: "Completed"
3. Click "Download Results" button
4. Select format (CSV, JSON, ZIP)
5. File downloads to browser's download folder

---

### 5.2 CSV Format

**Structure**:
```csv
note_id,patient_id,note_text,note_text_deidentified,entities_removed,method,confidence_score
N001,P12345,"Patient John Doe...","Patient [NAME]...",3,removal,0.96
N002,P12345,"Discharge summary...","Discharge summary...",5,replacement,0.94
```

**Columns**:
- `note_id`: Original note ID (preserved)
- `patient_id`: Original patient ID (preserved, but use with caution)
- `note_text`: **ORIGINAL NOTE** (includes PHI, handle with care)
- `note_text_deidentified`: **DE-IDENTIFIED NOTE** (safe for research)
- `entities_removed`: Count of PHI entities removed
- `method`: De-identification method used (removal, replacement, generalization)
- `confidence_score`: Average confidence of detected entities (0.0-1.0)

**Important**: CSV includes both original and de-identified notes. Delete `note_text` column before sharing de-identified data.

---

### 5.3 JSON Format

**Structure**:
```json
{
  "job_id": "job-abc123",
  "notes": [
    {
      "note_id": "N001",
      "patient_id": "P12345",
      "note_text_deidentified": "Patient [NAME] was seen on [DATE]...",
      "entities": [
        {
          "text": "John Doe",
          "type": "NAME",
          "start": 8,
          "end": 16,
          "confidence": 0.95,
          "replacement": "[NAME]"
        },
        {
          "text": "01/15/2024",
          "type": "DATE",
          "start": 30,
          "end": 40,
          "confidence": 0.97,
          "replacement": "[DATE]"
        }
      ],
      "method": "removal",
      "confidence_score": 0.96,
      "review_required": false,
      "manually_annotated": 0
    }
  ],
  "metadata": {
    "total_notes": 500,
    "total_entities_removed": 1234,
    "entity_type_distribution": {
      "NAME": 456,
      "DATE": 389,
      "MRN": 123,
      "PHONE": 89,
      "LOCATION": 67,
      ...
    },
    "processing_time_ms": 135000,
    "created_at": "2025-11-22T14:30:00Z",
    "completed_at": "2025-11-22T14:32:15Z"
  }
}
```

**Best for**: Programmatic analysis, NLP research, importing into other tools

---

### 5.4 Audit Log Export

**Purpose**: HIPAA-compliant audit trail for IRB reporting

**How to Export**:
1. Navigate to job details page
2. Click "Export Audit Log" button
3. Select format (CSV or JSON)
4. File downloads with audit events

**CSV Format**:
```csv
user_id,timestamp,action,resource_id,entities_detected,entities_removed,method,processing_time_ms,result
user-123,2025-11-22T14:30:00Z,NOTE_DEIDENTIFIED,note-001,3,3,removal,1523,success
user-123,2025-11-22T14:30:02Z,NOTE_DEIDENTIFIED,note-002,5,5,removal,1687,success
```

**Uses**:
- IRB reporting (demonstrate audit trail)
- Compliance review (show all actions logged)
- Performance analysis (identify slow notes)

---

## 6. Troubleshooting

### 6.1 Common Errors

#### Error: "Upload Failed: Invalid CSV Format"

**Cause**: CSV file missing required columns (`note_id`, `note_text`)

**Solution**:
1. Open CSV in Excel/LibreOffice
2. Verify columns: `note_id` (column A), `note_text` (column B)
3. Add missing columns if needed
4. Save as CSV (UTF-8 encoding)
5. Re-upload

---

#### Error: "Job Failed: Processing Timeout"

**Cause**: Notes too large (>1 MB each) or too many notes (>10,000)

**Solution**:
1. Split CSV into smaller files (<1,000 notes each)
2. Upload separately (Job 1: notes 1-1000, Job 2: notes 1001-2000, etc.)
3. Merge results after download

---

#### Error: "Access Denied: Insufficient Permissions"

**Cause**: User lacks `research_coordinator` role

**Solution**:
1. Contact IT administrator: [it-admin@institution.edu]
2. Request `research_coordinator` role
3. Provide IRB protocol number and PI approval
4. Wait for role assignment (1-2 business days)

---

#### Error: "MFA Code Invalid"

**Cause**: Time-based code expired (30-second window) or phone time offset

**Solution**:
1. Wait for next code (30 seconds)
2. Try again immediately
3. If persistent: Check phone time sync (Settings → Date & Time → Auto)
4. If still failing: Contact IT for backup codes

---

### 6.2 Performance Issues

#### Slow Upload (>5 minutes for 1,000 notes)

**Possible Causes**:
- Large file size (>100 MB)
- Network congestion
- Server load (many concurrent jobs)

**Solutions**:
- Compress CSV (gzip) before upload
- Upload during off-peak hours (evenings, weekends)
- Split into smaller batches

---

#### Slow Processing (>10 minutes for 1,000 notes)

**Expected**: 100 notes/minute (10 minutes for 1,000 notes is normal)

**If slower**:
- Check system status page (https://[your-institution]/deidentify/status)
- If server load >80%, wait for lower demand
- If persistent, contact IT support

---

## 7. FAQ

### 7.1 General Questions

**Q: How long does de-identification take?**
A: Approximately 100 notes/minute. For 500 notes, expect 5-10 minutes (including manual review time).

**Q: Can I cancel a job mid-processing?**
A: Yes. Navigate to job details page → Click "Cancel Job". Partial results (already processed notes) can be downloaded.

**Q: How long are results stored?**
A: 30 days. After 30 days, jobs are deleted automatically. Download results promptly.

**Q: Can I re-process the same notes with a different method?**
A: Yes. Upload the same CSV again and select a different method (e.g., Replacement instead of Removal).

---

### 7.2 Privacy and Security

**Q: Is the original note stored permanently?**
A: Original notes are stored in encrypted Elasticsearch index for 30 days (for re-processing if needed). After 30 days, original notes are deleted permanently.

**Q: Can I share de-identified notes with external collaborators?**
A: Yes, if IRB approves. De-identified data (HIPAA Safe Harbor method) is not considered PHI. However, verify with your institution's data sharing policy.

**Q: What if PHI is found after download?**
A: Report immediately to compliance officer. Do NOT share data until PHI is removed. Compliance officer will investigate and re-process notes.

**Q: Are my actions logged?**
A: Yes. All actions (upload, review, download) are logged for HIPAA compliance (8-year retention). Logs contain user ID, timestamp, action, but NO PHI.

---

### 7.3 Technical Questions

**Q: What format should my CSV be in?**
A: UTF-8 encoding, comma-separated, headers in first row. Minimum columns: `note_id`, `note_text`. Optional: `patient_id`, `note_type`, `note_date`.

**Q: Can I upload DOCX or PDF files?**
A: Not directly. Convert to plain text first (copy-paste into CSV `note_text` column). For bulk conversion, use tools like Pandoc or Adobe Acrobat.

**Q: What is the maximum file size?**
A: 100 MB per upload (approximately 10,000 notes at 10 KB each). For larger batches, split into multiple files.

**Q: Can I use the API instead of the web interface?**
A: Yes. See API documentation: https://[your-institution]/deidentify/api/docs

---

## 8. Best Practices

### 8.1 Before Upload

**1. Verify IRB Approval**
- Ensure IRB protocol covers use of de-identified clinical notes
- Document IRB number in job configuration (for audit trail)

**2. Clean Data**
- Remove duplicates (same note uploaded twice)
- Verify note IDs are unique
- Check for encoding issues (non-UTF-8 characters)

**3. Sample Test**
- Upload 10 sample notes first
- Verify de-identification quality
- Adjust confidence threshold if needed (default: 0.7)

---

### 8.2 During Review

**1. Prioritize Low-Confidence Notes**
- Review notes with entities <0.7 first (highest risk)
- Then review 0.7-0.8 (medium risk)
- Skip >0.8 unless compliance officer flags

**2. Document Decisions**
- If you mark entity as "Not PHI", add comment explaining why
- Example: "Normal" → "Not PHI (medical term, not patient name)"

**3. Don't Over-Annotate**
- Only annotate PHI that was missed by automated system
- Don't re-annotate entities already detected (wastes time)

---

### 8.3 After Download

**1. Verify Results**
- Spot-check 10-20 random notes
- Search for common PHI patterns (###-##-####, (###) ###-####)
- If PHI found, report to compliance officer immediately

**2. Delete Original Column**
- If using CSV, delete `note_text` column (original notes)
- Keep only `note_text_deidentified` column (safe for research)

**3. Store Securely**
- Even de-identified data should be stored securely (encrypted drive)
- Limit access to research team members only
- Delete data after research completes (per IRB protocol)

---

### 8.4 Continuous Improvement

**1. Provide Feedback**
- If you find edge cases (missed PHI types), report to IT
- Example: "Physician signatures often missed"
- Feedback improves model for future jobs

**2. Review Audit Reports**
- Monthly: Review your job history (are you using the system correctly?)
- Quarterly: Review compliance officer's sample review (were any PHI found?)

**3. Stay Updated**
- Read release notes when system is updated
- Attend annual refresher training
- Re-take training quiz if accuracy metrics drop

---

## Appendix A: Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Create new job | `Ctrl + N` |
| Upload CSV | `Ctrl + U` |
| Start job | `Ctrl + Enter` |
| Review next note | `→` (right arrow) |
| Review previous note | `←` (left arrow) |
| Approve note | `Ctrl + A` |
| Reject note | `Ctrl + R` |
| **Entity Type Shortcuts** (after text selection) | |
| NAME | `N` |
| DATE | `D` |
| LOCATION | `L` |
| PHONE | `P` |
| MRN | `M` |
| SSN | `S` |
| Cancel selection | `Esc` |

---

## Appendix B: Entity Type Reference

See Section 4.3 for full table of 18 HIPAA entity types with examples.

---

## Appendix C: Contact Information

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

**User Guide Version**: 1.0.0
**Last Updated**: 2025-11-22
**Next Review**: 2026-11-22
