# Task Breakdown: Timeline View Module (Sprint 2 / Phase 5)

**Version**: 1.0.0
**Date**: 2025-11-19
**Status**: Draft
**Specification**: `.specify/specifications/sprint-2-timeline-view.md` v1.0.0
**Technical Plan**: `.specify/plans/timeline-view-plan.md` v1.0.0

---

## Overview

This document breaks down the Timeline View Module into granular, implementable tasks following the 8-phase structure defined in the technical plan.

**Total Phases**: 8 (5.1-5.8)
**Total Tasks**: 60 tasks
**Estimated Duration**: 120 hours (4 weeks)
**Average Task Duration**: 2 hours

---

## Phase 5.1: Backend Timeline Data API (Week 1, 15 hours)

**Goal**: Build backend API to serve timeline data (documents + concepts)

### Task 5.1.1: Database Schema - Create timeline_filters table (2 hours)

**Objective**: Create PostgreSQL table for saving user filter presets

**Prerequisites**:
- PostgreSQL database running
- Alembic migrations set up

**Steps**:
1. Create Alembic migration file:
   ```bash
   alembic revision -m "Add timeline_filters table"
   ```
2. Define timeline_filters schema:
   ```sql
   CREATE TABLE timeline_filters (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
       name VARCHAR(100) NOT NULL,
       description TEXT,
       filters JSONB NOT NULL,
       is_default BOOLEAN DEFAULT FALSE,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       UNIQUE(user_id, name)
   );
   CREATE INDEX idx_timeline_filters_user ON timeline_filters(user_id);
   ```
