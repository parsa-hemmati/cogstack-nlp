# Tasks: EHR De-Identification (Sprint 4)

**Plan Reference**: `.specify/plans/sprint-4-ehr-deidentification-plan.md` (v1.0.0)
**Specification Reference**: `.specify/specifications/sprint-4-ehr-deidentification.md` (v1.0.0)
**Estimated Total Time**: 120 hours (4 weeks)
**Dependencies**:
- Sprints 1-3 completed
- CogStack-ModelServe running with medcat_ner_phi model
- PostgreSQL with pgcrypto extension
- Celery worker for batch processing

---

## Phase 4.1: CogStack-ModelServe Integration (30 hours)

### Task 4.1.1: Download and Configure PHI Detection Model

**Goal**: Setup medcat_ner_phi model in CogStack-ModelServe

**Phase**: Phase 4.1
**Dependencies**: None
**Estimated Time**: 4 hours

**Steps**:
1. **Download PHI NER model**
   - Download medcat_ner_phi from Model Zoo
   - Store in `medcat_models/ner_phi/`
   - Verify model integrity (checksum)
2. **Configure ModelServe**
   - Update docker-compose.yml to mount PHI model
   - Add MODEL_PHI_PATH environment variable
   - Restart ModelServe container
3. **Verify model loaded**
   - Call `/api/models` endpoint
   - Verify medcat_ner_phi listed

**Acceptance Criteria**:
- [ ] PHI model downloaded and extracted
- [ ] ModelServe configured with PHI model
- [ ] Model appears in `/api/models` response
- [ ] Manual test: Process text with PHI → entities detected

**Files Created/Modified**:
- `docker-compose.yml` - Updated with PHI model mount
- `.env` - Add MODEL_PHI_PATH

---

### Task 4.1.2: Create PHI Detection Service

**Goal**: Service to detect PHI using CogStack-ModelServe

