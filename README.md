# HourStack — Freelancer Time Tracker & Invoice Generator

A full-stack web application for freelancers to track billable hours, manage client projects, and automatically generate professional invoices.

## Features

- **Time Tracking** — Log work sessions with start/end times and descriptions
- **Project Management** — Create and manage multiple client projects
- **Invoice Generation** — Auto-generate invoices from tracked hours with unique numbering
- **Earnings Dashboard** — Real-time summary of total invoiced, paid, and pending amounts
- **Invoice Status Tracking** — Monitor invoices from draft through to paid
- **Client Management** — Organise and manage multiple clients
- **Secure Authentication** — JWT-based registration and login
- **Responsive Design** — Works on desktop and tablet

## Tech Stack

**Backend**
- FastAPI (Python)
- SQLAlchemy ORM — SQLite (development) / PostgreSQL (production)
- JWT authentication with bcrypt password hashing
- Pydantic v2 for data validation
- Auto-generated Swagger & ReDoc API docs

**Frontend**
- React 18
- Zustand (state management)
- Axios (HTTP client)
- React Router v6

**Infrastructure**
- Docker & Docker Compose
- Render deployment config included

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
cp .env.example .env            # configure environment variables
python main.py
```

API available at `http://localhost:8002`
Interactive docs at `http://localhost:8002/docs`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env            # set REACT_APP_API_URL
npm start
```

App available at `http://localhost:3000`

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Authenticate and receive JWT |
| GET/POST | `/api/projects/` | List or create projects |
| GET/POST | `/api/timelog/` | List or log work time |
| GET/POST | `/api/invoices/` | List or create invoices |
| GET | `/api/invoices/earnings/summary` | Earnings summary |
| GET/POST | `/api/clients/` | List or create clients |

All protected endpoints require: `Authorization: Bearer <token>`

## Deployment

The repository includes a `render.yaml` for one-click deployment to [Render](https://render.com) and a `docker-compose.yml` for containerised local or server deployment.

For production, set the following environment variables:

```
SECRET_KEY=
DATABASE_URL=postgresql://...
FRONTEND_URL=
```

## License

MIT
