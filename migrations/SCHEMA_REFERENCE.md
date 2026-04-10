# Database Schema Reference

## Overview

This document provides a quick reference for the AI Voice Automation system database schema.

## Tables

### 1. calls

Stores all inbound and outbound call records with metadata.

**Primary Key**: `id` (UUID)

**Key Columns**:
- `call_sid` (VARCHAR, UNIQUE) - Twilio call identifier
- `caller_phone` (VARCHAR) - Caller's phone number
- `direction` (VARCHAR) - 'inbound' or 'outbound'
- `status` (VARCHAR) - Call status
- `intent` (VARCHAR) - Detected caller intent
- `intent_confidence` (DECIMAL) - Confidence score (0.00-1.00)
- `started_at`, `ended_at` (TIMESTAMP) - Call timing
- `duration_seconds` (INTEGER) - Call duration
- `recording_url`, `transcript_url` (TEXT) - Media URLs
- `metadata` (JSONB) - Flexible metadata storage

**Indexes**: caller_phone, started_at, intent, status, direction

**Foreign Keys**: None (parent table)

---

### 2. transcripts

Stores conversation transcripts with speaker identification.

**Primary Key**: `id` (UUID)

**Key Columns**:
- `call_id` (UUID, FK) - References calls.id
- `speaker` (VARCHAR) - 'caller', 'assistant', or 'agent'
- `text` (TEXT) - Transcript text
- `timestamp_ms` (INTEGER) - Timestamp in milliseconds
- `language` (VARCHAR) - Language code
- `confidence` (DECIMAL) - Transcription confidence

**Indexes**: call_id, timestamp_ms, speaker

**Foreign Keys**: 
- `call_id` → `calls.id` (CASCADE DELETE)

---

### 3. leads

Stores captured lead information with qualification scores.

**Primary Key**: `id` (UUID)

**Key Columns**:
- `call_id` (UUID, FK) - References calls.id
- `name`, `phone`, `email` (VARCHAR) - Contact information
- `inquiry_details` (TEXT) - Lead inquiry description
- `budget_indication`, `timeline` (VARCHAR) - Qualification data
- `decision_authority` (BOOLEAN) - Decision maker flag
- `lead_score` (INTEGER) - Score 1-10
- `status` (VARCHAR) - Lead status (default: 'new')
- `crm_id`, `crm_type` (VARCHAR) - CRM integration fields
- `metadata` (JSONB) - Additional lead data

**Indexes**: phone, email, lead_score, status, created_at, call_id

**Foreign Keys**: 
- `call_id` → `calls.id` (SET NULL on delete)

---

### 4. appointments

Stores scheduled appointments with calendar integration.

**Primary Key**: `id` (UUID)

**Key Columns**:
- `call_id` (UUID, FK) - References calls.id
- `lead_id` (UUID, FK) - References leads.id
- `customer_name`, `customer_phone`, `customer_email` (VARCHAR) - Customer info
- `service_type` (VARCHAR) - Type of service
- `appointment_datetime` (TIMESTAMP) - Scheduled time
- `duration_minutes` (INTEGER) - Duration (default: 30)
- `status` (VARCHAR) - Appointment status (default: 'scheduled')
- `confirmation_sent`, `reminder_sent` (BOOLEAN) - Notification flags
- `calendar_event_id`, `calendar_provider` (VARCHAR) - Calendar integration
- `metadata` (JSONB) - Additional appointment data

**Indexes**: customer_phone, appointment_datetime, status, call_id, lead_id

**Foreign Keys**: 
- `call_id` → `calls.id` (SET NULL on delete)
- `lead_id` → `leads.id` (SET NULL on delete)

---

### 5. business_config

Stores business-specific configuration and settings.

**Primary Key**: `id` (UUID)

**Key Columns**:
- `business_id` (VARCHAR, UNIQUE) - Business identifier
- `business_name` (VARCHAR) - Business name
- `greeting_message`, `ai_personality` (TEXT) - AI configuration
- `business_hours` (JSONB) - Operating hours configuration
- `holiday_schedule` (JSONB) - Holiday dates
- `routing_rules` (JSONB) - Call routing configuration
- `crm_config` (JSONB) - CRM integration settings
- `notification_config` (JSONB) - Notification preferences
- `language_config` (JSONB) - Language settings
- `knowledge_base` (TEXT) - Business-specific knowledge
- `active` (BOOLEAN) - Active status