**Phase**: Phase 4.1
**Dependencies**: Task 4.1.1
**Estimated Time**: 6 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_phi_detection_service.py`
   - Test: `detect_phi(text)` returns detected entities
   - Test: Entity types correct (PERSON, DATE, ID, LOCATION, PHONE, EMAIL)
   - Test: Start/end positions correct
   - Test: Confidence scores included
2. **Implement**
   - Create `backend/app/services/phi_detection_service.py`
   - Create `PHIDetectionService` class
   - Implement `detect_phi(text)` method
   - Call CogStack-ModelServe `/api/process` with model="medcat_ner_phi"
   - Parse entities from response
   - Return list of `DetectedEntity` objects
3. **Verify**
   - Run: `pytest tests/unit/services/test_phi_detection_service.py`

**Acceptance Criteria**:
- [ ] Service detects PHI entities
- [ ] Entity types match expected (PERSON, DATE, ID, etc.)
- [ ] Positions accurate
- [ ] Tests passing (≥85% coverage)

**Test Coverage**:
- Unit tests: 12 tests (detection, entity types, positions)

**Files Created/Modified**:
- `backend/app/services/phi_detection_service.py` - PHI detection service
- `backend/app/schemas/phi.py` - DetectedEntity schema
- `tests/unit/services/test_phi_detection_service.py` - Detection tests

---

### Task 4.1.3: Test PHI Detection Accuracy

**Goal**: Validate PHI detection model accuracy

**Phase**: Phase 4.1
**Dependencies**: Task 4.1.2
**Estimated Time**: 4 hours

**Steps**:
1. **Create test dataset**
   - Collect 50 sample clinical notes with known PHI
   - Annotate ground truth PHI entities
2. **Run detection**
   - Process each note through PHI detection service
   - Compare detected entities to ground truth
3. **Calculate metrics**
   - Precision, recall, F1 score
   - Break down by entity type
4. **Verify targets**
   - Precision ≥90% for PERSON, DATE, ID
   - Recall ≥80% for critical entity types

**Acceptance Criteria**:
- [ ] Test dataset created (50 notes)
- [ ] Detection accuracy measured
- [ ] Precision ≥90% for critical types
- [ ] Recall ≥80% for critical types

**Files Created/Modified**:
- `tests/accuracy/test_phi_detection_accuracy.py` - Accuracy tests
- `tests/accuracy/phi_test_dataset.json` - Test dataset

---

### Task 4.1.4: Handle False Positives/Negatives

**Goal**: Implement strategies to reduce false positives/negatives

**Phase**: Phase 4.1
**Dependencies**: Task 4.1.3
**Estimated Time**: 4 hours

**Steps**:
1. **Analyze errors**
   - Review false positives (non-PHI detected as PHI)
   - Review false negatives (PHI missed)
2. **Implement post-processing**
   - Filter out common false positives (e.g., "patient" as PERSON)
   - Add context-based validation
3. **Re-test**
   - Run accuracy tests again
   - Verify improvements

**Acceptance Criteria**:
- [ ] False positive rate reduced ≥30%
- [ ] Precision improved
- [ ] No significant recall drop

**Files Created/Modified**:
- `backend/app/services/phi_detection_service.py` - Updated with post-processing

---

### Task 4.1.5: Unit Tests for PHI Detection

**Goal**: Comprehensive unit test coverage

**Phase**: Phase 4.1
**Dependencies**: Task 4.1.4
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests**
   - Test: Various PHI types detected
   - Test: Edge cases (multiple entities, overlapping)
   - Test: Non-PHI text returns empty list
   - Test: Error handling (ModelServe unavailable)
2. **Run tests**
   - Execute: `pytest tests/unit/services/test_phi_detection_service.py -v`

**Acceptance Criteria**:
- [ ] All unit tests passing
- [ ] Code coverage ≥90%

**Test Coverage**:
- Unit tests: 20+ tests

**Files Created/Modified**:
- `tests/unit/services/test_phi_detection_service.py` - Expanded tests

---

### Task 4.1.6: Performance Testing - PHI Detection

**Goal**: Verify PHI detection meets performance requirements

**Phase**: Phase 4.1
**Dependencies**: Task 4.1.2
**Estimated Time**: 3 hours

**Steps**:
1. **Create performance tests**
   - Test documents of varying sizes (1KB, 5KB, 10KB)
   - Measure detection time
2. **Run tests**
   - Execute tests
   - Record response times
3. **Verify targets**
   - <5 seconds per document (up to 10KB)

**Acceptance Criteria**:
- [ ] Detection time <5 seconds for 10KB document
- [ ] Linear scaling with document size

**Files Created/Modified**:
- `tests/performance/test_phi_detection_performance.py` - Performance tests

---

### Task 4.1.7: Create PHI Detection API Endpoint (Internal)

**Goal**: Internal API endpoint for PHI detection

**Phase**: Phase 4.1
**Dependencies**: Task 4.1.2
**Estimated Time**: 2 hours

**Steps**:
1. **Write tests**
   - Create `tests/integration/test_phi_detection_api.py`
   - Test: POST /api/internal/phi/detect returns entities
2. **Implement**
   - Create `backend/app/api/internal/endpoints/phi.py`
   - Create `POST /api/internal/phi/detect` endpoint
   - Call PHI detection service
   - Return JSON response
3. **Verify**
   - Run integration tests

**Acceptance Criteria**:
- [ ] Endpoint returns detected entities
- [ ] Internal-only access (not public)
- [ ] Tests passing

**Files Created/Modified**:
- `backend/app/api/internal/endpoints/phi.py` - PHI detection endpoint
- `tests/integration/test_phi_detection_api.py` - API tests

---

### Task 4.1.8: Integration Tests - CogStack-ModelServe

**Goal**: Integration tests for ModelServe communication

**Phase**: Phase 4.1
**Dependencies**: Task 4.1.2
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests**
   - Test: Service calls ModelServe correctly
   - Test: Response parsed correctly
   - Test: Error handling (ModelServe down)
   - Test: Timeout handling
2. **Run tests**
   - Execute: `pytest tests/integration/test_cogstack_modelserve.py`

**Acceptance Criteria**:
- [ ] All integration tests passing
- [ ] Error cases handled

**Test Coverage**:
- Integration tests: 8 tests

**Files Created/Modified**:
- `tests/integration/test_cogstack_modelserve.py` - ModelServe integration tests

---

## Phase 4.2: Redaction Modes (30 hours)

### Task 4.2.1: Create Surrogate Generation Service

**Goal**: Generate surrogates for detected PHI

**Phase**: Phase 4.2
**Dependencies**: Task 4.1.2
**Estimated Time**: 6 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_surrogate_generation.py`
   - Test: PERSON → "Patient-A", "Patient-B", etc.
   - Test: DATE → "01/15/19XX" (year masked)
   - Test: ID → "ID-0001", "ID-0002", etc.
   - Test: LOCATION → "Address-1", "Address-2", etc.
   - Test: Same entity gets same surrogate (consistency)
