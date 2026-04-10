# Real-Time Frontend Updates - Complete ✅

## Overview

Your frontend dashboard now receives real-time updates when appointments are booked, leads are created, or any other events happen during calls. No page refresh needed!

## How It Works

```
Phone Call → AI Tool Call → Database Update → Event Broadcast → Frontend Update
```

### Architecture

```
┌─────────────────────────────────────────┐
│         Phone Call (Twilio)              │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│    AI Agent (OpenAI + Tool Calling)      │
│    • book_appointment                    │
│    • create_lead                         │
│    • check_availability                  │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│      Tool Executor (Python)              │
│    • Executes function                   │
│    • Saves to database                   │
│    • Broadcasts event                    │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│    Event Broadcaster (SSE)               │
│    • Publishes to all subscribers        │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│    Frontend Dashboard (Browser)          │
│    • Receives event via SSE              │
│    • Shows notification                  │
│    • Updates metrics                     │
│    • Refreshes data                      │
└─────────────────────────────────────────┘
```

## Events That Trigger Frontend Updates

### 1. Appointment Booked
**When:** AI books an appointment using `book_appointment` tool

**Event Data:**
```json
{
  "type": "appointment_booked",
  "call_sid": "CA123...",
  "appointment_id": "appt-uuid-123",
  "customer_name": "John Doe",
  "customer_phone": "+1234567890",
  "date": "April 15, 2026",
  "time": "02:00 PM",
  "service": "haircut",
  "confirmation_sent": true
}
```

**Frontend Action:**
- ✅ Shows success notification: "Appointment booked: John Doe on April 15 at 02:00 PM"
- 📊 Updates total appointments counter
- 🔄 Refreshes dashboard analytics
- 📋 Adds to recent activity feed

### 2. Lead Created
**When:** AI captures a lead using `create_lead` tool

**Event Data:**
```json
{
  "type": "lead_created",
  "call_sid": "CA123...",
  "lead_id": "lead-uuid-456",
  "name": "Jane Smith",
  "phone": "+1987654321",
  "email": "jane@example.com",
  "score": 8,
  "inquiry_details": "Interested in premium package"
}
```

**Frontend Action:**
- ℹ️ Shows info notification: "New lead: Jane Smith (Score: 8/10)"
- 📊 Updates total leads counter
- 🔄 Refreshes dashboard analytics
- 📋 Adds to recent activity feed

### 3. Tool Execution
**When:** Any tool is executed

**Event Data:**
```json
{
  "type": "tool_execution",
  "call_sid": "CA123...",
  "tool_name": "check_availability",
  "success": true,
  "result": {
    "available": true,
    "slot_count": 5,
    "message": "Yes, we have 5 available slots..."
  }
}
```

**Frontend Action:**
- 📝 Logs tool execution
- 📋 Shows availability info in activity feed
- 🔍 Helps with debugging

### 4. Call Events
**Existing events that also update frontend:**

- `call_start` - Shows active call banner
- `call_update` - Updates intent, language, lead score
- `call_end` - Removes banner, refreshes call history
- `transcript` - Shows live conversation

## Frontend Components

### 1. Notification System
Real-time toast notifications appear in top-right corner:

```javascript
showNotification('success', 'Appointment booked: John Doe...')
showNotification('info', 'New lead: Jane Smith (Score: 8/10)')
showNotification('warning', 'Complaint logged from +1234567890')
```

**Features:**
- Auto-dismiss after 5 seconds
- Click to dismiss manually
- Color-coded by type (success, info, warning, error)
- Stacks multiple notifications

### 2. Activity Feed
Shows recent actions in chronological order:

```
02:30 PM  Available times: 09:00 AM, 09:30 AM, 10:00 AM...
02:31 PM  Appointment booked: John Doe on April 15 at 02:00 PM
02:32 PM  New lead: Jane Smith (Score: 8/10)
```

**Features:**
- Shows last 10 activities
- Auto-scrolls to newest
- Timestamped entries

### 3. Dashboard Metrics
Live counters that update automatically:

```
Total Calls: 127 → 128
Total Leads: 34 → 35
Total Appointments: 18 → 19
```

**Updates when:**
- Appointment booked
- Lead created
- Call completed

### 4. Active Call Banner
Shows when a call is in progress:

```
🔴 Live call: +1234567890
   Intent: appointment_booking (92% confidence)
   Language: English
   Lead Score: 7/10
```

## Testing Real-Time Updates

### 1. Open Dashboard
```bash
# Start server
python3 main.py

# Open in browser
http://localhost:5050/frontend/index.html
```

### 2. Make a Test Call
Call your Twilio number and say:
- "I want to book an appointment for tomorrow at 2pm"
- "I'm interested in your services"

