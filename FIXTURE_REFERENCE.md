# Test Fixture Reference Guide

**Location**: `backend/tests/conftest.py`
**Total Fixtures**: 28
**Status**: All validated and ready

---

## Database & Session Fixtures

### event_loop
```python
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
```
- Provides asyncio event loop for the entire test session
- Use for: Async test coordination

### db
```python
@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with in-memory SQLite."""
```
- Fresh in-memory SQLite database per test
- Auto-cleanup after test completes
- Use for: Any test needing database access

### client
```python
@pytest.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create FastAPI test client with database override."""
```
- FastAPI test client with mocked database
- Overrides get_db dependency
- Use for: API endpoint testing

### test_db (alias)
- Alias for db fixture for backwards compatibility

### async_client (alias)
- Alias for client fixture

### db_session (alias)
- Alias for db fixture

---

## Authentication Fixtures

### test_user_clinician
- Username: "test_clinician"
- Email: "clinician@test.com"
- Role: "clinician"
- Password: "test_password_123"
- Returns: User object (committed to db)

### test_user_researcher
- Username: "test_researcher"
- Email: "researcher@test.com"
- Role: "researcher"
- Password: "test_password_123"

### test_user_admin
- Username: "test_admin"
- Email: "admin@test.com"
- Role: "admin"
- Password: "admin_password_123"
- can_break_glass: True

### auth_headers_clinician
- Returns: `{"Authorization": "Bearer <jwt_token>"}`
- Token for: test_user_clinician
- Use for: API requests as clinician

### auth_headers_viewer
- Returns: Authorization headers dict
- Token for: test_user_researcher

### auth_headers_researcher
- Alias for auth_headers_viewer

### auth_headers_admin
- Returns: Authorization headers dict
- Token for: test_user_admin

---

## Test Data Fixtures

### test_patient
- NHS Number: "9876543210"
- Name: "Test Patient"
- DOB: 1985-06-15
- Returns: Patient object (committed)

### test_document
- Filename: "test_note.rtf"
- Patient: test_patient
- Uploaded by: test_user_clinician
- Status: COMPLETED
- Returns: Document object

### test_entity
- CUI: "C0011849" (Diabetes mellitus)
- Accuracy: 0.95
- Meta-annotations: Affirmed, Current, Patient, Definite
- Returns: ExtractedEntity object

### test_db_with_search_data
- Creates: 3 patients with diabetes annotations
- Patient 1: Current, Affirmed, Patient (should match)
- Patient 2: Current, Affirmed, Patient, Probable certainty
- Patient 3: Different condition (Hypertension)
- Returns: Database session

### test_db_with_annotations
- Creates: 4 patients demonstrating meta-annotation filtering
- Patient A: Affirmed, Current, Patient (control)
- Patient B: Negated (should be filtered out)
- Patient C: Family history (should be filtered)
- Patient D: Historical (should be filtered by temporal)
- Returns: Database session

### test_db_with_timeline_data
- Creates: 1 patient with 5 clinical events spanning Jan-Nov 2023
- Events: Diagnosis, Hypertension, Medication, Lab result, Procedure
- Returns: Dict with patient_id, patient_name, event_count, date_range

---

## Mock Service Fixtures

### mock_redis_client
- Methods: get, set, setex, delete, exists, expire, ttl, incr, decr, keys, scan
- Stream methods: xadd, xread
- Hash methods: hget, hset, hgetall
- Returns: AsyncMock with all methods configured

### mock_elasticsearch_client
- Methods: search, index, get, delete, update, bulk, count, exists
- Indices: exists, create, delete, refresh, get_mapping
- Returns: AsyncMock with realistic responses

### mock_medcat_client
- Methods: get_entities, get_cui2name
- Returns: MagicMock with sample data

---

## Utility Fixtures

### sample_search_response
- Structure: Standard ES response with 2 hits
- Includes: Highlights, aggregations by department/author
- Returns: Dict matching ES response format

### clean_test_env
- Sets: TESTING=true, LOG_LEVEL=WARNING, DISABLE_AUDIT_LOG=true
- Use for: Tests requiring specific environment vars
- Auto-cleanup: Yes (monkeypatch)

### anyio_backend
- Backend: "asyncio"
- Required for: Async test execution

---

## Quick Reference: Which Fixture to Use

| Scenario | Fixtures |
|----------|----------|
| Simple API test | client, auth_headers_clinician |
| Test with auth | auth_headers_{clinician,admin,researcher} |
| Test patient data | test_db_with_search_data |
| Test meta-annotations | test_db_with_annotations |
| Test timeline | test_db_with_timeline_data |
| Mock Elasticsearch | mock_elasticsearch_client |
| Mock Redis | mock_redis_client |
| Mock MedCAT | mock_medcat_client |
| Different roles | auth_headers_clinician + auth_headers_admin |
| Authorization tests | Different auth_headers fixtures |

---

**Last Updated**: 2025-11-27
**Test Agent**: Validation Complete
**Status**: Ready for Test Execution