2. **Implement**
   - Create `backend/app/services/surrogate_generation_service.py`
   - Implement `generate_surrogates(entities)` method
   - Use counters for each entity type
   - Map original → surrogate
   - Return mappings dict
3. **Verify**
   - Run: `pytest tests/unit/services/test_surrogate_generation.py`

**Acceptance Criteria**:
- [ ] Surrogates generated for all entity types
- [ ] Consistent mapping (same entity → same surrogate)
- [ ] Human-readable surrogates (Patient-A, not random UUIDs)
- [ ] Tests passing (≥90% coverage)

**Test Coverage**:
- Unit tests: 15 tests (generation, consistency, types)

**Files Created/Modified**:
- `backend/app/services/surrogate_generation_service.py` - Surrogate service
- `tests/unit/services/test_surrogate_generation.py` - Surrogate tests

---

### Task 4.2.2: Implement Redaction Modes (Mask, Surrogate, Remove)

**Goal**: Apply different redaction modes to text

**Phase**: Phase 4.2
**Dependencies**: Task 4.2.1
**Estimated Time**: 6 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_redaction.py`
   - Test: Mask mode replaces with [REDACTED]
   - Test: Surrogate mode replaces with surrogate
   - Test: Remove mode removes entity entirely
   - Test: Multiple entities in same text
   - Test: Overlapping entities handled
2. **Implement**
   - Add `apply_redaction(text, entities, mode, mappings)` method to DeidentificationService
   - Sort entities by position (reverse order to preserve offsets)
   - Replace each entity based on mode
   - Return redacted text
3. **Verify**
   - Run: `pytest tests/unit/services/test_redaction.py`

**Acceptance Criteria**:
- [ ] All three modes work correctly
- [ ] Multiple entities handled
- [ ] Overlapping entities handled gracefully
- [ ] Original text unchanged (immutability)
- [ ] Tests passing (≥90% coverage)

**Test Coverage**:
- Unit tests: 12 tests (modes, multiple entities, overlaps)

**Files Created/Modified**:
- `backend/app/services/deidentification_service.py` - Add redaction methods
- `tests/unit/services/test_redaction.py` - Redaction tests

---

### Task 4.2.3: Create De-identification Preview Endpoint

**Goal**: POST /api/v1/deidentify/preview endpoint

**Phase**: Phase 4.2
**Dependencies**: Task 4.2.2
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_deidentify_preview_api.py`
   - Test: POST /api/v1/deidentify/preview returns preview
   - Test: Preview includes original text, entities, redacted text
   - Test: Different redaction modes
2. **Implement**
   - Create `backend/app/api/v1/endpoints/deidentify.py`
   - Create `POST /api/v1/deidentify/preview` endpoint
   - Fetch document(s)
   - Detect PHI
   - Generate redacted preview
   - Return preview response
3. **Verify**
   - Run: `pytest tests/integration/test_deidentify_preview_api.py`

