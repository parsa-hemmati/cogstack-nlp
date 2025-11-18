# Tasks: Patient Search & Discovery

**Version**: 1.0.0
**Status**: Ready for Implementation
**Created**: 2025-11-18
**Technical Plan**: [patient-search-plan.md](../plans/patient-search-plan.md)

---

## Task Summary

**Total Tasks**: 8
**Estimated Time**: 4-6 hours
**Test Coverage Target**: 90%+

**Breakdown**:
- Phase 4.1: Database Indexes (30 min)
- Phase 4.2: Backend Search API (1.5 hours)
- Phase 4.3: Backend Highlights API (1 hour)
- Phase 4.4: Frontend Search Component (2 hours)
- Phase 4.5: Frontend Highlights Panel (1 hour)
- Phase 4.6: Search History (45 min)
- Phase 4.7: Integration Tests (1 hour)
- Phase 4.8: Documentation & Deployment (30 min)

---

## Phase 4.1: Database Indexes

### Task 4.1: Add Patient Search Indexes

**Goal**: Optimize PostgreSQL for search queries

**Prerequisites**: Phase 3 complete (extracted_entities table exists)

**Steps**:
1. Create migration file: `backend/alembic/versions/006_add_patient_search_indexes.py`
2. Add composite index:
   ```sql
   CREATE INDEX idx_entities_cui_meta
   ON extracted_entities (cui, (meta_anns->>'Negation'), (meta_anns->>'Temporality'), (meta_anns->>'Experiencer'));
   ```
3. Add GIN index for flexible JSON filtering:
   ```sql
   CREATE INDEX idx_entities_meta_anns_gin
   ON extracted_entities USING GIN (meta_anns);
   ```
4. Add patient and document lookup indexes:
   ```sql
   CREATE INDEX idx_entities_patient_id ON extracted_entities (patient_id);
   CREATE INDEX idx_entities_document_id ON extracted_entities (document_id);
   ```
5. Run migration: `docker-compose exec backend alembic upgrade head`
6. Verify indexes created: `\d+ extracted_entities` in psql
7. Benchmark query performance (before/after)

**Acceptance**:
- ✅ Migration runs without errors
- ✅ All 4 indexes created
- ✅ Query time <50ms for 10,000 patients (measure with EXPLAIN ANALYZE)
- ✅ Index usage confirmed in query plan

**Estimated Time**: 30 minutes

---

## Phase 4.2: Backend Search API

### Task 4.2.1: Create Pydantic Schemas

**Goal**: Define request/response schemas for search API

**Prerequisites**: None

**Steps**:
1. Create `backend/app/schemas/patient_search.py`
2. Define `MetaAnnotationFilters`:
   ```python
   class MetaAnnotationFilters(BaseModel):
       negation: Optional[str] = "Affirmed"  # Affirmed | Negated | Any
       temporality: Optional[str] = "Current"  # Current | Historical | Any
       experiencer: Optional[str] = "Patient"  # Patient | Family | Other | Any
       certainty: Optional[str] = None  # Confirmed | Suspected | Any
   ```
3. Define `PatientSearchRequest`:
   ```python
   class PatientSearchRequest(BaseModel):
       query: str = Field(..., min_length=1, max_length=200)
       filters: MetaAnnotationFilters = MetaAnnotationFilters()
       sort_by: str = "relevance"  # relevance | name | last_updated
       page: int = Field(1, ge=1)
       page_size: int = Field(20, ge=1, le=100)
   ```
4. Define `PatientSearchResult`:
   ```python
   class PatientSearchResult(BaseModel):
       patient_id: UUID
       nhs_number: str  # Masked: XXX-XXX-1234
       full_name: str
       date_of_birth: date
       age: int
       document_count: int
       concept_document_count: int
       last_updated: datetime
   ```
5. Define `PatientSearchResponse`:
   ```python
   class PatientSearchResponse(BaseModel):
       results: List[PatientSearchResult]
       total_count: int
       page: int
       page_size: int
       query_time_ms: int
   ```

**Acceptance**:
- ✅ All schemas defined with proper validation
- ✅ Pydantic validation works (test with invalid data)
- ✅ Type hints complete

**Estimated Time**: 15 minutes

