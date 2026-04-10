# Live Events Testing Guide

## What Was Added

### Frontend HTML (frontend/index.html)
1. ✅ Live call banner at the top (shows when call is active)
2. ✅ Live transcript panel in dashboard (shows real-time conversation)
3. ✅ Live metadata pills (intent, language, lead score)
4. ✅ CSS styling for transcript rows
5. ✅ Script inclusion for live_events.js

### New Elements Added

**Live Call Banner:**
```html
<div id="active-call-banner" style="display:none">
  <!-- Shows: "Live call: +1234567890" -->
  <!-- Displays: Intent, Language, Lead Score -->
</div>
```

**Live Transcript Panel:**
```html
<div id="live-transcript" class="transcript-container">
  <!-- Real-time conversation appears here -->
</div>
```

**Metadata Pills:**
```html
<span id="live-intent">—</span>
<span id="live-language">—</span>
<span id="live-lead-score">—</span>
```

## Testing Steps

### 1. Start the Server
```bash
python main.py
```

### 2. Open the Dashboard
```
http://localhost:5050/frontend/index.html
```

### 3. Open Browser Console
Press F12 and go to Console tab to see SSE events

### 4. Make a Test Call
Call your Twilio number and watch the dashboard

## Expected Behavior

### When Call Starts
1. ✅ Red banner appears at top: "Live call: +1234567890"
2. ✅ Console shows: `{type: "call_start", call_sid: "CA...", ...}`

### During Call (Real-time)
1. ✅ Each spoken sentence appears in Live Transcript panel
2. ✅ Caller messages have blue background
3. ✅ AI responses have green background
4. ✅ Language badge shows detected language (EN, HI, TA, etc.)

### When Intent Detected
1. ✅ Intent pill updates: "sales inquiry", "support request", etc.
2. ✅ Confidence shown on hover
3. ✅ Console shows: `{type: "call_update", intent: "...", ...}`

### When Language Detected
1. ✅ Language pill updates: "EN", "HI", "TA", etc.
2. ✅ Confidence shown on hover
3. ✅ Console shows: `{type: "call_update", language: "...", ...}`

### When Call Ends
1. ✅ Red banner disappears
2. ✅ Call history table refreshes automatically
3. ✅ Console shows: `{type: "call_end", duration_ms: ..., ...}`

## Visual Guide

### Live Call Banner (Active)
```
┌─────────────────────────────────────────────────────────┐
│ 📞 Live call: +1234567890                               │
│    Intent: sales inquiry  Language: EN  Score: 8        │
└─────────────────────────────────────────────────────────┘
```

### Live Transcript Panel
```
┌─────────────────────────────────────────────────────────┐
│ 💬 Live Transcript                                      │
├─────────────────────────────────────────────────────────┤
│ ┌─ Caller ─────────────────────────────────────── EN ─┐│
│ │ Hello, I'm interested in your services             ││
│ └──────────────────────────────────────────────────────┘│
│ ┌─ AI ────────────────────────────────────────── EN ─┐│
│ │ Thank you for calling! How can I help you today?   ││
│ └──────────────────────────────────────────────────────┘│
│ ┌─ Caller ─────────────────────────────────────── EN ─┐│
│ │ I'd like to know about pricing                     ││
│ └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Banner Not Appearing
**Check:**
1. Browser console for SSE connection: `SSE reconnecting...`
2. Network tab for `/api/events/live` (should be status 200)
3. Server logs for `broadcaster.publish("call_start")`

**Fix:**
```javascript
// In browser console:
const es = new EventSource('/api/events/live');
es.onmessage = (e) => console.log(JSON.parse(e.data));
```

### Transcript Not Updating
**Check:**
1. `#live-transcript` element exists in DOM
2. Console for transcript events
3. Server logs for `broadcaster.publish("transcript")`

**Fix:**
```javascript
// Manually test:
const container = document.getElementById('live-transcript');
console.log('Container found:', container !== null);
```

### Events Not Firing
**Check:**
1. Server restarted after code changes
2. `event_broadcaster.py` imported correctly
3. No errors in server logs

**Fix:**
```bash
# Restart server:
# Ctrl+C to stop
python main.py
```

### SSE Connection Drops
**Normal behavior** - browser auto-reconnects every few seconds

**Check:**
- Console shows: `SSE reconnecting...`
- Network tab shows repeated `/api/events/live` requests

## Browser Console Commands

### Test SSE Connection
```javascript
const es = new EventSource('/api/events/live');
es.onmessage = (e) => console.log('Event:', JSON.parse(e.data));
es.onerror = () => console.log('SSE error');
```

### Check Elements
```javascript
console.log('Banner:', document.getElementById('active-call-banner'));
console.log('Transcript:', document.getElementById('live-transcript'));
console.log('Intent:', document.getElementById('live-intent'));
```

### Manually Trigger Event
```javascript
// Simulate a transcript event:
handleLiveEvent({
  type: 'transcript',
  speaker: 'customer',
  text: 'Test message',
  language: 'en',
  call_sid: 'TEST123'
});
```

## Performance Monitoring

### Check SSE Stats
```javascript
// In browser console after a few minutes:
performance.getEntriesByType('resource')
  .filter(r => r.name.includes('/api/events/live'))
  .forEach(r => console.log('SSE:', r.duration + 'ms'));
```

### Check Memory Usage
```javascript
// Monitor transcript container size:
const container = document.getElementById('live-transcript');
console.log('Transcript rows:', container.children.length);
```

## Success Criteria

✅ SSE connection established (check Network tab)
✅ Live banner appears when call starts
✅ Transcript updates in real-time during call
✅ Intent and language pills update when detected
✅ Banner disappears when call ends
✅ Call history refreshes automatically
✅ No console errors
✅ Smooth animations and transitions

## Next Steps

1. **Customize Styling**: Edit CSS in `<style>` tag
2. **Add Filters**: Filter transcripts by language or speaker
3. **Add Export**: Download transcript as text file
4. **Add Notifications**: Browser notifications for new calls
5. **Add Audio**: Play notification sound on new call

## Files Modified

- ✅ `frontend/index.html` - Added HTML elements, CSS, script tag
- ✅ `frontend/live_events.js` - Already created
- ✅ `event_broadcaster.py` - Already created
- ✅ `handlers.py` - Already updated
- ✅ `main.py` - Already updated

## Status
✅ All files updated
✅ HTML elements added
✅ CSS styling added
✅ Script included
✅ Ready for testing!
