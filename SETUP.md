# leg_proj3 - Complete Setup Guide

## Overview

This is a complete full-stack application for freelancers to track time and generate invoices. It has been fully implemented and is ready to use.

## ✅ What's Included

### Backend (FastAPI)
- ✅ User authentication (register/login with JWT)
- ✅ Project management API
- ✅ Time logging API with automatic hour calculation
- ✅ Invoice generation with automatic numbering
- ✅ Client management
- ✅ Earnings tracking and summary
- ✅ Authorization header support
- ✅ Comprehensive error handling

### Frontend (React)
- ✅ Authentication flow (register/login)
- ✅ Dashboard with earnings summary
- ✅ Project management page
- ✅ Time tracking interface
- ✅ Invoice management page
- ✅ Navigation bar with routing
- ✅ Zustand state management
- ✅ Axios API client with auth interceptor
- ✅ Responsive design

## 🚀 Installation & Setup

### Step 1: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# Edit .env if needed (optional, defaults work fine)
# DATABASE_URL=sqlite:///./time_tracker.db
# SECRET_KEY=your-secret-key-change-in-production
```

### Step 2: Start Backend Server

```bash
# Make sure you're in backend directory with venv activated
python main.py
```

Expected output:
```
Uvicorn running on http://0.0.0.0:8002
Application startup complete
```

**Check backend is working:**
- API Docs: http://localhost:8002/docs
- Health Check: http://localhost:8002/

### Step 2.5: Run Backend Tests (Recommended)

```bash
# From backend directory with venv activated
pytest -q
```

Expected: all tests pass.

Note: test output is configured via `backend/pytest.ini` to suppress known third-party deprecation warnings from `httpx` and `python-jose`, so only actionable warnings from this codebase are shown.

### Step 3: Frontend Setup

Open a new terminal/command prompt:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# Start development server
npm start
```

Expected:
- Browser opens to http://localhost:3000
- App dashboard appears (or redirects to login)

## 📝 Using the Application

### First Time Users

1. **Register Account**
   - Go to http://localhost:3000/register
   - Fill in: Email, Username, Password
   - Optional: Company name and hourly rate
   - Click "Register"
   - You're automatically logged in!

2. **Create a Project**
   - Click "Projects" in navigation
   - Click "+ New Project"
   - Enter project name and hourly rate
   - Click "Create Project"

3. **Log Work Time**
   - Click "Time Logs" in navigation
   - Click "+ Log Time"
   - Select the project you created
   - Set start time and end time
   - Add description of work
   - Click "Log Time"

4. **Generate Invoice**
   - Click "Invoices" in navigation
   - Click "+ Create Invoice"
   - Enter hours worked and hourly rate
   - Set due date
   - Click "Create Invoice"

5. **View Dashboard**
   - Click "Dashboard" to see:
     - Total amount invoiced
     - Amount paid
     - Amount pending
     - Project overview

## 🔐 Test Credentials

After registration, use any credentials you created. Example:
- Username: testuser
- Password: password123
- Email: test@example.com
- Hourly Rate: $50

## 🛠️ Development

### File Structure Quick Reference

**Backend Important Files:**
- `main.py` - FastAPI app configuration
- `app/models/` - Database models
- `app/routes/` - API endpoints
- `app/schemas/` - Request/response validation
- `app/services/` - Business logic

**Frontend Important Files:**
- `src/pages/` - Page components
- `src/components/Navbar.jsx` - Navigation
- `src/store/authStore.js` - Auth state
- `src/utils/api.js` - API calls
- `src/App.jsx` - Main routing

### Adding Features

Example: Add a new endpoint

1. **Create schema** in `backend/app/schemas/new.py`
2. **Create model** in `backend/app/models/new.py`
3. **Create route** in `backend/app/routes/new.py`
4. **Include router** in `main.py`
5. **Create API call** in `frontend/src/utils/api.js`
6. **Create page component** in `frontend/src/pages/NewPage.jsx`
7. **Add route** in `App.jsx`

## 🔄 Common Tasks

### Restart Backend
```bash
cd backend
venv\Scripts\activate  # Windows
python main.py
```

### Restart Frontend
```bash
cd frontend
npm start
```

### Check Backend Logs
- Terminal where backend is running shows logs
- API Docs available at http://localhost:8002/docs

### Clear Database (SQLite)
```bash
# Delete the file
rm backend/time_tracker.db  # macOS/Linux
del backend\time_tracker.db  # Windows

# Restart backend - new database will be created automatically
```

### View API Requests (Browser)
1. Open http://localhost:3000
2. Press F12 (Developer Tools)
3. Go to Network tab
4. Make requests and see details

## 📊 API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /api/auth/register | Create account |
| POST | /api/auth/login | Login |
| GET | /api/projects/ | List projects |
| POST | /api/projects/ | Create project |
| GET | /api/timelog/ | List time logs |
| POST | /api/timelog/ | Create time log |
| GET | /api/invoices/ | List invoices |
| POST | /api/invoices/ | Create invoice |
| DELETE | /api/invoices/{id} | Delete invoice |

## ⚠️ Troubleshooting

### "Port 8002 already in use"
```bash
# Find and kill process on port 8002
# Windows:
netstat -ano | findstr :8002
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8002 | xargs kill -9
```

### "Cannot find module 'react'"
```bash
cd frontend
npm install
```

### "ModuleNotFoundError" in backend
```bash
cd backend
# Make sure venv is activated
pip install -r requirements.txt
```

### "CORS error" when fetching from frontend
- Backend CORS is configured in main.py for localhost:3000
- Make sure backend is running
- Check browser console for exact error message

### "`Unauthorized `(401) error
- User needs to log in first
- Check localStorage in browser DevTools - should have token
- Verify Authorization header format: `Bearer <token>`

## 🎯 Next Steps

1. Try all features end-to-end
2. Create multiple projects
3. Log time across different projects
4. Generate invoices
5. Track earnings

## 📈 Production Deployment

### Backend (example with Railway)
1. Add PostgreSQL database connection
2. Set SECRET_KEY environment variable
3. Update DATABASE_URL to PostgreSQL
4. Deploy

### Frontend (example with Vercel)
1. Build: `npm run build`
2. Upload to Vercel
3. Set environment variable: `REACT_APP_API_URL=https://your-backend.com`

## 💾 Data Persistence

- **SQLite**: Data stored in `backend/time_tracker.db`
- **PostgreSQL**: Configure DATABASE_URL in .env
- Database is automatically created on first run

## 📞 Support

- Check API docs at http://localhost:8002/docs
- Look at browser console (F12) for errors
- Check backend terminal for server errors
- Verify .env files are set up correctly

---

**Ready to start tracking time and generating invoices! 🚀**