---

### Task 4.2.2: Create Patient Search Service

**Goal**: Implement business logic for patient search

**Prerequisites**: Task 4.1 complete (indexes exist)

**Steps**:
1. Create `backend/app/services/patient_search_service.py`
2. Implement `PatientSearchService` class:
   ```python
   class PatientSearchService:
       def __init__(self, db: AsyncSession):
           self.db = db

       async def search(
           self,
           query: str,
           filters: MetaAnnotationFilters,
           page: int,
           page_size: int,
           sort_by: str
       ) -> PatientSearchResponse:
           # 1. Parse query (extract CUI if concept name provided)
           # 2. Build SQL query with meta-annotation filters
           # 3. Execute query
           # 4. Rank results
           # 5. Paginate
           # 6. Return response
           pass
   ```
3. Implement `_build_query()` method:
   - Start with base query: JOIN extracted_entities + patients
   - Add WHERE clause for CUI or pretty_name ILIKE query
   - Add meta-annotation filters (if not "Any")
   - Add GROUP BY patient_id
   - Add ORDER BY (relevance = concept_document_count DESC)
4. Implement `_mask_nhs_number()` helper:
   ```python
   def _mask_nhs_number(nhs_number: str) -> str:
       # "123-456-7890" → "XXX-XXX-7890"
       return "XXX-XXX-" + nhs_number[-4:]
   ```
5. Write 12 unit tests:
   - Test filter combinations
   - Test pagination
   - Test sorting
   - Test empty results
   - Test NHS number masking

**Acceptance**:
- ✅ Search returns results for valid queries
- ✅ Filters work correctly (negation, temporality, experiencer)
- ✅ Pagination works (page 1, page 2, etc.)
- ✅ NHS numbers masked in results
- ✅ 12 unit tests passing
- ✅ Query time <500ms for 10,000 patients

**Estimated Time**: 1 hour

---

### Task 4.2.3: Create Search API Endpoint

**Goal**: Expose search API via FastAPI router

**Prerequisites**: Task 4.2.2 complete (service implemented)

**Steps**:
1. Create `backend/app/routers/patient_search.py`
2. Implement endpoint:
   ```python
   @router.post("/search", response_model=PatientSearchResponse)
   @require_role("clinician", "researcher", "admin")
   async def search_patients(
       request: PatientSearchRequest,
       current_user: User = Depends(get_current_user),
       db: AsyncSession = Depends(get_db)
   ):
       # 1. Validate input (Pydantic handles this)
       # 2. Create service instance
       # 3. Execute search
       # 4. Log audit trail
       # 5. Return response
       pass
   ```
3. Add audit logging:
   ```python
   await audit_service.log(
       user_id=current_user.id,
       action="SEARCH_PATIENTS",
       resource_type="patient",
       details={
           "query": request.query,
           "filters": request.filters.dict(),
           "result_count": response.total_count
       }
   )
   ```
4. Add error handling (400, 401, 403, 500)
5. Register router in `backend/app/main.py`:
   ```python
   app.include_router(patient_search_router, prefix="/api/v1/patients", tags=["patients"])
   ```
6. Write 5 integration tests:
   - Test successful search
   - Test authentication required (401)
   - Test authorization (403 for wrong role)
   - Test validation errors (400)
   - Test audit logging

**Acceptance**:
- ✅ Endpoint accessible at POST /api/v1/patients/search
- ✅ Authentication required (JWT token)
- ✅ Authorization enforced (clinician, researcher, admin roles)
- ✅ Audit log created for each search
- ✅ 5 integration tests passing
- ✅ OpenAPI docs auto-generated

**Estimated Time**: 30 minutes

---

## Phase 4.3: Backend Highlights API

### Task 4.3: Create Concept Highlights Endpoint

**Goal**: Retrieve documents containing specific concept for a patient

**Prerequisites**: Task 4.2 complete (search API working)

**Steps**:
1. Add schemas to `backend/app/schemas/patient_search.py`:
   ```python
   class MetaAnnotationDisplay(BaseModel):
       Negation: str
       Temporality: str
       Experiencer: str
       Certainty: str

   class DocumentHighlight(BaseModel):
       document_id: UUID
       title: str
       date: date
       snippet: str  # 100 chars before + concept + 100 chars after
       meta_annotations: MetaAnnotationDisplay
       start_char: int
       end_char: int

   class ConceptHighlightResponse(BaseModel):
       documents: List[DocumentHighlight]
       total_count: int
   ```