**Indexes**: business_id, active

**Foreign Keys**: None

---

### 6. call_analytics

Aggregated analytics data for reporting and monitoring.

**Primary Key**: `id` (UUID)

**Key Columns**:
- `business_id` (VARCHAR) - Business identifier
- `date` (DATE) - Analytics date
- `hour` (INTEGER) - Hour of day (0-23)
- `total_calls`, `answered_calls`, `missed_calls` (INTEGER) - Call counts
- `average_duration_seconds` (DECIMAL) - Average call duration
- `intent_distribution` (JSONB) - Intent breakdown
- `language_distribution` (JSONB) - Language breakdown
- `leads_captured`, `appointments_booked`, `high_value_leads` (INTEGER) - Conversion metrics

**Unique Constraint**: (business_id, date, hour)

**Indexes**: (business_id, date), date, business_id

**Foreign Keys**: None

---

### 7. crm_sync_log

Tracks CRM synchronization status with retry logic support.

**Primary Key**: `id` (UUID)

**Key Columns**:
- `call_id` (UUID, FK) - References calls.id
- `lead_id` (UUID, FK) - References leads.id
- `crm_type` (VARCHAR) - CRM system type
- `operation` (VARCHAR) - Sync operation type
- `status` (VARCHAR) - 'pending', 'success', or 'failed'
- `attempt_count` (INTEGER) - Number of retry attempts
- `last_attempt_at` (TIMESTAMP) - Last sync attempt time
- `error_message` (TEXT) - Error details if failed
- `crm_record_id` (VARCHAR) - CRM system record ID

**Indexes**: status, call_id, lead_id, crm_type, status (partial index for pending)

**Foreign Keys**: 
- `call_id` → `calls.id` (CASCADE DELETE)
- `lead_id` → `leads.id` (CASCADE DELETE)

---

## Relationships

```
calls (1) ──< (N) transcripts
calls (1) ──< (N) leads
calls (1) ──< (N) appointments
calls (1) ──< (N) crm_sync_log

leads (1) ──< (N) appointments
leads (1) ──< (N) crm_sync_log
```

## Triggers

All tables with `updated_at` columns have automatic update triggers:
- `update_calls_updated_at`
- `update_leads_updated_at`
- `update_appointments_updated_at`
- `update_business_config_updated_at`
- `update_call_analytics_updated_at`
- `update_crm_sync_log_updated_at`

These triggers automatically set `updated_at = NOW()` on any UPDATE operation.

## Data Types

- **UUID**: Primary keys and foreign keys
- **VARCHAR**: Short text fields with length limits
- **TEXT**: Long text fields without length limits
- **TIMESTAMP**: Date and time with timezone support
- **DATE**: Date only
- **INTEGER**: Whole numbers
- **DECIMAL**: Precise decimal numbers
- **BOOLEAN**: True/false values
- **JSONB**: Binary JSON for flexible structured data

## Cascading Rules

- **transcripts**: DELETE CASCADE (deleted when call is deleted)
- **crm_sync_log**: DELETE CASCADE (deleted when call/lead is deleted)
- **leads**: SET NULL (call_id set to NULL when call is deleted)
- **appointments**: SET NULL (call_id and lead_id set to NULL when parent is deleted)

## Performance Considerations

1. **Indexes**: All foreign keys and frequently queried columns are indexed
2. **JSONB**: Used for flexible metadata with GIN indexing support
3. **Partitioning**: Consider partitioning `calls` and `transcripts` by date for large datasets
4. **Archival**: Implement data retention policies for old records (90+ days)

## Security

- Use row-level security (RLS) policies for multi-tenant isolation
- Encrypt sensitive data at application level before storage
- Use prepared statements to prevent SQL injection
- Implement role-based access control (RBAC) at database level
