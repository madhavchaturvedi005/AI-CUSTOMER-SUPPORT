-- Rollback Migration: 001_initial_schema.sql
-- Description: Drops all tables and functions created by initial schema migration
-- WARNING: This will permanently delete all data in these tables

-- Drop tables in reverse order of dependencies
DROP TABLE IF EXISTS crm_sync_log CASCADE;
DROP TABLE IF EXISTS call_analytics CASCADE;
DROP TABLE IF EXISTS business_config CASCADE;
DROP TABLE IF EXISTS appointments CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS transcripts CASCADE;
DROP TABLE IF EXISTS calls CASCADE;

-- Drop the trigger function
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Note: The pgcrypto extension is not dropped as it may be used by other schemas
-- If you need to drop it, run: DROP EXTENSION IF EXISTS pgcrypto;
