# Database Schema Documentation

## Overview

The Clinical Care Tools database contains 12 core tables organized into three categories:

1. **Authentication & Authorization** (3 tables)
2. **Project Management** (3 tables)
3. **Document & Data Processing** (4 tables)
4. **System Configuration** (1 table)
5. **Module-Specific** (2 tables)

## Entity Relationship Diagram

```
User
├── created_by (self-reference)
├── updated_by (self-reference)
└── 1:N relationships
    ├── sessions
    ├── audit_logs
    ├── projects_created
    ├── project_members
    ├── tasks_assigned
    └── documents_uploaded

Project
├── created_by → User
├── updated_by → User
└── 1:N relationships
    ├── project_members
    ├── tasks
    ├── documents
    └── extracted_entities

ProjectMember
├── project_id → Project
├── user_id → User
└── added_by → User

Task
├── project_id → Project
├── assigned_to → User
├── created_by → User
└── updated_by → User

Document
├── project_id → Project
├── uploaded_by → User
└── 1:N relationships
    └── extracted_entities

ExtractedEntity
├── document_id → Document
└── project_id → Project

Patient
└── source_document_ids (ARRAY of UUIDs)

Module
├── installed_by → User
└── updated_by → User

Session
└── user_id → User

AuditLog
└── user_id → User (optional)

PatientSearchResult
├── task_id → Task
└── user_id → User

TimelineView
├── task_id → Task
└── user_id → User
```

## Table Specifications

### Authentication & Authorization

#### users
Core user account model with authentication and authorization.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Auto-generated |
| username | VARCHAR(100) | UNIQUE, NOT NULL | Login identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Contact email |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hash |
| role | VARCHAR(50) | NOT NULL, CHECK | admin/clinician/researcher |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Account status |
| must_change_password | BOOLEAN | NOT NULL, DEFAULT true | First login flag |
| failed_login_attempts | INT | NOT NULL, DEFAULT 0 | Lockout counter |
| locked_until | TIMESTAMP | NULL | Lockout expiration |
| last_login | TIMESTAMP | NULL | Last successful login |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Account creation time |
| created_by | UUID | FK users(id) | Creator user ID |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |
| updated_by | UUID | FK users(id) | Updater user ID |

**Indexes**: username, email, role, is_active
**Constraints**: role IN ('admin', 'clinician', 'researcher'), failed_login_attempts >= 0

#### sessions
Active user sessions for token-based authentication.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Session ID |
| user_id | UUID | FK users(id), NOT NULL | User reference |
| token_hash | VARCHAR(255) | NOT NULL | SHA-256 hash of JWT |
| ip_address | VARCHAR(45) | NULL | Client IP (IPv4/IPv6) |
| user_agent | VARCHAR(500) | NULL | Client user agent |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Session start |
| expires_at | TIMESTAMP | NOT NULL | Token expiration |
| last_activity | TIMESTAMP | NOT NULL, DEFAULT now() | Last activity time |

**Indexes**: user_id, token_hash, expires_at, cleanup (where expires_at < now())
**Constraints**: expires_at > created_at

#### audit_logs
Immutable audit trail for HIPAA/GDPR compliance.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Log entry ID |
| user_id | UUID | FK users(id), NULL | User (NULL for system) |
| username | VARCHAR(100) | NOT NULL | Username at time of action |
| action | VARCHAR(100) | NOT NULL | login/logout/view/create/etc |
| resource_type | VARCHAR(100) | NOT NULL | user/project/document/patient |
| resource_id | VARCHAR(255) | NULL | Resource ID |
| resource_name | VARCHAR(255) | NULL | Human-readable resource name |
| details | JSON | NOT NULL, DEFAULT {} | Additional context |
| ip_address | VARCHAR(45) | NULL | Client IP |
| session_id | VARCHAR(255) | NULL | Session ID for correlation |
| timestamp | TIMESTAMP | NOT NULL, DEFAULT now() | Server-side timestamp |

**Indexes**: user_id, action, (resource_type, resource_id), timestamp DESC, session_id, (user_id, timestamp)
**Immutability**: No UPDATE or DELETE allowed (database rules prevent modification)

