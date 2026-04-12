# Route Architecture Diagram

## Before Fix ❌
```
User Request: http://localhost:5050/login.html
                    ↓
            FastAPI Router
                    ↓
        No route found for /login.html
                    ↓
            404 Not Found
```

Only accessible at: `/frontend/login.html` ❌

## After Fix ✅
```
User Request: http://localhost:5050/login.html
                    ↓
            FastAPI Router
                    ↓
        @app.get("/login.html")
                    ↓
    FileResponse("frontend/login.html")
                    ↓
        Login Page Served ✅
```

## Complete Route Map

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  GET /                                                    │
│  └─→ RedirectResponse("/login.html")                     │
│                                                           │
│  GET /login.html                                          │
│  └─→ FileResponse("frontend/login.html")                 │
│                                                           │
│  GET /index.html                                          │
│  └─→ FileResponse("frontend/index.html")                 │
│                                                           │
│  POST /api/login                                          │
│  └─→ Validate credentials → Generate token               │
│                                                           │
│  POST /api/logout                                         │
│  └─→ Invalidate session token                            │
│                                                           │
│  GET /api/verify-session?token=xxx                        │
│  └─→ Check if token is valid                             │
│                                                           │
│  /frontend/*                                              │
│  └─→ StaticFiles(directory="frontend")                   │
│      (CSS, JS, images, etc.)                              │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Authentication Flow

```
┌──────────┐
│  Browser │
└────┬─────┘
     │
     │ 1. Visit http://localhost:5050/
     ↓
┌────────────────┐
│  GET /         │
│  Redirect 307  │
└────┬───────────┘
     │
     │ 2. Redirect to /login.html
     ↓
┌────────────────────┐
│  GET /login.html   │
│  Serve login page  │
└────┬───────────────┘
     │
     │ 3. User enters credentials
     ↓
┌─────────────────────────────┐
│  POST /api/login            │
│  {username, password}       │
│  ↓                          │
│  Validate credentials       │
│  ↓                          │
│  Generate session token     │
│  ↓                          │
│  Return {token, username}   │
└────┬────────────────────────┘
     │
     │ 4. Save token to localStorage
     │ 5. Redirect to /index.html
     ↓
┌────────────────────────────┐
│  GET /index.html           │
│  Serve dashboard           │
│  ↓                         │
│  JavaScript runs:          │
│  - Get token from storage  │
│  - Call verify-session     │
└────┬───────────────────────┘
     │
     │ 6. Verify token
     ↓
┌─────────────────────────────────┐
│  GET /api/verify-session        │
│  ?token=xxx                     │
│  ↓                              │
│  Check if token exists          │
│  ↓                              │
│  Return {valid: true/false}     │
└────┬────────────────────────────┘
     │
     │ 7a. If valid: Show dashboard
     │ 7b. If invalid: Redirect to login
     ↓
┌──────────────┐
│  Dashboard   │
│  or Login    │
└──────────────┘
```

## Logout Flow

```
┌──────────┐
│  Browser │
└────┬─────┘
     │
     │ 1. Click logout button
     ↓
┌─────────────────────────┐
│  POST /api/logout       │
│  {token}                │
│  ↓                      │
│  Delete session         │
│  ↓                      │
│  Return success         │
└────┬────────────────────┘
     │
     │ 2. Clear localStorage
     │ 3. Redirect to /login.html
     ↓
┌────────────────┐
│  Login Page    │
└────────────────┘
```

## Key Points

1. **HTML files** served via `FileResponse` at root level
2. **Static assets** (CSS, JS) served via `/frontend` mount
3. **API endpoints** handle authentication logic
4. **Client-side JS** manages token storage and redirects
5. **Session storage** in-memory (use Redis in production)
