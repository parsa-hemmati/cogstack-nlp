# Timeline View - Phase 5.6: Export Capabilities (PDF, FHIR, JSON) (Detailed Tasks)

**Version**: 1.0.0
**Date**: 2025-11-19
**Status**: Ready for Implementation
**Specification**: `.specify/specifications/sprint-2-timeline-view.md` v1.0.0
**Technical Plan**: `.specify/plans/timeline-view-plan.md` v1.0.0 (Phase 5.6 section)

---

## Overview

**Phase Goal**: Implement comprehensive export capabilities allowing clinicians to export patient timelines to PDF (visual summary), FHIR R4 (EHR interoperability), and JSON (data analysis/research)

**Estimated Duration**: 15 hours (10 tasks, ~1.5 hours each)

**Dependencies**:
- ✅ Phase 5.1 COMPLETE (Backend Timeline Data API)
- ✅ Phase 5.2 COMPLETE (Frontend Timeline Component)
- ✅ Phase 5.3 COMPLETE (Concept Extraction & Display)
- ✅ Phase 5.4 COMPLETE (Filtering & Search)
- ✅ Phase 5.5 COMPLETE (Zoom, Pan, Temporal Analysis)

**Acceptance Criteria**:
- [ ] Export to PDF works (<5 seconds for typical timeline)
- [ ] PDF includes timeline visualization (embedded SVG)
- [ ] PDF includes patient demographics (de-identified option)
- [ ] PDF includes key concepts list
- [ ] PDF includes document list
- [ ] PDF watermarked: "Clinical Summary - Confidential"
- [ ] Export to FHIR R4 works (valid Composition resource)
- [ ] FHIR export includes all concepts as Observation references
- [ ] Export to JSON works (machine-readable, complete data)
- [ ] Audit log entry created for all exports (HIPAA compliance)
- [ ] Exports expire after 30 days (automatic cleanup)
- [ ] Export options dialog (filters, watermark, de-identification)
- [ ] Progress indicator during export generation
- [ ] Download link provided after export completion
- [ ] Unit test coverage ≥80%
- [ ] Integration tests for all export formats

---

## Task Breakdown

### Task 5.6.1: Install Export Dependencies (0.5 hours)

**Goal**: Install WeasyPrint for PDF generation and fhir.resources for FHIR R4 mapping

**Prerequisites**:
- Phase 5.5 complete
- Backend virtual environment active

**Steps**:
1. Install WeasyPrint for HTML → PDF conversion:
   ```bash
   cd backend
   pip install weasyprint==60.1
   ```
2. Install fhir.resources for FHIR R4 compliance:
   ```bash
   pip install fhir.resources==7.1.0
   ```
3. Update `backend/requirements.txt`:
   ```
   weasyprint==60.1
   fhir.resources==7.1.0
   ```
4. Test imports in Python REPL:
   ```python
   from weasyprint import HTML
   from fhir.resources.composition import Composition
   from fhir.resources.observation import Observation
   ```
5. Document dependencies in CONTEXT.md

**Acceptance Criteria**:
- [x] WeasyPrint installed and importable
- [x] fhir.resources installed and importable
- [x] requirements.txt updated
- [x] No dependency conflicts
- [x] CONTEXT.md updated with dependency notes

**Files Modified**:
- `backend/requirements.txt`
- `CONTEXT.md`

---

### Task 5.6.2: Create TimelineExportService (Backend) (3 hours)

**Goal**: Implement service layer for exporting timelines to PDF, FHIR, and JSON formats

**Prerequisites**:
- Task 5.6.1 complete (dependencies installed)
- TimelineService exists (Phase 5.1)

**Steps**:
1. Create `backend/app/services/timeline_export_service.py`:
   ```python
   from typing import Dict, Any, Optional
   from uuid import UUID
   from datetime import datetime, timedelta
   from weasyprint import HTML
   from fhir.resources.composition import Composition
   from fhir.resources.observation import Observation
   from app.schemas.timeline import TimelineResponse
   from app.services.timeline_service import TimelineService

   class TimelineExportService:
       """Service for exporting patient timelines to various formats."""

       async def export_to_pdf(
           self,
           patient_id: UUID,
           timeline_data: TimelineResponse,
           options: Dict[str, Any] = None
       ) -> bytes:
           """Generate PDF from timeline HTML template."""
           pass

       async def export_to_fhir(
           self,
           patient_id: UUID,
           timeline_data: TimelineResponse
       ) -> Composition:
           """Map timeline to FHIR R4 Composition resource."""
           pass

       async def export_to_json(
           self,
           timeline_data: TimelineResponse
       ) -> Dict[str, Any]:
           """Serialize timeline to JSON."""
           pass
   ```

2. Implement `export_to_pdf()`:
   - Render timeline HTML template with data
   - Convert HTML to PDF using WeasyPrint
   - Add watermark: "Clinical Summary - Confidential"
   - Embed timeline SVG visualization (if possible)
   - Include patient demographics (de-identified option)
   - Include key concepts table
   - Include document list
   - Return PDF bytes

3. Implement `export_to_fhir()`:
   - Create FHIR Composition resource (documentType = "clinical-timeline")
   - Map patient to subject reference
   - Map concepts to Observation resources (referenced in sections)
   - Map documents to DocumentReference resources
   - Include meta-annotations in Observation components
   - Return valid FHIR R4 Composition JSON

4. Implement `export_to_json()`:
   - Serialize TimelineResponse to JSON
   - Include metadata (export timestamp, filters applied)
   - Include all concepts with mentions
   - Include all documents
   - Return JSON dict

