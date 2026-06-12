# Setup Guide — HourStack

## Overview

This guide explains how to run HourStack locally for development, evaluation, or demonstration.

## Prerequisites

- Python 3.8+
- Node.js 14+
- npm

## 1) Backend Setup

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

- macOS/Linux:
  ```bash
  source venv/bin/activate
  ```
- Windows:
  ```bash
  venv\Scripts\activate
  ```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Create environment variables file:

- macOS/Linux:
  ```bash
  cp .env.example .env
  ```
- Windows:
  ```bash
  copy .env.example .env
  ```

Start the backend server:

```bash
python main.py
```

Backend endpoints:
- API base URL: `http://localhost:8002`
- Swagger docs: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`

## 2) Frontend Setup

Open a new terminal and run:

```bash
cd frontend
npm install
```

Create frontend environment file:

- macOS/Linux:
  ```bash
  cp .env.example .env
  ```
- Windows:
  ```bash
  copy .env.example .env
  ```

Set `REACT_APP_API_URL` in `.env` to your backend URL (for local development, use `http://localhost:8002`).

Start the frontend:

```bash
npm start
```

Frontend app URL:
- `http://localhost:3000`

## 3) Optional: Run Backend Tests

From the `backend` directory:

```bash
python -m pytest -q
```

If `pytest` is not available, install development dependencies first:

```bash
pip install -r requirements-dev.txt
```

## 4) Docker Setup (Optional)

From the repository root:

```bash
docker compose up --build
```

This starts the application stack using the provided `docker-compose.yml`.

## Troubleshooting

### Port 8002 already in use

- Stop any process using port `8002`, then restart `python main.py`.

### Frontend cannot reach backend

- Confirm backend is running on `http://localhost:8002`.
- Verify `REACT_APP_API_URL` in `frontend/.env`.

### Missing frontend packages

```bash
cd frontend
npm install
```

## Production Notes

For production deployment, configure at minimum:

- `SECRET_KEY`
- `DATABASE_URL`
- `FRONTEND_URL`

A sample Render deployment configuration is included in `render.yaml`.