2. Add method to `PatientSearchService`:
   ```python
   async def get_concept_highlights(
       self,
       patient_id: UUID,
       cui: str,
       filters: Optional[MetaAnnotationFilters] = None
   ) -> ConceptHighlightResponse:
       # 1. Query extracted_entities for patient + CUI
       # 2. Join with documents table
       # 3. Decrypt document content
       # 4. Extract snippet (100 chars before/after concept)
       # 5. Return highlights
       pass
   ```

3. Implement `_extract_snippet()` helper:
   ```python
   def _extract_snippet(text: str, start_char: int, end_char: int) -> str:
       # Extract 100 chars before, concept, 100 chars after
       # Handle edge cases (concept at start/end of document)
       snippet_start = max(0, start_char - 100)
       snippet_end = min(len(text), end_char + 100)
       snippet = text[snippet_start:snippet_end]

       # Bold the concept
       concept_start = start_char - snippet_start
       concept_end = end_char - snippet_start
       snippet = (
           snippet[:concept_start] +
           f"<b>{snippet[concept_start:concept_end]}</b>" +
           snippet[concept_end:]
       )
       return snippet
   ```

4. Create endpoint in `backend/app/routers/patient_search.py`:
   ```python
   @router.get("/{patient_id}/concept-highlights", response_model=ConceptHighlightResponse)
   @require_role("clinician", "researcher", "admin")
   async def get_concept_highlights(
       patient_id: UUID,
       cui: str = Query(...),
       filters: Optional[str] = None,  # JSON string
       current_user: User = Depends(get_current_user),
       db: AsyncSession = Depends(get_db)
   ):
       # 1. Validate patient exists
       # 2. Check user has access to patient
       # 3. Get highlights
       # 4. Log audit trail (VIEWED_DOCUMENT)
       # 5. Return response
       pass
   ```

5. Write 8 unit tests:
   - Test snippet extraction (normal case)
   - Test snippet extraction (concept at start)
   - Test snippet extraction (concept at end)
   - Test meta-annotations display
   - Test empty results
   - Test audit logging
   - Test authorization

**Acceptance**:
- ✅ Endpoint returns highlights within 300ms
- ✅ Snippets show context (100 chars before/after)
- ✅ Concept bolded in snippet
- ✅ Meta-annotations displayed correctly
- ✅ Audit log created for document views
- ✅ 8 unit tests passing

**Estimated Time**: 1 hour

---

## Phase 4.4: Frontend Search Component

### Task 4.4.1: Create Search Composable

**Goal**: Reusable search logic (Composition API)

**Prerequisites**: None

**Steps**:
1. Create `frontend/src/composables/usePatientSearch.ts`:
   ```typescript
   export function usePatientSearch() {
     const results = ref<PatientSearchResult[]>([])
     const totalCount = ref(0)
     const isLoading = ref(false)
     const error = ref<string | null>(null)
     const queryTimems = ref(0)

     const search = async (
       query: string,
       filters: MetaAnnotationFilters,
       page: number,
       pageSize: number
     ) => {
       isLoading.value = true
       error.value = null

       try {
         const response = await patientSearchApi.search({
           query,
           filters,
           page,
           page_size: pageSize
         })
         results.value = response.results
         totalCount.value = response.total_count
         queryTimeMs.value = response.query_time_ms
       } catch (err: any) {
         error.value = err.message
       } finally {
         isLoading.value = false
       }
     }

     return { results, totalCount, isLoading, error, queryTimeMs, search }
   }
   ```

2. Write 5 unit tests (`tests/unit/composables/usePatientSearch.test.ts`):
   - Test successful search
   - Test error handling
   - Test loading states
   - Test state updates

**Acceptance**:
- ✅ Composable manages state correctly
- ✅ API integration works
- ✅ Error handling functional
- ✅ 5 unit tests passing

**Estimated Time**: 30 minutes

---

### Task 4.4.2: Create API Client

