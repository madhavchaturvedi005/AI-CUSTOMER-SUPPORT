-- Migration: Add company_description column to business_config table
-- Purpose: Store detailed company description for AI system prompt
-- Date: 2026-04-10

-- Add company_description column if it doesn't exist
ALTER TABLE business_config
ADD COLUMN IF NOT EXISTS company_description TEXT DEFAULT '';

-- Add comment to document the column
COMMENT ON COLUMN business_config.company_description IS 'Detailed company description used in AI system prompt to provide context about the business';