### Project Management

#### projects
Shared workspaces for collaborative work.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Project ID |
| name | VARCHAR(255) | UNIQUE, NOT NULL | Project name |
| description | VARCHAR(2000) | NOT NULL, DEFAULT '' | Description |
| project_type | VARCHAR(100) | NOT NULL | patient_search/timeline/cds/cohort/annotation |
| status | VARCHAR(50) | NOT NULL, DEFAULT 'active' | active/complete/archived |
| dataset_id | UUID | NULL | Dataset reference (future) |
| medcat_model_id | UUID | NULL | MedCAT model reference (future) |
| configuration | JSON | NOT NULL, DEFAULT {} | Project-specific config |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation time |
| created_by | UUID | FK users(id), NOT NULL | Creator |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |
| updated_by | UUID | FK users(id), NOT NULL | Last updater |

**Indexes**: name, project_type, status, created_by
**Constraints**: status IN ('active', 'complete', 'archived')

#### project_members
Project membership with role-based access.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Membership ID |
| project_id | UUID | FK projects(id) ON DELETE CASCADE, NOT NULL | Project |
| user_id | UUID | FK users(id) ON DELETE CASCADE, NOT NULL | User |
| role | VARCHAR(50) | NOT NULL, DEFAULT 'member' | owner/member/viewer |
| joined_at | TIMESTAMP | NOT NULL, DEFAULT now() | Join date |
| added_by | UUID | FK users(id), NOT NULL | User who added member |

**Indexes**: project_id, user_id, role
**Constraints**: UNIQUE(project_id, user_id), role IN ('owner', 'member', 'viewer')

#### tasks
User assignments and task management.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Task ID |
| project_id | UUID | FK projects(id) ON DELETE CASCADE, NOT NULL | Project |
| assigned_to | UUID | FK users(id), NOT NULL | Assignee |
| created_by | UUID | FK users(id), NOT NULL | Creator |
| updated_by | UUID | FK users(id), NOT NULL | Last updater |
| name | VARCHAR(255) | NOT NULL | Task name |
| description | VARCHAR(2000) | NOT NULL, DEFAULT '' | Description |
| task_type | VARCHAR(100) | NOT NULL | annotation/search/review/validation |
| status | VARCHAR(50) | NOT NULL, DEFAULT 'pending' | pending/in_progress/complete/cancelled |
| priority | VARCHAR(50) | NOT NULL, DEFAULT 'medium' | low/medium/high/urgent |
| configuration | JSON | NOT NULL, DEFAULT {} | Task-specific config |
| due_date | TIMESTAMP | NULL | Due date |
| completed_at | TIMESTAMP | NULL | Completion time |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |

**Indexes**: project_id, assigned_to, status, priority, due_date, created_by
**Constraints**: status IN (...), priority IN (...)

### Document & Data Processing

#### documents
Encrypted clinical documents storage.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Document ID |
| project_id | UUID | FK projects(id) ON DELETE CASCADE, NOT NULL | Project |
| uploaded_by | UUID | FK users(id), NOT NULL | Uploader |
| filename | VARCHAR(255) | NOT NULL | Original filename |
| file_type | VARCHAR(50) | NOT NULL, DEFAULT 'rtf' | rtf/txt/docx/pdf |
| file_size | INT | NOT NULL | File size in bytes |
| content | BYTEA | NOT NULL | AES-256 encrypted content |
| content_hash | VARCHAR(64) | NOT NULL | SHA-256 hash for dedup |
| encryption_key_id | VARCHAR(100) | NOT NULL | Reference to KMS key |
| document_type | VARCHAR(100) | NULL | clinical_letter/discharge_summary/etc |
| document_date | TIMESTAMP | NULL | Date on document |
| author | VARCHAR(255) | NULL | Document author |
| medcat_status | VARCHAR(50) | NOT NULL, DEFAULT 'pending' | pending/processing/complete/failed |
| medcat_processed_at | TIMESTAMP | NULL | Processing completion time |
| medcat_error | VARCHAR(2000) | NULL | Error message if failed |
| contains_phi | BOOLEAN | NOT NULL, DEFAULT true | PHI indicator |
| phi_types | ARRAY | NOT NULL | Array of PHI types found |
| uploaded_at | TIMESTAMP | NOT NULL, DEFAULT now() | Upload time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |

