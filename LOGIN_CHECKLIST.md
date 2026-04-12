# Login System - Testing Checklist

## Pre-Testing Setup

- [ ] Ensure PostgreSQL is running (if using real database)
- [ ] Check `.env` file has all required variables
- [ ] Install dependencies: `pip install -r requirements.txt`

## Start the Server

```bash
python3 main.py
```

Expected output:
```
🚀 Initializing AI Voice Automation services...
   • CallManager: Ready
   • IntentDetector: Ready
   • LanguageManager: Ready
   • CallRouter: Ready
   • AppointmentManager: Ready (tool calling enabled)
   • Database: PostgreSQL
   • Cache: Redis
```

## Manual Testing Steps

### Test 1: Root Redirect
- [ ] Open browser: `http://localhost:5050/`
- [ ] Should automatically redirect to `/login.html`
- [ ] Login page should display with project summary

### Test 2: Login Page
- [ ] Verify login form is visible
- [ ] Check project summary on left side
- [ ] Verify responsive design (resize browser)

### Test 3: Invalid Login
- [ ] Enter wrong username: `test`
- [ ] Enter wrong password: `test123`
- [ ] Click "Sign In"
- [ ] Should show error message: "Invalid username or password"

### Test 4: Valid Login
- [ ] Enter username: `madhav5`
- [ ] Enter password: `M@dhav0505@#`
- [ ] Click "Sign In"
- [ ] Should show loading state
- [ ] Should redirect to `/index.html` (dashboard)

### Test 5: Dashboard Access
- [ ] Dashboard should load successfully
- [ ] User info should show in navbar: "madhav5"
- [ ] Logout icon should be visible
- [ ] All dashboard features should work

### Test 6: Session Persistence
- [ ] Refresh the page (F5)
- [ ] Should stay on dashboard (not redirect to login)
- [ ] User should remain logged in

### Test 7: Direct URL Access
- [ ] While logged in, visit: `http://localhost:5050/login.html`
- [ ] Should be able to access (already logged in)
- [ ] Visit: `http://localhost:5050/index.html`
- [ ] Should load dashboard

### Test 8: Logout
- [ ] Click logout icon in navbar
- [ ] Should redirect to `/login.html`
- [ ] Try to access: `http://localhost:5050/index.html`
- [ ] Should redirect back to login

### Test 9: Browser Storage
- [ ] Open browser DevTools (F12)
- [ ] Go to Application → Local Storage
- [ ] After login, should see:
  - `auth_token`: (long random string)
  - `username`: `madhav5`
- [ ] After logout, both should be cleared

### Test 10: API Endpoints
- [ ] Open browser DevTools → Network tab
- [ ] Login and check requests:
  - `POST /api/login` → Status 200
  - `GET /api/verify-session` → Status 200
  - `POST /api/logout` → Status 200

## Automated Testing

Run the test script:
```bash
python3 test_login_routes.py
```

Expected output:
```
🧪 Testing Login Routes
============================================================

1. Testing root redirect (/) -> /login.html
   ✅ Root redirects to login.html

2. Testing /login.html
   ✅ Login page loads successfully

3. Testing /index.html
   ✅ Dashboard page loads successfully

4. Testing /api/login
   ✅ Login API works - token received

5. Testing /api/verify-session
   ✅ Session verification works

============================================================
✅ Testing complete!
```

## Troubleshooting

### Issue: "Not Found" error
**Solution:**
- Check server is running: `python3 main.py`
- Verify URL: `http://localhost:5050/login.html`
- Check `frontend/` folder exists

### Issue: Login button does nothing
**Solution:**
- Open browser console (F12)
- Check for JavaScript errors
- Verify `/api/login` endpoint is accessible

### Issue: Redirect loop
**Solution:**
- Clear browser localStorage: `localStorage.clear()`
- Clear browser cache
- Restart server

### Issue: "Invalid credentials" but credentials are correct
**Solution:**
- Check for extra spaces in username/password
- Verify credentials in `main.py`:
  ```python
  VALID_CREDENTIALS = {
      "madhav5": "M@dhav0505@#"
  }
  ```

### Issue: Dashboard loads but shows no data
**Solution:**
- This is normal if no calls have been made yet
- Mock data should still show in charts
- Check browser console for API errors

## Success Criteria

✅ All tests pass
✅ Login works with correct credentials
✅ Invalid credentials show error
✅ Dashboard requires authentication
✅ Logout works and clears session
✅ Session persists on page refresh
✅ No console errors

## Next Steps

Once testing is complete:
1. Test with actual phone calls
2. Verify dashboard updates with real data
3. Test all dashboard features (calls, leads, appointments)
4. Consider production security improvements (see LOGIN_SYSTEM_GUIDE.md)
