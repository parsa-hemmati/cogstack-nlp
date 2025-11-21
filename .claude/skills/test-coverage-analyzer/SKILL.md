# Test Coverage Analyzer

Expert knowledge of testing strategies and coverage improvement for healthcare applications. Current project at 5% coverage, target 80%. Use when writing tests, analyzing coverage gaps, or planning test strategies. Based on Sprint 3 achieving 92% coverage for new code.

## When This Skill Activates

**Activates automatically when**:
- Writing unit, integration, or E2E tests
- Analyzing test coverage reports
- Planning testing strategies
- Setting up test infrastructure
- Debugging failing tests
- Improving test quality

**Keywords**: test, coverage, pytest, unittest, integration, E2E, TDD

## Knowledge Base

### Current Coverage Status

From PROJECT_STATUS_REPORT.md:

| Component | Current | Target | Gap |
|-----------|---------|--------|-----|
| **Overall System** | ~5% | 80% | 75% ⚠️ |
| **Sprint 3 New Code** | 92% | 80% | ✅ Exceeds |
| **Frontend** | ~10% | 80% | 70% ⚠️ |
| **API Endpoints** | ~20% | 100% | 80% ⚠️ |
| **Services** | ~15% | 90% | 75% ⚠️ |

### Test Pyramid Strategy

From Sprint 3 implementation:

```
         /\
        /  \      E2E Tests (10%)
       /----\     - Full workflows, UI interaction
      /      \    - Slow, expensive, high value
     /--------\
    /          \  Integration Tests (30%)
   /            \ - Service interactions, API contracts
  /--------------\- Database operations, external services
 /                \
/                  \ Unit Tests (60%)
--------------------  - Pure functions, isolated components
                     - Fast, cheap, high coverage
```

### Python Testing with pytest

#### 1. Basic Test Structure

```python
# tests/unit/services/test_patient_service.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.patient_service import PatientService

class TestPatientService:
    """Test patient service operations."""

    @pytest.fixture
    def service(self):
        """Create service instance with mocked dependencies."""
        db_mock = AsyncMock()
        cache_mock = AsyncMock()
        return PatientService(db=db_mock, cache=cache_mock)

    @pytest.fixture
    def sample_patient(self):
        """Sample patient data."""
        return {
            "patient_id": "NHS-123456",
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": "1980-01-15"
        }

    @pytest.mark.asyncio
    async def test_create_patient_success(self, service, sample_patient):
        """Test successful patient creation."""
        # Arrange
        service.db.add = AsyncMock()
        service.db.commit = AsyncMock()

        # Act
        result = await service.create_patient(sample_patient)

        # Assert
        assert result.patient_id == "NHS-123456"
        service.db.add.assert_called_once()
        service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_patient_duplicate(self, service, sample_patient):
        """Test duplicate patient handling."""
        # Arrange
        service.db.add = AsyncMock(side_effect=IntegrityError(...))

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            await service.create_patient(sample_patient)
```

#### 2. Parametrized Tests

```python
class TestQueryBuilder:
    """Test search query building."""

    @pytest.mark.parametrize("query_text,query_type,expected_field", [
        ("diabetes", "standard", "multi_match"),
        ("diab*", "wildcard", "wildcard"),
        ("diabets~", "fuzzy", "fuzzy"),
        ("/diabet.*/", "regex", "regexp"),
    ])
    def test_query_type_mapping(self, query_text, query_type, expected_field):
        """Test correct query type is built."""
        result = build_query(query_text, query_type)
        assert expected_field in str(result)

    @pytest.mark.parametrize("invalid_query,expected_error", [
        ("", "Query cannot be empty"),
        ("a", "Query too short"),
        ("*", "Invalid wildcard pattern"),
        ("/[invalid/", "Invalid regex"),
    ])
    def test_invalid_queries(self, invalid_query, expected_error):
        """Test invalid query handling."""
        with pytest.raises(ValueError, match=expected_error):
            validate_query(invalid_query)
```

#### 3. Fixtures and Factories

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.database import Base

