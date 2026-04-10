# Time Slots Configuration - Complete ✅

## What Was Added

Business hours and time slots have been configured in your appointment system. You can now book real appointments!

## Current Schedule

```
Monday       9:00 AM - 5:00 PM  (16 slots)
Tuesday      9:00 AM - 5:00 PM  (16 slots)
Wednesday    9:00 AM - 5:00 PM  (16 slots)
Thursday     9:00 AM - 5:00 PM  (16 slots)
Friday       9:00 AM - 5:00 PM  (16 slots)
Saturday     10:00 AM - 2:00 PM (8 slots)
Sunday       CLOSED
```

**Slot Duration:** 30 minutes  
**Total Weekly Slots:** 88 slots  
**Total Weekly Hours:** 44 hours

## How It Works

### 1. Time Slot Generation
The system automatically generates 30-minute slots during business hours:
- **Weekdays:** 9:00 AM, 9:30 AM, 10:00 AM, ... 4:30 PM
- **Saturday:** 10:00 AM, 10:30 AM, 11:00 AM, ... 1:30 PM
- **Sunday:** No slots (closed)

### 2. Availability Checking
When someone asks "What times are available?", the AI:
1. Calls `check_availability` tool
2. Gets real-time slot availability
3. Returns available times

### 3. Appointment Booking
When booking, the AI:
1. Checks if the requested time is available
2. Calls `book_appointment` tool
3. Creates database record
4. Sends SMS confirmation

## Test Results

```
✅ Business hours configured
✅ Time slots generated correctly
✅ 88 slots available per week
✅ Appointment booking works
✅ SMS confirmations sent
```

## Example Conversations

### Check Availability
```
Caller: "What times are available tomorrow?"

AI: [calls get_available_slots tool]
AI: "Tomorrow we have slots at 9:00 AM, 9:30 AM, 10:00 AM, 
     10:30 AM, and 11:00 AM. Which time works best for you?"
```

### Book Appointment
```
Caller: "I want to book a haircut for Friday at 2pm"

AI: [calls check_availability tool]
AI: "Perfect! 2pm is available on Friday. Can I get your name?"

Caller: "John Doe"

AI: [calls book_appointment tool]
AI: "Done! I've booked your haircut for Friday at 2pm. 
     You'll receive a confirmation text shortly."

[SMS sent to customer's phone]
```

### No Availability
```
Caller: "Can I book for Sunday?"

AI: [calls check_availability tool]
AI: "I'm sorry, we're closed on Sundays. We're open Monday 
     through Saturday. Would you like to book for Monday instead?"
```

## Customizing Your Schedule

### Option 1: Edit main.py Directly

In `main.py` around line 175, change the `business_hours` dictionary:

```python
business_hours = {
    "monday": [(9, 17)],      # 9 AM - 5 PM
    "tuesday": [(9, 17)],
    "wednesday": [(9, 17)],
    "thursday": [(9, 17)],
    "friday": [(9, 17)],
    "saturday": [(10, 14)],   # 10 AM - 2 PM
    "sunday": []              # Closed
}
```

### Option 2: Use Pre-configured Schedules

Run this to see all options:
```bash
python3 configure_business_hours.py
```

Available schedules:
- **Default:** Mon-Fri 9-5, Sat 10-2 (44 hrs/week)
- **24/7 Service:** Always open (168 hrs/week)
- **Extended Hours:** 7 AM - 9 PM (90 hrs/week)
- **Split Shift:** 9-12, 2-6 (39 hrs/week)
- **Weekdays Only:** Mon-Fri 9-5 (40 hrs/week)

### Option 3: Custom Schedule

Create your own schedule:

```python
# Example: Different hours each day
business_hours = {
    "monday": [(8, 18)],           # 8 AM - 6 PM
    "tuesday": [(8, 18)],
    "wednesday": [(8, 12)],        # Half day
    "thursday": [(8, 18)],
    "friday": [(8, 20)],           # Late night
    "saturday": [(9, 15)],         # 9 AM - 3 PM
    "sunday": [(10, 14)]           # Sunday hours
}

# Example: Split shifts with lunch break
business_hours = {
    "monday": [(9, 12), (14, 18)],  # 9-12, 2-6
    "tuesday": [(9, 12), (14, 18)],
    # ... etc
}
```

