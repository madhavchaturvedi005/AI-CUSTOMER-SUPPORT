# Login System Guide

## Overview
The dashboard now has a secure login system with session-based authentication.

## Login Credentials
- **Username**: `madhav5`
- **Password**: `M@dhav0505@#`

## How It Works

### 1. Routes
- `/` → Redirects to `/login.html`
- `/login.html` → Login page with project summary
- `/index.html` → Dashboard (requires authentication)

### 2. Authentication Flow
1. User visits `/` or `/login.html`
2. Enters credentials
3. Backend validates and generates session token
4. Token stored in localStorage
5. Redirects to `/index.html`
6. Dashboard checks token on load
7. If invalid, redirects back to login

### 3. Session Management
- Sessions stored in-memory (use Redis in production)
- Token verified on each dashboard load
- Logout clears token and redirects to login

## Testing

### Start the Server
```bash
python3 main.py
```

### Test the Routes
```bash
# In another terminal
python3 test_login_routes.py
```

### Manual Testing
1. Open browser: `http://localhost:5050`
2. Should redirect to login page
3. Enter credentials:
   - Username: `madhav5`
   - Password: `M@dhav0505@#`
4. Click "Sign In"
5. Should redirect to dashboard
6. Click logout icon in navbar
7. Should redirect back to login

## Features

### Login Page
- Beautiful gradient background
- Project summary on left side
- Responsive design
- Error handling
- Loading states

### Dashboard
- Authentication check on load
- User info in navbar
- Logout button
- Session verification

## Security Notes

⚠️ **For Production:**
- Move credentials to database with hashed passwords
- Use Redis for session storage
- Add HTTPS
- Implement rate limiting
- Add CSRF protection
- Set session expiration
- Add refresh tokens

## Troubleshooting

### "Not Found" Error
- Make sure server is running: `python3 main.py`
- Check the URL: `http://localhost:5050/login.html`
- Verify frontend folder exists

### Login Fails
- Check credentials are correct
- Check browser console for errors
- Verify `/api/login` endpoint is working

### Redirect Loop
- Clear localStorage: `localStorage.clear()`
- Check token is being saved
- Verify session verification endpoint
