# Freelancer Time Tracker & Invoice Generator

A full-stack web application for tracking billable hours and automatically generating professional invoices. Built with FastAPI backend and React frontend.

## ✨ Features

- **🕐 Time Tracking**: Log work hours with start/end times and descriptions
- **💼 Project Management**: Create and manage multiple client projects
- **📄 Invoice Generation**: Auto-generate invoices from tracked hours
- **📊 Dashboard**: Real-time earnings summary and analytics
- **💳 Invoice Status Tracking**: Monitor draft, sent, and paid invoices
- **👥 Client Management**: Manage multiple clients
- **🔐 Secure Authentication**: JWT-based login and registration
- **📱 Responsive Design**: Works on desktop and tablet

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.104.1 (Python)
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL
- **Authentication**: JWT + Passlib password hashing
- **Validation**: Pydantic v2
- **API Docs**: Auto-generated Swagger & ReDoc

### Frontend
- **Framework**: React 18.2.0
- **State Management**: Zustand 4.4.0
- **HTTP Client**: Axios 1.6.2
- **Routing**: React Router 6.20.0
- **Package Manager**: npm

## 📁 Project Structure

```
leg_proj3/
├── backend/
│   ├── app/
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── timelog.py
│   │   │   ├── invoice.py
│   │   │   └── client.py
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── routes/              # API endpoint handlers
│   │   │   ├── auth.py
│   │   │   ├── projects.py
│   │   │   ├── timelog.py
│   │   │   ├── invoices.py
│   │   │   └── clients.py
│   │   ├── services/            # Business logic
│   │   │   └── invoice_service.py
│   │   └── database.py
│   ├── main.py                  # FastAPI application entry point
│   ├── requirements.txt
│   ├── .env.example
│   └── time_tracker.db          # SQLite database
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── LoginPage.jsx
    │   │   ├── RegisterPage.jsx
    │   │   ├── DashboardPage.jsx
    │   │   ├── ProjectPage.jsx
    │   │   ├── TimeLogPage.jsx
    │   │   ├── InvoicePage.jsx
    │   │   └── *.css
    │   ├── components/
    │   │   ├── Navbar.jsx
    │   │   └── Navbar.css
    │   ├── store/
    │   │   └── authStore.js      # Zustand auth state
    │   ├── utils/
    │   │   └── api.js            # API client with axios
    │   ├── App.jsx
    │   └── index.js
    ├── package.json
    ├── .env.example
    └── public/
        └── index.html
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# Run backend server
python main.py
```

Backend runs on http://localhost:8002
- API Docs: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# Start development server
npm start
```

Frontend runs on http://localhost:3000

## 📝 API Documentation

### Authentication

```
POST /api/auth/register
{
  "email": "user@example.com",
  "username": "username",
  "password": "password",
  "company_name": "Company",
  "hourly_rate": 50.0
}

POST /api/auth/login
{
  "username": "username",
  "password": "password"
}
```

Returns:
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

### Projects

```
GET /api/projects/              # Get all projects
POST /api/projects/             # Create project
PUT /api/projects/{id}          # Update project
```

### Time Logs

```
GET /api/timelog/               # Get all time logs
POST /api/timelog/              # Create time log
GET /api/timelog/project/{id}   # Get project time logs
DELETE /api/timelog/{id}        # Delete time log
```

### Invoices

```
GET /api/invoices/              # Get all invoices
POST /api/invoices/             # Create invoice
PUT /api/invoices/{id}/status   # Update invoice status
DELETE /api/invoices/{id}       # Delete invoice
GET /api/invoices/earnings/summary  # Get earnings summary
```

### Clients

```
GET /api/clients/               # Get all clients
POST /api/clients/              # Create client
DELETE /api/clients/{id}        # Delete client
```

## 💻 Usage Guide

### Register & Login
1. Visit http://localhost:3000
2. Click "Register here" to create new account
3. Fill in email, username, password, company, and hourly rate
4. After registration, you're automatically logged in
5. Or login with existing credentials

### Create a Project
1. Navigate to Projects page
2. Click "+ New Project"
3. Enter project name, description, and hourly rate
4. Click "Create Project"

### Log Work Time
1. Go to Time Logs page
2. Click "+ Log Time"
3. Select project from dropdown
4. Set start and end times
5. Add work description
6. Click "Log Time"

### Generate Invoice
1. Navigate to Invoices page
2. Click "+ Create Invoice"
3. Enter total hours worked and hourly rate
4. Set due date
5. Click "Create Invoice"
6. Track invoice status (draft → sent → paid)

### Monitor Earnings
1. View Dashboard for earnings summary
2. See total invoiced, paid, and pending amounts
3. Track individual projects and earnings

## 🗄️ Database Schema

### users
```sql
id (PK), username, email, hashed_password, hourly_rate, 
company_name, created_at, updated_at
```

### projects
```sql
id (PK), user_id (FK), client_id (FK), name, description, 
hourly_rate, total_hours, total_earned, created_at, updated_at
```

### timelogs
```sql
id (PK), user_id (FK), project_id (FK), start_time, end_time, 
hours, description, created_at
```

### invoices
```sql
id (PK), user_id (FK), invoice_number, total_hours, hourly_rate, 
total_amount, status, due_date, paid_date, created_at, updated_at
```

### clients
```sql
id (PK), user_id (FK), name, email, rate, created_at, updated_at
```

## 🔒 Authentication

- JWT tokens stored in localStorage
- Authorization header: `Authorization: Bearer <token>`
- Tokens expire after 30 days
- Password hashed with bcrypt
- CORS enabled for development

## 🌐 Deployment

### Backend Deployment (Heroku, Railway, etc.)

```bash
# Set environment variables
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set DATABASE_URL="postgresql://..."

# Deploy
git push heroku main
```

### Frontend Deployment (Vercel, Netlify

)

```bash
# Build for production
npm run build

# Deploy to Vercel
vercel deploy
# Or deploy to Netlify via UI
```

## 🐛 Troubleshooting

### CORS Error
Make sure backend is running and CORS is properly configured in main.py

### 401 Unauthorized
- Check token is in Authorization header
- Ensure token is not expired
- Verify token format: `Bearer <token>`

### Database Connection Error
- Check DATABASE_URL in .env
- For PostgreSQL, verify connection string format
- SQLite should create file automatically

### Frontend won't fetch data
- Verify backend is running on port 8002
- Check REACT_APP_API_URL in .env
- Open browser console to see actual error

## 📈 Future Enhancements

- [ ] PDF invoice generation
- [ ] Email invoice delivery
- [ ] Payment gateway integration (Stripe)
- [ ] Recurring invoices
- [ ] Expense tracking
- [ ] Multiple currencies
- [ ] Dark mode
- [ ] Mobile app (React Native)
- [ ] Advanced analytics & reports
- [ ] Team collaboration features

## 📄 License

MIT License - Feel free to use this project for learning or commercial purposes.

## 🤝 Contributing

Contributions are welcome! Feel free to:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For issues or questions:
1. Check API documentation at `/docs`
2. Review error messages in browser console
3. Verify environment variables are set
4. Check backend logs for server errors

---

**Happy tracking! 📊**
