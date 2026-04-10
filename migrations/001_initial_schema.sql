-- Migration: 001_initial_schema.sql
-- Description: Initial database schema for AI Voice Automation system
-- Requirements: 1.1, 5.4, 6.4, 7.2, 8.3, 15.1, 16.3
-- Created: 2024

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- CALLS TABLE
-- ============================================================================
-- Stores all call records with metadata, status, and intent information
CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_sid VARCHAR(255) UNIQUE NOT NULL,
    caller_phone VARCHAR(20) NOT NULL,
    caller_name VARCHAR(255),
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    status VARCHAR(20) NOT NULL,
    language VARCHAR(5) DEFAULT 'en',
    intent VARCHAR(50),
    intent_confidence DECIMAL(3,2),
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    recording_url TEXT,
    transcript_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Performance indexes for calls table
CREATE INDEX idx_calls_caller_phone ON calls(caller_phone);
CREATE INDEX idx_calls_started_at ON calls(started_at);
CREATE INDEX idx_calls_intent ON calls(intent);
CREATE INDEX idx_calls_status ON calls(status);
CREATE INDEX idx_calls_direction ON calls(direction);

-- ============================================================================
-- TRANSCRIPTS TABLE
-- ============================================================================
-- Stores conversation transcripts with speaker identification and timing
CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    speaker VARCHAR(20) NOT NULL CHECK (speaker IN ('caller', 'assistant', 'agent')),
    text TEXT NOT NULL,
    timestamp_ms INTEGER NOT NULL,
    language VARCHAR(5),
    confidence DECIMAL(3,2),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Performance indexes for transcripts table
CREATE INDEX idx_transcripts_call_id ON transcripts(call_id);
CREATE INDEX idx_transcripts_timestamp ON transcripts(timestamp_ms);
CREATE INDEX idx_transcripts_speaker ON transcripts(speaker);

-- ============================================================================
-- LEADS TABLE
-- ============================================================================
-- Stores captured lead information with qualification scores
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    inquiry_details TEXT,
    budget_indication VARCHAR(100),
    timeline VARCHAR(100),
    decision_authority BOOLEAN DEFAULT FALSE,
    lead_score INTEGER CHECK (lead_score BETWEEN 1 AND 10),
    source VARCHAR(50) DEFAULT 'voice_call',
    status VARCHAR(50) DEFAULT 'new',
    assigned_to VARCHAR(255),
    crm_id VARCHAR(255),
    crm_type VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Performance indexes for leads table
CREATE INDEX idx_leads_phone ON leads(phone);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_lead_score ON leads(lead_score);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_leads_call_id ON leads(call_id);

-- ============================================================================
-- APPOINTMENTS TABLE
-- ============================================================================
-- Stores scheduled appointments with calendar integration details
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id) ON DELETE SET NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_email VARCHAR(255),
    service_type VARCHAR(255) NOT NULL,
    appointment_datetime TIMESTAMP NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    status VARCHAR(50) DEFAULT 'scheduled',
    notes TEXT,
    confirmation_sent BOOLEAN DEFAULT FALSE,
    calendar_event_id VARCHAR(255),
    calendar_provider VARCHAR(50),
    reminder_sent BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Performance indexes for appointments table
CREATE INDEX idx_appointments_customer_phone ON appointments(customer_phone);
CREATE INDEX idx_appointments_appointment_datetime ON appointments(appointment_datetime);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_call_id ON appointments(call_id);
CREATE INDEX idx_appointments_lead_id ON appointments(lead_id);

-- ============================================================================
-- BUSINESS_CONFIG TABLE
-- ============================================================================
-- Stores business-specific configuration including hours, routing, and CRM settings
CREATE TABLE business_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id VARCHAR(255) UNIQUE NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    greeting_message TEXT,
    ai_personality TEXT,
    business_hours JSONB NOT NULL DEFAULT '{}',
    holiday_schedule JSONB DEFAULT '[]',
    routing_rules JSONB DEFAULT '{}',
    crm_config JSONB DEFAULT '{}',
    notification_config JSONB DEFAULT '{}',
    language_config JSONB DEFAULT '{"default": "en", "supported": ["en", "hi"]}',
    knowledge_base TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Performance indexes for business_config table