**Acceptance Criteria**:
- [ ] Endpoint returns preview
- [ ] All redaction modes supported
- [ ] Response includes original text, entities, redacted text
- [ ] Tests passing

**Test Coverage**:
- Integration tests: 8 tests (preview, modes, multiple docs)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/deidentify.py` - De-identify endpoints
- `tests/integration/test_deidentify_preview_api.py` - Preview API tests

---

### Task 4.2.4: Create De-identification Apply Endpoint

**Goal**: POST /api/v1/deidentify/apply endpoint

**Phase**: Phase 4.2
**Dependencies**: Task 4.2.3
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Test: POST /api/v1/deidentify/apply creates de-identified document
   - Test: Original document unchanged
   - Test: De-identified document stored
   - Test: Audit log created
2. **Implement**
   - Create `POST /api/v1/deidentify/apply` endpoint
   - Detect PHI
   - Generate surrogates
   - Apply redaction
   - Store de-identified document
   - Create audit log
   - Return response
3. **Verify**
   - Run integration tests

**Acceptance Criteria**:
- [ ] De-identified document created
- [ ] Original document unchanged
- [ ] Audit log entry created
- [ ] Tests passing

**Test Coverage**:
- Integration tests: 10 tests (apply, storage, audit)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/deidentify.py` - Add apply endpoint
- `tests/integration/test_deidentify_apply_api.py` - Apply API tests

---

### Task 4.2.5: Unit Tests for Redaction Service

**Goal**: Comprehensive unit tests for redaction

**Phase**: Phase 4.2
**Dependencies**: Task 4.2.2
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests**
   - Test edge cases (empty text, no entities)
   - Test performance (large documents)
   - Test special characters in entities
2. **Run tests**
   - Execute: `pytest tests/unit/services/test_redaction.py -v`

**Acceptance Criteria**:
- [ ] All tests passing
- [ ] Code coverage ≥90%

**Files Created/Modified**:
- `tests/unit/services/test_redaction.py` - Expanded tests

---

### Task 4.2.6: Create Frontend De-identification Preview UI

**Goal**: UI to preview de-identification

**Phase**: Phase 4.2
**Dependencies**: Task 4.2.3
**Estimated Time**: 6 hours

**Steps**:
1. **Create component**
   - Create `webapp/src/views/DeidentificationView.vue`
   - Document selection table
   - Redaction mode selector (radio buttons)
   - Preview button
   - Preview dialog with original/redacted text
   - Highlighted PHI entities in preview
2. **Implement preview logic**
   - Call preview API
   - Display original text with highlighted PHI
   - Display redacted text
3. **Manual testing**
   - Test in browser

**Acceptance Criteria**:
- [ ] UI renders correctly
- [ ] Preview shows original + redacted text
- [ ] PHI entities highlighted
- [ ] Redaction modes work

**Files Created/Modified**:
- `webapp/src/views/DeidentificationView.vue` - De-identification view
- `webapp/src/stores/deidentification.ts` - De-identification store

---

### Task 4.2.7: Integration Tests - De-identification Workflow

**Goal**: End-to-end tests for de-identification

**Phase**: Phase 4.2
**Dependencies**: Task 4.2.4
**Estimated Time**: 1 hour

**Steps**:
1. **Write tests**
   - Test: Preview → Apply workflow
   - Test: All redaction modes
   - Test: Multiple documents
2. **Run tests**
   - Execute: `pytest tests/integration/test_deidentify_workflow.py`

**Acceptance Criteria**:
- [ ] All integration tests passing

**Files Created/Modified**:
- `tests/integration/test_deidentify_workflow.py` - Workflow tests

---

## Phase 4.3: Re-ID Mapping Storage (30 hours)

### Task 4.3.1: Enable pgcrypto Extension

**Goal**: Enable PostgreSQL pgcrypto for encryption

**Phase**: Phase 4.3
**Dependencies**: None
**Estimated Time**: 1 hour

