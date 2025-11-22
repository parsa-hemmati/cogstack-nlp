# API Documentation

Complete REST API reference for the Clinical Care Tools backend.

## Quick Links

- **API Base URL**: `http://localhost:8000` (development)
- **API Documentation**: `http://localhost:8000/api/docs` (Swagger UI)
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## Authentication

All API endpoints (except `/auth/*`) require authentication via JWT token.

### Login Endpoint

**Obtain JWT Token**

```
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

### Token Usage

Include token in Authorization header:

```
Authorization: Bearer {access_token}
```

### Refresh Token

**Obtain New Access Token**

```
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "{refresh_token}"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

### Token Expiration

- **Access Token**: 8 hours (configurable)
- **Refresh Token**: 7 days (configurable)

## API Endpoints

### Health & Status

#### Health Check
```
GET /api/health
```

**Response**:
```json
{
  "status": "ok",
  "timestamp": "2025-01-08T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "nlp_service": "healthy"
  }
}
```

### Authentication

#### User Login
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

#### User Logout
```
POST /api/auth/logout
Authorization: Bearer {token}
```

#### Refresh Token
```
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "string"
}
```

#### Get Current User
```
GET /api/auth/me
Authorization: Bearer {token}
```

**Response**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "created_at": "2025-01-08T10:00:00Z"
}
```

### Patients

#### List Patients
```
GET /api/patients?skip=0&limit=20
Authorization: Bearer {token}
```

**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 20, max: 100)

**Response**:
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "mrn": "MRN123456",
      "first_name": "John",
      "last_name": "Doe",
      "dob": "1960-05-15",
      "gender": "M",
      "created_at": "2025-01-08T10:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

#### Search Patients
```
POST /api/patients/search
Content-Type: application/json
Authorization: Bearer {token}

{
  "concept": "Type 2 Diabetes",
  "filters": {
    "negation": "Affirmed",
    "temporality": "Current",
    "experiencer": "Patient",
    "certainty": "Definite"
  },
  "limit": 20
}
```

**Response**:
```json
{
  "results": [
    {
      "patient_id": "123e4567-e89b-12d3-a456-426614174000",
      "mrn": "MRN123456",
      "first_name": "John",
      "last_name": "Doe",
      "score": 0.95,
      "matching_documents": 5,
      "last_mention": "2024-12-15"
    }
  ],
  "total": 42,
  "query_time_ms": 234
}
```

#### Get Patient Details
```
GET /api/patients/{patient_id}
Authorization: Bearer {token}
```

**Response**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "mrn": "MRN123456",
  "first_name": "John",
  "last_name": "Doe",
  "dob": "1960-05-15",
  "gender": "M",
  "age": 64,
  "document_count": 127,
  "entity_count": 3421,
  "created_at": "2025-01-08T10:00:00Z",
  "updated_at": "2025-01-08T10:00:00Z"
}
```

#### Create Patient
```
POST /api/patients
Content-Type: application/json
Authorization: Bearer {token}

{
  "mrn": "MRN123456",
  "first_name": "John",
  "last_name": "Doe",
  "dob": "1960-05-15",
  "gender": "M"
}
```

#### Update Patient
```
PUT /api/patients/{patient_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "first_name": "Jane",
  "gender": "F"
}
```

#### Delete Patient
```
DELETE /api/patients/{patient_id}
Authorization: Bearer {token}
```

### Documents

#### Upload Document
```
POST /api/documents/upload
Authorization: Bearer {token}

Content-Type: multipart/form-data
- file: (binary file - RTF, PDF, or TXT)
- patient_id: (UUID string)
- document_type: (optional: clinical_note, lab_report, discharge_summary, etc)
```

**Response**:
```json
{
  "id": "doc-123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "pat-123e4567-e89b-12d3-a456-426614174000",
  "filename": "clinical_note_2024.rtf",
  "document_type": "clinical_note",
  "status": "processing",
  "uploaded_at": "2025-01-08T10:00:00Z",
  "extraction_status": "pending"
}
```

#### List Patient Documents
```
GET /api/patients/{patient_id}/documents?skip=0&limit=20
Authorization: Bearer {token}
```