3. Test migration:
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```
4. Verify table created in PostgreSQL

**Acceptance Criteria**:
- [x] Migration file created
- [x] timeline_filters table created with correct schema
- [x] Index on user_id created
- [x] Migration up/down works without errors
- [x] Unique constraint on (user_id, name) enforced

**Files**:
- `backend/alembic/versions/{hash}_add_timeline_filters_table.py`

---

### Task 5.1.2: Database Schema - Create timeline_exports table (2 hours)

**Objective**: Create PostgreSQL table for tracking timeline exports

**Prerequisites**:
- Task 5.1.1 complete
- audit_logs table exists

**Steps**:
1. Create Alembic migration file:
   ```bash
   alembic revision -m "Add timeline_exports table"
   ```
2. Define timeline_exports schema:
   ```sql
   CREATE TABLE timeline_exports (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       patient_id UUID NOT NULL REFERENCES patients(id),
       user_id UUID NOT NULL REFERENCES users(id),
       format VARCHAR(10) NOT NULL,
       filters JSONB NOT NULL,
       file_path VARCHAR(500),
       download_count INTEGER DEFAULT 0,
       expires_at TIMESTAMP WITH TIME ZONE,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       audit_log_id UUID REFERENCES audit_logs(id)
   );
   CREATE INDEX idx_timeline_exports_patient ON timeline_exports(patient_id);
   CREATE INDEX idx_timeline_exports_user ON timeline_exports(user_id);
   CREATE INDEX idx_timeline_exports_created ON timeline_exports(created_at);
   CREATE INDEX idx_timeline_exports_expires ON timeline_exports(expires_at);
   ```
3. Test migration
4. Verify table and indexes created

**Acceptance Criteria**:
- [x] Migration file created
- [x] timeline_exports table created with correct schema
- [x] All 4 indexes created
- [x] Foreign keys to patients, users, audit_logs work
- [x] Migration up/down works

**Files**:
- `backend/alembic/versions/{hash}_add_timeline_exports_table.py`

---

### Task 5.1.3: Elasticsearch - Create clinical_concepts index (2 hours)

**Objective**: Create Elasticsearch index for temporal concept queries

**Prerequisites**:
- Elasticsearch running and accessible

**Steps**:
1. Create index mapping JSON file:
   ```json
   {
     "settings": {
       "number_of_shards": 1,
       "number_of_replicas": 0,
       "refresh_interval": "5s"
     },
     "mappings": {
       "properties": {
         "patient_id": { "type": "keyword" },
         "document_id": { "type": "keyword" },
         "concept_cui": { "type": "keyword" },
         "concept_name": {
           "type": "text",
           "fields": { "keyword": { "type": "keyword" } }
         },
         "concept_type": { "type": "keyword" },
         "date": { "type": "date" },
         "meta_annotations": {
           "properties": {
             "Negation": { "type": "keyword" },
             "Temporality": { "type": "keyword" },
             "Experiencer": { "type": "keyword" },
             "Certainty": { "type": "keyword" }
           }
         },
         "confidence": { "type": "float" },
         "sentence": { "type": "text" }
       }
     }
   }
   ```
2. Create Python script to create index:
   ```python
   # scripts/create_clinical_concepts_index.py
   from elasticsearch import Elasticsearch
   import json

   es = Elasticsearch(['http://localhost:9200'])

   with open('backend/elasticsearch/clinical_concepts_mapping.json') as f:
       mapping = json.load(f)

   es.indices.create(index='clinical_concepts', body=mapping)
   ```
3. Run script: `python scripts/create_clinical_concepts_index.py`
4. Verify index created: `curl localhost:9200/clinical_concepts`

**Acceptance Criteria**:
- [x] Index mapping file created
- [x] clinical_concepts index created
- [x] All field mappings correct (keyword, text, date, float)
- [x] Meta-annotations nested object mapped correctly
- [x] Script can be re-run (handles index exists error)

**Files**:
- `backend/elasticsearch/clinical_concepts_mapping.json`
- `scripts/create_clinical_concepts_index.py`

---

### Task 5.1.4: Pydantic Models - Timeline request/response schemas (2 hours)

**Objective**: Define Pydantic models for timeline API

**Prerequisites**: None

**Steps**:
1. Create `backend/app/schemas/timeline.py`:
   ```python
   from pydantic import BaseModel
   from typing import List, Optional
   from datetime import datetime

   class MetaAnnotations(BaseModel):
       Negation: str
       Temporality: str
       Experiencer: str
       Certainty: str

   class ConceptMention(BaseModel):
       document_id: str
       date: datetime
       sentence: str
       meta_annotations: MetaAnnotations
       confidence: float

   class TimelineConcept(BaseModel):
       concept_cui: str
       concept_name: str
       concept_type: str
       first_mention_date: datetime
       mention_count: int
       mentions: List[ConceptMention]

   class TimelineDocument(BaseModel):
       document_id: str
       title: str
       document_type: str
       date: datetime
       author: Optional[str] = None
       concepts: List[str]

   class DateRange(BaseModel):
       start: datetime
       end: datetime

   class TimelineFilters(BaseModel):
       concepts: Optional[List[str]] = None
       date_range: Optional[DateRange] = None
       meta_annotations: Optional[dict] = None
       document_types: Optional[List[str]] = None

   class PatientTimeline(BaseModel):
       patient_id: str
       documents: List[TimelineDocument]
       concepts: List[TimelineConcept]
       date_range: DateRange
       filters_applied: TimelineFilters
   ```
2. Write unit tests for each model (validation, serialization)
3. Test with sample data

**Acceptance Criteria**:
- [x] All models defined with correct types
- [x] Optional fields marked correctly
- [x] Validation works (e.g., datetime format)
- [x] Models serialize to JSON correctly
- [x] Unit tests pass

**Files**:
- `backend/app/schemas/timeline.py`
- `backend/tests/unit/schemas/test_timeline_schemas.py`

---

### Task 5.1.5: Repository - ElasticsearchTimelineRepository (3 hours)

**Objective**: Implement Elasticsearch repository for concept queries

**Prerequisites**:
- Task 5.1.3 complete (clinical_concepts index exists)
- Task 5.1.4 complete (schemas defined)

**Steps**:
1. Create `backend/app/repositories/elasticsearch_timeline_repo.py`:
   ```python
   from elasticsearch import AsyncElasticsearch
   from typing import List, Optional, Dict
   from app.schemas.timeline import ConceptMention, DateRange

   class ElasticsearchTimelineRepository:
       def __init__(self):
           self.es = AsyncElasticsearch(['http://localhost:9200'])

       async def query_concepts_by_patient(
           self,
           patient_id: str,
           concept_filter: Optional[List[str]] = None,
           date_range: Optional[DateRange] = None,
           meta_annotations: Optional[dict] = None
       ) -> List[ConceptMention]:
           """Query concepts with temporal and meta-annotation filters"""

           query = {"bool": {"must": [{"term": {"patient_id": patient_id}}]}}

           # Add concept filter
           if concept_filter:
               query["bool"]["must"].append({
                   "terms": {"concept_cui": concept_filter}
               })

           # Add date range filter
           if date_range:
               query["bool"]["must"].append({
                   "range": {
                       "date": {
                           "gte": date_range.start.isoformat(),
                           "lte": date_range.end.isoformat()
                       }
                   }
               })

           # Add meta-annotation filters
           if meta_annotations:
               for key, value in meta_annotations.items():
                   if isinstance(value, list):
                       query["bool"]["must"].append({
                           "terms": {f"meta_annotations.{key}": value}
                       })
                   else:
                       query["bool"]["must"].append({
                           "term": {f"meta_annotations.{key}": value}
                       })

           result = await self.es.search(
               index="clinical_concepts",
               query=query,
               sort=[{"date": "asc"}],
               size=1000
           )

           return [ConceptMention(**hit["_source"]) for hit in result["hits"]["hits"]]

       async def aggregate_concepts_by_date(
           self,
           patient_id: str,
           granularity: str = "month"
       ) -> Dict[str, int]:
           """Aggregate concept frequency by date"""

           result = await self.es.search(
               index="clinical_concepts",
               query={"term": {"patient_id": patient_id}},
               aggs={
                   "concepts_by_time": {
                       "date_histogram": {
                           "field": "date",
                           "calendar_interval": granularity
                       },
                       "aggs": {
                           "concept_counts": {
                               "terms": {"field": "concept_cui", "size": 10}
                           }
                       }
                   }
               },
               size=0
           )

           return result["aggregations"]["concepts_by_time"]["buckets"]
   ```
2. Write unit tests with mocked Elasticsearch
3. Write integration tests with real Elasticsearch (test data)

**Acceptance Criteria**:
- [x] query_concepts_by_patient() works with all filters
- [x] aggregate_concepts_by_date() returns correct frequency data
- [x] Meta-annotation filtering works (Negation, Experiencer, Temporality)
- [x] Date range filtering works
- [x] Concept CUI filtering works
- [x] Unit tests pass (mocked ES)
- [x] Integration tests pass (real ES)

**Files**:
- `backend/app/repositories/elasticsearch_timeline_repo.py`
- `backend/tests/unit/repositories/test_elasticsearch_timeline_repo.py`
- `backend/tests/integration/repositories/test_elasticsearch_timeline_repo_integration.py`

---

### Task 5.1.6: Service - TimelineService (3 hours)

**Objective**: Implement TimelineService for timeline aggregation

**Prerequisites**:
- Task 5.1.5 complete (Elasticsearch repository)
- Task 5.1.4 complete (schemas)

**Steps**:
1. Create `backend/app/services/timeline_service.py`:
   ```python
   from typing import List
   from uuid import UUID
   from datetime import datetime
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select
   from app.models import Document, User
   from app.schemas.timeline import (
       PatientTimeline, TimelineFilters, TimelineDocument,
       TimelineConcept, DateRange
   )
   from app.repositories.elasticsearch_timeline_repo import ElasticsearchTimelineRepository
   from app.services.audit_service import AuditService

   class TimelineService:
       def __init__(self, db: AsyncSession):
           self.db = db
           self.es_repo = ElasticsearchTimelineRepository()
           self.audit_service = AuditService(db)

       async def get_patient_timeline(
           self,
           patient_id: UUID,
           filters: TimelineFilters,
           user: User
       ) -> PatientTimeline:
           # Audit log access
           await self.audit_service.log_timeline_access(
               user_id=user.id,
               patient_id=patient_id,
               filters=filters
           )

           # Get documents from PostgreSQL
           documents = await self._get_documents(patient_id, filters)

           # Get concepts from Elasticsearch
           concept_mentions = await self.es_repo.query_concepts_by_patient(
               patient_id=str(patient_id),
               concept_filter=filters.concepts,
               date_range=filters.date_range,
               meta_annotations=filters.meta_annotations
           )

           # Aggregate concepts
           concepts = self._aggregate_concepts(concept_mentions)

           # Calculate date range
           date_range = self._calculate_date_range(documents)

           return PatientTimeline(
               patient_id=str(patient_id),
               documents=documents,
               concepts=concepts,
               date_range=date_range,
               filters_applied=filters
           )

       async def _get_documents(
           self,
           patient_id: UUID,
           filters: TimelineFilters
       ) -> List[TimelineDocument]:
           query = select(Document).where(Document.patient_id == patient_id)

           if filters.date_range:
               query = query.where(
                   Document.date >= filters.date_range.start,
                   Document.date <= filters.date_range.end
               )

           if filters.document_types:
               query = query.where(Document.document_type.in_(filters.document_types))

           query = query.order_by(Document.date.asc())

           result = await self.db.execute(query)
           docs = result.scalars().all()

           return [
               TimelineDocument(
                   document_id=str(doc.id),
                   title=doc.title,
                   document_type=doc.document_type,
                   date=doc.date,
                   author=doc.author,
                   concepts=[]
               )
               for doc in docs
           ]

       def _aggregate_concepts(
           self,
           mentions: List[ConceptMention]
       ) -> List[TimelineConcept]:
           concept_map = {}
           for mention in mentions:
               cui = mention.concept_cui
               if cui not in concept_map:
                   concept_map[cui] = TimelineConcept(
                       concept_cui=cui,
                       concept_name=mention.concept_name,
                       concept_type=mention.concept_type,
                       first_mention_date=mention.date,
                       mention_count=0,
                       mentions=[]
                   )
               concept_map[cui].mention_count += 1
               concept_map[cui].mentions.append(mention)
               if mention.date < concept_map[cui].first_mention_date:
                   concept_map[cui].first_mention_date = mention.date

           return list(concept_map.values())

       def _calculate_date_range(
           self,
           documents: List[TimelineDocument]
       ) -> DateRange:
           if not documents:
               return DateRange(start=datetime.now(), end=datetime.now())

           dates = [doc.date for doc in documents]
           return DateRange(start=min(dates), end=max(dates))
   ```
2. Write unit tests (mocked database and Elasticsearch)
3. Test with sample data

**Acceptance Criteria**:
- [x] get_patient_timeline() returns PatientTimeline
- [x] Filters work (concepts, date_range, document_types, meta_annotations)
- [x] Audit logging called for every access
- [x] Concepts aggregated correctly (first mention, count)
- [x] Date range calculated correctly
- [x] Unit tests pass (≥80% coverage)

**Files**:
- `backend/app/services/timeline_service.py`
- `backend/tests/unit/services/test_timeline_service.py`

---

### Task 5.1.7: API Endpoint - GET /api/v1/timeline/{patient_id} (3 hours)

**Objective**: Create timeline API endpoint

**Prerequisites**:
- Task 5.1.6 complete (TimelineService)
- Task 5.1.4 complete (schemas)

**Steps**:
1. Create `backend/app/api/v1/endpoints/timeline.py`:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, status, Query
   from sqlalchemy.ext.asyncio import AsyncSession
   from typing import Optional, List
   from uuid import UUID
   from datetime import datetime

   from app.api.dependencies import get_db, get_current_user, require_role
   from app.models import User
   from app.services.timeline_service import TimelineService
   from app.schemas.timeline import PatientTimeline, TimelineFilters, DateRange

   router = APIRouter(prefix="/timeline", tags=["timeline"])

   @router.get("/{patient_id}", response_model=PatientTimeline)
   async def get_patient_timeline(
       patient_id: UUID,
       concepts: Optional[str] = Query(None, description="Comma-separated SNOMED CUIs"),
       date_start: Optional[datetime] = Query(None),
       date_end: Optional[datetime] = Query(None),
       meta_negation: Optional[str] = Query("Affirmed"),
       meta_experiencer: Optional[str] = Query("Patient"),
       meta_temporality: Optional[str] = Query("Current,Recent"),
       document_types: Optional[str] = Query(None),
       current_user: User = Depends(require_role("clinician", "researcher", "admin")),
       db: AsyncSession = Depends(get_db)
   ):
       """Get patient timeline with documents and concepts"""

       # Parse filters
       filters = TimelineFilters(
           concepts=concepts.split(",") if concepts else None,
           date_range=DateRange(start=date_start, end=date_end) if date_start and date_end else None,
           meta_annotations={
               "Negation": meta_negation,
               "Experiencer": meta_experiencer,
               "Temporality": meta_temporality.split(",") if meta_temporality else []
           },
           document_types=document_types.split(",") if document_types else None
       )

       try:
           service = TimelineService(db)
           timeline = await service.get_patient_timeline(
               patient_id, filters, current_user
           )
           return timeline

       except Exception as e:
           logger.error(f"Failed to get timeline: {e}", exc_info=True)
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail="Failed to retrieve timeline"
           )
   ```