**Steps**:
1. **Create migration**
   - Run: `alembic revision -m "enable pgcrypto"`
   - Add: `CREATE EXTENSION IF NOT EXISTS pgcrypto;`
2. **Apply migration**
   - Run: `alembic upgrade head`
3. **Verify**
   - Check extension: `SELECT * FROM pg_extension WHERE extname='pgcrypto';`

**Acceptance Criteria**:
- [ ] pgcrypto extension enabled
- [ ] Encryption functions available

**Files Created/Modified**:
- `backend/alembic/versions/XXX_enable_pgcrypto.py` - Migration

---

### Task 4.3.2: Create reidentification_mappings Table

**Goal**: Table to store encrypted re-ID mappings

**Phase**: Phase 4.3
**Dependencies**: Task 4.3.1
**Estimated Time**: 2 hours

**Steps**:
1. **Create migration**
   - Run: `alembic revision -m "create reidentification_mappings"`
   - Define table schema (see technical plan)
   - Add indexes on document_id, surrogate_value
   - Create encryption/decryption functions
2. **Apply migration**
   - Run: `alembic upgrade head`
3. **Verify**
   - Check table: `\d reidentification_mappings`

**Acceptance Criteria**:
- [ ] Table created successfully
- [ ] Encryption functions created
- [ ] Indexes created

**Files Created/Modified**:
- `backend/alembic/versions/XXX_create_reidentification_mappings.py` - Migration

---

### Task 4.3.3: Create Re-ID Mapping Service

**Goal**: Service to store/retrieve encrypted mappings

**Phase**: Phase 4.3
**Dependencies**: Task 4.3.2
**Estimated Time**: 6 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/services/test_reid_mapping_service.py`
   - Test: Store mapping encrypts original value
   - Test: Retrieve mapping decrypts successfully
   - Test: Encryption key required
   - Test: Mappings isolated by document_id
2. **Implement**
   - Create `backend/app/services/reid_mapping_service.py`
   - Implement `store_mapping(document_id, entity_mappings)` method
   - Use pgcrypto encrypt_value() function
   - Store encrypted original → surrogate pairs
   - Implement `retrieve_mapping(document_id, surrogate)` method
   - Use pgcrypto decrypt_value() function
3. **Verify**
   - Run: `pytest tests/unit/services/test_reid_mapping_service.py`

**Acceptance Criteria**:
- [ ] Mappings stored successfully
- [ ] Original values encrypted
- [ ] Decryption works correctly
- [ ] Encryption key from environment variable
- [ ] Tests passing (≥90% coverage)

**Test Coverage**:
- Unit tests: 12 tests (store, retrieve, encryption, key management)

**Files Created/Modified**:
- `backend/app/services/reid_mapping_service.py` - Re-ID mapping service
- `tests/unit/services/test_reid_mapping_service.py` - Mapping tests

---

### Task 4.3.4: Integrate Mapping Storage into Apply Endpoint

**Goal**: Store re-ID mappings when applying de-identification

**Phase**: Phase 4.3
**Dependencies**: Task 4.3.3
**Estimated Time**: 3 hours

**Steps**:
1. **Update endpoint**
   - Modify `POST /api/v1/deidentify/apply` endpoint
   - Add `store_mapping` parameter (default: true)
   - If true, call reid_mapping_service.store_mapping()
   - Return mapping_id in response
2. **Test**
   - Update integration tests
   - Verify mappings stored

**Acceptance Criteria**:
- [ ] Mappings stored on apply
- [ ] store_mapping parameter works
- [ ] mapping_id returned in response
- [ ] Tests updated

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/deidentify.py` - Updated apply endpoint
- `tests/integration/test_deidentify_apply_api.py` - Updated tests

---

### Task 4.3.5: Create Encryption Key Management

**Goal**: Secure encryption key management

**Phase**: Phase 4.3
**Dependencies**: Task 4.3.3
**Estimated Time**: 4 hours