**Indexes**: project_id, content_hash, medcat_status, uploaded_by, uploaded_at DESC, document_type
**Constraints**: file_size > 0 AND file_size < 10485760 (10MB), medcat_status IN (...)

#### extracted_entities
Medical entities extracted by MedCAT NLP.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Entity ID |
| document_id | UUID | FK documents(id) ON DELETE CASCADE, NOT NULL | Source document |
| project_id | UUID | FK projects(id) ON DELETE CASCADE, NOT NULL | Project |
| cui | VARCHAR(20) | NOT NULL | UMLS/SNOMED-CT concept |
| concept_name | VARCHAR(500) | NOT NULL | Human-readable name |
| source_value | VARCHAR(2000) | NOT NULL | Text from document |
| start_char | INT | NOT NULL | Character position |
| end_char | INT | NOT NULL | Character position |
| confidence | FLOAT | NOT NULL | MedCAT confidence (0.0-1.0) |
| meta_annotations | JSON | NOT NULL, DEFAULT {} | MetaCAT results |
| entity_type | VARCHAR(100) | NOT NULL | PERSON/NHS_NUMBER/DATE/etc |
| is_phi | BOOLEAN | NOT NULL, DEFAULT false | PHI flag |
| phi_category | VARCHAR(100) | NULL | DIRECT_IDENTIFIER/QUASI_IDENTIFIER/etc |
| structured_data | JSON | NULL | Type-specific fields |
| extracted_at | TIMESTAMP | NOT NULL, DEFAULT now() | Extraction time |
| medcat_version | VARCHAR(50) | NOT NULL | MedCAT version used |

**Indexes**: document_id, project_id, cui, entity_type, is_phi, structured_data (GIN)
**Constraints**: confidence >= 0.0 AND confidence <= 1.0, end_char > start_char

#### patients
Aggregated patient records from extracted entities.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Patient ID |
| nhs_number | VARCHAR(10) | UNIQUE, NULL | NHS number (10 digits) |
| mrn | VARCHAR(50) | UNIQUE, NULL | Medical Record Number |
| first_name | VARCHAR(100) | NULL | First name |
| last_name | VARCHAR(100) | NULL | Last name |
| date_of_birth | DATE | NULL | Date of birth |
| gender | VARCHAR(20) | NULL | Gender |
| address_line1 | VARCHAR(255) | NULL | Address line 1 |
| address_line2 | VARCHAR(255) | NULL | Address line 2 |
| city | VARCHAR(100) | NULL | City |
| postcode | VARCHAR(10) | NULL | Postcode |
| source_document_ids | ARRAY | NOT NULL | Document UUIDs |
| last_updated_from | UUID | NULL | Most recent source doc |
| confidence_score | FLOAT | NULL | Patient match confidence |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |

**Indexes**: nhs_number (unique where not null), mrn (unique where not null), last_name, postcode, updated_at DESC
**Constraints**: nhs_number IS NOT NULL OR mrn IS NOT NULL, nhs_number ~ '^\d{10}$'

### System Configuration

#### modules
Installed system modules registry.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Module ID |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Kebab-case name |
| display_name | VARCHAR(255) | NOT NULL | Human-readable name |
| description | VARCHAR(2000) | NOT NULL, DEFAULT '' | Description |
| version | VARCHAR(50) | NOT NULL | Semantic version |
| is_enabled | BOOLEAN | NOT NULL, DEFAULT true | Active flag |
| configuration | JSON | NOT NULL, DEFAULT {} | Module config |
| permissions | JSON | NOT NULL, DEFAULT [] | Permission array |
| routes | JSON | NOT NULL, DEFAULT [] | Route definitions |
| installed_at | TIMESTAMP | NOT NULL, DEFAULT now() | Installation time |
| installed_by | UUID | FK users(id), NOT NULL | Installer |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |
| updated_by | UUID | FK users(id), NULL | Last updater |

