-- Clinical Care Tools - PostgreSQL Database Initialization Script
-- Version: 1.0.0
-- Created: 2025-01-08
-- Purpose: Initialize PostgreSQL database schema with all required tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema
CREATE SCHEMA IF NOT EXISTS clinical_care;

-- Set search path
SET search_path TO clinical_care, public;

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'clinician',
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    CHECK (role IN ('admin', 'clinician', 'researcher', 'analyst', 'audit_viewer'))
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ============================================================================
-- PATIENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mrn VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    dob DATE NOT NULL,
    gender VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    metadata JSONB DEFAULT '{}',
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
    CHECK (gender IN ('M', 'F', 'Other', 'Prefer not to say', NULL))
);

CREATE INDEX idx_patients_mrn ON patients(mrn);
CREATE INDEX idx_patients_name ON patients(first_name, last_name);
CREATE INDEX idx_patients_dob ON patients(dob);
CREATE INDEX idx_patients_created_at ON patients(created_at);

-- ============================================================================
-- DOCUMENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL,
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500),
    document_type VARCHAR(100),
    content_type VARCHAR(100),
    file_size BIGINT,
    content BYTEA,
    text_content TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    extracted BOOLEAN DEFAULT false,
    extracted_at TIMESTAMP WITH TIME ZONE,
    extraction_error TEXT,
    entity_count INTEGER DEFAULT 0,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    CHECK (status IN ('pending', 'processing', 'extracted', 'error')),
    CHECK (document_type IN ('clinical_note', 'lab_report', 'discharge_summary', 'imaging_report', 'medication_list', 'other', NULL))
);

CREATE INDEX idx_documents_patient_id ON documents(patient_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_extracted ON documents(extracted);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at);
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);

-- ============================================================================
-- ENTITIES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    cui VARCHAR(20) NOT NULL,
    name VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    confidence_score NUMERIC(5,2) CHECK (confidence_score >= 0 AND confidence_score <= 100),
    char_span_start INTEGER,
    char_span_end INTEGER,
    matched_text VARCHAR(500),
    negation VARCHAR(50) DEFAULT 'Affirmed',
    temporality VARCHAR(50) DEFAULT 'Current',
    experiencer VARCHAR(50) DEFAULT 'Patient',
    certainty VARCHAR(50) DEFAULT 'Definite',
    additional_annotations JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    CHECK (negation IN ('Affirmed', 'Negated', 'Unknown')),
    CHECK (temporality IN ('Recent', 'Current', 'Historical', 'Unknown')),
    CHECK (experiencer IN ('Patient', 'Family', 'Other', 'Unknown')),
    CHECK (certainty IN ('Definite', 'Probable', 'Possible', 'Unknown'))
);

CREATE INDEX idx_entities_document_id ON entities(document_id);
CREATE INDEX idx_entities_patient_id ON entities(patient_id);
CREATE INDEX idx_entities_cui ON entities(cui);
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_confidence_score ON entities(confidence_score);
CREATE INDEX idx_entities_negation ON entities(negation);
CREATE INDEX idx_entities_temporality ON entities(temporality);
CREATE INDEX idx_entities_experiencer ON entities(experiencer);
CREATE INDEX idx_entities_certainty ON entities(certainty);
CREATE INDEX idx_entities_created_at ON entities(created_at);

-- Full-text search index on entity names
CREATE INDEX idx_entities_name_text ON entities USING gin(to_tsvector('english', name));

-- ============================================================================
-- AUDIT_LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    username VARCHAR(255),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    resource_name VARCHAR(500),
    ip_address VARCHAR(50),
    user_agent TEXT,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    details JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CHECK (action IN ('VIEW', 'CREATE', 'UPDATE', 'DELETE', 'EXPORT', 'SEARCH', 'LOGIN', 'LOGOUT', 'ERROR')),
    CHECK (status IN ('success', 'failure')),
    CHECK (resource_type IN ('patient', 'document', 'entity', 'user', 'cohort', 'system', NULL))
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp);