**Steps**:
1. **Generate encryption key**
   - Generate 32-byte random key: `openssl rand -base64 32`
   - Store in environment variable: REID_ENCRYPTION_KEY
   - Add to .env.template with placeholder
2. **Implement key rotation**
   - Create script: `scripts/rotate_reid_encryption_key.py`
   - Re-encrypt all mappings with new key
   - Update environment variable
3. **Document key management**
   - Add to README.md
   - Add to deployment docs

**Acceptance Criteria**:
- [ ] Encryption key generated
- [ ] Key stored in environment variable
- [ ] Key rotation script created
- [ ] Documentation updated

**Files Created/Modified**:
- `scripts/rotate_reid_encryption_key.py` - Key rotation script
- `README.md` - Add key management section
- `.env.template` - Add REID_ENCRYPTION_KEY

---

### Task 4.3.6: Test Encryption Security

**Goal**: Verify encryption security

**Phase**: Phase 4.3
**Dependencies**: Task 4.3.3
**Estimated Time**: 3 hours

**Steps**:
1. **Security tests**
   - Test: Encrypted value != plaintext
   - Test: Same plaintext encrypts to different ciphertext (salt)
   - Test: Cannot decrypt without key
   - Test: Key rotation works
2. **Manual verification**
   - Check database: encrypted values unreadable
   - Check decryption with correct key works

**Acceptance Criteria**:
- [ ] Encrypted values unreadable in database
- [ ] Decryption requires correct key
- [ ] Key rotation successful

**Files Created/Modified**:
- `tests/security/test_reid_encryption.py` - Security tests

---

### Task 4.3.7: Create Re-identification API Endpoint (Admin Only)

**Goal**: Endpoint to re-identify document (admin only)

**Phase**: Phase 4.3
**Dependencies**: Task 4.3.3
**Estimated Time**: 3 hours

**Steps**:
1. **Write tests**
   - Create `tests/integration/test_reidentify_api.py`
   - Test: POST /api/v1/reidentify returns original text
   - Test: Admin-only access (403 for non-admin)
   - Test: Audit log created
2. **Implement**
   - Create `POST /api/v1/reidentify` endpoint
   - Fetch de-identified document
   - Retrieve mappings from database
   - Decrypt original values
   - Replace surrogates with original values
   - Create audit log (re-identification is sensitive!)
   - Return original text
3. **Verify**
   - Run integration tests

**Acceptance Criteria**:
- [ ] Endpoint re-identifies document
- [ ] Admin-only access
- [ ] Audit log created
- [ ] Tests passing

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/reidentify.py` - Re-identification endpoint
- `tests/integration/test_reidentify_api.py` - Re-ID API tests

---

### Task 4.3.8: Integration Tests - Mapping Storage

**Goal**: Integration tests for mapping storage

**Phase**: Phase 4.3
**Dependencies**: Task 4.3.4
**Estimated Time**: 2 hours

**Steps**:
1. **Write tests**
   - Test: Apply de-identification → mappings stored
   - Test: Re-identify document → original text recovered
   - Test: Mappings isolated by document
2. **Run tests**
   - Execute: `pytest tests/integration/test_reid_mapping_integration.py`

**Acceptance Criteria**:
- [ ] All integration tests passing

**Files Created/Modified**:
- `tests/integration/test_reid_mapping_integration.py` - Mapping integration tests

---

### Task 4.3.9: Performance Testing - Encryption/Decryption

**Goal**: Verify encryption performance acceptable

**Phase**: Phase 4.3
**Dependencies**: Task 4.3.3
**Estimated Time**: 6 hours

**Steps**:
1. **Performance tests**
   - Test storing 100 mappings
   - Test retrieving 100 mappings
   - Measure time
2. **Verify targets**
   - Store 100 mappings: <5 seconds
   - Retrieve 1 mapping: <100ms

**Acceptance Criteria**:
- [ ] Encryption performance acceptable
- [ ] No significant overhead

**Files Created/Modified**:
- `tests/performance/test_reid_mapping_performance.py` - Performance tests

---

## Phase 4.4: Batch Processing (30 hours)

### Task 4.4.1: Create deidentification_jobs Table

**Goal**: Table to track batch de-identification jobs

**Phase**: Phase 4.4
**Dependencies**: None
**Estimated Time**: 2 hours

**Steps**:
1. **Create migration**
   - Run: `alembic revision -m "create deidentification_jobs"`
   - Define table schema (see technical plan)
   - Add indexes on user_id, status
2. **Apply migration**
   - Run: `alembic upgrade head`

**Acceptance Criteria**:
- [ ] Table created successfully
- [ ] Indexes created

**Files Created/Modified**:
- `backend/alembic/versions/XXX_create_deidentification_jobs.py` - Migration

---

### Task 4.4.2: Create Batch De-identification Celery Task

**Goal**: Celery task for batch de-identification

**Phase**: Phase 4.4
**Dependencies**: Task 4.4.1
**Estimated Time**: 8 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/unit/tasks/test_batch_deidentify.py`
   - Test: Task processes all documents
   - Test: Job status updated (pending → processing → completed)
   - Test: Error handling (partial failures)
