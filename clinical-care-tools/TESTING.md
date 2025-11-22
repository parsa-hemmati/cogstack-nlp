# Testing Framework Documentation

**Clinical Care Tools - Comprehensive Testing Infrastructure**

**Version**: 1.0.0
**Last Updated**: 2025-11-22
**Target Coverage**: 85% overall, 90% for auth/PHI/security code

---

## Table of Contents

1. [Overview](#overview)
2. [Backend Testing](#backend-testing)
3. [Frontend Testing](#frontend-testing)
4. [Running Tests](#running-tests)
5. [Coverage Requirements](#coverage-requirements)
6. [CI/CD Integration](#cicd-integration)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Clinical Care Tools application uses a comprehensive, layered testing approach:

```
┌─────────────────────────────────────────────────────────────┐
│ E2E Tests (10%)                                              │
│ - Complete user workflows                                   │
│ - Integration across all layers                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Integration Tests (30%)                                      │
│ - API endpoint contracts                                    │
│ - Service interactions                                       │
│ - Database operations                                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Unit Tests (60%)                                             │
│ - Individual functions/methods                              │
│ - Business logic                                             │
│ - Utilities and helpers                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Testing

### Structure

```
backend/tests/
├── conftest.py                          # Fixtures & global setup
├── pytest.ini                          # Pytest configuration
├── .coveragerc                         # Coverage configuration
│
├── unit/                               # Unit tests (60%)
│   ├── services/
│   │   ├── test_auth_service.py
│   │   ├── test_session_service.py
│   │   ├── test_rbac_service.py
│   │   └── test_audit_service.py
│   ├── models/
│   └── utils/
│
├── integration/                        # Integration tests (30%)
│   └── endpoints/
│       ├── test_auth_endpoints.py
│       ├── test_user_endpoints.py
│       └── test_health_endpoints.py
│
└── e2e/                               # E2E tests (10%)
    └── test_user_journey.py
```

### Key Fixtures (conftest.py)

#### Database Fixtures
```python
# SQLite in-memory database for testing
db_engine          # Database engine
db_session_factory # Session factory
db_session         # Individual test session (auto-rollback)
```

#### Authentication Fixtures
```python
test_user_data           # Regular user credentials
test_admin_user_data     # Admin user credentials
test_clinician_user_data # Clinician user credentials
access_token             # Valid JWT token
admin_access_token       # Admin JWT token
clinician_access_token   # Clinician JWT token
auth_headers             # Authorization headers
admin_auth_headers       # Admin auth headers
```

#### Mock Service Fixtures
```python
mock_medcat_service       # Mock MedCAT NLP service
mock_elasticsearch_service # Mock Elasticsearch
mock_redis_service        # Mock Redis cache
```

#### Test Data Factories
```python
user_factory        # Create test users
patient_factory     # Create test patients
document_factory    # Create test documents
```

### Running Backend Tests

#### All tests
```bash
cd backend
pytest tests/
```

#### Specific test category
```bash
# Unit tests only
pytest tests/unit/ -m unit

# Integration tests only
pytest tests/integration/ -m integration

# E2E tests only
pytest tests/e2e/ -m e2e

# Security-critical tests
pytest tests/ -m security

# Compliance tests
pytest tests/ -m compliance
```

#### With coverage
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

#### Parallel execution
```bash
pytest tests/ -n auto  # Requires pytest-xdist
```

#### Specific test file
```bash
pytest tests/unit/services/test_auth_service.py -v
```

#### Specific test function
```bash
pytest tests/unit/services/test_auth_service.py::TestAuthService::test_register_user_success -v
```

---

## Frontend Testing

### Structure

```
frontend/tests/
├── setup.ts                            # Global test setup
├── vitest.config.ts                   # Vitest configuration
│
├── unit/                               # Unit tests (60%)
│   ├── components/
│   │   └── LoginForm.spec.ts
│   ├── stores/
│   │   └── auth.spec.ts
│   └── composables/
│
├── integration/                        # Integration tests (30%)
│   └── views/
│       └── LoginView.spec.ts
│
└── e2e/                               # E2E tests (10%) - optional
```

### Key Setup (tests/setup.ts)

#### Vuetify Configuration
```typescript
vuetify  // Vuetify instance with components & directives
```

#### Mock Services
```typescript
mockAxios    // Mock HTTP client
mockRouter   // Mock Vue Router
```

#### Storage Mocks
```typescript
localStorage     // Mock browser local storage
sessionStorage   // Mock browser session storage
```

#### Test Utilities
```typescript
createMockAuthToken()  // Generate test JWT
createMockUser()       // Create test user object
createMockPatient()    // Create test patient object
createMockResponse()   // Create API response mock
```

### Running Frontend Tests

#### All tests
```bash
cd frontend
npm run test
```

#### Watch mode (development)
```bash
npm run test -- --watch
```

#### With coverage
```bash
npm run test:coverage
```

#### UI mode (visual test runner)
```bash
npm run test:ui
```

#### Specific test file
```bash
npm run test -- LoginForm.spec.ts
```

#### Specific test pattern
```bash
npm run test -- --grep "login"
```

---

## Running All Tests

### Local Development

#### Backend
```bash
cd backend

# Install test dependencies
pip install -e ".[dev]"
pip install -r requirements.txt

# Run all tests with coverage
pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm ci

# Run all tests with coverage
npm run test:coverage

# View coverage report
open coverage/index.html
```

### Docker (Recommended for CI/Consistency)

```bash
# Backend tests
docker-compose -f docker-compose.test.yml run --rm backend pytest tests/

# Frontend tests
docker-compose -f docker-compose.test.yml run --rm frontend npm run test

# All tests
docker-compose -f docker-compose.test.yml run --rm tests
```

---

## Coverage Requirements

### Overall Target
- **Backend**: 85% minimum, 90% for critical paths
- **Frontend**: 85% minimum, 90% for auth/UI critical paths

### Critical Paths (90% Required)

#### Backend
- Authentication (`app/services/auth_service.py`)
- Session management (`app/services/session_service.py`)
- RBAC (`app/services/rbac_service.py`)
- Audit logging (`app/services/audit_service.py`)
- PHI encryption (`app/services/encryption_service.py`)
- Security middleware (`app/middleware/auth_middleware.py`)

#### Frontend
- Auth store (`src/stores/auth.ts`)
- Login form (`src/components/LoginForm.vue`)
- Protected routes (`src/router/guards.ts`)
- PHI data handling

### Viewing Coverage Reports

#### Backend HTML Report
```bash
cd backend
open htmlcov/index.html
```

#### Frontend HTML Report
```bash
cd frontend
open coverage/index.html
```

#### Terminal Summary
```bash
# Backend
pytest tests/ --cov=app --cov-report=term-missing

# Frontend
npm run test:coverage -- --reporter=default
```

---

## CI/CD Integration

### Workflows

#### `.github/workflows/test-backend.yml`
- Runs on: Push to main/develop, PRs
- Matrix: Python 3.11, 3.12
- Services: PostgreSQL, Redis
- Steps:
  - Lint (Black, isort)
  - Type check (mypy)
  - Run tests with coverage
  - Upload to Codecov
  - Security scan (Bandit, Safety)

#### `.github/workflows/test-frontend.yml`
- Runs on: Push to main/develop, PRs
- Matrix: Node 18.x, 20.x
- Steps:
  - Lint (ESLint)
  - Type check (vue-tsc)
  - Run tests with coverage
  - Build application
  - Upload to Codecov

#### `.github/workflows/test-all.yml`
- Orchestrates all tests
- Requires passing quality gates
- Posts coverage summaries to PRs
- Runs nightly (2 AM UTC)

### PR Checks

When you open a PR:

1. ✅ **Backend Tests** - All pytest tests pass
2. ✅ **Frontend Tests** - All vitest tests pass
3. ✅ **Code Quality** - Linting passes
4. ✅ **Type Safety** - Type checking passes
5. ✅ **Security** - No vulnerabilities detected
6. 📊 **Coverage** - Coverage reports posted to PR

### View in GitHub

- **Checks Tab**: See test results, logs, artifacts
- **Coverage Badge**: Link in PR description
- **Artifacts**: Download detailed reports (7-30 days retention)

---

## Best Practices

### Writing Tests

#### 1. **Use Test Markers** (Backend)
```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.e2e          # E2E tests
@pytest.mark.slow         # Slow tests
@pytest.mark.security     # Security-critical
@pytest.mark.compliance   # Compliance-related
```

#### 2. **Use Descriptive Names**
```python
# Good ✅
def test_login_fails_with_invalid_credentials(self):

# Bad ❌
def test_login(self):
```

#### 3. **Follow AAA Pattern** (Arrange-Act-Assert)
```python
def test_register_user_success(self):
    # Arrange
    user_data = {"email": "test@example.com", "password": "pass123"}

    # Act
    result = service.register(user_data)

    # Assert
    assert result.email == user_data["email"]
```

#### 4. **Test Error Cases**
```python
def test_login_invalid_password(self):
    # Should fail
    with pytest.raises(InvalidCredentialsError):
        service.authenticate("user@example.com", "wrong_password")
```

#### 5. **Mock External Services**
```python
def test_process_documents(self, mock_medcat_service):
    mock_medcat_service.get_entities.return_value = {
        "entities": [{"text": "diabetes", "cui": "C0011847"}]
    }

    result = service.process("Patient has diabetes")
    assert len(result) == 1
```

#### 6. **Test Database Isolation**
```python
def test_user_creation(self, db_session):
    user = create_user(db_session, "test@example.com")

    # Test uses db_session
    assert user.email == "test@example.com"

    # Automatically rolled back after test
```

#### 7. **Use Fixtures for Reusable Setup**
```python
@pytest.fixture
def authenticated_user(client, auth_headers):
    """User already logged in"""
    return client, auth_headers

def test_get_profile(self, authenticated_user):
    client, headers = authenticated_user
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
```

### Frontend Best Practices

#### 1. **Use Component Testing Library**
```typescript
import { mount } from '@vue/test-utils'
import LoginForm from '@/components/LoginForm.vue'

it('should render form', () => {
  const wrapper = mount(LoginForm)
  expect(wrapper.find('form').exists()).toBe(true)
})
```

#### 2. **Test User Interactions**
```typescript
it('should emit login on form submission', async () => {
  const wrapper = mount(LoginForm)
  await wrapper.find('input[type="email"]').setValue('test@example.com')
  await wrapper.find('button').trigger('click')

  expect(wrapper.emitted('login')).toBeTruthy()
})
```

#### 3. **Mock API Calls**
```typescript
import { mockAxios } from '@/tests/setup'

vi.mock('axios', () => ({ default: mockAxios }))

it('should fetch user data', async () => {
  mockAxios.get.mockResolvedValue({ data: { name: 'John' } })

  const response = await fetchUser()
  expect(response.name).toBe('John')
})
```

#### 4. **Test Store Actions**
```typescript
it('should login user', async () => {
  const store = useAuthStore()
  await store.login('test@example.com', 'password')

  expect(store.isAuthenticated).toBe(true)
  expect(store.user.email).toBe('test@example.com')
})
```

### Coverage Guidelines

#### Minimum Coverage
- **Backend**: 85% (all modules)
- **Frontend**: 85% (all modules)

#### Critical Paths (90%+)
- Authentication/authorization
- PHI/PII handling
- Audit logging
- Encryption/decryption
- Role-based access control

#### What NOT to Test Exhaustively
- Vue component template syntax (Vuetify handles this)
- External library code (only test our usage)
- Auto-generated code (migrations, etc.)

### Naming Conventions

#### Backend Test Files
```
test_<module>.py              # test_auth_service.py
test_<module>_<feature>.py    # test_auth_service_login.py
```

#### Frontend Test Files
```
<Component>.spec.ts           # LoginForm.spec.ts
<Store>.spec.ts              # auth.spec.ts
<Composable>.spec.ts         # useAuth.spec.ts
```

#### Test Classes/Suites
```python
class Test<Feature>:      # class TestAuthService:
    def test_<action>:    # def test_login_success:
```

---

## Troubleshooting

### Backend Issues

#### Database connection error
```
ERROR: can't connect to test database
```

**Solution**: Ensure pytest.ini has correct DATABASE_URL:
```ini
[pytest]
env =
    DATABASE_URL=sqlite:///:memory:
```

#### Import errors
```
ModuleNotFoundError: No module named 'app'
```

**Solution**: Install package in development mode:
```bash
cd backend
pip install -e .
```

#### Fixture not found
```
fixture 'db_session' not found
```

**Solution**: Ensure conftest.py is in tests/ directory and uses proper scope.

#### Coverage below threshold
```
FAILED Coverage: 84% is below 85%
```

**Solution**: Write more tests for uncovered code or review which code is truly critical.

### Frontend Issues

#### Tests not found
```
no tests found in src/
```

**Solution**: Tests must be in `tests/` directory with `.spec.ts` or `.test.ts` extension.

#### Component not rendering
```
Expected to have text "Login" but received ""
```

**Solution**: Ensure global plugins (Vuetify) are mounted:
```typescript
const wrapper = mount(LoginForm, {
  global: { plugins: [vuetify] }
})
```

#### Mock not working
```
ReferenceError: mockAxios is not defined
```

**Solution**: Import from setup file:
```typescript
import { mockAxios } from '@/tests/setup'
```

### General Issues

#### Tests hang or timeout
```
Test timeout exceeded (10000ms)
```

**Solution**:
- Check for unresolved promises
- Increase timeout: `testTimeout: 20000`
- Look for infinite loops or missing `await`

#### Intermittent failures
```
Test passes locally, fails in CI
```

**Solution**:
- Use `flushPromises()` for async operations
- Ensure proper test isolation
- Check for race conditions
- Avoid hardcoded timeouts

#### Coverage not updating
```
Coverage report shows old percentages
```

**Solution**: Clear coverage cache and rebuild:
```bash
rm -rf htmlcov/ .coverage coverage/
pytest tests/ --cov=app --cov-report=html
```

---

## Performance Optimization

### Backend

#### Parallel Test Execution
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

#### Skip Slow Tests During Development
```bash
pytest tests/ -m "not slow"
```

#### Database Optimization
- Uses SQLite in-memory (vs PostgreSQL in CI)
- Transactions auto-rollback (no cleanup needed)
- Connection pooling optimized

### Frontend

#### Parallel Test Execution
```bash
npm run test -- --threads 4 --maxThreads 8
```

#### Watch Mode
```bash
npm run test -- --watch
```

---

## Resources

### Documentation
- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Vue Test Utils](https://test-utils.vuejs.org/)
- [Codecov Integration](https://docs.codecov.io/docs)

### Tools
- [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage plugin
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) - Async support
- [@testing-library/vue](https://testing-library.com/docs/vue-testing-library/intro) - User-centric testing
- [Vitest UI](https://vitest.dev/guide/ui.html) - Visual test runner

---

## Support

For questions about testing:
1. Check this documentation
2. Review examples in existing tests
3. Check GitHub issues
4. Consult team documentation in CONTEXT.md