-- Partition audit_logs by month for better performance
CREATE TABLE IF NOT EXISTS audit_logs_2025_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE IF NOT EXISTS audit_logs_2025_02 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- ============================================================================
-- SESSIONS TABLE (for Redis-backed session management)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id UUID NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- ============================================================================
-- COHORTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS cohorts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    criteria JSONB NOT NULL,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    patient_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_cohorts_created_by ON cohorts(created_by);
CREATE INDEX idx_cohorts_created_at ON cohorts(created_at);
CREATE INDEX idx_cohorts_is_active ON cohorts(is_active);

-- ============================================================================
-- COHORT_PATIENTS TABLE (Junction table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cohort_patients (
    cohort_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cohort_id, patient_id),
    FOREIGN KEY (cohort_id) REFERENCES cohorts(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE INDEX idx_cohort_patients_cohort_id ON cohort_patients(cohort_id);
CREATE INDEX idx_cohort_patients_patient_id ON cohort_patients(patient_id);

-- ============================================================================
-- CREATE DEFAULT ADMIN USER (Change password on first login!)
-- ============================================================================

-- Hash of 'admin123' using bcrypt (should be replaced in production)
-- You can generate a proper hash using:
-- python3 -c "from passlib.context import CryptContext; pwd = CryptContext(schemes=['bcrypt']); print(pwd.hash('admin123'))"

INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active)
VALUES (
    'admin',
    'admin@clinical-care-tools.local',
    '$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',  -- Placeholder - CHANGE THIS!
    'System',
    'Administrator',
    'admin',
    true
) ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- CREATE VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Patient overview with document and entity counts
CREATE OR REPLACE VIEW patient_overview AS
SELECT
    p.id,
    p.mrn,
    p.first_name,
    p.last_name,
    p.dob,
    EXTRACT(YEAR FROM AGE(p.dob))::INT AS age,
    p.gender,
    COUNT(DISTINCT d.id) AS document_count,
    COUNT(DISTINCT e.id) AS entity_count,
    MAX(d.uploaded_at) AS last_document_date,
    p.created_at,
    p.updated_at
FROM patients p
LEFT JOIN documents d ON p.id = d.patient_id
LEFT JOIN entities e ON p.id = e.patient_id
GROUP BY p.id;

-- Patient search results (for search queries)
CREATE OR REPLACE VIEW patient_search_results AS
SELECT
    p.id,
    p.mrn,
    p.first_name,
    p.last_name,
    e.cui,
    e.name,
    COUNT(*) AS mention_count,
    AVG(e.confidence_score) AS avg_confidence,
    MAX(d.uploaded_at) AS last_mention_date
FROM patients p
JOIN entities e ON p.id = e.patient_id
JOIN documents d ON e.document_id = d.id
GROUP BY p.id, p.mrn, p.first_name, p.last_name, e.cui, e.name;

-- ============================================================================
-- GRANT PERMISSIONS (for security)
-- ============================================================================

-- Clinical user permissions
CREATE ROLE clinical_user NOLOGIN;
GRANT USAGE ON SCHEMA clinical_care TO clinical_user;
GRANT SELECT ON ALL TABLES IN SCHEMA clinical_care TO clinical_user;
GRANT INSERT ON users, patients, documents, entities, audit_logs TO clinical_user;
GRANT UPDATE ON patients, documents TO clinical_user;

-- Researcher permissions (read-only)
CREATE ROLE research_user NOLOGIN;
GRANT USAGE ON SCHEMA clinical_care TO research_user;
GRANT SELECT ON ALL TABLES IN SCHEMA clinical_care TO research_user;

-- Admin user (full access)
CREATE ROLE admin_user NOLOGIN;
GRANT USAGE ON SCHEMA clinical_care TO admin_user;
GRANT ALL ON ALL TABLES IN SCHEMA clinical_care TO admin_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA clinical_care TO admin_user;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Enable logging of all DDL statements
SET log_statement = 'all';

-- End of initialization script
-- Database is now ready for application use