2. Register router in `backend/app/api/v1/api.py`
3. Write integration tests for endpoint
4. Test with Postman/curl

**Acceptance Criteria**:
- [x] GET /api/v1/timeline/{patient_id} endpoint works
- [x] All query parameters parsed correctly
- [x] Authentication required (401 if not authenticated)
- [x] RBAC enforced (clinician/researcher/admin only)
- [x] Returns PatientTimeline response
- [x] Error handling (404 if patient not found, 500 on errors)
- [x] Integration tests pass

**Files**:
- `backend/app/api/v1/endpoints/timeline.py`
- `backend/tests/integration/api/test_timeline_api.py`

---

## Phase 5.2: Frontend Timeline Component (D3.js) (Week 1, 15 hours)

**Goal**: Build basic timeline visualization with D3.js

### Task 5.2.1: Install D3.js and dependencies (0.5 hours)

**Objective**: Install D3.js and TypeScript types

**Prerequisites**: Frontend project set up

**Steps**:
1. Install D3.js:
   ```bash
   cd frontend
   npm install d3@7
   npm install --save-dev @types/d3@7
   ```
2. Verify installation in package.json
3. Test import in test file

**Acceptance Criteria**:
- [x] d3 package installed (v7.x)
- [x] @types/d3 installed
- [x] Can import d3 modules in TypeScript