**Goal**: TypeScript API client for patient search

**Prerequisites**: None

**Steps**:
1. Create `frontend/src/api/patientSearch.ts`:
   ```typescript
   export interface MetaAnnotationFilters {
     negation?: string
     temporality?: string
     experiencer?: string
     certainty?: string
   }

   export interface PatientSearchRequest {
     query: string
     filters?: MetaAnnotationFilters
     sort_by?: string
     page?: number
     page_size?: number
   }

   export interface PatientSearchResult {
     patient_id: string
     nhs_number: string
     full_name: string
     date_of_birth: string
     age: number
     document_count: number
     concept_document_count: number
     last_updated: string
   }

   export interface PatientSearchResponse {
     results: PatientSearchResult[]
     total_count: number
     page: number
     page_size: number
     query_time_ms: number
   }

   export const patientSearchApi = {
     async search(request: PatientSearchRequest): Promise<PatientSearchResponse> {
       const response = await api.post('/patients/search', request)
       return response.data
     },

     async getConceptHighlights(
       patientId: string,
       cui: string,
       filters?: MetaAnnotationFilters
     ): Promise<ConceptHighlightResponse> {
       const response = await api.get(`/patients/${patientId}/concept-highlights`, {
         params: { cui, filters: JSON.stringify(filters) }
       })
       return response.data
     }
   }
   ```

**Acceptance**:
- ✅ API client defined with proper types
- ✅ Methods match backend endpoints
- ✅ Type safety enforced

**Estimated Time**: 15 minutes

---

### Task 4.4.3: Create Search UI Component

**Goal**: Patient search interface

**Prerequisites**: Task 4.4.1 and 4.4.2 complete

**Steps**:
1. Create `frontend/src/components/PatientSearch.vue`:
   ```vue
   <template>
     <v-container>
       <v-row>
         <v-col cols="12">
           <h1>Patient Search</h1>
         </v-col>
       </v-row>

       <!-- Search Box -->
       <v-row>
         <v-col cols="12" md="8">
           <v-text-field
             v-model="query"
             label="Search by condition or concept"
             placeholder="e.g., atrial flutter, diabetes"
             @keydown.enter="handleSearch"
             :loading="isLoading"
             clearable
           />
         </v-col>
         <v-col cols="12" md="4">
           <v-btn
             color="primary"
             @click="handleSearch"
             :loading="isLoading"
             :disabled="!query"
             block
           >
             Search
           </v-btn>
         </v-col>
       </v-row>

       <!-- Filters -->
       <v-row>
         <v-col cols="12">
           <v-chip-group v-model="filters" multiple>
             <v-chip filter outlined>
               Negation: {{ filters.negation }}
             </v-chip>
             <v-chip filter outlined>
               Temporality: {{ filters.temporality }}
             </v-chip>
             <v-chip filter outlined>
               Experiencer: {{ filters.experiencer }}
             </v-chip>
           </v-chip-group>
         </v-col>
       </v-row>

       <!-- Results -->
       <v-row>
         <v-col cols="12">
           <v-data-table
             :items="results"
             :headers="headers"
             :loading="isLoading"
             :items-per-page="pageSize"
             hide-default-footer
           >
             <template #item.nhs_number="{ item }">
               {{ item.nhs_number }}
             </template>
             <template #item.concept_document_count="{ item }">
               <v-btn text color="primary">
                 {{ item.concept_document_count }} documents
               </v-btn>
             </template>
           </v-data-table>
         </v-col>
       </v-row>

       <!-- Pagination -->
       <v-row>
         <v-col cols="12">
           <v-pagination
             v-model="page"
             :length="Math.ceil(totalCount / pageSize)"
             @input="handlePageChange"
           />
         </v-col>
       </v-row>
     </v-container>
   </template>

   <script setup lang="ts">
   import { ref } from 'vue'
   import { usePatientSearch } from '@/composables/usePatientSearch'

   const query = ref('')
   const filters = ref({
     negation: 'Affirmed',
     temporality: 'Current',
     experiencer: 'Patient'
   })
   const page = ref(1)
   const pageSize = ref(20)

   const {
     results,
     totalCount,
     isLoading,
     error,
     search
   } = usePatientSearch()

   const handleSearch = async () => {
     await search(query.value, filters.value, page.value, pageSize.value)
   }

   const handlePageChange = async (newPage: number) => {
     page.value = newPage
     await search(query.value, filters.value, page.value, pageSize.value)
   }

   const headers = [
     { title: 'Name', value: 'full_name' },
     { title: 'NHS Number', value: 'nhs_number' },
     { title: 'Date of Birth', value: 'date_of_birth' },
     { title: 'Age', value: 'age' },
     { title: 'Documents', value: 'concept_document_count' }
   ]
   </script>
   ```