CREATE INDEX idx_business_config_business_id ON business_config(business_id);
CREATE INDEX idx_business_config_active ON business_config(active);

-- ============================================================================
-- CALL_ANALYTICS TABLE
-- ============================================================================
-- Aggregated analytics data for reporting and monitoring
CREATE TABLE call_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    hour INTEGER CHECK (hour BETWEEN 0 AND 23),
    total_calls INTEGER DEFAULT 0,
    answered_calls INTEGER DEFAULT 0,
    missed_calls INTEGER DEFAULT 0,
    average_duration_seconds DECIMAL(10,2),
    intent_distribution JSONB DEFAULT '{}',
    language_distribution JSONB DEFAULT '{}',
    leads_captured INTEGER DEFAULT 0,
    appointments_booked INTEGER DEFAULT 0,
    high_value_leads INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(business_id, date, hour)
);

-- Performance indexes for call_analytics table
CREATE INDEX idx_analytics_business_date ON call_analytics(business_id, date);
CREATE INDEX idx_analytics_date ON call_analytics(date);
CREATE INDEX idx_analytics_business_id ON call_analytics(business_id);

-- ============================================================================
-- CRM_SYNC_LOG TABLE
-- ============================================================================
-- Tracks CRM synchronization status with retry logic support
CREATE TABLE crm_sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    crm_type VARCHAR(50) NOT NULL,
    operation VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'success', 'failed')),
    attempt_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP,
    error_message TEXT,
    crm_record_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Performance indexes for crm_sync_log table
CREATE INDEX idx_crm_sync_status ON crm_sync_log(status);
CREATE INDEX idx_crm_sync_call_id ON crm_sync_log(call_id);
CREATE INDEX idx_crm_sync_lead_id ON crm_sync_log(lead_id);
CREATE INDEX idx_crm_sync_crm_type ON crm_sync_log(crm_type);
CREATE INDEX idx_crm_sync_pending ON crm_sync_log(status) WHERE status = 'pending';

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- ============================================================================
-- Automatically update updated_at timestamp on row modifications

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_calls_updated_at
    BEFORE UPDATE ON calls
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at
    BEFORE UPDATE ON appointments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_business_config_updated_at
    BEFORE UPDATE ON business_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_call_analytics_updated_at
    BEFORE UPDATE ON call_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crm_sync_log_updated_at
    BEFORE UPDATE ON crm_sync_log
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE calls IS 'Stores all inbound and outbound call records with metadata';
COMMENT ON TABLE transcripts IS 'Stores conversation transcripts with speaker identification';
COMMENT ON TABLE leads IS 'Stores captured lead information with qualification scores';
COMMENT ON TABLE appointments IS 'Stores scheduled appointments with calendar integration';
COMMENT ON TABLE business_config IS 'Stores business-specific configuration and settings';
COMMENT ON TABLE call_analytics IS 'Aggregated analytics data for reporting';
COMMENT ON TABLE crm_sync_log IS 'Tracks CRM synchronization status and retry attempts';

COMMENT ON COLUMN calls.call_sid IS 'Twilio call SID - unique identifier from Twilio';
COMMENT ON COLUMN calls.intent_confidence IS 'Confidence score for intent detection (0.00-1.00)';
COMMENT ON COLUMN leads.lead_score IS 'Lead qualification score (1-10, higher is better)';
COMMENT ON COLUMN appointments.duration_minutes IS 'Scheduled appointment duration in minutes';
COMMENT ON COLUMN crm_sync_log.attempt_count IS 'Number of sync attempts (for retry logic)';