### 3. Watch Dashboard
You'll see:
1. **Call Start** - Active call banner appears
2. **Transcript** - Live conversation appears
3. **Intent Detection** - Intent badge updates
4. **Tool Execution** - Activity feed shows actions
5. **Appointment/Lead** - Notification pops up
6. **Metrics Update** - Counters increment
7. **Call End** - Banner disappears

## Event Flow Example

### Booking an Appointment

```
1. Caller: "I want to book a haircut for Friday at 2pm"
   → Frontend shows transcript

2. AI: [calls check_availability tool]
   → Frontend shows: "Checking availability..."

3. Tool returns: Available
   → Frontend shows: "Available times: 02:00 PM"

4. AI: "Can I get your name?"
   → Frontend shows transcript

5. Caller: "John Doe"
   → Frontend shows transcript

6. AI: [calls book_appointment tool]
   → Frontend shows: "Booking appointment..."

7. Appointment booked successfully
   → Frontend shows notification: "✅ Appointment booked: John Doe on April 15 at 02:00 PM"
   → Total appointments counter: 18 → 19
   → Dashboard refreshes
   → Activity feed updates

8. Call ends
   → Active call banner disappears
   → Call history refreshes
```

## Server-Sent Events (SSE)

The frontend uses SSE to receive real-time updates:

```javascript
const es = new EventSource('/api/events/live');

es.onmessage = function(e) {
    const event = JSON.parse(e.data);
    handleLiveEvent(event);
};
```

**Benefits:**
- Automatic reconnection
- One-way server → client
- Works through firewalls
- No WebSocket complexity
- Browser handles connection

## Customizing Notifications

### Change Notification Duration
In `frontend/live_events.js`:

```javascript
// Auto-remove after 5 seconds (default)
setTimeout(() => {
    notification.style.opacity = '0';
    setTimeout(() => notification.remove(), 300);
}, 5000);  // Change this value (milliseconds)
```

### Add Custom Event Types
In `frontend/live_events.js`:

```javascript
case 'custom_event':
    showNotification('info', event.message);
    // Your custom handling
    break;
```

### Style Notifications
Add CSS to `frontend/index.html`:

```css
.notification {
    padding: 15px 20px;
    margin-bottom: 10px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    animation: slideIn 0.3s ease-out;
}

.notification-success {
    background: #10b981;
    color: white;
}

.notification-info {
    background: #3b82f6;
    color: white;
}

.notification-warning {
    background: #f59e0b;
    color: white;
}
```

## Broadcasting Custom Events

### From Tool Executor
```python
from event_broadcaster import broadcaster
import asyncio

# Broadcast custom event
asyncio.create_task(broadcaster.publish("custom_event", {
    "call_sid": call_sid,
    "message": "Something happened",
    "data": {"key": "value"}
}))
```

### From Anywhere in Code
```python
from event_broadcaster import broadcaster
import asyncio

await broadcaster.publish("event_type", {
    "call_sid": "CA123...",
    "your_data": "here"
})
```

## Debugging

### Check SSE Connection
Open browser console:
```javascript
// Should see:
EventSource connected
SSE reconnecting... (if disconnected)
```

### View Events
```javascript
// Add to live_events.js
console.log('Received event:', event);
```

### Test Event Broadcasting
```python
# In Python console
from event_broadcaster import broadcaster
import asyncio

asyncio.run(broadcaster.publish("test", {
    "call_sid": "test",
    "message": "Test event"
}))
```

## What Gets Updated

| Action | Frontend Update |
|--------|----------------|
| Appointment booked | ✅ Notification, counter, activity feed, dashboard |
| Lead created | ℹ️ Notification, counter, activity feed, dashboard |
| Availability checked | 📋 Activity feed entry |
| Slots retrieved | 📋 Activity feed with times |
| Call started | 🔴 Active call banner |
| Intent detected | 🎯 Intent badge update |
| Language detected | 🌍 Language pill update |
| Call ended | Banner removed, history refreshed |
| Transcript | 💬 Live conversation display |

## Benefits

✅ **Real-time visibility** - See what's happening as it happens  
✅ **No refresh needed** - Updates appear automatically  
✅ **Better monitoring** - Track appointments and leads live  
✅ **Instant feedback** - Know when actions complete  
✅ **Activity tracking** - See all actions in chronological order  
✅ **Metric updates** - Counters update in real-time  

## Summary

Your dashboard now receives real-time updates for:
- ✅ Appointments booked
- ✅ Leads created
- ✅ Tool executions
- ✅ Call events
- ✅ Transcripts
- ✅ Intent/language detection

Everything happens automatically via Server-Sent Events (SSE). No polling, no manual refresh needed!

Open your dashboard and make a test call to see it in action! 🎉