**Response**:
```json
{
  "items": [
    {
      "id": "doc-123e4567-e89b-12d3-a456-426614174000",
      "filename": "clinical_note_2024.rtf",
      "document_type": "clinical_note",
      "uploaded_at": "2025-01-08T10:00:00Z",
      "status": "extracted",
      "entity_count": 342
    }
  ],
  "total": 127,
  "skip": 0,
  "limit": 20
}
```

#### Get Document Details
```
GET /api/documents/{document_id}
Authorization: Bearer {token}
```

**Response**:
```json
{
  "id": "doc-123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "pat-123e4567-e89b-12d3-a456-426614174000",
  "filename": "clinical_note_2024.rtf",
  "document_type": "clinical_note",
  "uploaded_at": "2025-01-08T10:00:00Z",
  "status": "extracted",
  "content_preview": "Patient presents with Type 2 Diabetes...",
  "entity_count": 342
}
```

#### Get Document Content
```
GET /api/documents/{document_id}/content
Authorization: Bearer {token}
```

**Response**: Binary file (RTF, PDF, or TXT)

#### Delete Document
```
DELETE /api/documents/{document_id}
Authorization: Bearer {token}
```

### Entities

#### Get Document Entities
```
GET /api/documents/{document_id}/entities?skip=0&limit=50
Authorization: Bearer {token}
```

**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 50)

**Response**:
```json
{
  "items": [
    {
      "id": "ent-123e4567-e89b-12d3-a456-426614174000",
      "cui": "C0011849",
      "name": "Diabetes Mellitus, Type 2",
      "confidence_score": 0.95,
      "char_span": {
        "start": 32,
        "end": 47
      },
      "meta_annotations": {
        "Negation": "Affirmed",
        "Temporality": "Current",
        "Experiencer": "Patient",
        "Certainty": "Definite"
      },
      "position_in_text": "Patient presents with Type 2 Diabetes"
    }
  ],
  "total": 342,
  "skip": 0,
  "limit": 50
}
```

#### Search Entities
```
POST /api/entities/search
Content-Type: application/json
Authorization: Bearer {token}

{
  "concept": "diabetes",
  "patient_id": "pat-123e4567-e89b-12d3-a456-426614174000",
  "filters": {
    "negation": "Affirmed",
    "min_confidence": 0.8
  },
  "limit": 100
}
```

### Export

#### Export Patient Data
```
POST /api/patients/{patient_id}/export
Content-Type: application/json
Authorization: Bearer {token}

{
  "format": "csv",
  "include": ["demographics", "entities", "timeline"]
}
```

**Format Options**:
- `csv`: Comma-separated values
- `json`: JSON format
- `fhir`: FHIR R4 bundles

**Response**: Binary file (CSV, JSON, or XML)

#### Export Cohort
```
POST /api/cohorts/{cohort_id}/export
Content-Type: application/json
Authorization: Bearer {token}

{
  "format": "csv"
}
```

### User Management

#### List Users
```
GET /api/users?skip=0&limit=20
Authorization: Bearer {token}
```

**Note**: Only admin users can access this endpoint

#### Create User
```
POST /api/users
Content-Type: application/json
Authorization: Bearer {token}

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "role": "clinician"
}
```

**Role Options**:
- `admin`: Full system access
- `clinician`: Patient data access
- `researcher`: Read-only access

#### Update User
```
PUT /api/users/{user_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "email": "newemail@example.com",
  "role": "researcher"
}
```

#### Delete User
```
DELETE /api/users/{user_id}
Authorization: Bearer {token}
```

### Audit Logs

#### Get Audit Logs
```
GET /api/audit-logs?skip=0&limit=100&resource_type=patient
Authorization: Bearer {token}
```

**Query Parameters**:
- `skip`: Number of records to skip
- `limit`: Maximum records to return
- `resource_type`: Filter by resource type (patient, document, etc)
- `user_id`: Filter by user
- `action`: Filter by action (VIEW, EXPORT, CREATE, DELETE)
- `start_date`: Filter by start date (ISO 8601)
- `end_date`: Filter by end date (ISO 8601)

**Response**:
```json
{
  "items": [
    {
      "id": 1,
      "user_id": "usr-123e4567-e89b-12d3-a456-426614174000",
      "username": "admin",
      "action": "VIEW",
      "resource_type": "patient",
      "resource_id": "pat-123e4567-e89b-12d3-a456-426614174000",
      "ip_address": "192.168.1.100",
      "timestamp": "2025-01-08T10:30:00Z",
      "details": {
        "reason": "Clinical decision support"
      }
    }
  ],
  "total": 15234,
  "skip": 0,
  "limit": 100
}
```