**Indexes**: name, is_enabled

### Module-Specific Tables

#### patient_search_results
Patient Search module results.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Result ID |
| task_id | UUID | FK tasks(id) ON DELETE CASCADE, NOT NULL | Task |
| user_id | UUID | FK users(id), NOT NULL | User |
| query | JSON | NOT NULL | Search criteria |
| result_count | INT | NOT NULL | Result count |
| results | JSON | NOT NULL | Result data |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation time |

**Indexes**: task_id, user_id

#### timeline_views
Timeline module view tracking.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | View ID |
| task_id | UUID | FK tasks(id) ON DELETE CASCADE, NOT NULL | Task |
| user_id | UUID | FK users(id), NOT NULL | User |
| patient_id | VARCHAR(255) | NOT NULL | Patient identifier |
| viewed_at | TIMESTAMP | NOT NULL, DEFAULT now() | View time |

**Indexes**: task_id, user_id, patient_id

## Data Flow Example: Patient Search Workflow

1. **User Uploads Document**
   - `Document` created with encrypted content
   - `medcat_status` set to 'pending'
   - `AuditLog` entry created (action='create', resource='document')

2. **MedCAT Processes Document**
   - Document content decrypted in-memory
   - MedCAT extracts entities
   - `ExtractedEntity` records created for each entity
   - `medcat_status` updated to 'complete' or 'failed'
   - `AuditLog` entry created (action='update', resource='document')

3. **Patient Record Aggregation**
   - System identifies PHI entities (name, NHS number, DOB, address)
   - `Patient` record created or updated
   - `source_document_ids` array updated
   - `confidence_score` calculated from entity confidence values

4. **User Searches for Patient**
   - User creates search `Task`
   - Search query filters `ExtractedEntity` records
   - `PatientSearchResult` created with results
   - `AuditLog` entry created (action='search', resource='patient', details contains query)

5. **User Views Patient Timeline**
   - User navigates to patient timeline
   - `TimelineView` entry created
   - System retrieves `Document` records for patient
   - Decrypts content and displays timeline
   - `AuditLog` entry created (action='view', resource='patient')

## Security Notes

1. **Encryption at Rest**
   - Document content encrypted with AES-256
   - Encryption key stored separately in KMS/HSM
   - Never persist unencrypted PHI in database

2. **Audit Trail**
   - All PHI access logged to `audit_logs`
   - Logs are immutable (database constraints prevent modification)
   - 7-year retention policy for healthcare compliance

3. **Access Control**
   - User roles: admin, clinician, researcher
   - Project membership controls document access
   - RBAC enforced at API layer

4. **Data Retention**
   - Documents retained per project settings
   - Audit logs retained 7 years (2555 days)
   - Soft delete could be implemented via `deleted_at` column

## Performance Considerations

1. **Indexing Strategy**
   - All foreign keys indexed
   - Frequent filter columns indexed (status, role, type)
   - GIN index on JSON columns for fast filtering
   - DESC index on timestamp columns for latest-first queries

2. **Query Patterns**
   - Join Project → ProjectMember → User for access control
   - Join Document → ExtractedEntity for cohort identification
   - Use ARRAY queries on `source_document_ids` for patient history

3. **Partitioning (Production)**
   - Partition `audit_logs` by month (large table)
   - Partition `extracted_entities` by project (many rows)
   - Use partial indexes for soft deletes if implemented

## Future Extensions

1. **Soft Deletes**
   - Add `deleted_at` column to users, projects, documents
   - Use partial indexes where deleted_at IS NULL
   - Soft delete audit logs after retention period

2. **Change Data Capture**
   - Add CDC triggers to replicate changes to audit system
   - Enable time-travel queries (temporal tables)

3. **Full-Text Search**
   - Add tsvector columns to documents and extracted_entities
   - Enable full-text search on clinical content

4. **Data Warehouse**
   - Replicate data to analytical database
   - Create fact tables for reporting
   - Maintain real-time analytics dashboard
