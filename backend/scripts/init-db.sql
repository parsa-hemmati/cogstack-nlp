-- Database initialization script for Clinical Care Tools
-- This file is executed once when postgres container first starts
--
-- Note: Database, user, and basic auth are already configured via POSTGRES_* env vars
-- This file is for any additional schema setup needed before Alembic migrations

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- For UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- For text similarity/search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For multi-column indexes

-- Ensure UTF-8 encoding
SET client_encoding = 'UTF8';

-- Schema is managed by Alembic migrations
-- This file only handles extension setup