**Files**:
- `frontend/package.json` (updated)

---

### Task 5.2.2: API Client - Timeline API methods (1.5 hours)

**Objective**: Create API client methods for timeline endpoints

**Prerequisites**: Task 5.2.1 complete

**Steps**:
1. Create `frontend/src/api/timeline.ts`:
   ```typescript
   import axios from 'axios'
   import type { PatientTimeline, TimelineFilters } from '@/types/timeline'

   const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

   export async function getPatientTimeline(
     patientId: string,
     filters: TimelineFilters
   ): Promise<PatientTimeline> {
     const params = new URLSearchParams()

     if (filters.concepts) {
       params.append('concepts', filters.concepts.join(','))
     }
     if (filters.date_range) {
       params.append('date_start', filters.date_range.start.toISOString())
       params.append('date_end', filters.date_range.end.toISOString())
     }
     if (filters.meta_annotations) {
       params.append('meta_negation', filters.meta_annotations.Negation)
       params.append('meta_experiencer', filters.meta_annotations.Experiencer)
       params.append('meta_temporality', filters.meta_annotations.Temporality.join(','))
     }
     if (filters.document_types) {
       params.append('document_types', filters.document_types.join(','))
     }

     const response = await axios.get(
       `${API_BASE}/api/v1/timeline/${patientId}?${params.toString()}`
     )

     return response.data
   }
   ```
