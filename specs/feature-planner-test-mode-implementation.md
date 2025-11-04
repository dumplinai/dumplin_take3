# Feature: Test Mode URL Switching

## Feature Description
Enable simple test mode that allows the frontend and backend to communicate during local development. When `TEST_MODE=true` is set in both `.env` files, the frontend will use `TEST_BACKEND_URL` to connect to a local or test backend server instead of production.

This allows developers to:
- Run the frontend app locally and connect to a local backend
- Test and troubleshoot features without affecting production
- Easily switch between test and production by changing one environment variable

## Scope
- **Frontend (Flutter)**: Read TEST_MODE from .env and use TEST_BACKEND_URL when true
- **Backend (FastAPI)**: Read TEST_MODE from .env and log when running in test mode

## User Story
As a **developer**
I want to **set TEST_MODE=true in both .env files**
So that **the frontend connects to my local test backend for development and troubleshooting**

## Problem Statement
The frontend has `TEST_MODE` and `TEST_BACKEND_URL` defined in `.env` but they're not being used. The `BASE_URL` in `app_constants.dart` is hardcoded to production, so all API requests go to production regardless of TEST_MODE setting.

Developers need a simple way to point the frontend to a local/test backend without changing code.

## Solution Statement
Make the frontend dynamically read `TEST_MODE` from `.env` and switch the `BASE_URL` to `TEST_BACKEND_URL` when test mode is enabled. The backend will also read `TEST_MODE` and log when it's running in test mode.

## Relevant Files
Use these files to implement the feature:

### Frontend Files

#### `frontend/.env` (lines 1-7)
- **Why relevant**: Contains TEST_MODE=true and TEST_BACKEND_URL that need to be used
- **Changes needed**: Already configured, just need to be consumed by the app

#### `frontend/lib/utils/app_constants.dart` (lines 12-18)
- **Why relevant**: Contains hardcoded BASE_URL that ignores TEST_MODE
- **Changes needed**: Change BASE_URL to read TEST_MODE and use TEST_BACKEND_URL when true
- **Current issue**: `static const String BASE_URL = PROD_URL;` is hardcoded

#### `frontend/lib/main.dart`
- **Why relevant**: Entry point where dotenv is loaded
- **Changes needed**: Add simple log showing which URL is being used

### Backend Files

#### `backend/.env` (lines 8-10)
- **Why relevant**: Needs TEST_MODE variable added
- **Changes needed**: Add `TEST_MODE=true` for local development

#### `backend/app/core/config.py` (lines 40-41)
- **Why relevant**: Configuration file that loads environment variables
- **Changes needed**: Add TEST_MODE property

#### `backend/main.py` (lines 10-14)
- **Why relevant**: Startup function
- **Changes needed**: Log when TEST_MODE is enabled

## Implementation Plan

### Phase 1: Backend Configuration
Add TEST_MODE to backend configuration so it can log when running in test mode.

### Phase 2: Frontend URL Switching
Implement dynamic URL selection in frontend based on TEST_MODE from .env.

### Phase 3: Testing
Test that frontend connects to test backend when TEST_MODE=true.

## Step by Step Tasks

### Step 1: Add TEST_MODE to Backend .env
- Open `backend/.env`
- Add line: `TEST_MODE=true` (for local development)
- This variable will be used to indicate the backend is running in test mode

### Step 2: Update Backend Configuration
- Open `backend/app/core/config.py`
- Add TEST_MODE property after line 41:
  ```python
  TEST_MODE: bool = os.getenv("TEST_MODE", "false").lower() == "true"
  ```
- This reads TEST_MODE from environment and converts to boolean

### Step 3: Add Backend Startup Logging
- Open `backend/main.py`
- In the `create_app()` function, after line 11 add:
  ```python
  if settings.TEST_MODE:
      logger.info("🧪 TEST MODE ENABLED - Backend running in test mode")
  ```
- This logs when backend starts in test mode

