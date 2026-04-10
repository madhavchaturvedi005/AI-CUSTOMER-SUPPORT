# Database Migrations

This directory contains SQL migration files for the AI Voice Automation system database schema.

## Prerequisites

- PostgreSQL 12 or higher
- Database user with CREATE TABLE, CREATE INDEX, and CREATE FUNCTION privileges

## Running Migrations

### Option 1: Using psql command line

```bash
psql -U your_username -d your_database -f migrations/001_initial_schema.sql
```

### Option 2: Using environment variables

```bash
psql $DATABASE_URL -f migrations/001_initial_schema.sql
```

### Option 3: Using Python with psycopg2

```python
import psycopg2
import os

# Read migration file
with open('migrations/001_initial_schema.sql', 'r') as f:
    migration_sql = f.read()

# Connect and execute
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()
cursor.execute(migration_sql)
conn.commit()
cursor.close()
conn.close()
```

## Migration Files

### 001_initial_schema.sql

Creates the initial database schema including:

- **calls**: All call records with metadata and status
- **transcripts**: Conversation transcripts with speaker identification
- **leads**: Captured lead information with qualification scores
- **appointments**: Scheduled appointments with calendar integration
- **business_config**: Business-specific configuration and settings
- **call_analytics**: Aggregated analytics data for reporting
- **crm_sync_log**: CRM synchronization tracking with retry logic

**Requirements Addressed**: 1.1, 5.4, 6.4, 7.2, 8.3, 15.1, 16.3

**Features**:
- Foreign key constraints with appropriate cascading rules
- Performance-optimized indexes on frequently queried columns
- Automatic timestamp updates via triggers
- JSONB columns for flexible metadata storage
- Check constraints for data validation
- Comprehensive table and column comments

## Verification

After running the migration, verify the schema:

```sql
-- List all tables
\dt

-- Describe a specific table
\d calls

-- List all indexes
\di

-- List all triggers
\dy
```

## Rollback

To rollback the initial schema (WARNING: This will delete all data):

```sql
DROP TABLE IF EXISTS crm_sync_log CASCADE;
DROP TABLE IF EXISTS call_analytics CASCADE;
DROP TABLE IF EXISTS business_config CASCADE;
DROP TABLE IF EXISTS appointments CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS transcripts CASCADE;
DROP TABLE IF EXISTS calls CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
```

## Notes

- The schema uses UUID primary keys for better distribution and security
- JSONB columns are used for flexible metadata and configuration storage
- Indexes are created on foreign keys and frequently queried columns
- Cascading deletes are configured to maintain referential integrity
- Triggers automatically update `updated_at` timestamps on modifications