2. Add route in `frontend/src/router/index.ts`:
   ```typescript
   {
     path: '/patients/search',
     name: 'PatientSearch',
     component: () => import('@/components/PatientSearch.vue'),
     meta: { requiresAuth: true }
   }
   ```

3. Add navigation link in `frontend/src/App.vue`:
   ```vue
   <v-list-item to="/patients/search">
     <v-list-item-title>Patient Search</v-list-item-title>
   </v-list-item>
   ```

**Acceptance**:
- ✅ Search box functional
- ✅ Filters work (3 meta-annotations)
- ✅ Results displayed in table
- ✅ Pagination works
- ✅ Loading spinner shown during search
- ✅ Error messages displayed

**Estimated Time**: 1 hour 15 minutes

---

## Phase 4.5: Frontend Highlights Panel

### Task 4.5: Create Document Highlights Component

**Goal**: Expandable highlights panel with document modal

**Prerequisites**: Task 4.4.3 complete (search UI working)

**Steps**:
1. Update `PatientSearch.vue` to add expandable rows:
   ```vue
   <v-data-table
     :items="results"
     :headers="headers"
     show-expand
   >
     <template #expanded-item="{ item }">
       <DocumentHighlights
         :patient-id="item.patient_id"
         :cui="extractedCUI"
         :filters="filters"
       />
     </template>
   </v-data-table>
   ```

2. Create `frontend/src/components/DocumentHighlights.vue`:
   ```vue
   <template>
     <v-container>
       <v-row>
         <v-col cols="12">
           <v-list v-if="!loading">
             <v-list-item
               v-for="doc in documents"
               :key="doc.document_id"
               @click="openDocument(doc.document_id)"
             >
               <v-list-item-title>{{ doc.title }}</v-list-item-title>
               <v-list-item-subtitle>{{ doc.date }}</v-list-item-subtitle>
               <v-list-item-subtitle v-html="doc.snippet" />
               <v-chip-group>
                 <v-chip :color="getMetaColor(doc.meta_annotations.Negation)">
                   {{ doc.meta_annotations.Negation }}
                 </v-chip>
                 <v-chip :color="getMetaColor(doc.meta_annotations.Temporality)">
                   {{ doc.meta_annotations.Temporality }}
                 </v-chip>
                 <v-chip :color="getMetaColor(doc.meta_annotations.Experiencer)">
                   {{ doc.meta_annotations.Experiencer }}
                 </v-chip>
               </v-chip-group>
             </v-list-item>
           </v-list>
           <v-progress-circular v-else indeterminate />
         </v-col>
       </v-row>
     </v-container>
   </template>

   <script setup lang="ts">
   import { ref, onMounted } from 'vue'
   import { patientSearchApi } from '@/api/patientSearch'

   const props = defineProps<{
     patientId: string
     cui: string
     filters: MetaAnnotationFilters
   }>()

   const documents = ref([])
   const loading = ref(false)

   onMounted(async () => {
     loading.value = true
     const response = await patientSearchApi.getConceptHighlights(
       props.patientId,
       props.cui,
       props.filters
     )
     documents.value = response.documents
     loading.value = false
   })

   const getMetaColor = (value: string) => {
     if (value === 'Affirmed' || value === 'Current' || value === 'Patient') return 'green'
     if (value === 'Negated' || value === 'Historical' || value === 'Family') return 'red'
     return 'grey'
   }
   </script>
   ```

