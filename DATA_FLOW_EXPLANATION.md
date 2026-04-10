# Data Flow: Where GET /api/appointments Gets Its Data

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    1. PHONE CALL                             │
│  Caller: "I want to book an appointment for tomorrow at 2pm"│
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              2. AI AGENT (OpenAI Realtime)                   │
│  • Understands request                                       │
│  • Decides to use book_appointment tool                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         3. TOOL EXECUTOR (tools/tool_executor.py)            │
│  book_appointment() function executes                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│    4. APPOINTMENT MANAGER (appointment_manager.py)           │
│  book_appointment() method:                                  │
│  • Validates data                                            │
│  • Calls database.create_appointment()                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│           5. DATABASE SERVICE (database.py)                  │
│  create_appointment() method:                                │
│  • Executes SQL INSERT                                       │
│  • Saves to PostgreSQL appointments table                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         6. POSTGRESQL DATABASE (appointments table)          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ id | customer_name | phone | date | time | service    │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 1  | John Doe      | +123  | ...  | ...  | haircut    │ │ ← NEW ROW
│  │ 2  | Jane Smith    | +987  | ...  | ...  | coloring   │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│        7. EVENT BROADCASTER (event_broadcaster.py)           │
│  Broadcasts "appointment_booked" event via SSE               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         8. FRONTEND (frontend/live_events.js)                │
│  Receives event → calls refreshAppointments()                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         9. API REQUEST: GET /api/appointments                │
│  Frontend makes HTTP request to server                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│        10. API ENDPOINT (main.py line 1015)                  │
│  @app.get("/api/appointments")                               │
│  async def get_appointments():                               │
│      # Query database                                        │
│      rows = await conn.fetch("""                             │
│          SELECT * FROM appointments                          │
│          WHERE appointment_datetime >= NOW()                 │
│          ORDER BY appointment_datetime ASC                   │
│      """)                                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         11. POSTGRESQL DATABASE (appointments table)         │
│  Executes SELECT query, returns all appointments            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│        12. API RESPONSE (JSON)                               │
│  {                                                           │
│    "appointments": [                                         │
│      {                                                       │
│        "id": "1",                                            │
│        "customer_name": "John Doe",                          │
│        "customer_phone": "+1234567890",                      │
│        "service_type": "haircut",                            │
│        "appointment_datetime": "2026-04-15T14:00:00Z",       │
│        "duration_minutes": 30,                               │
│        "status": "scheduled"                                 │
│      },                                                      │
│      ...                                                     │
│    ]                                                         │
│  }                                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         13. FRONTEND TABLE UPDATE                            │
│  Renders appointments in dashboard table                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Customer    │ Phone       │ Date    │ Time  │ Service │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ John Doe    │ +1234567890 │ Apr 15  │ 02:00 │ Haircut │ │ ← APPEARS
│  │ Jane Smith  │ +1987654321 │ Apr 14  │ 10:00 │ Coloring│ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Code Locations

### 1. Tool Execution (tools/tool_executor.py)
```python
async def book_appointment(self, args, context):
    # Calls appointment_manager.book_appointment()
    appointment, appointment_id = await self.appointment_manager.book_appointment(
        call_id=call_id,
        customer_name=args.get("customer_name"),
        customer_phone=args.get("customer_phone"),
        appointment_datetime=appointment_datetime,
        service_type=args.get("service_type")
    )
```

### 2. Appointment Manager (appointment_manager.py)
```python
async def book_appointment(self, ...):
    # Validates and creates appointment
    appointment_id = await self.create_calendar_entry(appointment, call_id)
    return appointment, appointment_id

async def create_calendar_entry(self, appointment, call_id):
    # Saves to database
    appointment_id = await self.database.create_appointment(
        call_id=call_id,
        customer_name=appointment.customer_name,
        customer_phone=appointment.customer_phone,
        # ... other fields
    )
    return appointment_id
```

### 3. Database Service (database.py)
```python
async def create_appointment(self, ...):
    async with self.pool.acquire() as conn:
        appointment_id = await conn.fetchval("""
            INSERT INTO appointments (
                call_id, customer_name, customer_phone,
                service_type, appointment_datetime, 
                duration_minutes, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, call_id, customer_name, customer_phone, 
             service_type, appointment_datetime, 
             duration_minutes, "scheduled")
    return str(appointment_id)
```

### 4. API Endpoint (main.py line 1015)
```python
@app.get("/api/appointments")
async def get_appointments():
    if database_service and not isinstance(database_service, AsyncMock):
        async with database_service.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM appointments
                WHERE appointment_datetime >= NOW()
                ORDER BY appointment_datetime ASC
                LIMIT 50
            """)
            
            appointments = []
            for row in rows:
                appointments.append({
                    "id": str(row['id']),
                    "customer_name": row['customer_name'],
                    "customer_phone": row['customer_phone'],
                    # ... other fields
                })
            
            return JSONResponse(content={"appointments": appointments})
    
    # Falls back to mock data if database not available
    return JSONResponse(content={"appointments": [...]})
```

### 5. Frontend Request (frontend/live_events.js)
```javascript
function refreshAppointments() {
    fetch('/api/appointments')
        .then(r => r.json())
        .then(data => {
            if (window.renderAppointmentsTable) {
                window.renderAppointmentsTable(data.appointments || []);
            }
        })
        .catch(err => console.error('Error refreshing appointments:', err));
}
```

## Database Table Structure

### appointments table (PostgreSQL)
```sql
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id),
    customer_name VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(50) NOT NULL,
    customer_email VARCHAR(255),
    service_type VARCHAR(100) NOT NULL,
    appointment_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    status VARCHAR(50) DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Two Modes of Operation

### Mode 1: Real Database (USE_REAL_DB=true)
```
Tool Executor → Appointment Manager → Database Service → PostgreSQL
                                                              ↓
API Endpoint → Query PostgreSQL → Return Real Data
```

### Mode 2: Mock Database (USE_REAL_DB=false, default)
```
Tool Executor → Appointment Manager → Mock Database (in-memory)
                                                              ↓
API Endpoint → Return Mock Data (hardcoded examples)
```

## How to Enable Real Database

### 1. Set Environment Variable
```bash
# In .env file
USE_REAL_DB=true
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### 2. Run Database Migration
```bash
# Create tables
psql -U user -d dbname -f migrations/001_initial_schema.sql
```

### 3. Restart Server
```bash
python3 main.py
```

Now appointments will be saved to and fetched from PostgreSQL!

## Summary

**GET /api/appointments fetches data from:**

1. **With Real Database (USE_REAL_DB=true):**
   - PostgreSQL `appointments` table
   - Query: `SELECT * FROM appointments WHERE appointment_datetime >= NOW()`
   - Returns actual booked appointments

2. **Without Real Database (default):**
   - Mock data (hardcoded in main.py)
   - Returns 3 example appointments
   - Used for testing/demo

**Data gets INTO the database via:**
- Phone call → AI tool call → Tool Executor → Appointment Manager → Database Service → PostgreSQL INSERT

**Data gets OUT of the database via:**
- Frontend request → API endpoint → Database Service → PostgreSQL SELECT → JSON response → Frontend table

The complete round trip ensures appointments booked during calls appear in the dashboard automatically! 🔄