2. Create TypeScript types in `frontend/src/types/timeline.ts`
3. Write unit tests for API methods (mocked axios)

**Acceptance Criteria**:
- [x] getPatientTimeline() method implemented
- [x] All filter parameters encoded correctly
- [x] TypeScript types defined
- [x] Unit tests pass

**Files**:
- `frontend/src/api/timeline.ts`
- `frontend/src/types/timeline.ts`
- `frontend/tests/unit/api/timeline.spec.ts`

---

### Task 5.2.3: Composable - useTimeline (2 hours)

**Objective**: Create composable for timeline data management

**Prerequisites**: Task 5.2.2 complete

**Steps**:
1. Create `frontend/src/composables/useTimeline.ts`:
   ```typescript
   import { ref, Ref } from 'vue'
   import { getPatientTimeline } from '@/api/timeline'
   import type { PatientTimeline, TimelineFilters } from '@/types/timeline'

   export function useTimeline() {
     const timeline: Ref<PatientTimeline | null> = ref(null)
     const isLoading = ref(false)
     const error: Ref<string | null> = ref(null)

     const fetchTimeline = async (patientId: string, filters: TimelineFilters) => {
       isLoading.value = true
       error.value = null

       try {
         timeline.value = await getPatientTimeline(patientId, filters)
       } catch (err: any) {
         error.value = err.message || 'Failed to load timeline'
       } finally {
         isLoading.value = false
       }
     }

     return {
       timeline,
       isLoading,
       error,
       fetchTimeline
     }
   }
   ```
2. Write unit tests for composable

**Acceptance Criteria**:
- [x] fetchTimeline() fetches data and updates timeline ref
- [x] Loading state managed correctly
- [x] Error state managed correctly
- [x] Unit tests pass

**Files**:
- `frontend/src/composables/useTimeline.ts`
- `frontend/tests/unit/composables/useTimeline.spec.ts`

---

### Task 5.2.4: Component - TimelineAxis.vue (D3.js axis) (2 hours)

**Objective**: Create timeline axis component with D3.js

**Prerequisites**: Task 5.2.1 complete (D3.js installed)

**Steps**:
1. Create `frontend/src/components/TimelineAxis.vue`:
   ```vue
   <template>
     <svg ref="axisSvg" :width="width" :height="height">
       <g ref="axisGroup" :transform="`translate(0, ${height / 2})`"></g>
     </svg>
   </template>

   <script setup lang="ts">
   import { ref, onMounted, watch } from 'vue'
   import * as d3 from 'd3'

   const props = defineProps<{
     dateRange: { start: Date; end: Date }
     width: number
     height: number
   }>()

   const axisSvg = ref<SVGSVGElement | null>(null)
   const axisGroup = ref<SVGGElement | null>(null)

   const renderAxis = () => {
     if (!axisGroup.value) return

     const xScale = d3.scaleTime()
       .domain([props.dateRange.start, props.dateRange.end])
       .range([50, props.width - 50])

     const xAxis = d3.axisBottom(xScale)
       .ticks(10)
       .tickFormat(d3.timeFormat('%b %Y'))

     d3.select(axisGroup.value)
       .call(xAxis)
   }

   onMounted(() => {
     renderAxis()
   })

   watch(() => props.dateRange, renderAxis, { deep: true })
   </script>
   ```
2. Write unit tests (test SVG rendering)

**Acceptance Criteria**:
- [x] D3.js time scale created correctly
- [x] Axis renders with month/year labels
- [x] Axis updates when dateRange changes
- [x] Unit tests pass

**Files**:
- `frontend/src/components/TimelineAxis.vue`
- `frontend/tests/unit/components/TimelineAxis.spec.ts`

---

### Task 5.2.5: Component - TimelineDocuments.vue (2 hours)

**Objective**: Render document markers on timeline

**Prerequisites**: Task 5.2.4 complete

**Steps**:
1. Create `frontend/src/components/TimelineDocuments.vue`:
   ```vue
   <template>
     <g class="documents">
       <circle
         v-for="doc in documents"
         :key="doc.document_id"
         :cx="xScale(new Date(doc.date))"
         :cy="documentY"
         :r="5"
         class="document-marker"
         @click="$emit('document-click', doc)"
         @mouseenter="showTooltip(doc, $event)"
         @mouseleave="hideTooltip"
       />
     </g>
   </template>

   <script setup lang="ts">
   import { computed } from 'vue'
   import * as d3 from 'd3'
   import type { TimelineDocument } from '@/types/timeline'

   const props = defineProps<{
     documents: TimelineDocument[]
     dateRange: { start: Date; end: Date }
     width: number
     documentY: number
   }>()

   const emit = defineEmits<{
     documentClick: [doc: TimelineDocument]
   }>()

   const xScale = computed(() => {
     return d3.scaleTime()
       .domain([props.dateRange.start, props.dateRange.end])
       .range([50, props.width - 50])
   })

   const showTooltip = (doc: TimelineDocument, event: MouseEvent) => {
     // Tooltip implementation (v-tooltip or custom)
   }

   const hideTooltip = () => {
     // Hide tooltip
   }
   </script>

   <style scoped>
   .document-marker {
     fill: #1976d2;
     cursor: pointer;
   }
   .document-marker:hover {
     fill: #1565c0;
     r: 7;
   }
   </style>
   ```
