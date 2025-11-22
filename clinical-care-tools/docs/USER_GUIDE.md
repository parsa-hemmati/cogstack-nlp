# Clinical User Guide

Complete user guide for clinicians and researchers using Clinical Care Tools.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Login & Authentication](#login--authentication)
3. [Patient Management](#patient-management)
4. [Document Upload & Processing](#document-upload--processing)
5. [Entity Extraction & Viewing](#entity-extraction--viewing)
6. [Timeline Visualization](#timeline-visualization)
7. [Patient Search & Discovery](#patient-search--discovery)
8. [Data Export](#data-export)
9. [Cohort Building](#cohort-building)
10. [Best Practices](#best-practices)
11. [FAQ](#faq)

## Getting Started

### System Access

Clinical Care Tools is a web-based application. You can access it from:

**URL**: `https://clinical.healthcare.org` (or your organization's URL)

**Browser Support**:
- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Permissions & Roles

Your access level depends on your role:

| Action | Clinician | Researcher | Admin |
|--------|-----------|------------|-------|
| View patients | ✓ | ✓ | ✓ |
| Search for patients | ✓ | ✓ | ✓ |
| Upload documents | ✓ | ✗ | ✓ |
| Export data | ✓ | Limited | ✓ |
| Manage users | ✗ | ✗ | ✓ |
| View audit logs | Limited | ✗ | ✓ |

## Login & Authentication

### First Login

1. Navigate to: `https://clinical.healthcare.org`
2. Enter your credentials:
   - **Username**: [provided by administrator]
   - **Password**: [provided by administrator]
3. Click "Sign In"

**Initial Password**:
Your administrator will provide an initial password. You should change this on first login:
1. Click your profile icon (top right)
2. Select "Settings"
3. Click "Change Password"
4. Enter new password (minimum 12 characters)

### Password Requirements

- Minimum 12 characters
- Mix of:
  - Uppercase letters (A-Z)
  - Lowercase letters (a-z)
  - Numbers (0-9)
  - Special characters (!@#$%^&*)

### Session Management

- **Session Duration**: 8 hours
- **Auto-Logout**: After 1 hour of inactivity
- **Multiple Sessions**: Not allowed (new login invalidates previous)

### Logout

1. Click your profile icon (top right)
2. Select "Logout"
3. Confirm logout

**Important**: Always logout when finished, especially on shared computers.

## Patient Management

### View Patient List

1. From the left menu, select **"Patients"**
2. The patient list displays:
   - Patient Name
   - Medical Record Number (MRN)
   - Date of Birth
   - Number of documents
   - Last update date

3. **Sorting**: Click column headers to sort
4. **Pagination**: Use page controls at the bottom

### View Patient Details

1. Click on a patient name in the list
2. Patient details panel opens showing:
   - Full demographics
   - Date of birth & age
   - Gender
   - Document count
   - Total extracted medical concepts
   - Created/updated timestamps

### Add New Patient

Only clinicians with appropriate permissions can add patients.

1. Click **"Add Patient"** button (top right)
2. Enter patient information:
   - **MRN** (Medical Record Number) - Required, unique
   - **First Name** - Required
   - **Last Name** - Required
   - **Date of Birth** - Required (YYYY-MM-DD format)
   - **Gender** - Required (M/F/Other)
3. Click **"Save"** button

The patient record is created and you can begin uploading documents.

## Document Upload & Processing

### Upload Documents

Documents contain the clinical information that is processed for medical concept extraction.

**Supported Formats**:
- RTF (Rich Text Format)
- PDF (Portable Document Format)
- TXT (Plain Text)

**File Size Limits**:
- Maximum 50 MB per document
- Maximum 200 pages

**To Upload a Document**:

1. Navigate to patient record
2. Click **"Upload Document"** button
3. A dialog appears:
   - **Select File**: Browse and select document
   - **Document Type** (optional):
     - Clinical Note
     - Lab Report
     - Discharge Summary
     - Imaging Report
     - Medication List
     - Other
4. Click **"Upload"**

**Processing**:
- Documents are processed automatically
- Extract time: 10-30 seconds (depending on length)
- Progress bar shows extraction status
- You'll be notified when complete

### View Uploaded Documents

1. In patient record, scroll to **"Documents"** section
2. List shows:
   - Document filename
   - Upload date
   - Document type
   - Number of extracted entities
   - Processing status (Pending, Processing, Complete, Error)

3. Click document to view details and extracted entities

## Entity Extraction & Viewing

### Understanding Extracted Entities

Medical entities are automatically extracted from documents. Each entity includes:

**Entity Information**:
- **Concept Name**: Medical term (e.g., "Type 2 Diabetes Mellitus")
- **SNOMED Code**: Standard medical code (e.g., "C0011847")
- **Confidence Score**: 0-100% (how confident the extraction is)
- **Position**: Where in the document it appears

**Meta-Annotations** (Additional Context):

These provide important clinical context:

1. **Negation Status**:
   - **Affirmed**: The condition is present
   - **Negated**: The condition is NOT present
   - Example: "Patient denies chest pain" = Negated chest pain

2. **Temporality** (When):
   - **Recent**: Recent past events
   - **Current**: Currently occurring
   - **Historical**: Past events (months/years ago)

3. **Experiencer** (Who):
   - **Patient**: Applies to the patient
   - **Family**: Applies to family member
   - **Other**: Applies to someone else
   - Example: "Father has hypertension" = Family experiencer

4. **Certainty** (How sure):
   - **Definite**: Confirmed/certain
   - **Probable**: Likely/probable
   - **Possible**: Possible/uncertain
   - Example: "Possible diabetes" = Possible certainty

### View Entities in Document

1. Click on a document
2. **Document View** shows:
   - Full document text (if PDF/RTF readable)
   - Extracted entities highlighted in text
   - Entity list with details

3. **Entity Details** include:
   - Medical concept name
   - Confidence score (as percentage)
   - Meta-annotations (Negation, Temporality, Experiencer, Certainty)
   - Exact text location in document

### Filter Entities

You can filter extracted entities by various criteria:

1. In document view, use the **Filter** panel
2. Available filters:
   - **Negation Status**: Show only Affirmed/Negated/All
   - **Temporality**: Show only Current/Recent/Historical/All
   - **Experiencer**: Show only Patient/Family/Other/All
   - **Certainty**: Show only Definite/Probable/Possible/All
   - **Confidence Score**: Minimum confidence threshold

3. Apply filters to focus on relevant entities

**Common Use Case**:
- Filter for: Affirmed + Current + Patient
- Result: Only conditions currently affecting the patient
- This excludes: Family history, past conditions, possible/uncertain conditions

## Timeline Visualization

The timeline view shows clinical events chronologically.

### Access Timeline

1. In patient record, click **"Timeline"** tab
2. Timeline displays events chronologically (oldest to newest)

### Timeline Display

**Event Types**:
- Document uploads
- Medical concept mentions
- Medication changes
- Lab results

**Event Information**:
- Date/time of event
- Type of event
- Associated concepts/values
- Confidence score (for extracted concepts)

### Filtering Timeline

1. Click **"Filters"** button
2. Select date range:
   - Preset ranges: Last 30 days, Last 6 months, Last year, All time
   - Custom date range
3. Select entity types to display
4. Apply filters

### Zoom & Pan

- **Zoom**: Use scroll wheel or pinch gesture
- **Pan**: Click and drag to navigate
- **Reset**: Click "Reset View" button

## Patient Search & Discovery

### Simple Search

Find patients with specific medical conditions:

1. From left menu, click **"Search"**
2. Enter medical concept:
   - Example: "Type 2 Diabetes"
   - Example: "Hypertension"
   - Example: "Atrial Fibrillation"
3. Click **"Search"** button

**Results** show:
- Patient name
- MRN
- Match confidence score
- Number of matching documents
- Date of most recent mention

### Advanced Filtering

Refine search results with clinical filters:

**Filter Options**:
- **Negation**: Only Affirmed (present) conditions
  - Use to exclude patients with family history or negations
- **Temporality**: Only Current conditions
  - Use to find patients with active conditions
- **Experiencer**: Only Patient
  - Use to exclude family history
- **Certainty**: Only Definite
  - Use to exclude probable/possible conditions
- **Confidence Score**: Minimum 80%
  - Use to focus on high-confidence extractions

**Example Searches**:

1. **Active Type 2 Diabetes Patients**:
   - Concept: "Type 2 Diabetes"
   - Negation: Affirmed (present)
   - Temporality: Current
   - Confidence: >80%

2. **Patients with Family History of Hypertension**:
   - Concept: "Hypertension"
   - Experiencer: Family
   - Negation: Affirmed

3. **High-Risk Diabetic Patients**:
   - Search 1: Type 2 Diabetes (Current, Patient)
   - Search 2: Chronic Kidney Disease (Current, Patient)
   - Combine results

### Export Search Results

1. After search, click **"Export"** button
2. Choose format:
   - CSV (opens in Excel/Sheets)
   - JSON (structured data)
   - FHIR (for EHR systems)

3. Downloaded file contains:
   - Patient demographics
   - Matching concepts
   - Confidence scores
   - Document references

## Data Export

### Export Patient Data

1. In patient record, click **"Export"** button
2. Choose data to include:
   - [ ] Demographics
   - [ ] Documents (original files)
   - [ ] Extracted Entities
   - [ ] Timeline
   - [ ] Audit Log (admin only)
3. Choose format:
   - **CSV**: Spreadsheet compatible
   - **JSON**: Structured data
   - **FHIR**: EHR system compatible
4. Click **"Export"**

### Export Search Results

After a search, you can export all results:

1. Click **"Export Results"** button
2. Choose format and data
3. File downloads to your computer

### Export Restrictions

- You can only export patients you have access to
- Researcher role has limited export options
- Audit logs are exported only to admins
- All exports are logged for compliance

## Cohort Building

A cohort is a group of patients meeting specific criteria.

### Create New Cohort

1. Click **"Cohorts"** in left menu
2. Click **"Create Cohort"**
3. Enter cohort name and description
4. Define inclusion criteria:
   - Medical concepts (e.g., "Type 2 Diabetes")
   - Labs (e.g., "HbA1c > 8.0%")
   - Demographics (e.g., "Age > 65")
   - Temporal (e.g., "Diagnosis in last 6 months")

### Example Cohorts

**Example 1: Diabetic Patients Needing Medication Review**
```
Name: Diabetes Medication Review
Criteria:
- Diagnosis: Type 2 Diabetes (Affirmed, Current)
- Age: > 60 years
- Duration: Diagnosed > 5 years
- Last Visit: < 3 months ago
Result: 234 patients
```

**Example 2: High-Risk Cardiac Patients**
```
Name: High-Risk Cardiac Cohort
Criteria:
- Include: Atrial Fibrillation OR Heart Failure
- Exclude: Anticoagulation therapy
- Age: > 70 years
Result: 47 patients
```

### Manage Cohorts

1. In **"Cohorts"** menu, view your cohorts
2. For each cohort, you can:
   - **View**: See list of patients in cohort
   - **Edit**: Modify inclusion/exclusion criteria
   - **Export**: Download patient list
   - **Delete**: Remove cohort

## Best Practices

### Searching

1. **Use specific concepts**: "Type 2 Diabetes" vs "Diabetes"
2. **Filter appropriately**: Exclude family history, negations
3. **Review high-confidence matches**: >80% confidence
4. **Spot-check results**: Verify a few manually before trusting

### Interpreting Meta-Annotations

1. **For Clinical Decisions**:
   - Only use: Affirmed + Current + Patient + Definite
   - Skip: Negated, Historical, Family, Possible

2. **For Research**:
   - Be transparent about filters used
   - Document inclusion/exclusion criteria
   - Report confidence scores in results

### Document Upload

1. **Use consistent naming**: "Patient-MRN-Date-Type"
2. **Clean documents**: Remove headers/footers if possible
3. **OCR PDFs**: If scanned, ensure text is readable
4. **Review extractions**: Check a few entities manually

### Data Export

1. **Check privacy**: Verify no protected health information (PHI) is exposed
2. **Use secure transfer**: Use SFTP or encrypted email
3. **Document lineage**: Note date/criteria of export
4. **De-identify if needed**: Remove identifying information for research

## FAQ

### General

**Q: What is Clinical Care Tools?**
A: A web-based platform for extracting medical concepts from clinical documents and searching for patients by medical conditions.

**Q: What data does it contain?**
A: Patient demographics, clinical documents (RTF/PDF/TXT), and extracted medical concepts (diagnoses, medications, procedures, labs).

**Q: Who maintains the data?**
A: Your organization's clinical informaticists and IT team. Ask them for data governance questions.

### Authentication

**Q: I forgot my password. What do I do?**
A: Click "Forgot Password" on login screen. If that doesn't work, contact your administrator.

**Q: My session expired. Why?**
A: Sessions expire after 8 hours or 1 hour of inactivity. Login again.

**Q: Can I use Clinical Care Tools on my phone?**
A: The application is not optimized for mobile. Use a desktop/laptop browser.

### Searching & Data

**Q: Why didn't my search find a patient?**
A: Possible reasons:
- Patient hasn't been added to the system
- Documents haven't been uploaded
- Concept name doesn't match exactly (try synonyms)
- Filters are too restrictive (try removing some)
- Condition is documented as negated or family history

**Q: How confident should the extraction scores be?**
A:
- \>90%: Very high confidence, safe to use
- 80-90%: Good confidence, review a few examples
- 70-80%: Moderate confidence, verify manually before using
- <70%: Low confidence, probably errors

**Q: Can I manually correct extracted entities?**
A: No, extractions are read-only. Contact your administrator if you find errors.

**Q: How long does document processing take?**
A: Usually 10-30 seconds. Longer documents may take up to 2 minutes.

### Export & Compliance

**Q: Can I export patient data?**
A: Depends on your role. Clinicians can export their own patient's data. Researchers may have restrictions. Ask your administrator.

**Q: Is data export secure?**
A: Yes, all exports are encrypted in transit (HTTPS/TLS) and logged for audit.

**Q: How long is data retained?**
A: Clinical data is retained for 7 years (per NHS guidance). Audit logs are retained for 7 years. Ask your organization's data retention policy.

**Q: Is my usage logged?**
A: Yes, all access to patient data (view, search, export) is logged for compliance and audit purposes.

### Technical

**Q: Which browser should I use?**
A: Chrome, Firefox, Safari, or Edge (recent versions). Contact your IT if you have issues.

**Q: The page won't load. What's wrong?**
A:
1. Check your internet connection
2. Clear browser cache (Ctrl+Shift+Delete)
3. Try a different browser
4. Contact your IT support

**Q: Why am I seeing "Authorization denied"?**
A: Your role doesn't have permission for that action. Contact your administrator for access.

**Q: The extracted text is wrong. Is this a bug?**
A: The NLP extraction is not 100% accurate. Always review high-stakes findings. Report systematic errors to your administrator.

### Data Quality

**Q: How accurate is the medical concept extraction?**
A: Typical accuracy:
- Common concepts (diabetes, hypertension): 85-95%
- Rare/specific concepts: 70-85%
- Negations and context: 80-90%

Always review important findings manually.

**Q: What causes extraction errors?**
A: Common issues:
- Handwritten/scanned documents: Harder to process
- Abbreviations: May not be recognized
- Misspellings: Reduces matching
- Negations: May miss "patient denies X"
- Dual mentions: May find both condition and "ruled out"

**Q: Can I train the system to improve accuracy?**
A: No, but errors can be reported to your administrator for feedback to the MedCAT team.

### Support

**Q: Who can I contact for help?**
A:
- Technical issues: Your IT support team
- Feature requests: Your clinical informatics team
- Bug reports: Clinical Care Tools issue tracker
- Usage questions: This user guide or your supervisor

**Q: Is there training available?**
A: Your organization should provide orientation. Ask your supervisor or training department.

**Q: I found a bug. Who do I report it to?**
A: Report to your clinical informatics team or IT support with:
- Description of the problem
- Steps to reproduce
- Your username (will be in logs anyway)
- Browser and operating system

---

**Last Updated**: 2025-01-08
**Version**: 1.0.0
**Contact**: clinical-care-tools-support@[organization].org
