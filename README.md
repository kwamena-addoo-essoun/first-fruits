# Freelancer Time Tracker & Invoice Generator

Track billable hours and automatically generate invoices.

## Features

- **Time Tracking**: Log work hours with project details
- **Project Management**: Create and manage client projects
- **Auto-Invoice Generation**: Generate invoices from time logs
- **Earnings Dashboard**: Real-time earnings summary
- **Invoice Status**: Track draft, sent, and paid invoices
- **Client Management**: Manage multiple clients

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy
- **Frontend**: React, Zustand
- **Database**: SQLite/PostgreSQL

## API Endpoints

- `POST /api/auth/register` - Register
- `POST /api/auth/login` - Login
- `GET /api/projects/` - Get projects
- `POST /api/timelog/` - Log time
- `POST /api/invoices/` - Create invoice
- `GET /api/invoices/earnings/summary` - Get earnings

## Quick Start

1. Backend: `pip install -r requirements.txt && python main.py`
2. Frontend: `npm install && npm start`
