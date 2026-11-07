-- =============================================================================
-- PostgreSQL initialization script
-- Enables required extensions for SNOMED/SDD search
-- =============================================================================

-- Full-text search is built-in; enable trigram for fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

