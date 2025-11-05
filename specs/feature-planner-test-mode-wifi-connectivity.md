# Feature: Test Mode with WiFi Connectivity

## Feature Description
Enable a simple test mode that allows the Flutter frontend running on a phone to communicate with the FastAPI backend running on a computer over the same WiFi network. When `TEST_MODE=true` is set in both the backend and frontend `.env` files, both applications will switch to test URLs that enable local network communication.

This feature allows developers to:
- Run the backend server on their computer (e.g., Windows PC)
- Connect to that backend from their phone app over WiFi
- Test and troubleshoot features in a real mobile environment without affecting production
- Easily switch between test and production by changing one environment variable

## Scope
- **Frontend (Flutter)**: Read TEST_MODE from .env and use TEST_BACKEND_URL when enabled
- **Backend (FastAPI)**: Read TEST_MODE from .env, bind to 0.0.0.0 (all network interfaces), and log test mode status

## User Story
As a **developer**
I want to **set TEST_MODE=true in both .env files and use my computer's local IP address**
So that **my phone app can connect to the backend server running on my computer over WiFi**

## Problem Statement
Currently, the frontend has hardcoded production URLs in `app_constants.dart`. Even though `TEST_MODE` and `TEST_BACKEND_URL` are defined in the frontend `.env` file, they are not being used. The backend configuration already has TEST_MODE support but needs proper WiFi network binding.

Developers need:
1. A simple way to point the frontend to a local backend server using the computer's WiFi IP
2. The backend to accept connections from other devices on the same network
3. Clear visibility into which mode is active (test vs production)

## Solution Statement
Implement dynamic URL selection in the frontend based on TEST_MODE environment variable, and ensure the backend binds to all network interfaces (0.0.0.0) to accept WiFi connections. Both frontend and backend will log their test mode status for clear visibility.

The frontend will read TEST_MODE and switch BASE_URL to TEST_BACKEND_URL (e.g., `http://192.168.1.100:8002/api/v1`), while the backend will bind to 0.0.0.0 to accept connections from the local network.

## Relevant Files

### Frontend Files

#### `frontend/.env`
- **Why relevant**: Contains TEST_MODE and TEST_BACKEND_URL environment variables
- **Current state**: Variables exist but are not being consumed by the app
- **Changes needed**: Update TEST_BACKEND_URL to use computer's local network IP address
- **Example**: `TEST_BACKEND_URL=http://192.168.1.100:8002/api/v1`

#### `frontend/lib/utils/app_constants.dart` (lines 12-18)
- **Why relevant**: Contains hardcoded BASE_URL that ignores TEST_MODE
- **Current issue**: `static const String BASE_URL = PROD_URL;` is hardcoded to production
- **Changes needed**: Implement dynamic URL selection based on TEST_MODE
- **Impact**: All API calls (chat, places, favorites, feedback, greet) will use the test URL when TEST_MODE=true

#### `frontend/lib/main.dart` (line 32)
- **Why relevant**: Entry point where dotenv is loaded
- **Changes needed**: Add logging to show which backend URL is being used
- **Purpose**: Give developers immediate visibility into which mode is active

### Backend Files

#### `backend/.env` (line 8)
- **Why relevant**: Contains environment configuration including TEST_MODE
- **Current state**: TEST_MODE variable is not set
- **Changes needed**: Add TEST_MODE=true for test environments
- **Additional**: Verify HOST=0.0.0.0 for WiFi connectivity

#### `backend/app/core/config.py` (lines 32-43)
- **Why relevant**: Configuration file that loads environment variables
- **Current state**: Already has TEST_MODE property (line 43)
- **Changes needed**: None - already properly configured
- **Verification**: HOST defaults to 0.0.0.0 which allows WiFi connections

#### `backend/main.py` (lines 13-15)
- **Why relevant**: Startup function that initializes the FastAPI app
- **Current state**: Already logs test mode status when TEST_MODE=true
- **Changes needed**: None - already properly implemented
- **Verification**: Logs "🧪 TEST MODE ENABLED - Backend running in test mode"

#### `backend/run.py` (lines 5-10)
- **Why relevant**: Script that starts the uvicorn server
- **Current state**: Uses settings.HOST which defaults to 0.0.0.0
- **Changes needed**: None - already properly configured for network access
- **Verification**: Binds to 0.0.0.0 which accepts connections from any network interface