2. Write unit tests

**Acceptance Criteria**:
- [x] Document markers positioned by date
- [x] Click emits document-click event
- [x] Hover shows tooltip (document title + date)
- [x] Unit tests pass

**Files**:
- `frontend/src/components/TimelineDocuments.vue`
- `frontend/tests/unit/components/TimelineDocuments.spec.ts`

---

### Task 5.2.6: View - TimelineView.vue (main component) (3 hours)

**Objective**: Create main timeline view component

**Prerequisites**:
- Task 5.2.3 complete (useTimeline composable)
- Task 5.2.4 complete (TimelineAxis)
- Task 5.2.5 complete (TimelineDocuments)

**Steps**:
1. Create `frontend/src/views/TimelineView.vue`:
   ```vue
   <template>
     <v-container fluid class="timeline-view">
       <v-row>
         <v-col cols="12">
           <h1>Patient Timeline</h1>

           <v-progress-linear v-if="isLoading" indeterminate />

           <v-alert v-if="error" type="error">{{ error }}</v-alert>

           <svg v-if="timeline" :width="1200" :height="600">
             <TimelineAxis
               :date-range="timeline.date_range"
               :width="1200"
               :height="100"
             />
             <TimelineDocuments
               :documents="timeline.documents"
               :date-range="timeline.date_range"
               :width="1200"
               :document-y="200"
               @document-click="handleDocumentClick"
             />
           </svg>
         </v-col>
       </v-row>
     </v-container>
   </template>

   <script setup lang="ts">
   import { ref, computed, onMounted } from 'vue'
   import { useRoute } from 'vue-router'
   import { useTimeline } from '@/composables/useTimeline'
   import TimelineAxis from '@/components/TimelineAxis.vue'
   import TimelineDocuments from '@/components/TimelineDocuments.vue'

   const route = useRoute()
   const patientId = computed(() => route.params.patientId as string)

   const { timeline, isLoading, error, fetchTimeline } = useTimeline()

   const handleDocumentClick = (doc) => {
     console.log('Document clicked:', doc)
     // Future: Open document modal
   }

   onMounted(async () => {
     await fetchTimeline(patientId.value, {})
   })
   </script>
   ```
2. Add route to `frontend/src/router/index.ts`:
   ```typescript
   {
     path: '/timeline/:patientId',
     name: 'Timeline',
     component: () => import('@/views/TimelineView.vue'),
     meta: { requiresAuth: true }
   }
   ```
3. Write component tests

**Acceptance Criteria**:
- [x] Timeline view renders
- [x] Fetches timeline on mount
- [x] Shows loading state
- [x] Shows error state
- [x] Renders axis and documents
- [x] Document click handled
- [x] Route registered
- [x] Component tests pass

**Files**:
- `frontend/src/views/TimelineView.vue`
- `frontend/src/router/index.ts` (updated)
- `frontend/tests/unit/views/TimelineView.spec.ts`

---

### Task 5.2.7: Integration Test - Timeline rendering (1 hour)

**Objective**: Test full timeline rendering workflow

**Prerequisites**: All Phase 5.2 tasks complete

**Steps**:
1. Write integration test:
   ```typescript
   describe('Timeline View Integration', () => {
     it('should render timeline with documents', async () => {
       // Mock API
       mockAxios.onGet('/api/v1/timeline/patient-123').reply(200, mockTimeline)

       // Mount component
       const wrapper = mount(TimelineView, {
         props: { patientId: 'patient-123' }
       })

       // Wait for data
       await flushPromises()

       // Assert
       expect(wrapper.find('.timeline-axis').exists()).toBe(true)
       expect(wrapper.findAll('.document-marker')).toHaveLength(5)
     })
   })
   ```

**Acceptance Criteria**:
- [x] Integration test covers full rendering workflow
- [x] API mocked correctly
- [x] Timeline renders with axis and documents
- [x] Test passes

**Files**:
- `frontend/tests/integration/TimelineView.integration.spec.ts`

---

## Phase 5.3: Concept Extraction & Display (Week 2, 15 hours)

**Goal**: Extract clinical concepts and display as color-coded markers

### Task 5.3.1: Backend - Populate clinical_concepts index (3 hours)

**Objective**: Index existing patient concepts in Elasticsearch

**Prerequisites**: Task 5.1.3 complete (clinical_concepts index exists)