3. Create `frontend/src/components/DocumentModal.vue`:
   ```vue
   <template>
     <v-dialog v-model="visible" max-width="800">
       <v-card>
         <v-card-title>{{ document.title }}</v-card-title>
         <v-card-text>
           <div v-html="document.content" />
         </v-card-text>
         <v-card-actions>
           <v-btn @click="visible = false">Close</v-btn>
         </v-card-actions>
       </v-card>
     </v-dialog>
   </template>

   <script setup lang="ts">
   import { ref } from 'vue'

   const props = defineProps<{
     documentId: string
   }>()

   const visible = ref(false)
   const document = ref<any>(null)

   const openDocument = async () => {
     // Fetch document content from API
     visible.value = true
   }
   </script>
   ```

**Acceptance**:
- ✅ Expandable rows work
- ✅ Highlights displayed correctly
- ✅ Meta-annotations color-coded (green=Affirmed, red=Negated)
- ✅ Snippet shows concept bolded
- ✅ Modal opens with full document
- ✅ Loading states handled

**Estimated Time**: 1 hour

---

## Phase 4.6: Search History

### Task 4.6: Implement Search History (Redis Cache)

**Goal**: Track recent searches per user

**Prerequisites**: Task 4.2.3 complete (search API working)

**Steps**:
1. Update `PatientSearchService` to save search history:
   ```python
   async def save_search_history(
       self,
       user_id: UUID,
       query: str,
       filters: MetaAnnotationFilters
   ):
       # Save to Redis LIST (max 10 items)
       key = f"search_history:{user_id}"
       history_item = {
           "query": query,
           "filters": filters.dict(),
           "timestamp": datetime.utcnow().isoformat()
       }

       # LPUSH to add to front, LTRIM to keep last 10
       await redis.lpush(key, json.dumps(history_item))
       await redis.ltrim(key, 0, 9)
       await redis.expire(key, 604800)  # 7 days TTL
   ```

2. Add `get_search_history()` method:
   ```python
   async def get_search_history(self, user_id: UUID) -> List[dict]:
       key = f"search_history:{user_id}"
       history = await redis.lrange(key, 0, 9)
       return [json.loads(item) for item in history]
   ```

3. Create endpoint in `backend/app/routers/patient_search.py`:
   ```python
   @router.get("/search/history")
   async def get_search_history(
       current_user: User = Depends(get_current_user)
   ):
       service = PatientSearchService()
       history = await service.get_search_history(current_user.id)
       return {"history": history}
   ```

4. Update search endpoint to save history:
   ```python
   await search_service.save_search_history(
       current_user.id,
       request.query,
       request.filters
   )
   ```

5. Update frontend to show recent searches:
   - Add autocomplete dropdown to search box
   - Fetch history on component mount
   - Click to re-run search

**Acceptance**:
- ✅ Search history saved to Redis
- ✅ Last 10 searches displayed
- ✅ Click re-runs search instantly
- ✅ TTL: 7 days
- ✅ 3 unit tests (save, retrieve, max 10)

**Estimated Time**: 45 minutes

---

## Phase 4.7: Integration Tests

### Task 4.7: Create Integration Tests

**Goal**: End-to-end tests for patient search

**Prerequisites**: All previous tasks complete

**Steps**:
1. Create test fixtures (`tests/fixtures/patient_search.py`):
   - 100 patients with diverse conditions
   - 500 documents with extracted entities
   - Meta-annotations coverage (negated, historical, family)

2. Create integration tests (`tests/integration/test_patient_search_api.py`):
   ```python
   def test_search_with_filters(client, auth_headers):
       # Test search with negation filter
       response = client.post(
           "/api/v1/patients/search",
           json={
               "query": "diabetes",
               "filters": {"negation": "Affirmed"},
               "page": 1,
               "page_size": 20
           },
           headers=auth_headers
       )
       assert response.status_code == 200
       assert response.json()["total_count"] > 0
   ```

3. Create performance tests:
   ```python
   def test_search_performance(client, auth_headers):
       # Measure response time
       import time
       start = time.time()
       response = client.post("/api/v1/patients/search", ...)
       duration_ms = (time.time() - start) * 1000
       assert duration_ms < 500  # P95 target
   ```