## Implementation Plan

### Phase 1: Backend Verification
Verify that the backend is properly configured to accept WiFi connections and log test mode status. The backend already has most of the necessary infrastructure in place.

### Phase 2: Frontend URL Switching
Implement dynamic URL selection in the frontend based on TEST_MODE from .env, replacing the hardcoded production URL.

### Phase 3: Environment Setup & WiFi Testing
Configure environment variables with the correct local network IP address and test end-to-end connectivity over WiFi.

## Step by Step Tasks

### 1. Find Your Computer's Local IP Address
- **Windows**: Open Command Prompt and run `ipconfig`
  - Look for "IPv4 Address" under your WiFi adapter
  - Example: `192.168.1.100`
- **Mac/Linux**: Open Terminal and run `ifconfig` or `ip addr`
  - Look for your WiFi interface IP address
- **Note**: This IP will be used in TEST_BACKEND_URL

### 2. Configure Backend Environment
- Open `backend/.env`
- Verify or add: `TEST_MODE=true`
- Verify: `HOST=0.0.0.0` (allows connections from network)
- Verify: `PORT=8002` (or your preferred port)
- The backend configuration is already set up properly for WiFi connectivity

### 3. Update Frontend Environment
- Open `frontend/.env`
- Set: `TEST_MODE=true`
- Update `TEST_BACKEND_URL` with your computer's local IP:
  ```
  TEST_BACKEND_URL=http://YOUR_COMPUTER_IP:8002/api/v1
  ```
  - Example: `TEST_BACKEND_URL=http://192.168.1.100:8002/api/v1`
  - **Important**: Use `http://` not `https://` for local development
  - **Important**: Replace `YOUR_COMPUTER_IP` with actual IP from Step 1

### 4. Implement Frontend URL Switching
- Open `frontend/lib/utils/app_constants.dart`
- Locate lines 12-18 (the URL configuration section)
- Replace the hardcoded BASE_URL with dynamic selection:
  ```dart
  // API Base URLs
  static const String PROD_URL =
      'https://dumplin-chatbot-production.up.railway.app/api/v1';
  static const String DEV_URL =
      'https://dumplin-chatbot-production-7871.up.railway.app/api/v1';
  static const String PIPELINE_URL =
      "https://post-data-injestion-pipeline-production.up.railway.app";

  // Dynamic URL selection based on TEST_MODE
  static final bool _isTestMode =
      dotenv.env['TEST_MODE']?.toLowerCase() == 'true';
  static final String _testBackendUrl =
      dotenv.env['TEST_BACKEND_URL'] ?? DEV_URL;
  static final String BASE_URL = _isTestMode ? _testBackendUrl : PROD_URL;

  // Helper to check test mode status
  static bool get isTestMode => _isTestMode;
  static String get backendUrl => BASE_URL;
  ```
- This changes BASE_URL from a hardcoded constant to a computed value based on TEST_MODE

### 5. Add Frontend Logging
- Open `frontend/lib/main.dart`
- Find the `main()` function where `dotenv.load()` is called (around line 32)
- Add logging after `await dotenv.load();`:
  ```dart
  // Log backend URL configuration
  if (kDebugMode) {
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    print('🔗 Backend URL: ${AppConstants.BASE_URL}');
    if (AppConstants.isTestMode) {
      print('🧪 TEST MODE: Connected to test backend');
      print('📱 Make sure your phone and computer are on the same WiFi');
    } else {
      print('🌐 PRODUCTION MODE: Connected to production backend');
    }
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  }
  ```
- Verify the import exists at the top: `import 'package:flutter/foundation.dart';` (should be on line 1)

### 6. Test Backend Connectivity
- Start the backend server on your computer:
  ```bash
  cd backend
  python run.py
  ```
- Verify you see the log: "🧪 TEST MODE ENABLED - Backend running in test mode"
- Verify the server is listening on 0.0.0.0:8002
- Test from your computer browser: `http://localhost:8002/health`
  - Should return: `{"status":"healthy"}`