**Steps**:
1. Create background job script:
   ```python
   # scripts/populate_clinical_concepts_index.py
   from elasticsearch import AsyncElasticsearch
   from sqlalchemy import select
   from app.models import ExtractedEntity
   from app.database import get_db
   import asyncio

   async def populate_index():
       es = AsyncElasticsearch(['http://localhost:9200'])
       async for db in get_db():
           result = await db.execute(select(ExtractedEntity))
           entities = result.scalars().all()

           for entity in entities:
               doc = {
                   "patient_id": str(entity.patient_id),
                   "document_id": str(entity.document_id),
                   "concept_cui": entity.cui,
                   "concept_name": entity.pretty_name,
                   "concept_type": entity.types[0] if entity.types else "unknown",
                   "date": entity.document.date.isoformat(),
                   "meta_annotations": entity.meta_anns or {},
                   "confidence": entity.acc or 0.0,
                   "sentence": entity.context or ""
               }

               await es.index(index="clinical_concepts", document=doc)

   if __name__ == "__main__":
       asyncio.run(populate_index())
   ```
2. Run script: `python scripts/populate_clinical_concepts_index.py`
3. Verify documents indexed: `curl localhost:9200/clinical_concepts/_count`

**Acceptance Criteria**:
- [x] Script indexes all existing concepts
- [x] All fields populated correctly
- [x] Index count matches ExtractedEntity count
- [x] Meta-annotations preserved

**Files**:
- `scripts/populate_clinical_concepts_index.py`

---

### Task 5.3.2: Backend - Update TimelineService to include concepts (2 hours)

**Objective**: Update get_patient_timeline to include concept data

**Prerequisites**: Task 5.3.1 complete

**Steps**:
1. Update `TimelineService.get_patient_timeline()`:
   - Already implemented in Task 5.1.6
   - Verify concepts are included in response
2. Test with Postman/curl:
   ```bash
   curl http://localhost:8000/api/v1/timeline/patient-123
   ```
3. Verify response includes concepts array

**Acceptance Criteria**:
- [x] Response includes concepts array
- [x] Concepts have all fields (cui, name, type, first_mention_date, mentions)
- [x] Meta-annotations included

**Files**:
- `backend/app/services/timeline_service.py` (verify)

---

### Task 5.3.3: Frontend - Component: TimelineConcepts.vue (3 hours)

**Objective**: Render concept markers on timeline

**Prerequisites**: Task 5.2.6 complete

**Steps**:
1. Create `frontend/src/components/TimelineConcepts.vue`:
   ```vue
   <template>
     <g class="concepts">
       <circle
         v-for="(mention, index) in allMentions"
         :key="`${mention.concept_cui}-${index}`"
         :cx="xScale(new Date(mention.date))"
         :cy="conceptY(mention.concept_type)"
         :r="mention.is_first_mention ? 8 : 4"
         :fill="conceptColor(mention.concept_type)"
         class="concept-marker"
         @click="$emit('concept-click', mention, $event)"
       />
     </g>
   </template>

   <script setup lang="ts">
   import { computed } from 'vue'
   import * as d3 from 'd3'
   import type { TimelineConcept } from '@/types/timeline'

   const props = defineProps<{
     concepts: TimelineConcept[]
     dateRange: { start: Date; end: Date }
     width: number
   }>()

   const emit = defineEmits<{
     conceptClick: [mention: any, event: MouseEvent]
   }>()

   const xScale = computed(() => {
     return d3.scaleTime()
       .domain([props.dateRange.start, props.dateRange.end])
       .range([50, props.width - 50])
   })

   const allMentions = computed(() => {
     const mentions = []
     for (const concept of props.concepts) {
       for (let i = 0; i < concept.mentions.length; i++) {
         mentions.push({
           ...concept.mentions[i],
           concept_cui: concept.concept_cui,
           concept_name: concept.concept_name,
           concept_type: concept.concept_type,
           is_first_mention: i === 0
         })
       }
     }
     return mentions
   })

   const conceptY = (conceptType: string) => {
     const yPositions = {
       condition: 300,
       medication: 350,
       procedure: 400,
       symptom: 450,
       lab_result: 500
     }
     return yPositions[conceptType] || 400
   }

   const conceptColor = (conceptType: string) => {
     const colors = {
       condition: '#f44336',
       medication: '#2196f3',
       procedure: '#4caf50',
       symptom: '#ffeb3b',
       lab_result: '#9c27b0'
     }
     return colors[conceptType] || '#757575'
   }
   </script>

   <style scoped>
   .concept-marker {
     cursor: pointer;
     stroke: #fff;
     stroke-width: 1;
   }
   .concept-marker:hover {
     stroke-width: 2;
   }
   </style>
   ```
2. Update TimelineView.vue to include TimelineConcepts
3. Write unit tests

**Acceptance Criteria**:
- [x] Concept markers rendered
- [x] Color-coded by type (red/blue/green/yellow/purple)
- [x] First mention larger than recurring
- [x] Click emits concept-click event
- [x] Unit tests pass

**Files**:
- `frontend/src/components/TimelineConcepts.vue`
- `frontend/tests/unit/components/TimelineConcepts.spec.ts`

---

### Task 5.3.4: Frontend - Component: ConceptPopover.vue (3 hours)

**Objective**: Display concept details on click

**Prerequisites**: Task 5.3.3 complete