@pytest.fixture(scope="session")
async def test_db():
    """Create test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(test_db):
    """Create database session."""
    async with AsyncSession(test_db) as session:
        yield session
        await session.rollback()

@pytest.fixture
def make_patient():
    """Factory for creating patients."""
    def _make_patient(**kwargs):
        defaults = {
            "patient_id": f"NHS-{random.randint(1000000, 9999999)}",
            "first_name": "Test",
            "last_name": "Patient",
            "date_of_birth": "1990-01-01"
        }
        defaults.update(kwargs)
        return Patient(**defaults)
    return _make_patient
```

#### 4. Mocking External Services

```python
class TestMedCATIntegration:
    """Test MedCAT service integration."""

    @pytest.fixture
    def mock_medcat_response(self):
        """Mock MedCAT API response."""
        return {
            "entities": [
                {
                    "cui": "C0011849",
                    "pretty_name": "Diabetes Mellitus",
                    "start": 10,
                    "end": 18,
                    "meta_anns": {
                        "Negation": "Affirmed",
                        "Temporality": "Current"
                    }
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_extract_entities(self, mock_medcat_response):
        """Test entity extraction from text."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.json = \
                AsyncMock(return_value=mock_medcat_response)

            service = MedCATService()
            entities = await service.extract_entities("Patient has diabetes")

            assert len(entities) == 1
            assert entities[0]["cui"] == "C0011849"