### 7. Test WiFi Network Access
- Ensure both your computer and phone are on the same WiFi network
- From your phone's browser, visit: `http://YOUR_COMPUTER_IP:8002/health`
  - Example: `http://192.168.1.100:8002/health`
  - Should return: `{"status":"healthy"}`
- If this fails:
  - Check Windows Firewall settings
  - Allow Python/port 8002 through the firewall
  - Verify both devices are on the same WiFi network (not guest network)

### 8. Build and Test Frontend App
- Connect your phone via USB or use wireless debugging
- Build and run the frontend:
  ```bash
  cd frontend
  flutter run
  ```
- Check the startup logs for:
  - "🔗 Backend URL: http://YOUR_COMPUTER_IP:8002/api/v1"
  - "🧪 TEST MODE: Connected to test backend"
- Test the app functionality:
  - Send a chat message
  - Check backend logs to confirm the request was received
  - Verify the response appears in the app

### 9. Test Production Mode
- Set `TEST_MODE=false` in both `.env` files (or remove the lines)
- Restart both backend and frontend
- Verify frontend logs show: "🌐 PRODUCTION MODE: Connected to production backend"
- Verify app connects to production URLs

### 10. Documentation & Troubleshooting
- Document the local IP address for team reference
- Note: IP address may change if using DHCP - consider setting a static IP
- Create a quick reference guide for switching modes

## Testing Strategy

### Unit Tests
Not applicable - this is a configuration change with no new business logic

### Integration Tests
Manual integration testing required to verify network connectivity

### Manual Testing Checklist

#### Test Case 1: Local WiFi Connectivity (Test Mode)
**Setup**:
- Set `TEST_MODE=true` in `backend/.env`
- Set `TEST_MODE=true` and correct IP in `TEST_BACKEND_URL` in `frontend/.env`
- Both devices on same WiFi network

**Steps**:
1. Start backend server on computer
2. Verify backend log shows "TEST MODE ENABLED"
3. Test `/health` endpoint from computer browser
4. Test `/health` endpoint from phone browser
5. Start frontend app on phone
6. Verify startup logs show test backend URL
7. Send a chat message in the app
8. Verify backend receives request and logs it
9. Verify frontend receives response

**Expected Results**:
- All health checks return `{"status":"healthy"}`
- Frontend logs show test URL with local IP
- Chat messages successfully reach backend
- Responses successfully return to frontend
- No connection errors

#### Test Case 2: Production Mode
**Setup**:
- Set `TEST_MODE=false` in both `.env` files

**Steps**:
1. Start backend (if needed for production)
2. Start frontend app on phone
3. Verify logs show production URL
4. Test app functionality

**Expected Results**:
- Frontend uses production URLs
- No test mode logs appear
- App connects to production backend

#### Test Case 3: Fallback Behavior
**Setup**:
- Set `TEST_MODE=true` in `frontend/.env`
- Remove or leave `TEST_BACKEND_URL` blank

**Steps**:
1. Start frontend app
2. Check startup logs

**Expected Results**:
- App falls back to DEV_URL
- No crashes or errors

### Edge Cases

1. **TEST_MODE not set in .env**
   - Should default to `false` (production mode)
   - App should work normally with production URLs

2. **TEST_MODE with different casing** ("True", "TRUE", "tRuE")
   - Should work due to `.toLowerCase()` comparison
   - Any casing should be recognized

3. **Wrong IP address in TEST_BACKEND_URL**
   - Network requests will timeout
   - App should show connection error messages
   - Should not crash the app

4. **Backend not running**
   - Frontend should show connection error
   - Error message should be user-friendly
   - Should not crash the app

5. **Phone and computer on different WiFi networks**
   - Connection will fail (no route to host)
   - Should show connection error
   - Document that both devices must be on same network

6. **Windows Firewall blocking connection**
   - Health check from phone will fail
   - Need to allow Python.exe or port 8002 through firewall
   - Document firewall configuration steps

7. **Computer IP address changes**
   - Connection will fail if IP changes (DHCP)
   - Need to update TEST_BACKEND_URL with new IP
   - Consider configuring static IP for development machine

## Acceptance Criteria