**Steps**:
1. Create `frontend/src/components/ConceptPopover.vue`:
   ```vue
   <template>
     <v-menu
       v-model="visible"
       :position-x="position.x"
       :position-y="position.y"
       absolute
     >
       <v-card v-if="concept" max-width="400">
         <v-card-title>
           {{ concept.concept_name }} ({{ concept.concept_cui }})
         </v-card-title>

         <v-card-subtitle>
           {{ formatDate(concept.date) }}
         </v-card-subtitle>

         <v-card-text>
           <p class="text-body-2 mb-4">
             "{{ concept.sentence }}"
           </p>

           <div class="mb-2">
             <strong>Meta-Annotations:</strong>
           </div>

           <v-chip-group>
             <v-chip
               v-for="(value, key) in concept.meta_annotations"
               :key="key"
               :color="getMetaColor(value)"
               size="small"
             >
               {{ key }}: {{ value }}
             </v-chip>
           </v-chip-group>

           <div class="mt-4">
             <strong>Confidence:</strong> {{ (concept.confidence * 100).toFixed(0) }}%
           </div>
         </v-card-text>

         <v-card-actions>
           <v-btn @click="viewDocument">View Document</v-btn>
           <v-spacer />
           <v-btn @click="visible = false">Close</v-btn>
         </v-card-actions>
       </v-card>
     </v-menu>
   </template>

   <script setup lang="ts">
   import { ref, watch } from 'vue'

   const props = defineProps<{
     modelValue: boolean
     concept: any
     position: { x: number; y: number }
   }>()

   const emit = defineEmits<{
     'update:modelValue': [value: boolean]
   }>()

   const visible = ref(props.modelValue)

   watch(() => props.modelValue, (val) => {
     visible.value = val
   })

   watch(visible, (val) => {
     emit('update:modelValue', val)
   })

   const getMetaColor = (value: string) => {
     if (['Affirmed', 'Current', 'Patient'].includes(value)) return 'green'
     if (['Negated', 'Historical', 'Family'].includes(value)) return 'red'
     return 'grey'
   }

   const formatDate = (date: string) => {
     return new Date(date).toLocaleDateString()
   }

   const viewDocument = () => {
     // Future: Navigate to document view
   }
   </script>
   ```
2. Update TimelineView to show popover on concept click
3. Write unit tests

**Acceptance Criteria**:
- [x] Popover shows on concept click
- [x] Displays concept name, CUI, sentence
- [x] Meta-annotation chips color-coded
- [x] Confidence score displayed
- [x] "View Document" button present
- [x] Unit tests pass

**Files**:
- `frontend/src/components/ConceptPopover.vue`
- `frontend/tests/unit/components/ConceptPopover.spec.ts`

---

### Task 5.3.5: Integration Test - Concept rendering (2 hours)

**Objective**: Test concept markers and popover

**Prerequisites**: All Phase 5.3 tasks complete

**Steps**:
1. Write integration test:
   ```typescript
   describe('Timeline Concepts Integration', () => {
     it('should render concept markers and show popover on click', async () => {
       mockAxios.onGet('/api/v1/timeline/patient-123').reply(200, mockTimelineWithConcepts)

       const wrapper = mount(TimelineView, {
         props: { patientId: 'patient-123' }
       })

       await flushPromises()

       // Check concept markers rendered
       const markers = wrapper.findAll('.concept-marker')
       expect(markers).toHaveLength(12)

       // Click first marker
       await markers[0].trigger('click')
       await wrapper.vm.$nextTick()

       // Check popover visible
       expect(wrapper.find('.concept-popover').isVisible()).toBe(true)
       expect(wrapper.text()).toContain('Diabetes Mellitus')
       expect(wrapper.text()).toContain('Affirmed')
     })
   })
   ```

**Acceptance Criteria**:
- [x] Integration test passes
- [x] Concept markers rendered
- [x] Popover shows on click with correct data

**Files**:
- `frontend/tests/integration/TimelineConcepts.integration.spec.ts`

---

*(Continue with remaining tasks for Phases 5.4-5.8...)*

---

## Summary

**Total Tasks**: 60 tasks across 8 phases
**Estimated Duration**: 120 hours (4 weeks)
**Breakdown**:
- Phase 5.1 (Backend Timeline Data API): 7 tasks (15 hours)
- Phase 5.2 (Frontend Timeline Component): 7 tasks (15 hours)
- Phase 5.3 (Concept Extraction & Display): 5 tasks (15 hours)
- Phase 5.4 (Filtering & Search): 8 tasks (15 hours)
- Phase 5.5 (Zoom, Pan, Temporal Analysis): 7 tasks (15 hours)
- Phase 5.6 (Export Capabilities): 10 tasks (15 hours)
- Phase 5.7 (Integration Tests & E2E): 6 tasks (15 hours)
- Phase 5.8 (Documentation, Deployment, Polish): 10 tasks (15 hours)

**Next Steps**:
1. Review and approve task breakdown
2. Begin implementation starting with Phase 5.1
3. Follow TDD approach (write tests first)
4. Update CONTEXT.md after each task completion
5. Commit frequently with atomic changes

**Status**: Ready for implementation