### Step 4: Update Frontend URL Selection
- Open `frontend/lib/utils/app_constants.dart`
- Replace lines 12-18 with:
  ```dart
  // API Base URLs
  static const String PROD_URL =
      'https://dumplin-chatbot-production.up.railway.app/api/v1';
  static const String DEV_URL =
      'https://dumplin-chatbot-production-7871.up.railway.app/api/v1';

  // Dynamic URL selection based on TEST_MODE
  static final bool _isTestMode =
      dotenv.env['TEST_MODE']?.toLowerCase() == 'true';
  static final String _testBackendUrl =
      dotenv.env['TEST_BACKEND_URL'] ?? DEV_URL;
  static final String BASE_URL = _isTestMode ? _testBackendUrl : PROD_URL;

  // Helper to check test mode
  static bool get isTestMode => _isTestMode;
  ```
- This reads TEST_MODE from .env and switches URL accordingly

### Step 5: Add Frontend Startup Logging
- Open `frontend/lib/main.dart`
- After the `await dotenv.load();` line, add:
  ```dart
  // Log which backend URL is being used
  if (kDebugMode) {
    print('🔗 Backend URL: ${AppConstants.BASE_URL}');
    if (AppConstants.isTestMode) {
      print('🧪 TEST MODE: Connecting to test backend');
    }
  }
  ```
- Add import at top if needed: `import 'package:flutter/foundation.dart' show kDebugMode;`
- This shows which URL the app will use on startup

### Step 6: Test the Implementation
- Set `TEST_MODE=true` in both `backend/.env` and `frontend/.env`
- Start the backend (should see "TEST MODE ENABLED" log)
- Start the frontend (should see the test backend URL in startup logs)
- Send a chat message and verify it reaches your test backend
- Set `TEST_MODE=false` and verify it uses production URL

## Testing Strategy

### Manual Testing
**Test Case 1: Test Mode Enabled**
1. Set `TEST_MODE=true` in `backend/.env`
2. Set `TEST_MODE=true` in `frontend/.env`
3. Start backend - verify log shows "TEST MODE ENABLED"
4. Start frontend - verify log shows test backend URL
5. Use the app - verify API calls go to test backend

**Test Case 2: Test Mode Disabled**
1. Set `TEST_MODE=false` in both .env files (or remove the line)
2. Start backend - verify no test mode log
3. Start frontend - verify log shows production URL
4. Verify app connects to production backend

**Test Case 3: Missing TEST_BACKEND_URL**
1. Set `TEST_MODE=true` in `frontend/.env`
2. Remove or comment out `TEST_BACKEND_URL`
3. Verify frontend falls back to DEV_URL

### Edge Cases
1. **TEST_MODE not set**: Should default to false (production mode)
2. **TEST_MODE with wrong casing**: "True" or "TRUE" should work (case-insensitive)
3. **Invalid TEST_BACKEND_URL**: App should fail gracefully with error message
4. **Backend not running**: Frontend should show appropriate error when test backend is unreachable

## Acceptance Criteria

1. **Backend Test Mode**:
   - [ ] `TEST_MODE` can be set in `backend/.env`
   - [ ] Backend logs "TEST MODE ENABLED" when `TEST_MODE=true`
   - [ ] Backend works normally when `TEST_MODE=false` or unset

2. **Frontend URL Switching**:
   - [ ] When `TEST_MODE=true`, frontend uses `TEST_BACKEND_URL`
   - [ ] When `TEST_MODE=false`, frontend uses `PROD_URL`
   - [ ] Frontend logs which backend URL is being used on startup
   - [ ] Frontend falls back to DEV_URL if TEST_BACKEND_URL is missing

3. **End-to-End Communication**:
   - [ ] With `TEST_MODE=true` on both sides, frontend successfully talks to test backend
   - [ ] With `TEST_MODE=false`, frontend talks to production backend
   - [ ] Developers can switch modes by changing the .env variable
   - [ ] No code changes needed to switch between test and production

4. **Developer Experience**:
   - [ ] Clear logs show which mode is active
   - [ ] Simple one-variable change to switch modes
   - [ ] Works for local development and troubleshooting