## Error Handling

### Error Response Format

```json
{
  "detail": "Resource not found",
  "error_code": "NOT_FOUND",
  "status": 404
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful request |
| 201 | Created | Resource created |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate resource |
| 422 | Unprocessable | Validation error |
| 500 | Server Error | Internal error |
| 503 | Service Unavailable | Service down |

### Common Errors

#### Invalid Credentials
```json
{
  "detail": "Incorrect username or password",
  "error_code": "INVALID_CREDENTIALS",
  "status": 401
}
```

#### Token Expired
```json
{
  "detail": "Token has expired",
  "error_code": "TOKEN_EXPIRED",
  "status": 401
}
```

#### Insufficient Permissions
```json
{
  "detail": "You do not have permission to access this resource",
  "error_code": "FORBIDDEN",
  "status": 403
}
```

#### Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "concept"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "error_code": "VALIDATION_ERROR",
  "status": 422
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Authenticated Users**: 100 requests/minute
- **Search Queries**: 10 requests/minute per user
- **Upload Operations**: 5 requests/minute per user

Rate limit headers in response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641658000
```

## Pagination

List endpoints support pagination:

**Query Parameters**:
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum items to return (default: 20, max: 100)

**Response Format**:
```json
{
  "items": [...],
  "total": 1000,
  "skip": 0,
  "limit": 20
}
```

**Example**:
```
GET /api/patients?skip=20&limit=20
```

## Filtering & Searching

### Meta-Annotation Filters

When searching or filtering, use these values:

**Negation**:
- `Affirmed`: Concept is present/true
- `Negated`: Concept is absent/false

**Temporality**:
- `Recent`: Recent or recent past
- `Current`: Currently occurring
- `Historical`: Historical or past

**Experiencer**:
- `Patient`: Applies to the patient
- `Family`: Applies to family member
- `Other`: Applies to other person

**Certainty**:
- `Definite`: Certain/confirmed
- `Probable`: Likely/probable
- `Possible`: Possible/uncertain

## Cross-Origin Requests (CORS)

CORS is enabled for:
- `http://localhost:8080` (development frontend)
- `http://localhost:3000` (alternative dev frontend)
- Configure in `.env`: `CORS_ORIGINS`

Production should restrict to specific origins.

## Postman Collection

Import the collection for testing:

```bash
# Download from
GET /api/postman-collection

# Or use the provided JSON file
clinical-care-tools.postman_collection.json
```

## WebSocket Connections (Optional)

Real-time updates for document processing:

```
WS ws://localhost:8000/ws/{user_id}
```

**Message Format**:
```json
{
  "type": "extraction_complete",
  "document_id": "doc-123...",
  "entity_count": 342,
  "timestamp": "2025-01-08T10:00:00Z"
}
```

## Versioning

The API uses URL-based versioning:

- Current Version: `v1`
- Future: `v2`, `v3`, etc.

Base URL: `/api/v1/`

Migration guide provided for version upgrades.

## Performance Tips

1. **Use pagination** - Don't request all records at once
2. **Cache results** - Store search results client-side
3. **Batch operations** - Upload multiple documents together
4. **Use filters** - Narrow results with meta-annotations
5. **Monitor response times** - Log slow queries

## Examples

### Search for Type 2 Diabetes Patients

```bash
curl -X POST http://localhost:8000/api/patients/search \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "concept": "Type 2 Diabetes",
    "filters": {
      "negation": "Affirmed",
      "temporality": "Current"
    }
  }'
```

### Upload and Extract Document

```bash
# 1. Upload document
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer {token}" \
  -F "patient_id=pat-123..." \
  -F "file=@clinical_note.rtf"

# 2. Get extracted entities
curl -X GET "http://localhost:8000/api/documents/doc-123.../entities" \
  -H "Authorization: Bearer {token}"
```

### Export Patient Cohort

```bash
curl -X POST http://localhost:8000/api/patients/export \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"format": "csv"}' \
  -o cohort.csv
```

---

**Last Updated**: 2025-01-08
**Version**: 1.0.0
**OpenAPI Schema**: http://localhost:8000/openapi.json
