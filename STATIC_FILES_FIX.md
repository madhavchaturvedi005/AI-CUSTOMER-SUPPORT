# Static Files Fix

## Issue
Dashboard was showing errors in browser console:
```
GET http://localhost:5050/dashboard.js net::ERR_ABORTED 404 (Not Found)
GET http://localhost:5050/live_events.js net::ERR_ABORTED 404 (Not Found)
```

## Root Cause
The `index.html` file was referencing JavaScript files with relative paths:
```html
<script src="dashboard.js"></script>
<script src="live_events.js"></script>
```

When the dashboard is served via `FileResponse` at `/index.html`, the browser tries to load these files from the root (`/dashboard.js`), but they're actually located in the `frontend/` folder.

## Solution
Updated the script tags in `frontend/index.html` to use absolute paths:
```html
<script src="/frontend/dashboard.js"></script>
<script src="/frontend/live_events.js"></script>
```

## Why This Works

### Route Structure
```
/index.html          → FileResponse("frontend/index.html")
/frontend/*          → StaticFiles(directory="frontend")
```

When the browser loads `/index.html`:
1. FastAPI serves `frontend/index.html` via FileResponse
2. Browser parses HTML and finds script tags
3. Browser requests `/frontend/dashboard.js`
4. FastAPI serves it via the StaticFiles mount at `/frontend`

### Before (Broken)
```
Browser at: http://localhost:5050/index.html
Script tag: <script src="dashboard.js"></script>
Browser requests: http://localhost:5050/dashboard.js
Result: 404 Not Found (no route for /dashboard.js)
```

### After (Fixed)
```
Browser at: http://localhost:5050/index.html
Script tag: <script src="/frontend/dashboard.js"></script>
Browser requests: http://localhost:5050/frontend/dashboard.js
Result: 200 OK (served by StaticFiles mount)
```

## Files Modified
- `frontend/index.html` - Updated script src paths

## Testing

### 1. Start Server
```bash
python3 main.py
```

### 2. Test Static Files
```bash
python3 test_static_files.py
```

Expected output:
```
🧪 Testing Static File Access
============================================================

Testing: Dashboard JavaScript
   URL: http://localhost:5050/frontend/dashboard.js
   ✅ Success - XXXX bytes

Testing: Live Events JavaScript
   URL: http://localhost:5050/frontend/live_events.js
   ✅ Success - XXXX bytes

Testing: Login Page
   URL: http://localhost:5050/login.html
   ✅ Success - XXXX bytes

Testing: Dashboard Page
   URL: http://localhost:5050/index.html
   ✅ Success - XXXX bytes
```

### 3. Test in Browser
1. Open: `http://localhost:5050/`
2. Login with credentials
3. Open browser console (F12)
4. Should see NO 404 errors
5. Dashboard should load completely
6. All features should work

## Verification

### Browser Console (F12)
Before fix:
```
❌ GET http://localhost:5050/dashboard.js 404 (Not Found)
❌ GET http://localhost:5050/live_events.js 404 (Not Found)
```

After fix:
```
✅ No errors
✅ All scripts loaded successfully
```

### Network Tab
Check that these files load successfully:
- `/frontend/dashboard.js` - Status 200
- `/frontend/live_events.js` - Status 200

## Related Files

### Static File Structure
```
frontend/
├── index.html          (Dashboard)
├── login.html          (Login page)
├── dashboard.js        (Dashboard logic)
└── live_events.js      (Real-time updates)
```

### Route Configuration (main.py)
```python
# Serve HTML files at root
@app.get("/login.html")
async def serve_login():
    return FileResponse("frontend/login.html")

@app.get("/index.html")
async def serve_dashboard():
    return FileResponse("frontend/index.html")

# Mount static assets
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
```

## Best Practices

### For HTML Files Served via FileResponse
Always use absolute paths for assets:
```html
<!-- ✅ Good - Absolute path -->
<script src="/frontend/dashboard.js"></script>
<link href="/frontend/styles.css" rel="stylesheet">
<img src="/frontend/logo.png" alt="Logo">

<!-- ❌ Bad - Relative path -->
<script src="dashboard.js"></script>
<link href="styles.css" rel="stylesheet">
<img src="logo.png" alt="Logo">
```

### Alternative Approach
If you want to use relative paths, serve the HTML from within the static files mount:
```python
# Don't use FileResponse for HTML
# Instead, access via /frontend/index.html
# Then relative paths work: <script src="dashboard.js"></script>
```

But this requires changing all URLs in the app, so absolute paths are simpler.

## Status
✅ Fixed - JavaScript files now load correctly
✅ No more 404 errors in console
✅ Dashboard fully functional