```

### Integration Testing

#### 1. API Testing with httpx

```python
# tests/integration/test_search_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.integration
class TestSearchAPI:
    """Integration tests for search API."""

    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    async def auth_headers(self, client):
        """Get authentication headers."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "test", "password": "test"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_search_workflow(self, client, auth_headers):
        """Test complete search workflow."""
        # 1. Validate query
        response = await client.post(
            "/api/v1/search/validate",
            params={"q": "diabetes", "query_type": "standard"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["valid"] is True

        # 2. Execute search
        response = await client.get(
            "/api/v1/search",
            params={"q": "diabetes"},
            headers=auth_headers
        )
        assert response.status_code == 200
        results = response.json()
        assert "results" in results
        assert results["execution_time_ms"] < 500
```

#### 2. Database Integration

```python
@pytest.mark.integration
class TestDatabaseOperations:
    """Test database operations."""

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session):
        """Test transaction rollback on error."""
        service = PatientService(db_session)

        # Start transaction
        patient = await service.create_patient({"patient_id": "NHS-111"})
        assert patient.id is not None

        # Cause error to trigger rollback
        with pytest.raises(ValueError):
            await service.create_patient({"patient_id": "NHS-111"})

        # Verify rollback
        count = await db_session.scalar(
            select(func.count()).select_from(Patient)
        )
        assert count == 0  # Transaction rolled back
```

### End-to-End Testing

From Sprint 3 E2E tests:

```python
# tests/e2e/test_search_complete_workflow.py
@pytest.mark.e2e
class TestSearchE2E:
    """End-to-end tests for search functionality."""

    @pytest.mark.asyncio
    async def test_all_query_types(self, client, auth_headers, sample_docs):
        """Test all 7 query types work correctly."""
        test_cases = [
            ("standard", "diabetes"),
            ("boolean", "diabetes AND hypertension"),
            ("wildcard", "diab*"),
            ("fuzzy", "diabets~"),
            ("proximity", "patient NEAR diabetes"),
            ("range", "date:[2023-01-01 TO 2023-12-31]"),
            ("regex", "/diabet.*/")
        ]

        for query_type, query in test_cases:
            response = await client.get(
                "/api/v1/search",
                params={"q": query, "query_type": query_type},
                headers=auth_headers
            )
            assert response.status_code == 200, f"Failed: {query_type}"

    @pytest.mark.asyncio
    async def test_performance_requirements(self, client, auth_headers):
        """Test search meets performance requirements."""
        import time

        queries = [
            ("diabetes", "standard", 500),
            ("heart disease", "fuzzy", 600),
            ("diab*", "wildcard", 800)
        ]

        for query, qtype, max_ms in queries:
            start = time.time()
            response = await client.get(
                "/api/v1/search",
                params={"q": query, "query_type": qtype},
                headers=auth_headers
            )
            elapsed_ms = (time.time() - start) * 1000

            assert response.status_code == 200
            assert elapsed_ms < max_ms, f"{qtype} took {elapsed_ms}ms"
```

### Coverage Measurement

#### 1. pytest-cov Configuration

```ini
# pyproject.toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["app"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__init__.py",
    "*/config.py"
]

[tool.coverage.report]
precision = 2
skip_empty = true
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod"
]

[tool.coverage.html]
directory = "htmlcov"
```

#### 2. Running Coverage

```bash
# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test types
pytest -m "unit" --cov=app
pytest -m "integration" --cov=app
pytest -m "e2e" --cov=app

# Generate reports
coverage html  # HTML report in htmlcov/
coverage json  # JSON for CI/CD
coverage xml   # XML for tools
```

### Coverage Improvement Strategy

#### Phase 1: Critical Path Coverage (Target: 50%)
```python
# Priority 1: Authentication & Authorization
tests/unit/test_auth_service.py         # 20 tests
tests/integration/test_auth_api.py      # 10 tests

# Priority 2: Patient Operations
tests/unit/test_patient_service.py      # 15 tests
tests/integration/test_patient_api.py   # 8 tests

# Priority 3: Search Functionality
tests/unit/test_search_service.py       # 25 tests
tests/integration/test_search_api.py    # 12 tests
```

#### Phase 2: Service Layer (Target: 70%)
```python
# All service classes
tests/unit/services/test_*.py           # ~100 tests

# API endpoints
tests/integration/api/test_*.py         # ~50 tests
```

#### Phase 3: Complete Coverage (Target: 80%+)
```python
# Edge cases and error paths
tests/unit/test_error_handling.py
tests/unit/test_edge_cases.py

# Performance tests
tests/performance/test_load.py
tests/performance/test_concurrent.py
```

### Test Quality Metrics

```python
class TestQualityAnalyzer:
    """Analyze test quality beyond coverage."""

    def analyze_test_suite(self, test_dir: str) -> Dict:
        """Analyze test suite quality."""

        metrics = {
            "total_tests": 0,
            "assertion_density": 0,  # Assertions per test
            "mock_usage": 0,        # Tests using mocks
            "parametrized": 0,      # Parametrized tests
            "async_tests": 0,       # Async test coverage
            "fixtures_used": set(),
            "test_types": {"unit": 0, "integration": 0, "e2e": 0}
        }

        # Analyze each test file
        for test_file in Path(test_dir).rglob("test_*.py"):
            metrics.update(self._analyze_file(test_file))

        return metrics

    def get_recommendations(self, metrics: Dict) -> List[str]:
        """Get test improvement recommendations."""

        recommendations = []

        if metrics["assertion_density"] < 2:
            recommendations.append("Increase assertions per test (current: {:.1f})".format(
                metrics["assertion_density"]
            ))

        if metrics["parametrized"] < metrics["total_tests"] * 0.3:
            recommendations.append("Use more parametrized tests for better coverage")

        if metrics["test_types"]["e2e"] < metrics["total_tests"] * 0.1:
            recommendations.append("Add more E2E tests (current: {:.1%})".format(
                metrics["test_types"]["e2e"] / metrics["total_tests"]
            ))

        return recommendations
```

### Common Testing Patterns

#### 1. Testing Async Code
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result == expected
```

#### 2. Testing with Database
```python
@pytest.mark.asyncio
async def test_with_db(db_session):
    # Use transaction that auto-rolls back
    await db_session.execute(...)
    await db_session.commit()
```

#### 3. Testing Error Cases
```python
@pytest.mark.parametrize("bad_input,error_msg", [
    (None, "cannot be null"),
    ("", "cannot be empty"),
    ("invalid", "invalid format")
])
def test_validation(bad_input, error_msg):
    with pytest.raises(ValueError, match=error_msg):
        validate(bad_input)
```

## Example Coverage Improvement Plan

### Week 1: Foundation (5% → 25%)
```bash
# Day 1-2: Auth tests
write tests/unit/test_auth_service.py       # 20 tests
write tests/integration/test_auth_api.py    # 10 tests

# Day 3-4: Patient tests
write tests/unit/test_patient_service.py    # 15 tests
write tests/integration/test_patient_api.py # 8 tests

# Day 5: Run and measure
pytest --cov=app --cov-report=html
```

### Week 2: Core Features (25% → 50%)
```bash
# Search functionality
write tests/unit/services/elasticsearch/test_*.py
write tests/integration/test_search_*.py

# Document management
write tests/unit/test_document_service.py
write tests/integration/test_document_api.py
```

### Week 3: Complete Coverage (50% → 80%)
```bash
# Remaining services
write tests/unit/services/test_*.py

# E2E tests
write tests/e2e/test_*.py

# Edge cases
write tests/unit/test_edge_cases.py
```

## Related Skills

- **search-performance-optimizer**: For performance test strategies
- **healthcare-compliance-checker**: For compliance test requirements
- **infrastructure-expert**: For test infrastructure setup

## References

- [pytest Documentation](https://docs.pytest.org/)
- [Sprint 3 Test Suite](clinical-care-tools/backend/tests/)
- [Coverage Report](htmlcov/index.html)