2. **Implement**
   - Create `backend/app/tasks/batch_deidentify.py`
   - Create Celery task: `deidentify_batch_task(job_id, document_ids, ...)`
   - For each document: detect PHI, apply redaction, store
   - Update job progress: processed_documents, failed_documents
   - Set job status: completed or failed
3. **Verify**
   - Run: `pytest tests/unit/tasks/test_batch_deidentify.py`

**Acceptance Criteria**:
- [ ] Task processes all documents
- [ ] Progress tracked in database
- [ ] Job status updated correctly
- [ ] Partial failures handled
- [ ] Tests passing (≥85% coverage)

**Test Coverage**:
- Unit tests: 10 tests (processing, progress, errors)

**Files Created/Modified**:
- `backend/app/tasks/batch_deidentify.py` - Batch task
- `tests/unit/tasks/test_batch_deidentify.py` - Task tests

---

### Task 4.4.3: Create Batch De-identification API Endpoint

**Goal**: POST /api/v1/deidentify/batch endpoint

**Phase**: Phase 4.4
**Dependencies**: Task 4.4.2
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests** (TDD approach)
   - Create `tests/integration/test_batch_deidentify_api.py`
   - Test: POST /api/v1/deidentify/batch creates job
   - Test: Job ID returned
   - Test: Job status queryable
2. **Implement**
   - Create `POST /api/v1/deidentify/batch` endpoint
   - Create job record in database
   - Queue Celery task
   - Return job_id
   - Create `GET /api/v1/deidentify/batch/{job_id}` endpoint for status
3. **Verify**
   - Run: `pytest tests/integration/test_batch_deidentify_api.py`

**Acceptance Criteria**:
- [ ] Endpoint creates job
- [ ] Job queued successfully
- [ ] Status endpoint returns job status
- [ ] Tests passing

**Test Coverage**:
- Integration tests: 8 tests (create job, status, completion)

**Files Created/Modified**:
- `backend/app/api/v1/endpoints/deidentify.py` - Add batch endpoints
- `tests/integration/test_batch_deidentify_api.py` - Batch API tests

---

### Task 4.4.4: Frontend Batch De-identification UI

**Goal**: UI for batch de-identification

**Phase**: Phase 4.4
**Dependencies**: Task 4.4.3
**Estimated Time**: 6 hours

**Steps**:
1. **Implement UI**
   - Add multi-select to document table
   - Add "Batch De-identify" button
   - Show job progress dialog
   - Poll job status every 2 seconds
   - Show completion notification
2. **Manual testing**
   - Test with 10 documents
   - Test with 100 documents

**Acceptance Criteria**:
- [ ] Multi-select works
- [ ] Batch de-identify creates job
- [ ] Progress shown in real-time
- [ ] Completion notification shown

