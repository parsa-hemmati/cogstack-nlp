# Patient Timeline - User Guide

**Version**: 1.0.0  
**Last Updated**: 2025-11-22  
**Audience**: Clinicians, Researchers, Care Coordinators

---

## Overview

The Patient Timeline provides a chronological visualization of a patient's medical history, integrating:
- Clinical documents (discharge summaries, progress notes, lab results)
- Medical concepts (diagnoses, medications, procedures)
- Temporal relationships (when conditions began, treatments started)
- Meta-annotations (affirmed vs. negated, patient vs. family history)

This tool helps clinicians:
- **Identify care gaps** (e.g., missing follow-ups, untreated conditions)
- **Review longitudinal trends** (e.g., disease progression over years)
- **Prepare for appointments** (quick overview of patient history)
- **Support clinical decisions** (evidence-based on patient's actual record)

---

## Accessing the Timeline

### From Patient Search

1. Navigate to **Patient Search** in the main menu
2. Search for patient by NHS number, name, or MRN
3. Click **Timeline** button in the patient row

### From Patient Profile

1. Open patient profile page
2. Click **Timeline** tab in the navigation bar

### Direct Link

Visit: `https://your-app.com/patients/{patient_id}/timeline`

---

## Understanding the Timeline View

### Timeline Components

```
┌─────────────────────────────────────────────────────────────┐
│ Patient Header                                              │
│ NHS: 1234567890 | DOB: 1950-05-15 | Age: 74               │
├─────────────────────────────────────────────────────────────┤
│ Filters (Sidebar)      │ Timeline Visualization             │
│                        │ ┌──────────────────────────────┐  │
│ □ Date Range          │ │ 2019 | 2020 | 2021 | 2022   │  │
│ □ Concepts            │ │  •     •      ••     •••     │  │
│ □ Meta-Annotations    │ │  │     │      ││     │││     │  │
│ □ Document Types      │ │  ▼     ▼      ▼▼     ▼▼▼     │  │
│                        │ └──────────────────────────────┘  │
│ Saved Presets          │ Concept Frequency Chart          │
│ ★ My Default Filter   │ ┌──────────────────────────────┐  │
│   Diabetes Patients    │ │ █ Diabetes (15)              │  │
│   Recent Visits        │ │ ▆ Hypertension (12)          │  │
│                        │ │ ▄ Atrial Fib (8)             │  │
│                        │ └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Timeline Axis

- **Horizontal axis**: Time (from earliest to most recent document)
- **Vertical position**: Document types (clinical notes, lab results, etc.)
- **Markers**: 
  - **Circles**: Clinical concepts (conditions, symptoms)
  - **Squares**: Documents
  - **Size**: Marker size indicates number of mentions
  - **Color**: Concept type (condition=red, medication=blue, procedure=green)

### Event Markers

- **Filled circle**: First mention of a concept
- **Hollow circle**: Recurring mention
- **Hover**: Displays concept name, date, confidence score
- **Click**: Opens detailed view with full context

---

## Using Filters

### Date Range Filter

**Use case**: Review recent activity (e.g., last 6 months)

1. Click **Date Range** in filter sidebar
2. Select **Start Date** (e.g., 2024-01-01)
3. Select **End Date** (e.g., 2024-06-30)
4. Click **Apply Filters**

**Result**: Timeline shows only events within the date range

### Concept Filter

**Use case**: Find all mentions of a specific condition

1. Click **Concepts** in filter sidebar
2. Type concept name in search box (e.g., "diabetes")
3. Select from autocomplete suggestions
4. Click **Apply Filters**

**Result**: Timeline highlights only selected concept(s)

**Pro tip**: Select multiple concepts to compare (e.g., "diabetes" + "hypertension")

### Meta-Annotation Filters

**Use case**: Exclude family history, negated mentions, hypotheticals

| Filter | Options | Example Use Case |
|--------|---------|------------------|
| **Negation** | Affirmed, Negated | Exclude "Patient denies chest pain" |
| **Experiencer** | Patient, Family, Other | Exclude "Father had diabetes" |
| **Temporality** | Current, Recent, Past, Future, Hypothetical | Focus on active conditions only |
| **Certainty** | High, Medium, Low | Filter low-confidence mentions |

**Example**:
```
Negation: Affirmed
Experiencer: Patient
Temporality: Current, Recent
```

**Result**: Shows only affirmed, current patient conditions (excludes family history, negated mentions, past conditions)

### Document Type Filter

**Use case**: View only discharge summaries

1. Click **Document Types** in filter sidebar
2. Select types: `discharge_summary`, `clinical_note`, `lab_results`, etc.
3. Click **Apply Filters**

---

## Saved Filter Presets

### Creating a Preset

1. Apply desired filters (date range, concepts, meta-annotations)
2. Click **Save Preset** button
3. Enter preset name (e.g., "Diabetes Follow-up")
4. Click **Save**

### Loading a Preset

1. Click **Presets** dropdown
2. Select preset from list
3. Filters auto-apply

### Setting a Default Preset

1. Click star icon next to preset name
2. Preset auto-loads when timeline opens

### Example Presets

| Preset Name | Filters | Use Case |
|-------------|---------|----------|
| **Recent Activity** | Date: Last 6 months | Quick review before appointment |
| **Diabetes Management** | Concept: Diabetes, HbA1c<br>Meta: Affirmed, Current | Diabetes care gap analysis |
| **Cardiovascular Risk** | Concepts: Hypertension, Diabetes, Smoking, Obesity<br>Meta: Affirmed, Patient | Risk factor identification |
| **Discharge Summaries** | Document Type: discharge_summary | Review major events only |

---

## Navigating the Timeline

### Zoom & Pan

| Action | How To | Use Case |
|--------|--------|----------|
| **Zoom In** | Click `+` button or press `+` key | Focus on specific time period |
| **Zoom Out** | Click `-` button or press `-` key | See full history at once |
| **Reset Zoom** | Click reset button or press `0` key | Return to default view |
| **Pan** | Click and drag timeline | Move left/right through time |

### Keyboard Shortcuts

- **Tab**: Navigate between elements
- **Arrow Keys**: Navigate between event markers
- **Enter**: Open event detail
- **Escape**: Close modal
- **+**: Zoom in
- **-**: Zoom out
- **0**: Reset zoom

---

## Viewing Event Details

### Opening Event Detail

1. **Hover** over concept marker to see quick info
2. **Click** marker to open full detail modal

### Event Detail Information

**Basic Info**:
- Concept name (e.g., "Diabetes Mellitus Type 2")
- SNOMED CT code (CUI)
- Date of mention
- Document source

**Meta-Annotations**:
- Negation: Affirmed / Negated
- Experiencer: Patient / Family / Other
- Temporality: Current / Recent / Past / Future / Hypothetical
- Certainty: High / Medium / Low

**Context**:
- Sentence snippet with concept highlighted
- Full sentence (click "Show More")
- Document preview (click "View Document")

**Confidence**:
- NLP confidence score (0-1)
- Visual indicator (green=high, yellow=medium, red=low)

---

## Exporting Timeline Data

### Export Formats

| Format | Contents | Use Case |
|--------|----------|----------|
| **PDF** | Timeline visualization + event list | Sharing with patient or external provider |
| **FHIR R4** | FHIR Observations + Conditions | EHR integration, research export |
| **JSON** | Raw timeline data | Custom analysis, data science |

### Exporting Steps

1. Click **Export** button in top-right
2. Select format (PDF, FHIR, JSON)
3. Choose options:
   - Include PHI: Yes/No (default: No)
   - Date range: All/Current filter
4. Click **Export**
5. Download file

**Note**: All exports are audit-logged for HIPAA compliance

---

## Common Workflows

### 1. Pre-Appointment Review

**Goal**: Quick overview of patient history before appointment

**Steps**:
1. Open patient timeline
2. Apply **Recent Activity** preset (last 6 months)
3. Review major events (hospitalizations, new diagnoses)
4. Export PDF for appointment notes

**Time**: 2-3 minutes

### 2. Care Gap Analysis

**Goal**: Identify missing preventive care or treatment gaps

**Steps**:
1. Open patient timeline
2. Apply concept filters for target conditions (e.g., Diabetes, Hypertension)
3. Apply meta-annotation filters (Affirmed, Patient, Current)
4. Review timeline for:
   - Missing follow-up appointments
   - Untreated conditions
   - Medication adherence gaps
5. Document gaps in care plan

**Time**: 5-10 minutes

### 3. Medication Reconciliation

**Goal**: Review all medications patient is taking

**Steps**:
1. Open patient timeline
2. Apply **Document Type** filter: `discharge_summary`, `medication_list`
3. Apply **Concept Type** filter: `medication`
4. Apply **Temporality** filter: `Current`
5. Compare medications across documents
6. Identify discrepancies

**Time**: 5-10 minutes

### 4. Research Cohort Review

**Goal**: Review multiple patients for research study eligibility

**Steps**:
1. Create preset with inclusion criteria
   - Example: Diabetes + Hypertension, Affirmed, Age 50+
2. Apply preset to each patient
3. Review timeline to confirm eligibility
4. Export FHIR data for analysis

**Time**: 3-5 minutes per patient

---

## Troubleshooting

### Timeline Not Loading

**Symptoms**: Blank timeline, "Loading..." message persists

**Causes**:
- Patient has no documents in system
- Network connectivity issues
- Invalid patient ID

**Solutions**:
1. Refresh page (F5)
2. Verify patient has documents in system
3. Check browser console for errors
4. Contact IT support if issue persists

### Filters Not Working

**Symptoms**: Apply filters, but timeline doesn't update

**Causes**:
- Filters too restrictive (no results)
- Browser cache issue

**Solutions**:
1. Clear all filters and re-apply one by one
2. Clear browser cache (Ctrl+Shift+Delete)
3. Try different filter combinations

### Performance Issues

**Symptoms**: Slow loading, laggy interactions

**Causes**:
- Patient has >10,000 events
- Old browser
- Network latency

**Solutions**:
1. Apply date range filter to reduce data volume
2. Use Chrome or Firefox (latest version)
3. Close other browser tabs
4. Contact IT for performance optimization

---

## FAQ

**Q: Can I see deleted documents?**  
A: No, deleted documents are not shown on the timeline.

**Q: How often is the timeline updated?**  
A: Timeline data is updated in real-time as documents are processed (typically within 1 hour of document upload).

**Q: Can I print the timeline?**  
A: Yes, export as PDF and print from your PDF viewer.

**Q: Is there a mobile app?**  
A: Not currently. Use a tablet or desktop for best experience.

**Q: How do I report an error in the timeline?**  
A: Click "Report Issue" button, describe the problem, and include patient ID (no PHI in description).

**Q: Can I share my saved presets with colleagues?**  
A: Not yet. Preset sharing is planned for a future release.

---

## Support

- **Email**: support@yourhospital.com
- **Phone**: 555-1234 ext. 5678
- **Hours**: Monday-Friday, 8am-5pm
- **In-Person**: IT Help Desk, Building A, Room 101

---

## Privacy & Security

- All timeline views are **audit-logged** for HIPAA compliance
- Access is restricted based on **role-based permissions**
- PHI exports require **additional authentication**
- Data is **encrypted** in transit (TLS 1.3) and at rest (AES-256)

**Remember**: Only access patient timelines when clinically necessary.

---

*For technical documentation, see [Timeline API Documentation](../technical/timeline-api.md)*