4. Create E2E tests (`tests/e2e/patient-search.spec.ts`):
   ```typescript
   test('search flow', async ({ page }) => {
     await page.goto('/patients/search')
     await page.fill('input[placeholder*="Search"]', 'diabetes')
     await page.click('button:has-text("Search")')
     await page.waitForSelector('.v-data-table')
     expect(await page.locator('.v-data-table tr').count()).toBeGreaterThan(0)
   })
   ```

**Acceptance**:
- ✅ 15 integration tests passing
- ✅ 5 E2E tests passing
- ✅ Performance target met (<500ms P95)
- ✅ Test coverage: 90%+
- ✅ All edge cases covered (empty results, invalid queries)

**Estimated Time**: 1 hour

---

## Phase 4.8: Documentation & Deployment

### Task 4.8: Documentation & Deployment

**Goal**: Document API and deploy Phase 4

**Prerequisites**: All tasks complete, tests passing

**Steps**:
1. Update OpenAPI spec (auto-generated by FastAPI)
2. Add usage examples to `docs/DEVELOPMENT.md`:
   ```markdown
   ## Patient Search API

   ### Search for patients by concept
   ```bash
   curl -X POST http://localhost:8000/api/v1/patients/search \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "atrial flutter",
       "filters": {
         "negation": "Affirmed",
         "temporality": "Current",
         "experiencer": "Patient"
       }
     }'
   ```
   ```

3. Update CONTEXT.md:
   - Add Phase 4 completion entry
   - Document new endpoints
   - Note performance metrics
   - Update "Current Phase" section

4. Deploy to development:
   ```bash
   docker-compose restart backend
   docker-compose restart frontend
   curl http://localhost:8000/health
   ```

5. Manual smoke testing:
   - Test search with various queries
   - Test filters
   - Test concept highlights
   - Test search history
   - Verify audit logs

**Acceptance**:
- ✅ OpenAPI docs complete
- ✅ DEVELOPMENT.md updated with examples
- ✅ CONTEXT.md updated
- ✅ All services healthy after deployment
- ✅ Smoke tests pass

**Estimated Time**: 30 minutes

---

## Task Dependencies

```
Task 4.1 (Indexes) ────────► Task 4.2.2 (Service) ────► Task 4.2.3 (API)
                                    │                         │
                                    │                         ▼
Task 4.2.1 (Schemas) ───────────────┤                   Task 4.3 (Highlights API)
                                    │                         │
                                    ▼                         │
                          Task 4.4.1 (Composable)             │
                                    │                         │
                          Task 4.4.2 (API Client)             │
                                    │                         │
                                    ▼                         │
                          Task 4.4.3 (Search UI) ─────────────┤
                                    │                         │
                                    ▼                         │
                          Task 4.5 (Highlights UI) ───────────┤
                                    │                         │
                          Task 4.6 (Search History) ──────────┤
                                    │                         │
                                    ▼                         │
                          Task 4.7 (Integration Tests) ───────┤
                                    │                         │
                                    ▼                         │
                          Task 4.8 (Documentation) ───────────┘
```

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests | E2E Tests | Total |
|-----------|------------|-------------------|-----------|-------|
| Patient Search Service | 12 | 5 | - | 17 |
| Concept Highlights | 8 | 3 | - | 11 |
| Search History | 3 | 2 | - | 5 |
| Frontend Composable | 5 | - | - | 5 |
| Frontend Components | - | - | 5 | 5 |
| **Total** | **28** | **10** | **5** | **43** |

**Target Coverage**: 90%+
**Expected Coverage**: 92% (based on Phase 3 patterns)

---

## Performance Targets

| Metric | Target (P95) | Measurement Method |
|--------|--------------|---------------------|
| Search query | <500ms | Integration tests + Prometheus |
| Concept highlights | <300ms | Integration tests |
| Pagination | <200ms | Integration tests |
| Search history | <50ms | Integration tests |

---

## References

- **Specification**: `.specify/specifications/patient-search.md`
- **Technical Plan**: `.specify/plans/patient-search-plan.md`
- **Phase 3 Tasks**: `.specify/tasks/document-management-tasks.md` (reference for patterns)
- **Skills**: `.claude/skills/medcat-meta-annotations/`

---

**Tasks Version**: 1.0.0
**Status**: Ready for Implementation
**Total Estimated Time**: 4-6 hours
**Phase**: 4 (Patient Search & Discovery)