### Backend Test Mode Configuration
- [x] Backend already has `TEST_MODE` property in config.py (line 43)
- [x] Backend already logs test mode status in main.py (lines 13-15)
- [x] Backend already binds to 0.0.0.0 for network access (config.py line 32)
- [ ] `TEST_MODE=true` added to backend/.env
- [ ] Backend startup shows "TEST MODE ENABLED" log when TEST_MODE=true

### Frontend URL Switching
- [ ] Frontend reads `TEST_MODE` from .env file
- [ ] When `TEST_MODE=true`, frontend uses `TEST_BACKEND_URL`
- [ ] When `TEST_MODE=false` or unset, frontend uses `PROD_URL`
- [ ] Frontend logs backend URL on startup
- [ ] Frontend falls back to `DEV_URL` if `TEST_BACKEND_URL` is missing
- [ ] No hardcoded URLs remain in app_constants.dart BASE_URL

### WiFi Connectivity
- [ ] Backend accepts connections from phone over WiFi
- [ ] Phone can access `http://COMPUTER_IP:8002/health` endpoint
- [ ] Frontend on phone successfully sends chat requests to backend on computer
- [ ] Backend on computer successfully sends responses to frontend on phone
- [ ] Connection works when both devices are on the same WiFi network

### Developer Experience
- [ ] Clear startup logs show which mode is active
- [ ] Logs show the exact backend URL being used
- [ ] Simple one-variable change to switch between test and production
- [ ] Works across phone/computer on same WiFi
- [ ] No code changes needed to switch modes
- [ ] Documentation includes steps to find local IP address
- [ ] Documentation includes firewall configuration steps

### Error Handling
- [ ] Graceful error messages when backend is unreachable
- [ ] No crashes when TEST_BACKEND_URL is invalid
- [ ] Clear error messages guide troubleshooting

## Network Configuration Notes

### Finding Your Local IP Address

**Windows**:
```cmd
ipconfig
```
Look for "IPv4 Address" under your WiFi adapter (typically starts with 192.168.x.x or 10.x.x.x)

**Mac**:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Linux**:
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

### Windows Firewall Configuration

If your phone cannot reach the backend:

1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Click "Inbound Rules" → "New Rule"
4. Select "Port" → Next
5. Select "TCP" and enter port "8002" → Next
6. Select "Allow the connection" → Next
7. Check all profiles (Domain, Private, Public) → Next
8. Name it "Dumplin Backend Test Mode" → Finish

Or create a rule for Python:
1. "Inbound Rules" → "New Rule"
2. Select "Program" → Next
3. Browse to your Python installation (e.g., `C:\Python\python.exe`) → Next
4. "Allow the connection" → Next
5. Check all profiles → Next
6. Name it "Python - Dumplin Backend" → Finish

### Alternative: Using ngrok (if WiFi doesn't work)

If you cannot get local WiFi to work, you can use ngrok as an alternative:

```bash
# Install ngrok
# Start your backend on port 8002
# In another terminal:
ngrok http 8002
```

Then use the ngrok URL in TEST_BACKEND_URL (e.g., `https://abc123.ngrok.io/api/v1`)

## Troubleshooting Guide

### Issue: "Connection refused" or "Network error"
**Possible causes**:
- Backend not running
- Wrong IP address in TEST_BACKEND_URL
- Phone and computer on different WiFi networks
- Windows Firewall blocking connection

**Solutions**:
1. Verify backend is running: check for startup logs
2. Test health endpoint from computer browser first
3. Test health endpoint from phone browser
4. Check both devices are on same WiFi (Settings → WiFi)
5. Configure Windows Firewall to allow connection

### Issue: "TEST_MODE=true but still using production URL"
**Possible causes**:
- .env file not loaded
- Frontend not rebuilt after .env change
- Syntax error in .env file

**Solutions**:
1. Verify `TEST_MODE=true` (no spaces around =)
2. Rebuild the frontend app completely
3. Check startup logs to see if TEST_MODE is recognized
4. Ensure .env file is in the frontend root directory

### Issue: IP address keeps changing
**Solution**:
Configure a static IP for your development computer in router settings or Windows network settings.

### Issue: Backend receives request but frontend doesn't show response
**Possible causes**:
- CORS configuration issue
- Response format mismatch

**Solutions**:
1. Check backend CORS settings (should already allow all origins)
2. Check backend logs for errors
3. Monitor network requests in Flutter DevTools