**Files Created/Modified**:
- `webapp/src/views/DeidentificationView.vue` - Add batch UI
- `webapp/src/stores/deidentification.ts` - Add batch actions

---

### Task 4.4.5: Integration Tests - Batch Processing

**Goal**: Integration tests for batch processing

**Phase**: Phase 4.4
**Dependencies**: Task 4.4.3
**Estimated Time**: 4 hours

**Steps**:
1. **Write tests**
   - Test: Batch 10 documents
   - Test: Batch 100 documents
   - Test: Job completion
   - Test: Partial failures
2. **Run tests**
   - Execute: `pytest tests/integration/test_batch_deidentify.py`

**Acceptance Criteria**:
- [ ] All integration tests passing

**Files Created/Modified**:
- `tests/integration/test_batch_deidentify.py` - Batch integration tests

---

### Task 4.4.6: Performance Testing - Batch Processing

**Goal**: Verify batch processing performance

**Phase**: Phase 4.4
**Dependencies**: Task 4.4.2
**Estimated Time**: 4 hours

**Steps**:
1. **Performance tests**
   - Batch 100 documents
   - Measure total time
   - Verify <10 minutes
2. **Optimize if needed**
   - Parallel processing (multiple workers)
   - Batch PHI detection calls

**Acceptance Criteria**:
- [ ] 100 documents processed in <10 minutes
- [ ] Throughput ≥10 documents/minute

**Files Created/Modified**:
- `tests/performance/test_batch_deidentify_performance.py` - Performance tests

---

### Task 4.4.7: Job Cleanup Background Task

**Goal**: Clean up old completed jobs

**Phase**: Phase 4.4
**Dependencies**: Task 4.4.1
**Estimated Time**: 2 hours

**Steps**:
1. **Create Celery task**
   - Create `backend/app/tasks/cleanup_jobs.py`
   - Implement `cleanup_old_jobs()` task
   - Delete jobs >30 days old
   - Schedule to run daily
2. **Test**
   - Manual verification

**Acceptance Criteria**:
- [ ] Cleanup task created
- [ ] Scheduled to run daily
- [ ] Old jobs deleted

**Files Created/Modified**:
- `backend/app/tasks/cleanup_jobs.py` - Cleanup task

---

## Deployment Checklist

### Infrastructure
- [ ] CogStack-ModelServe running with medcat_ner_phi model
- [ ] PostgreSQL pgcrypto extension enabled
- [ ] Celery worker running for batch processing
- [ ] Redis running (Celery backend)

### Configuration
- [ ] Environment variables set:
  - `REID_ENCRYPTION_KEY` (32-byte key)
  - `CELERY_BROKER_URL=redis://redis:6379/0`
  - `CELERY_RESULT_BACKEND=redis://redis:6379/0`
- [ ] Database migrations applied

### Security
- [ ] Encryption key generated and stored securely
- [ ] Key rotation procedure documented
- [ ] Audit logging enabled

### Testing
- [ ] PHI detection accuracy validated (≥90% precision)
- [ ] All unit/integration tests passing
- [ ] Performance targets met

---

## Summary

**Total Tasks**: 35 tasks across 4 phases
**Total Estimated Time**: 120 hours (4 weeks)

**Phase Breakdown**:
- Phase 4.1 (CogStack-ModelServe Integration): 30 hours, 8 tasks
- Phase 4.2 (Redaction Modes): 30 hours, 7 tasks
- Phase 4.3 (Re-ID Mapping Storage): 30 hours, 9 tasks
- Phase 4.4 (Batch Processing): 30 hours, 7 tasks

**Test Coverage Targets**:
- Unit tests: ≥90%
- Integration tests: ≥85%
- Accuracy: Precision ≥90%, Recall ≥80%

**Performance Targets**:
- PHI detection: <5 seconds per document
- Batch processing: ≥10 documents/minute
- Encryption overhead: <1 second per 100 mappings