### Changing Slot Duration

In `main.py`, change `slot_duration_minutes`:

```python
appointment_manager = AppointmentManager(
    database=database_service,
    business_hours=business_hours,
    slot_duration_minutes=15  # 15-minute slots
    # or 60 for 1-hour slots
)
```

Common durations:
- **15 minutes:** Quick services (consultations)
- **30 minutes:** Standard (haircuts, checkups)
- **60 minutes:** Long services (massages, detailed work)

## Testing Your Schedule

### 1. View Available Slots
```bash
python3 test_time_slots.py
```

Shows:
- Your business hours
- Available slots for next 7 days
- Total slots per day
- Test booking

### 2. Test with Tools
```bash
python3 test_tool_calling.py
```

Tests:
- check_availability tool
- get_available_slots tool
- book_appointment tool

### 3. Live Test
Start your server and call:
```bash
python3 main.py
```

Then call your number and say:
- "What times are available tomorrow?"
- "I want to book for Friday at 2pm"
- "Can I schedule an appointment?"

## How Slots Are Managed

### Slot Generation
```python
# For Monday 9 AM - 5 PM with 30-min slots:
09:00 AM  ✓ Available
09:30 AM  ✓ Available
10:00 AM  ✓ Available
10:30 AM  ✓ Available
...
04:00 PM  ✓ Available
04:30 PM  ✓ Available
```

### Booking Process
1. Customer requests time
2. System checks if slot exists
3. System checks if slot is available (not booked)
4. If available, creates appointment
5. Sends SMS confirmation
6. Slot becomes unavailable

### Preventing Double-Booking
The `_is_slot_available()` method checks:
- Is the time within business hours?
- Is the slot already booked?
- Is there enough time before closing?

## Integration with Database

When appointments are booked:

```sql
INSERT INTO appointments (
    call_id,
    customer_name,
    customer_phone,
    service_type,
    appointment_datetime,
    duration_minutes,
    status
) VALUES (
    'call-123',
    'John Doe',
    '+1234567890',
    'haircut',
    '2026-04-11 14:00:00',
    30,
    'scheduled'
);
```

## SMS Confirmations

Automatic SMS sent after booking:

```
Appointment Confirmed!
Service: haircut
Date/Time: April 11, 2026 at 02:00 PM
Duration: 30 minutes
Name: John Doe

Thank you for booking with us!
```

## Troubleshooting

### No Slots Available
**Problem:** AI says no slots available  
**Solution:** 
- Check business hours are set correctly
- Verify current time is within business hours
- Check if looking at future dates

### Wrong Time Zone
**Problem:** Slots show wrong times  
**Solution:**
- All times are in UTC
- Adjust business hours for your timezone
- Or modify appointment_manager.py to use local timezone

### Slots Not Showing
**Problem:** get_available_slots returns empty  
**Solution:**
```bash
python3 test_time_slots.py
```
Check if slots are being generated

### Can't Book Appointments
**Problem:** Booking fails  
**Solution:**
- Check database connection
- Verify appointment_manager is initialized
- Check tool executor has appointment_manager

## Next Steps

1. ✅ Business hours configured
2. ✅ Time slots working
3. ✅ Booking system ready
4. 🔄 Test with real calls
5. 🔄 Adjust schedule as needed
6. 🔄 Monitor bookings

## Quick Commands

```bash
# View schedule options
python3 configure_business_hours.py

# Test time slots
python3 test_time_slots.py

# Test full system
python3 test_tool_calling.py

# Start server
python3 main.py
```

## Summary

✅ **88 appointment slots per week**  
✅ **30-minute slot duration**  
✅ **Monday-Saturday availability**  
✅ **Automatic SMS confirmations**  
✅ **Real-time availability checking**  
✅ **Double-booking prevention**

Your appointment booking system is fully configured and ready to use! 🎉

Call your Twilio number and try booking an appointment!