5. Write comprehensive docstrings with examples

**Acceptance Criteria**:
- [x] TimelineExportService class created
- [x] `export_to_pdf()` generates valid PDF
- [x] PDF includes timeline visualization, concepts, documents
- [x] PDF watermarked correctly
- [x] `export_to_fhir()` generates valid FHIR R4 Composition
- [x] FHIR output validates against FHIR R4 schema
- [x] `export_to_json()` serializes timeline completely
- [x] All methods have docstrings
- [x] Type hints on all parameters and returns

**Files Created**:
- `backend/app/services/timeline_export_service.py` (~250 lines)

**Testing**: Unit tests in Task 5.6.6

---

### Task 5.6.3: Create PDF HTML Template (1.5 hours)

**Goal**: Create Jinja2 HTML template for PDF rendering with timeline visualization and clinical data

**Prerequisites**:
- Task 5.6.2 complete (TimelineExportService created)

**Steps**:
1. Create `backend/app/templates/timeline/timeline_pdf.html`:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>Clinical Timeline - {{ patient_name }}</title>
       <style>
           @page {
               size: A4;
               margin: 2cm;
               @bottom-right {
                   content: "Page " counter(page) " of " counter(pages);
               }
           }
           body {
               font-family: Arial, sans-serif;
               font-size: 10pt;
           }
           .watermark {
               position: fixed;
               top: 50%;
               left: 50%;
               transform: translate(-50%, -50%) rotate(-45deg);
               font-size: 72pt;
               opacity: 0.1;
               color: red;
               z-index: -1;
           }
           /* ... more styles ... */
       </style>
   </head>
   <body>
       <div class="watermark">Clinical Summary - Confidential</div>
       <header>
           <h1>Patient Clinical Timeline</h1>
           <p>Generated: {{ export_date }}</p>
           {% if not de_identified %}
           <p>Patient: {{ patient_name }} (MRN: {{ patient_mrn }})</p>
           {% else %}
           <p>Patient: [De-identified]</p>
           {% endif %}
       </header>

       <section class="timeline-visualization">
           <h2>Timeline Visualization</h2>
           <!-- Embedded SVG or image here -->
           {{ timeline_svg|safe }}
       </section>

       <section class="key-concepts">
           <h2>Key Clinical Concepts</h2>
           <table>
               <thead>
                   <tr>
                       <th>Concept</th>
                       <th>Type</th>
                       <th>First Mentioned</th>
                       <th>Mentions</th>
                   </tr>
               </thead>
               <tbody>
                   {% for concept in concepts %}
                   <tr>
                       <td>{{ concept.concept_name }}</td>
                       <td>{{ concept.concept_type }}</td>
                       <td>{{ concept.first_mention_date|date }}</td>
                       <td>{{ concept.mention_count }}</td>
                   </tr>
                   {% endfor %}
               </tbody>
           </table>
       </section>

       <section class="documents">
           <h2>Source Documents</h2>
           <ul>
               {% for doc in documents %}
               <li>{{ doc.date|date }}: {{ doc.title }} ({{ doc.document_type }})</li>
               {% endfor %}
           </ul>
       </section>
   </body>
   </html>
   ```

2. Test template rendering with Jinja2:
   ```python
   from jinja2 import Template
   template = Template(open('timeline_pdf.html').read())
   html = template.render(patient_name="Test Patient", ...)
   ```

3. Test PDF generation with WeasyPrint:
   ```python
   from weasyprint import HTML
   HTML(string=html).write_pdf('test_timeline.pdf')
   ```

4. Verify PDF output:
   - Watermark visible but not obstructive
   - Timeline visualization embedded
   - Concepts table formatted correctly
   - Documents list complete
   - Page numbers present

**Acceptance Criteria**:
- [x] HTML template created with Jinja2 syntax
- [x] Watermark renders correctly (diagonal, low opacity)
- [x] Template renders patient demographics
- [x] Template renders concepts table
- [x] Template renders documents list
- [x] Template supports SVG embedding (timeline_svg variable)
- [x] PDF generates without errors
- [x] PDF is A4 size with proper margins
- [x] Page numbers appear on all pages

**Files Created**:
- `backend/app/templates/timeline/timeline_pdf.html` (~150 lines)

---

### Task 5.6.4: Add Export API Endpoints (2 hours)

**Goal**: Create REST API endpoints for timeline export (POST /export, GET /download)

**Prerequisites**:
- Task 5.6.2 complete (TimelineExportService)
- Task 5.6.3 complete (PDF template)

**Steps**:
1. Modify `backend/app/api/v1/endpoints/timeline.py`, add export endpoints:
   ```python
   from app.schemas.timeline_export import (
       ExportRequest,
       ExportResponse,
       ExportFormat
   )
   from app.services.timeline_export_service import TimelineExportService

   @router.post(
       "/{patient_id}/export",
       response_model=ExportResponse,
       status_code=202
   )
   async def export_timeline(
       patient_id: UUID,
       export_request: ExportRequest,
       current_user: User = Depends(get_current_user),
       db: AsyncSession = Depends(get_db)
   ):
       """
       Export patient timeline to PDF, FHIR, or JSON.

       Returns export_id for async download via GET /exports/{export_id}/download
       """
       # Create export record in timeline_exports table
       # Queue background task for export generation
       # Log audit trail
       # Return export_id
       pass

   @router.get(
       "/exports/{export_id}/download",
       response_class=FileResponse
   )
   async def download_export(
       export_id: UUID,
       current_user: User = Depends(get_current_user),
       db: AsyncSession = Depends(get_db)
   ):
       """Download generated export file."""
       # Verify export belongs to user or user has permission
       # Check export not expired (30 days)
       # Increment download_count
       # Return file with appropriate Content-Type
       pass
   ```

2. Create `backend/app/schemas/timeline_export.py`:
   ```python
   from enum import Enum
   from pydantic import BaseModel, Field
   from typing import Optional, Dict, Any
   from uuid import UUID
   from datetime import datetime

   class ExportFormat(str, Enum):
       PDF = "pdf"
       FHIR = "fhir"
       JSON = "json"

   class ExportRequest(BaseModel):
       format: ExportFormat
       filters: Optional[Dict[str, Any]] = None
       options: Optional[Dict[str, Any]] = None  # watermark, de_identified

   class ExportResponse(BaseModel):
       export_id: UUID
       status: str  # "queued", "processing", "completed", "failed"
       download_url: Optional[str] = None
       expires_at: datetime
   ```

3. Implement background task for export generation:
   ```python
   from app.core.background_tasks import background_tasks

   @background_tasks.task
   async def generate_export(export_id: UUID):
       """Background task to generate export file."""
       # Fetch export record
       # Fetch timeline data
       # Generate export (PDF/FHIR/JSON)
       # Save to file_path
       # Update export status to "completed"
       # Handle errors gracefully
       pass
   ```

4. Add audit logging for exports:
   ```python
   audit_logger.info({
       "user_id": current_user.id,
       "action": "EXPORT_TIMELINE",
       "patient_id": patient_id,
       "export_format": export_request.format,
       "timestamp": datetime.now().isoformat()
   })
   ```

5. Add automatic cleanup for expired exports:
   ```python
   # Scheduled task (runs daily)
   @scheduler.task(cron="0 0 * * *")
   async def cleanup_expired_exports():
       """Delete export files older than 30 days."""
       cutoff = datetime.now() - timedelta(days=30)
       expired = await db.query(TimelineExport).filter(
           TimelineExport.created_at < cutoff
       ).all()
       for export in expired:
           if export.file_path and os.path.exists(export.file_path):
               os.remove(export.file_path)
           await db.delete(export)
       await db.commit()
   ```

**Acceptance Criteria**:
- [x] POST /api/v1/timeline/{patient_id}/export endpoint created
- [x] GET /api/v1/timeline/exports/{export_id}/download endpoint created
- [x] ExportRequest and ExportResponse schemas defined
- [x] Export record saved to timeline_exports table
- [x] Background task generates export file
- [x] Audit log entry created for all exports
- [x] Download increments download_count
- [x] Expired exports cleaned up automatically
- [x] 403 error if user lacks permission
- [x] 404 error if export not found or expired

**Files Modified**:
- `backend/app/api/v1/endpoints/timeline.py` (+100 lines)

**Files Created**:
- `backend/app/schemas/timeline_export.py` (~50 lines)

**Testing**: Integration tests in Task 5.6.7

---

### Task 5.6.5: Create TimelineExportToolbar Component (Frontend) (2.5 hours)

**Goal**: Build Vue component with export buttons, options dialog, and download handling

**Prerequisites**:
- Task 5.6.4 complete (export API endpoints)
- Phase 5.2 complete (TimelineView exists)

**Steps**:
1. Create `frontend/src/components/TimelineExportToolbar.vue`:
   ```vue
   <template>
     <v-toolbar density="compact" color="transparent">
       <v-toolbar-title>Export</v-toolbar-title>

       <v-btn
         prepend-icon="mdi-file-pdf-box"
         @click="showExportDialog('pdf')"
         :loading="exportLoading.pdf"
       >
         PDF
       </v-btn>

       <v-btn
         prepend-icon="mdi-hospital-box"
         @click="showExportDialog('fhir')"
         :loading="exportLoading.fhir"
       >
         FHIR
       </v-btn>

       <v-btn
         prepend-icon="mdi-code-json"
         @click="showExportDialog('json')"
         :loading="exportLoading.json"
       >
         JSON
       </v-btn>

       <!-- Export Options Dialog -->
       <v-dialog v-model="dialog" max-width="500">
         <v-card>
           <v-card-title>Export Timeline ({{ exportFormat.toUpperCase() }})</v-card-title>
           <v-card-text>
             <v-checkbox
               v-model="exportOptions.de_identified"
               label="De-identify patient data"
               hint="Remove patient name and MRN from export"
             />
             <v-checkbox
               v-if="exportFormat === 'pdf'"
               v-model="exportOptions.watermark"
               label="Add watermark"
             />
             <v-checkbox
               v-model="exportOptions.apply_filters"
               label="Apply current filters"
             />
           </v-card-text>
           <v-card-actions>
             <v-btn @click="dialog = false">Cancel</v-btn>
             <v-btn color="primary" @click="exportTimeline">Export</v-btn>
           </v-card-actions>
         </v-card>
       </v-dialog>

       <!-- Download Snackbar -->
       <v-snackbar v-model="snackbar.show" :color="snackbar.color">
         {{ snackbar.message }}
         <template v-slot:actions>
           <v-btn v-if="downloadUrl" @click="downloadFile">Download</v-btn>
           <v-btn @click="snackbar.show = false">Close</v-btn>
         </template>
       </v-snackbar>
     </v-toolbar>
   </template>

   <script setup lang="ts">
   import { ref, reactive } from 'vue'
   import { useTimelineExport } from '@/composables/useTimelineExport'

   interface Props {
     patientId: string
     filters?: any
   }

   const props = defineProps<Props>()

   const { exportTimeline: apiExportTimeline, downloadExport } = useTimelineExport()

   const dialog = ref(false)
   const exportFormat = ref<'pdf' | 'fhir' | 'json'>('pdf')
   const exportLoading = reactive({ pdf: false, fhir: false, json: false })
   const exportOptions = reactive({
     de_identified: false,
     watermark: true,
     apply_filters: false
   })
   const snackbar = reactive({
     show: false,
     message: '',
     color: 'success'
   })
   const downloadUrl = ref<string | null>(null)

   const showExportDialog = (format: 'pdf' | 'fhir' | 'json') => {
     exportFormat.value = format
     dialog.value = true
   }

   const exportTimeline = async () => {
     exportLoading[exportFormat.value] = true
     dialog.value = false

     try {
       const result = await apiExportTimeline(
         props.patientId,
         exportFormat.value,
         exportOptions.apply_filters ? props.filters : undefined,
         exportOptions
       )

       downloadUrl.value = result.download_url
       snackbar.message = `Export ${exportFormat.value.toUpperCase()} ready!`
       snackbar.color = 'success'
       snackbar.show = true
     } catch (error) {
       snackbar.message = `Export failed: ${error.message}`
       snackbar.color = 'error'
       snackbar.show = true
     } finally {
       exportLoading[exportFormat.value] = false
     }
   }

   const downloadFile = () => {
     if (downloadUrl.value) {
       window.open(downloadUrl.value, '_blank')
       snackbar.show = false
     }
   }
   </script>
   ```

2. Create `frontend/src/composables/useTimelineExport.ts`:
   ```typescript
   import { ref } from 'vue'
   import api from '@/api/client'

   export interface ExportRequest {
     format: 'pdf' | 'fhir' | 'json'
     filters?: any
     options?: {
       de_identified?: boolean
       watermark?: boolean
       apply_filters?: boolean
     }
   }

   export interface ExportResponse {
     export_id: string
     status: string
     download_url: string | null
     expires_at: string
   }

   export function useTimelineExport() {
     const isLoading = ref(false)
     const error = ref<string | null>(null)

     const exportTimeline = async (
       patientId: string,
       format: 'pdf' | 'fhir' | 'json',
       filters?: any,
       options?: any
     ): Promise<ExportResponse> => {
       isLoading.value = true
       error.value = null

       try {
         const response = await api.post(
           `/api/v1/timeline/${patientId}/export`,
           { format, filters, options }
         )
         return response.data
       } catch (err) {
         error.value = err.message
         throw err
       } finally {
         isLoading.value = false
       }
     }

     const downloadExport = (exportId: string) => {
       const url = `/api/v1/timeline/exports/${exportId}/download`
       window.open(url, '_blank')
     }

     return {
       isLoading,
       error,
       exportTimeline,
       downloadExport
     }
   }
   ```

3. Integrate toolbar into `frontend/src/views/TimelineView.vue`:
   ```vue
   <template>
     <v-container fluid>
       <!-- Existing timeline toolbar -->
       <v-row>
         <v-col cols="12">
           <TimelineExportToolbar
             :patient-id="patientId"
             :filters="appliedFilters"
           />
         </v-col>
       </v-row>
       <!-- Rest of timeline view -->
     </v-container>
   </template>
   ```

**Acceptance Criteria**:
- [x] TimelineExportToolbar component created
- [x] Export buttons for PDF, FHIR, JSON
- [x] Export options dialog (de-identify, watermark, apply filters)
- [x] Progress indicator during export
- [x] Success/error snackbar
- [x] Download button appears after export completion
- [x] useTimelineExport composable created
- [x] Integrated into TimelineView

**Files Created**:
- `frontend/src/components/TimelineExportToolbar.vue` (~150 lines)
- `frontend/src/composables/useTimelineExport.ts` (~60 lines)

**Files Modified**:
- `frontend/src/views/TimelineView.vue` (+5 lines)

**Testing**: Unit tests in Task 5.6.8

---

### Task 5.6.6: Unit Tests for TimelineExportService (Backend) (2 hours)

**Goal**: Write comprehensive unit tests for all export methods (PDF, FHIR, JSON)

**Prerequisites**:
- Task 5.6.2 complete (TimelineExportService)
- Task 5.6.3 complete (PDF template)

**Steps**:
1. Create `backend/tests/unit/services/test_timeline_export_service.py`:
   ```python
   import pytest
   from unittest.mock import AsyncMock, MagicMock, patch
   from uuid import uuid4
   from app.services.timeline_export_service import TimelineExportService
   from app.schemas.timeline import TimelineResponse, ConceptSummary

   @pytest.fixture
   def export_service():
       return TimelineExportService()

   @pytest.fixture
   def sample_timeline():
       return TimelineResponse(
           patient_id=uuid4(),
           documents=[...],
           concepts=[...],
           date_range={...},
           filters_applied={}
       )

   # PDF Export Tests

   def test_export_to_pdf_generates_valid_pdf(export_service, sample_timeline):
       """Test PDF export returns valid PDF bytes."""
       pdf_bytes = await export_service.export_to_pdf(
           patient_id=sample_timeline.patient_id,
           timeline_data=sample_timeline
       )

       assert pdf_bytes is not None
       assert len(pdf_bytes) > 0
       assert pdf_bytes[:4] == b'%PDF'  # PDF header

   def test_export_to_pdf_includes_watermark(export_service, sample_timeline):
       """Test PDF includes watermark text."""
       pdf_bytes = await export_service.export_to_pdf(
           patient_id=sample_timeline.patient_id,
           timeline_data=sample_timeline,
           options={"watermark": True}
       )

       # Check PDF contains watermark text
       pdf_text = extract_text_from_pdf(pdf_bytes)
       assert "Clinical Summary - Confidential" in pdf_text

   def test_export_to_pdf_de_identified(export_service, sample_timeline):
       """Test PDF de-identifies patient data when requested."""
       pdf_bytes = await export_service.export_to_pdf(
           patient_id=sample_timeline.patient_id,
           timeline_data=sample_timeline,
           options={"de_identified": True}
       )

       pdf_text = extract_text_from_pdf(pdf_bytes)
       assert "[De-identified]" in pdf_text
       assert sample_timeline.patient_name not in pdf_text  # No PII

   def test_export_to_pdf_performance(export_service, sample_timeline):
       """Test PDF generation completes in <5 seconds."""
       import time
       start = time.time()

       pdf_bytes = await export_service.export_to_pdf(
           patient_id=sample_timeline.patient_id,
           timeline_data=sample_timeline
       )

       duration = time.time() - start
       assert duration < 5.0, f"PDF generation took {duration}s (target <5s)"

   # FHIR Export Tests

   def test_export_to_fhir_generates_composition(export_service, sample_timeline):
       """Test FHIR export returns valid Composition resource."""
       fhir_composition = await export_service.export_to_fhir(
           patient_id=sample_timeline.patient_id,
           timeline_data=sample_timeline
       )

       assert fhir_composition.resource_type == "Composition"
       assert fhir_composition.type.coding[0].code == "clinical-timeline"
       assert fhir_composition.subject.reference == f"Patient/{sample_timeline.patient_id}"

   def test_export_to_fhir_includes_observations(export_service, sample_timeline):
       """Test FHIR Composition includes Observation references for concepts."""
       fhir_composition = await export_service.export_to_fhir(
           patient_id=sample_timeline.patient_id,
           timeline_data=sample_timeline
       )

       sections = fhir_composition.section
       assert len(sections) > 0

       # Check first section has Observation entries
       first_section = sections[0]
       assert first_section.entry is not None
       assert len(first_section.entry) == len(sample_timeline.concepts)

   def test_export_to_fhir_validates_schema(export_service, sample_timeline):
       """Test FHIR output validates against FHIR R4 schema."""
       from fhir.resources.composition import Composition

       fhir_composition = await export_service.export_to_fhir(
           patient_id=sample_timeline.patient_id,
           timeline_data=sample_timeline
       )

       # Serialize and deserialize to validate schema
       json_str = fhir_composition.json()
       reloaded = Composition.parse_raw(json_str)

       assert reloaded.resource_type == "Composition"

   # JSON Export Tests

   def test_export_to_json_serializes_timeline(export_service, sample_timeline):
       """Test JSON export serializes complete timeline."""
       json_data = await export_service.export_to_json(
           timeline_data=sample_timeline
       )

       assert json_data is not None
       assert "patient_id" in json_data
       assert "concepts" in json_data
       assert "documents" in json_data
       assert len(json_data["concepts"]) == len(sample_timeline.concepts)

   def test_export_to_json_includes_metadata(export_service, sample_timeline):
       """Test JSON export includes export metadata."""
       json_data = await export_service.export_to_json(
           timeline_data=sample_timeline
       )

       assert "export_metadata" in json_data
       assert "export_timestamp" in json_data["export_metadata"]
       assert "filters_applied" in json_data["export_metadata"]

   def test_export_to_json_machine_readable(export_service, sample_timeline):
       """Test JSON export is valid and machine-readable."""
       import json

       json_data = await export_service.export_to_json(
           timeline_data=sample_timeline
       )

       # Serialize and deserialize to verify valid JSON
       json_str = json.dumps(json_data)
       reloaded = json.loads(json_str)

       assert reloaded["patient_id"] == str(sample_timeline.patient_id)
   ```

2. Run tests and verify ≥80% coverage:
   ```bash
   pytest backend/tests/unit/services/test_timeline_export_service.py -v --cov=app.services.timeline_export_service
   ```

3. Fix any failing tests

**Acceptance Criteria**:
- [x] 10+ unit tests created (PDF, FHIR, JSON)
- [x] All export methods tested
- [x] PDF watermark tested
- [x] PDF de-identification tested
- [x] PDF performance tested (<5 seconds)
- [x] FHIR schema validation tested
- [x] FHIR Observation mapping tested
- [x] JSON serialization tested
- [x] Test coverage ≥80%
- [x] All tests passing

**Files Created**:
- `backend/tests/unit/services/test_timeline_export_service.py` (~300 lines)

---

### Task 5.6.7: Integration Tests for Export API Endpoints (1.5 hours)

**Goal**: Write integration tests for export endpoints (POST /export, GET /download)

**Prerequisites**:
- Task 5.6.4 complete (export API endpoints)
- Task 5.6.6 complete (unit tests passing)

**Steps**:
1. Create `backend/tests/integration/api/test_timeline_export_api.py`:
   ```python
   import pytest
   from httpx import AsyncClient
   from uuid import uuid4
   from app.main import app

   @pytest.mark.integration
   async def test_export_timeline_pdf(async_client: AsyncClient, test_user_token):
       """Test POST /api/v1/timeline/{patient_id}/export (PDF)."""
       patient_id = uuid4()

       response = await async_client.post(
           f"/api/v1/timeline/{patient_id}/export",
           json={"format": "pdf", "options": {"watermark": True}},
           headers={"Authorization": f"Bearer {test_user_token}"}
       )

       assert response.status_code == 202
       data = response.json()
       assert "export_id" in data
       assert data["status"] == "queued"

   @pytest.mark.integration
   async def test_export_timeline_fhir(async_client: AsyncClient, test_user_token):
       """Test POST /api/v1/timeline/{patient_id}/export (FHIR)."""
       patient_id = uuid4()

       response = await async_client.post(
           f"/api/v1/timeline/{patient_id}/export",
           json={"format": "fhir"},
           headers={"Authorization": f"Bearer {test_user_token}"}
       )

       assert response.status_code == 202
       data = response.json()
       assert data["status"] == "queued"

   @pytest.mark.integration
   async def test_download_export(async_client: AsyncClient, test_user_token):
       """Test GET /api/v1/timeline/exports/{export_id}/download."""
       # First create an export
       export_response = await async_client.post(
           f"/api/v1/timeline/{uuid4()}/export",
           json={"format": "json"},
           headers={"Authorization": f"Bearer {test_user_token}"}
       )
       export_id = export_response.json()["export_id"]

       # Wait for export to complete (poll status)
       # ... (or mock background task completion)

       # Download export
       download_response = await async_client.get(
           f"/api/v1/timeline/exports/{export_id}/download",
           headers={"Authorization": f"Bearer {test_user_token}"}
       )

       assert download_response.status_code == 200
       assert download_response.headers["content-type"] in [
           "application/json",
           "application/pdf",
           "application/fhir+json"
       ]

   @pytest.mark.integration
   async def test_export_audit_logged(async_client: AsyncClient, test_user_token, db):
       """Test export creates audit log entry."""
       patient_id = uuid4()

       response = await async_client.post(
           f"/api/v1/timeline/{patient_id}/export",
           json={"format": "pdf"},
           headers={"Authorization": f"Bearer {test_user_token}"}
       )

       # Verify audit log entry created
       audit_entry = await db.query(AuditLog).filter(
           AuditLog.action == "EXPORT_TIMELINE",
           AuditLog.patient_id == patient_id
       ).first()

       assert audit_entry is not None
       assert audit_entry.user_id == test_user_id

   @pytest.mark.integration
   async def test_export_unauthorized(async_client: AsyncClient):
       """Test export requires authentication."""
       patient_id = uuid4()

       response = await async_client.post(
           f"/api/v1/timeline/{patient_id}/export",
           json={"format": "pdf"}
       )

       assert response.status_code == 401
   ```

2. Run integration tests:
   ```bash
   pytest backend/tests/integration/api/test_timeline_export_api.py -v
   ```

**Acceptance Criteria**:
- [x] 5+ integration tests created
- [x] POST /export tested for all formats (PDF, FHIR, JSON)
- [x] GET /download tested
- [x] Audit logging tested
- [x] Authentication tested
- [x] All tests passing

**Files Created**:
- `backend/tests/integration/api/test_timeline_export_api.py` (~150 lines)

---

### Task 5.6.8: Unit Tests for TimelineExportToolbar (Frontend) (1.5 hours)

**Goal**: Write unit tests for export toolbar component and composable

**Prerequisites**:
- Task 5.6.5 complete (TimelineExportToolbar created)

**Steps**:
1. Create `frontend/tests/unit/components/TimelineExportToolbar.spec.ts`:
   ```typescript
   import { describe, it, expect, vi } from 'vitest'
   import { mount } from '@vue/test-utils'
   import TimelineExportToolbar from '@/components/TimelineExportToolbar.vue'

   describe('TimelineExportToolbar', () => {
     it('renders export buttons (PDF, FHIR, JSON)', () => {
       const wrapper = mount(TimelineExportToolbar, {
         props: { patientId: 'patient-123' }
       })

       const buttons = wrapper.findAll('button')
       expect(buttons.length).toBeGreaterThanOrEqual(3)

       const buttonTexts = buttons.map(btn => btn.text())
       expect(buttonTexts).toContain('PDF')
       expect(buttonTexts).toContain('FHIR')
       expect(buttonTexts).toContain('JSON')
     })

     it('opens export dialog when PDF button clicked', async () => {
       const wrapper = mount(TimelineExportToolbar, {
         props: { patientId: 'patient-123' }
       })

       const pdfButton = wrapper.findAll('button').find(btn =>
         btn.text().includes('PDF')
       )
       await pdfButton!.trigger('click')

       // Dialog should be visible
       expect(wrapper.find('.v-dialog').exists()).toBe(true)
       expect(wrapper.find('.v-dialog').text()).toContain('Export Timeline')
     })

     it('calls exportTimeline when Export button clicked in dialog', async () => {
       const mockExport = vi.fn(() => Promise.resolve({
         export_id: 'export-123',
         status: 'completed',
         download_url: '/download/export-123'
       }))

       vi.mock('@/composables/useTimelineExport', () => ({
         useTimelineExport: () => ({
           exportTimeline: mockExport,
           isLoading: ref(false),
           error: ref(null)
         })
       }))

       const wrapper = mount(TimelineExportToolbar, {
         props: { patientId: 'patient-123' }
       })

       // Open dialog
       await wrapper.findAll('button').find(btn =>
         btn.text().includes('PDF')
       )!.trigger('click')

       // Click Export in dialog
       await wrapper.find('.v-card-actions button[color="primary"]').trigger('click')

       expect(mockExport).toHaveBeenCalledOnce()
       expect(mockExport).toHaveBeenCalledWith(
         'patient-123',
         'pdf',
         undefined,
         expect.objectContaining({ watermark: true })
       )
     })

     it('shows snackbar with download link after successful export', async () => {
       const wrapper = mount(TimelineExportToolbar, {
         props: { patientId: 'patient-123' }
       })

       // Simulate successful export
       // ... trigger export and wait for response ...

       // Snackbar should be visible
       const snackbar = wrapper.find('.v-snackbar')
       expect(snackbar.exists()).toBe(true)
       expect(snackbar.text()).toContain('Export PDF ready!')

       // Download button should be present
       const downloadButton = snackbar.find('button')
       expect(downloadButton.text()).toContain('Download')
     })

     it('shows error snackbar on export failure', async () => {
       const mockExport = vi.fn(() => Promise.reject(new Error('Export failed')))

       // ... mount component with mocked export ...

       // Trigger export
       // ... click PDF button, then Export ...

       // Error snackbar should be visible
       const snackbar = wrapper.find('.v-snackbar')
       expect(snackbar.exists()).toBe(true)
       expect(snackbar.text()).toContain('Export failed')
     })
   })
   ```

2. Create `frontend/tests/unit/composables/useTimelineExport.spec.ts`:
   ```typescript
   import { describe, it, expect, vi } from 'vitest'
   import { useTimelineExport } from '@/composables/useTimelineExport'

   describe('useTimelineExport', () => {
     it('calls API with correct parameters', async () => {
       const mockApi = {
         post: vi.fn(() => Promise.resolve({
           data: { export_id: 'export-123', status: 'queued' }
         }))
       }

       const { exportTimeline } = useTimelineExport(mockApi)

       await exportTimeline('patient-123', 'pdf', { concept: 'diabetes' }, { watermark: true })

       expect(mockApi.post).toHaveBeenCalledWith(
         '/api/v1/timeline/patient-123/export',
         {
           format: 'pdf',
           filters: { concept: 'diabetes' },
           options: { watermark: true }
         }
       )
     })

     it('sets isLoading during export', async () => {
       const { exportTimeline, isLoading } = useTimelineExport()

       expect(isLoading.value).toBe(false)

       const promise = exportTimeline('patient-123', 'pdf')
       expect(isLoading.value).toBe(true)

       await promise
       expect(isLoading.value).toBe(false)
     })

     it('sets error on export failure', async () => {
       const mockApi = {
         post: vi.fn(() => Promise.reject(new Error('Network error')))
       }

       const { exportTimeline, error } = useTimelineExport(mockApi)

       await expect(exportTimeline('patient-123', 'pdf')).rejects.toThrow()

       expect(error.value).toBe('Network error')
     })
   })
   ```

3. Run tests and verify coverage:
   ```bash
   npm run test:unit -- TimelineExportToolbar.spec.ts
   npm run test:unit -- useTimelineExport.spec.ts
   ```

**Acceptance Criteria**:
- [x] 5+ component tests created
- [x] Button rendering tested
- [x] Dialog opening tested
- [x] Export triggering tested
- [x] Snackbar success/error tested
- [x] 3+ composable tests created
- [x] API call tested
- [x] Loading state tested
- [x] Error handling tested
- [x] All tests passing

**Files Created**:
- `frontend/tests/unit/components/TimelineExportToolbar.spec.ts` (~150 lines)
- `frontend/tests/unit/composables/useTimelineExport.spec.ts` (~80 lines)

---

### Task 5.6.9: Integration Test for Full Export Workflow (1 hour)

**Goal**: Create end-to-end integration test validating complete export workflow (request → generate → download)

**Prerequisites**:
- Task 5.6.7 complete (backend integration tests)
- Task 5.6.8 complete (frontend unit tests)

**Steps**:
1. Create `frontend/tests/integration/TimelineExport.integration.spec.ts`:
   ```typescript
   import { describe, it, expect, vi } from 'vitest'
   import { mount } from '@vue/test-utils'
   import TimelineView from '@/views/TimelineView.vue'
   import { createRouter, createMemoryHistory } from 'vue-router'

   describe('Timeline Export Integration', () => {
     it('completes full export workflow: click PDF → options → export → download', async () => {
       const router = createRouter({
         history: createMemoryHistory(),
         routes: [
           { path: '/timeline/:patientId', name: 'TimelineView', component: TimelineView }
         ]
       })

       router.push('/timeline/patient-123')
       await router.isReady()

       const wrapper = mount(TimelineView, {
         global: { plugins: [router] }
       })

       // Wait for timeline to load
       await vi.waitFor(() => {
         expect(wrapper.find('.timeline-svg').exists()).toBe(true)
       }, { timeout: 2000 })

       // Click PDF export button
       const exportToolbar = wrapper.findComponent({ name: 'TimelineExportToolbar' })
       const pdfButton = exportToolbar.findAll('button').find(btn =>
         btn.text().includes('PDF')
       )
       await pdfButton!.trigger('click')

       // Export dialog should open
       const dialog = wrapper.find('.v-dialog')
       expect(dialog.exists()).toBe(true)

       // Configure export options
       const watermarkCheckbox = dialog.findAll('input[type="checkbox"]')[0]
       await watermarkCheckbox.setValue(true)

       // Click Export button
       const exportButton = dialog.find('button[color="primary"]')
       await exportButton.trigger('click')

       // Wait for export to complete (snackbar appears)
       await vi.waitFor(() => {
         expect(wrapper.find('.v-snackbar').exists()).toBe(true)
       }, { timeout: 5000 })

       // Snackbar should show success message
       const snackbar = wrapper.find('.v-snackbar')
       expect(snackbar.text()).toContain('Export PDF ready!')

       // Download button should be present
       const downloadButton = snackbar.find('button')
       expect(downloadButton.text()).toContain('Download')
     })

     it('exports with filters applied when option selected', async () => {
       // ... mount TimelineView with filters applied ...

       // Open export dialog
       // Enable "Apply current filters" checkbox
       // Click Export

       // Verify API call includes filters
       expect(mockApi.post).toHaveBeenCalledWith(
         expect.any(String),
         expect.objectContaining({
           filters: expect.objectContaining({ concept: 'diabetes' })
         })
       )
     })

     it('handles export failure gracefully', async () => {
       // ... mock API to reject export request ...

       // Trigger export

       // Error snackbar should appear
       const snackbar = wrapper.find('.v-snackbar')
       expect(snackbar.text()).toContain('Export failed')
       expect(snackbar.classes()).toContain('error')
     })
   })
   ```

2. Run integration test:
   ```bash
   npm run test:integration -- TimelineExport.integration.spec.ts
   ```

**Acceptance Criteria**:
- [x] 3+ integration tests created
- [x] Full export workflow tested (PDF, FHIR, JSON)
- [x] Export options tested (watermark, de-identify, filters)
- [x] Success flow tested
- [x] Error handling tested
- [x] All tests passing

**Files Created**:
- `frontend/tests/integration/TimelineExport.integration.spec.ts` (~120 lines)

---

### Task 5.6.10: Update Documentation and Commit Phase 5.6 (0.5 hours)

**Goal**: Update CONTEXT.md, AUDIT.md, and commit Phase 5.6 completion

**Prerequisites**:
- Tasks 5.6.1-5.6.9 complete
- All tests passing

**Steps**:
1. Update CONTEXT.md with Phase 5.6 completion:
   ```markdown
   ### [2025-11-19] - Phase 5.6: Export Capabilities (PDF, FHIR, JSON) - COMPLETE

   **Commits**: [commit SHA] - Phase 5.6 complete

   **Added**:
   - TimelineExportService for PDF, FHIR, JSON export
   - WeasyPrint integration for HTML → PDF
   - fhir.resources integration for FHIR R4 Composition
   - PDF HTML template with watermark and de-identification
   - Export API endpoints (POST /export, GET /download)
   - TimelineExportToolbar component
   - useTimelineExport composable
   - Audit logging for all exports
   - Automatic cleanup of expired exports (30 days)
   - 26 comprehensive tests (10 unit + 5 integration backend, 8 unit + 3 integration frontend)

   **Impact**:
   - ✅ Clinicians can export timelines to PDF for referrals/audits
   - ✅ Clinicians can export to FHIR R4 for EHR integration
   - ✅ Researchers can export to JSON for data analysis
   - ✅ HIPAA compliance via audit logging
   - ✅ De-identification option protects patient privacy
   - 🎯 Phase 5.6 delivers: Multi-format export with compliance
   ```

2. Update AUDIT.md with Phase 5.6 compliance review

3. Run validation script:
   ```bash
   ./scripts/validate-code.sh --full
   ```

4. Commit Phase 5.6:
   ```bash
   git add -A
   git commit -m "feat(timeline): Phase 5.6 - Export capabilities (PDF, FHIR, JSON) complete"
   ```

**Acceptance Criteria**:
- [x] CONTEXT.md updated with Phase 5.6 entry
- [x] AUDIT.md updated with compliance review
- [x] All tests passing
- [x] Validation script passes
- [x] Commit created with proper message

**Files Modified**:
- `CONTEXT.md`
- `AUDIT.md`

---

## Summary

**Phase 5.6 Deliverables**:
- ✅ TimelineExportService (PDF, FHIR, JSON)
- ✅ PDF HTML template with watermark
- ✅ Export API endpoints with audit logging
- ✅ TimelineExportToolbar component
- ✅ useTimelineExport composable
- ✅ 26 comprehensive tests (backend + frontend)
- ✅ Automatic export cleanup (30 days)

**Dependencies Installed**:
- WeasyPrint 60.1 (HTML → PDF)
- fhir.resources 7.1.0 (FHIR R4 compliance)

**Files Created** (10 files):
- `backend/app/services/timeline_export_service.py` (~250 lines)
- `backend/app/templates/timeline/timeline_pdf.html` (~150 lines)
- `backend/app/schemas/timeline_export.py` (~50 lines)
- `backend/tests/unit/services/test_timeline_export_service.py` (~300 lines)
- `backend/tests/integration/api/test_timeline_export_api.py` (~150 lines)
- `frontend/src/components/TimelineExportToolbar.vue` (~150 lines)
- `frontend/src/composables/useTimelineExport.ts` (~60 lines)
- `frontend/tests/unit/components/TimelineExportToolbar.spec.ts` (~150 lines)
- `frontend/tests/unit/composables/useTimelineExport.spec.ts` (~80 lines)
- `frontend/tests/integration/TimelineExport.integration.spec.ts` (~120 lines)

**Files Modified** (3 files):
- `backend/app/api/v1/endpoints/timeline.py` (+100 lines)
- `frontend/src/views/TimelineView.vue` (+5 lines)
- `backend/requirements.txt` (+2 dependencies)

**Total Lines of Code**: ~1,460 lines
**Test Coverage**: ≥80% (26 tests)
**Estimated Duration**: 15 hours (10 tasks)

**Next Phase**: Phase 5.7 (Integration Tests & E2E Tests)
