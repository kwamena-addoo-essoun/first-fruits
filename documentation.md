# HourStack — Product & Technical Documentation

**Version:** 1.1.0  
**Last Updated:** March 27, 2026  
**Status:** Production-Ready  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Overview](#2-product-overview)
3. [Key Features](#3-key-features)
4. [Business Model & Pricing](#4-business-model--pricing)
5. [System Architecture](#5-system-architecture)
6. [Technology Stack](#6-technology-stack)
7. [Database Schema](#7-database-schema)
8. [API Reference](#8-api-reference)
9. [Security](#9-security)
10. [Email & Notifications](#10-email--notifications)
11. [PDF Invoice Generation](#11-pdf-invoice-generation)
12. [AI Chatbot Assistant](#12-ai-chatbot-assistant)
13. [Deployment](#13-deployment)
14. [Development Setup](#14-development-setup)
15. [Product Roadmap](#15-product-roadmap)

---

## 1. Executive Summary

HourStack is a **SaaS (Software-as-a-Service) time tracking and invoicing platform** purpose-built for freelancers and independent contractors. It eliminates the friction of manual hour logging and invoice creation by providing a unified, web-based workspace where a freelancer can track work hours, manage multiple clients and projects, and generate and deliver professional PDF invoices — all in one place.

The platform operates on a **freemium model** with a paid Pro tier, enabling sustainable recurring revenue while maintaining a low barrier to entry for new users. The core application is fully built, tested, and deployment-ready.

**Target Market:** Freelance developers, designers, consultants, writers, and any independent professional who bills clients by the hour.

---

## 2. Product Overview

### What Problem Does HourStack Solve?

Freelancers typically juggle multiple apps to manage their business: a spreadsheet for hours, a separate tool for invoices, email for delivery, and a bank account for tracking payments. This fragmented workflow creates:

- Lost billable hours from manual and inconsistent logging
- Time wasted formatting invoices in Word or Excel
- Late payments from non-systematic follow-up
- No clear view of monthly or project-level earnings

HourStack consolidates the entire billing workflow into a single platform.

### Core Workflow

```
Log Hours  →  Group by Project  →  Generate Invoice  →  Email to Client  →  Mark as Paid
```

1. **Freelancer** registers and configures their hourly rate and company details.
2. **Clients** are added to the account — each with a name, email, and optional rate.
3. **Projects** are created and linked to clients.
4. **Time logs** are recorded against projects with start/end times and descriptions.
5. At billing time, an **invoice** is auto-generated from all uninvoiced time logs for a project — hours are calculated automatically.
6. The **PDF invoice** can be downloaded or **emailed directly to the client** (Pro plan).
7. Invoice status is tracked through a **draft → sent → paid** lifecycle.
8. The **Dashboard** provides a real-time earnings summary across all invoices.

---

## 3. Key Features

### Time Tracking
- Log work sessions with a start time, end time, and free-text description.
- Hours are calculated automatically from start/end timestamps.
- Supports open-ended sessions (end time nullable — timer-style logging).
- Time logs are flagged as "invoiced" once included in an invoice, preventing double-billing.

### Project Management
- Create and manage unlimited projects (Pro) or up to 3 (Free).
- Associate projects with a specific client.
- Each project tracks total cumulative hours and total earned.
- Projects can have their own hourly rate, overriding the account default.

### Client Management
- Maintain a client directory with name, email, and custom billing rates.
- All data (projects, time logs, invoices) is scoped per client.
- Client name is snapshot-captured at invoice creation to preserve historical accuracy even if the client record is later edited.

### Invoice Generation
- One-click invoice generation from all uninvoiced time logs for a project.
- Auto-computes total hours and applies the project's hourly rate.
- Unique sequential invoice numbers generated automatically (`INV-{user_id}-{sequence}`).
- Invoices include client name, project name, hours breakdown, rate, total amount, issue date, and due date.
- Optional free-text notes field per invoice.
- Invoice status lifecycle: **Draft → Sent → Paid**, with a `paid_date` timestamp recorded upon payment.

### PDF Generation
- Professional PDF invoices generated on the server using **ReportLab**.
- PDFs are generated on-demand and streamed to the browser or attached to emails.
- PDF includes all invoice metadata, itemisation, and totals in a clean, branded layout.

### Email Delivery (Pro)
- Emailing invoices directly to clients is a **Pro-only** feature.
- Supports two delivery methods: **Resend API** (preferred) and **SMTP** (fallback).
- Automated transactional emails also handle:
  - Email address verification on registration
  - Password reset requests

### Earnings Dashboard
- Real-time summary of total invoiced, total paid, and outstanding amounts.
- Aggregated from all user invoices across all clients and projects.

### Admin Panel
- Superuser admin accounts with elevated access.
- Admin can list all registered users, force-verify emails, and delete user accounts.
- Role enforced via JWT claim (`is_admin`) and server-side middleware — not just client-side.

### AI Chatbot Assistant
- Context-aware AI assistant powered by **GPT-4o mini** (OpenAI).
- Floating 💬 widget fixed to the bottom-right of every authenticated page.
- Knows the user's live data: earnings, projects, uninvoiced hours, recent invoices.
- Can answer natural-language questions like "How much have I earned this month?" or "Do I have uninvoiced hours?"
- Conversation history maintained within the session (capped at 20 messages for cost efficiency).
- Gracefully disabled if `OPENAI_API_KEY` is not configured — returns a clear error rather than crashing.

---

## 4. Business Model & Pricing

HourStack uses a **freemium SaaS model** with a single paid tier:

| Feature | Free Plan | Pro Plan |
|---------|-----------|----------|
| Active projects | **3** | Unlimited |
| Invoices per month | **10** | Unlimited |
| PDF download | ✅ | ✅ |
| Email invoice to client | ❌ | ✅ |
| Client management | ✅ | ✅ |
| Time tracking | ✅ | ✅ |
| Dashboard & analytics | ✅ | ✅ |

**Pro Plan Pricing:** $12 / month (recurring)

### Billing Infrastructure
- Payments and subscriptions are processed through **Lemon Squeezy**, a Merchant of Record that handles sales tax, VAT, and compliance globally.
- The backend stores `stripe_customer_id` and `stripe_subscription_id` per user for subscription lifecycle management.
- Webhooks from Lemon Squeezy automatically upgrade/downgrade the user's `plan` field in the database upon subscription changes.
- Plan limits are **enforced on the backend** — not just the frontend — preventing circumvention via API calls.
- Upgrade prompts are surfaced in the UI when a free user hits a limit.

### Revenue Potential (Illustrative)

| Paid Users | Monthly Revenue |
|------------|----------------|
| 100 | $1,200 |
| 500 | $6,000 |
| 1,000 | $12,000 |
| 5,000 | $60,000 |

---

## 5. System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Client (Browser)                     │
│                   React SPA — localhost:3000                │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS / REST (JSON)
                            │ Authorization: Bearer <JWT>
┌───────────────────────────▼─────────────────────────────────┐
│                     FastAPI Backend                         │
│                    uvicorn — port 8002                      │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Routes    │  │   Services   │  │   Middleware     │   │
│  │  auth       │  │ InvoiceSvc   │  │  JWT Auth        │   │
│  │  users      │  │ EmailSvc     │  │  Rate Limiting   │   │
│  │  clients    │  │ PDF Gen      │  │  CORS            │   │
│  │  projects   │  └──────────────┘  └──────────────────┘   │
│  │  timelog    │                                            │
│  │  invoices   │  ┌──────────────────────────────────────┐  │
│  │  billing    │  │         SQLAlchemy ORM               │  │
│  │  admin      │  └────────────────┬─────────────────────┘  │
│  │  chat       │                   │                        │
│  └─────────────┘                   │                        │
└───────────────────────────────────┬─────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────┐
         │                   Database                      │
         │        PostgreSQL (prod) / SQLite (dev)         │
         └─────────────────────────────────────────────────┘
```

### Deployment Model

In production, the **React build output is served statically by the FastAPI backend** — there is no separate frontend server. The React app is built (`npm run build`) and its output is mounted as a static directory within FastAPI, with an SPA catch-all returning `index.html` for client-side routing. This simplifies infrastructure to a single deployable service.

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API framework | FastAPI | Async-capable, auto-generates OpenAPI docs, excellent DX |
| ORM | SQLAlchemy 2.0 | Battle-tested, supports both SQLite and PostgreSQL |
| Migrations | Alembic | Schema versioning; safe to run on production DB |
| Auth | JWT (HS256) | Stateless, scalable — no session store needed |
| Password hashing | PBKDF2-SHA256 | OWASP-compliant, strong key derivation |
| Frontend state | Zustand | Lightweight, minimal boilerplate vs Redux |
| Rate limiting | SlowAPI | Per-IP limits on sensitive endpoints |

---

## 6. Technology Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.8+ |
| Web framework | FastAPI | 0.104.1 |
| ASGI server | Uvicorn | 0.24.0 |
| ORM | SQLAlchemy | 2.0.23 |
| DB migrations | Alembic | 1.14.1 |
| Data validation | Pydantic | 2.5.0 |
| Auth (JWT) | python-jose | 3.3.0 |
| Password hashing | Passlib | 1.7.4 |
| PDF generation | ReportLab | 4.2.5 |
| Rate limiting | SlowAPI | 0.1.9 |
| Database drivers | psycopg2-binary | 2.9.9 |
| HTTP client | httpx | 0.26.0 |
| Environment | python-dotenv | 1.0.0 |
| AI / LLM | OpenAI SDK | 2.30.0 |

### Frontend

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | JavaScript (JSX) | ES2022 |
| UI framework | React | 18.2.0 |
| State management | Zustand | 4.4.0 |
| HTTP client | Axios | 1.6.2 |
| Routing | React Router | 6.20.0 |
| Package manager | npm | — |

### Infrastructure

| Component | Technology |
|-----------|-----------|
| Database (dev) | SQLite |
| Database (prod) | PostgreSQL 16 |
| Containerisation | Docker + Docker Compose |
| Cloud hosting | Render (configured) |
| Email delivery | Resend API / SMTP fallback |
| Payments | Lemon Squeezy |

---

## 7. Database Schema

### Entity Relationship Overview

```
users
  ├── clients        (one-to-many)
  ├── projects       (one-to-many)
  ├── timelogs       (one-to-many)
  └── invoices       (one-to-many)

clients
  └── projects       (one-to-many)

projects
  ├── timelogs       (one-to-many)
  └── invoices       (one-to-many)
```

All foreign-key relationships from owned entities back to `users` use **cascade delete** — deleting a user removes all their data.

---

### `users`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer (PK) | Auto-increment |
| `user_id` | String (UUID) | Public-facing unique identifier |
| `email` | String | Unique, indexed |
| `username` | String | Unique, indexed |
| `hashed_password` | String | PBKDF2-SHA256 hash |
| `hourly_rate` | Float | Default account rate |
| `company_name` | String | Optional |
| `is_admin` | Boolean | Default: false |
| `is_verified` | Boolean | Email verification gate |
| `plan` | String | `"free"` or `"pro"` |
| `stripe_customer_id` | String | Lemon Squeezy customer reference |
| `stripe_subscription_id` | String | Active subscription reference |
| `created_at` | DateTime | UTC |

---

### `clients`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer (PK) | Auto-increment |
| `client_id` | String (UUID) | Public-facing identifier |
| `user_id` | Integer (FK → users) | Owning freelancer |
| `name` | String | Client display name |
| `email` | String | For invoice delivery |
| `rate` | String | Custom rate label (optional) |
| `created_at` | DateTime | UTC |

---

### `projects`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer (PK) | Auto-increment |
| `project_id` | String (UUID) | Public-facing identifier |
| `user_id` | Integer (FK → users) | Owning freelancer |
| `client_id` | Integer (FK → clients) | Associated client |
| `name` | String | Project name |
| `description` | String | Optional description |
| `hourly_rate` | Float | Project-specific rate |
| `is_active` | Boolean | Soft active/inactive flag |
| `total_hours` | Float | Cumulative tracked hours |
| `total_earned` | Float | Cumulative earned value |
| `created_at` | DateTime | UTC |

---

### `timelogs`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer (PK) | Auto-increment |
| `log_id` | String (UUID) | Public-facing identifier |
| `user_id` | Integer (FK → users) | Owning freelancer |
| `project_id` | Integer (FK → projects) | Associated project |
| `start_time` | DateTime | Session start |
| `end_time` | DateTime | Session end (nullable if timer running) |
| `hours` | Float | Computed from start/end (nullable if running) |
| `description` | Text | Work description |
| `is_invoiced` | Integer | `0` = uninvoiced, `1` = invoiced |
| `created_at` | DateTime | UTC |

---

### `invoices`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer (PK) | Auto-increment |
| `invoice_id` | String (UUID) | Public-facing identifier |
| `user_id` | Integer (FK → users) | Owning freelancer |
| `client_id` | Integer (FK → clients) | Associated client |
| `project_id` | Integer (FK → projects) | Associated project |
| `invoice_number` | String | Auto-generated: `INV-{user_id}-{seq}` |
| `client_name` | String | Snapshot at creation time |
| `project_name` | String | Snapshot at creation time |
| `notes` | Text | Optional invoice notes |
| `total_hours` | Float | Billed hours |
| `hourly_rate` | Float | Applied rate |
| `total_amount` | Float | `total_hours × hourly_rate` |
| `status` | String | `draft`, `sent`, `paid` |
| `issue_date` | DateTime | Auto-set at creation |
| `due_date` | DateTime | Set by user |
| `paid_date` | DateTime | Set when status → `paid` |
| `created_at` | DateTime | UTC |

---

### `email_verification_tokens`

Stores short-lived tokens (24-hour TTL) used to verify a user's email on registration.

### `password_reset_tokens`

Stores short-lived, single-use tokens (1-hour TTL) for the forgot-password flow.

---

## 8. API Reference

> **Base URL:** `http://localhost:8002` (development) / `https://hourstack.onrender.com` (production)  
> **Interactive Docs:** `/docs` (Swagger UI) · `/redoc` (ReDoc)  
> **Authentication:** All endpoints except auth routes require `Authorization: Bearer <JWT>` header.

---

### Authentication — `/api/auth`

#### `POST /api/auth/register`
Register a new user account.

**Rate limit:** 5 requests/minute per IP

**Request body:**
```json
{
  "email": "jane@example.com",
  "username": "janedoe",
  "password": "securepassword",
  "company_name": "Jane Doe Consulting",
  "hourly_rate": 85.00
}
```

**Response `201`:**
```json
{
  "id": 1,
  "user_id": "uuid-string",
  "email": "jane@example.com",
  "username": "janedoe",
  "company_name": "Jane Doe Consulting",
  "hourly_rate": 85.00,
  "plan": "free",
  "is_verified": false,
  "created_at": "2026-03-27T10:00:00Z"
}
```

A verification email is dispatched automatically. Login is blocked until the email is verified.

---

#### `POST /api/auth/login`
Authenticate and receive a JWT access token.

**Rate limit:** 10 requests/minute per IP

**Request body:**
```json
{
  "username": "janedoe",
  "password": "securepassword"
}
```

> The `username` field accepts either a username or email address.

**Response `200`:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

**Error responses:**
- `401` — Invalid credentials
- `403` — Email not verified (`EMAIL_NOT_VERIFIED`)

---

#### `POST /api/auth/refresh`
Exchange a valid JWT for a new 24-hour token.

---

#### `POST /api/auth/forgot-password`
Trigger a password reset email.

**Rate limit:** 3 requests/minute per IP

**Request body:**
```json
{ "email": "jane@example.com" }
```

---

#### `POST /api/auth/reset-password`
Complete the password reset using the token from the email.

**Request body:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "new-secure-password"
}
```

---

#### `POST /api/auth/verify-email`
Verify a user's email address using the token from the registration email.

---

#### `POST /api/auth/resend-verification`
Resend the email verification link.

**Rate limit:** 3 requests/minute per IP

---

### Users — `/api/users`

#### `GET /api/users/me`
Get the authenticated user's profile.

**Response `200`:**
```json
{
  "id": 1,
  "username": "janedoe",
  "email": "jane@example.com",
  "company_name": "Jane Doe Consulting",
  "hourly_rate": 85.00,
  "plan": "free",
  "is_verified": true,
  "created_at": "2026-03-27T10:00:00Z"
}
```

---

#### `PUT /api/users/me`
Update the authenticated user's profile (hourly rate, company name, etc.).

---

### Clients — `/api/clients`

#### `GET /api/clients/`
List all clients for the authenticated user.

#### `POST /api/clients/`
Create a new client.

**Request body:**
```json
{
  "name": "Acme Corp",
  "email": "billing@acme.com",
  "rate": "85"
}
```

#### `DELETE /api/clients/{client_id}`
Delete a client record.

---

### Projects — `/api/projects`

#### `GET /api/projects/`
List all projects.

#### `POST /api/projects/`
Create a new project.

**Free plan restriction:** Returns `403` if the user already has 3 projects.

**Request body:**
```json
{
  "name": "Website Redesign",
  "description": "Full redesign of the corporate site",
  "hourly_rate": 90.00,
  "client_id": 1
}
```

#### `PUT /api/projects/{project_id}`
Update a project's details.

#### `DELETE /api/projects/{project_id}`
Delete a project and all its associated time logs.

---

### Time Logs — `/api/timelog`

#### `GET /api/timelog/`
List all time logs for the authenticated user.

#### `POST /api/timelog/`
Create a new time log entry.

**Request body:**
```json
{
  "project_id": 1,
  "start_time": "2026-03-27T09:00:00Z",
  "end_time": "2026-03-27T12:30:00Z",
  "description": "Implemented authentication module"
}
```

> `end_time` is optional — omit it to start an open-ended timer session. Hours are auto-calculated on save.

#### `GET /api/timelog/project/{project_id}`
List all time logs for a specific project.

#### `PUT /api/timelog/{log_id}`
Update an existing time log entry.

#### `DELETE /api/timelog/{log_id}`
Delete a time log entry.

---

### Invoices — `/api/invoices`

#### `GET /api/invoices/`
List all invoices for the authenticated user.

#### `POST /api/invoices/`
Create an invoice. Supports two modes:

**Mode 1 — Auto-compute from project time logs:**
```json
{
  "project_id": 1,
  "hourly_rate": 90.00,
  "due_date": "2026-04-27T00:00:00Z",
  "notes": "Payment due within 30 days."
}
```
All uninvoiced time logs for the project are summed automatically and marked as invoiced.

**Mode 2 — Manual entry:**
```json
{
  "total_hours": 20.5,
  "hourly_rate": 90.00,
  "client_id": 1,
  "due_date": "2026-04-27T00:00:00Z"
}
```

**Free plan restriction:** Returns `403` if the user has already created 10 invoices in the current calendar month.

**Response `200`:**
```json
{
  "id": 1,
  "invoice_number": "INV-1-0001",
  "client_name": "Acme Corp",
  "project_name": "Website Redesign",
  "total_hours": 20.5,
  "hourly_rate": 90.00,
  "total_amount": 1845.00,
  "status": "draft",
  "issue_date": "2026-03-27T10:00:00Z",
  "due_date": "2026-04-27T00:00:00Z"
}
```

#### `PUT /api/invoices/{invoice_id}/status`
Update invoice status.

**Request body:**
```json
{ "status": "paid" }
```

Valid values: `draft`, `sent`, `paid`. Setting `paid` automatically records `paid_date`.

#### `DELETE /api/invoices/{invoice_id}`
Delete an invoice.

#### `GET /api/invoices/{invoice_id}/pdf`
Stream the invoice as a downloadable PDF.

#### `POST /api/invoices/{invoice_id}/send`
Email the invoice PDF to the associated client. **Pro plan only** — returns `403` for free users.

#### `GET /api/invoices/earnings/summary`
Get a summary of total earnings.

**Response `200`:**
```json
{
  "total_invoiced": 12500.00,
  "total_paid": 9800.00,
  "total_pending": 2700.00,
  "invoice_count": 14
}
```

---

### Billing — `/api/billing`

#### `GET /api/billing/status`
Returns the current user's plan, whether billing is enabled, and whether a billing account exists.

#### `POST /api/billing/checkout`
Creates a Lemon Squeezy checkout session and returns a redirect URL to the payment page.

#### `GET /api/billing/portal`
Returns a URL to the Lemon Squeezy customer portal for managing or cancelling a subscription.

#### `POST /api/billing/webhook`
Receives and validates signed webhook events from Lemon Squeezy to update subscription status. This endpoint is not called by the frontend.

---

### Chat — `/api/chat`

#### `POST /api/chat/message`
Send a message to the AI assistant and receive a context-aware reply.

**Authentication:** Required (Bearer JWT)

**Request body:**
```json
{
  "messages": [
    { "role": "user", "content": "How much have I earned this month?" }
  ]
}
```

The `messages` array should contain the full conversation history (alternating `user` / `assistant` roles). The backend caps this at the last 20 messages automatically.

**Response `200`:**
```json
{
  "reply": "You've earned $1,845.00 this month across 2 invoices."
}
```

**Error responses:**
- `400` — No messages provided
- `503` — `OPENAI_API_KEY` not configured
- `502` — OpenAI API unreachable or returned an error

The assistant is injected with a personalised system prompt containing:
- The user's plan, hourly rate, and company name
- Total invoiced, paid, and outstanding earnings
- Total uninvoiced hours and their estimated value
- Active projects with hours and earnings per project
- The 5 most recent invoices

---

### Admin — `/api/admin`

> All admin endpoints require a user with `is_admin = true`. Non-admins receive `403`.

#### `GET /api/admin/users`
List all registered users with their plan, verification status, and metadata.

#### `PATCH /api/admin/users/{user_id}/verify`
Manually mark a user's email as verified.

#### `DELETE /api/admin/users/{user_id}`
Delete a user and all their associated data (cascade).

#### `DELETE /api/admin/users`
Batch delete all non-admin users. Intended for development/testing use only.

---

## 9. Security

### Authentication & Authorisation
- **JWT tokens** (HS256) are issued upon login with a **24-hour expiry**.
- The `SECRET_KEY` is required at startup — the application will **refuse to start** if the key is missing, empty, or set to a known insecure default.
- Keys shorter than 32 characters trigger a startup warning.
- Admin role is encoded as a claim in the JWT and **re-verified server-side** on every admin request.
- All resource endpoints filter by `user_id` — users cannot access other users' data.

### Password Security
- Passwords are hashed using **PBKDF2-SHA256** via Passlib — compliant with OWASP recommendations.
- Plain-text passwords are never stored or logged.

### Rate Limiting
All sensitive endpoints are rate-limited per IP using SlowAPI:

| Endpoint | Limit |
|----------|-------|
| `POST /api/auth/login` | 10 / minute |
| `POST /api/auth/register` | 5 / minute |
| `POST /api/auth/forgot-password` | 3 / minute |
| `POST /api/auth/resend-verification` | 3 / minute |

### CORS
- Allowed origins are configured via the `ALLOWED_ORIGINS` environment variable.
- The development default (`localhost:3000`) is explicitly not used in production.
- Only required HTTP methods and headers are permitted.

### Business Logic Enforcement
- Free-plan limits (projects, invoices, email sending) are enforced **exclusively on the backend**, not the frontend, preventing bypass via direct API calls.

### Email Verification
- New accounts must verify their email before logging in.
- Verification tokens are single-use, expire after 24 hours, and are generated using `secrets.token_urlsafe(32)` (cryptographically secure).

### Password Reset
- Reset tokens expire after 1 hour.
- Tokens are single-use and purged after successful reset.

### Webhook Signature Validation
- Lemon Squeezy webhook payloads are validated using **HMAC-SHA256** signature verification before any database changes are made.

---

## 10. Email & Notifications

The email service supports two delivery methods, with automatic fallback:

### Primary: Resend API
Configured via `RESEND_API_KEY` and `RESEND_FROM`. Recommended for all hosted deployments due to reliability and compatibility with Render's network.

### Fallback: SMTP
Configured via `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`. Supports both STARTTLS (port 587) and SSL (port 465). Tested with Gmail App Passwords.

### Transactional Emails Sent

| Event | Recipient | Content |
|-------|-----------|---------|
| Registration | New user | Email verification link (24h TTL) |
| Forgot password | User | Password reset link (1h TTL) |
| Invoice send | Client (Pro only) | Invoice PDF as attachment |

---

## 11. PDF Invoice Generation

Invoices are rendered to PDF server-side using **ReportLab**, a mature Python PDF library. Generation is on-demand — no files are persisted to disk.

### PDF Content
- Invoice title and number
- Freelancer company name and contact details
- Client name
- Issue date and due date
- Project name
- Hours, hourly rate, and total amount
- Optional notes

### Delivery Methods
- **Download:** `GET /api/invoices/{id}/pdf` streams the PDF as `application/pdf` with `Content-Disposition: attachment`.
- **Email:** `POST /api/invoices/{id}/send` generates the PDF and attaches it to an email sent to the client's address (Pro only).

---

## 12. AI Chatbot Assistant

### Overview

HourStack includes a built-in AI assistant powered by **OpenAI GPT-4o mini**. The assistant is context-aware — every conversation is prefixed with a live snapshot of the authenticated user's data so it can answer personalised questions without the user having to provide any context manually.

### How It Works

```
User types message
        ↓
Frontend sends POST /api/chat/message  { messages: [...history] }
        ↓
Backend queries DB → builds personalised system prompt
        ↓
OpenAI API called with system prompt + conversation history
        ↓
Reply streamed back to frontend and displayed in chat panel
```

### UI
- Floating **💬 button** fixed to the bottom-right corner on all authenticated pages.
- Opens a dark-themed chat panel with auto-scroll and a typing indicator.
- **Enter** sends a message; **Shift+Enter** inserts a newline.
- Chat history is maintained for the duration of the browser session.
- Only visible when the user is logged in.

### Context Injected Per Request

| Data | Source |
|------|--------|
| Username, company, hourly rate, plan | `users` table |
| Total invoiced / paid / pending | `invoices` table (all time) |
| Earned this month | `invoices` filtered by current month |
| Uninvoiced hours + estimated value | `timelogs` where `is_invoiced = 0` |
| Active projects (up to 10) | `projects` table |
| 5 most recent invoices | `invoices` sorted by `created_at` |

### Configuration

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | **Required.** Your OpenAI API key from platform.openai.com |
| `OPENAI_CHAT_MODEL` | Optional. Defaults to `gpt-4o-mini`. Can be set to `gpt-4o` for higher quality. |

### Cost Estimate

Using **GPT-4o mini** (the default):
- Each conversation turn costs roughly $0.0001–$0.0003 depending on context size.
- 1,000 conversations/month ≈ **$0.10–$0.30** — negligible cost at early scale.
- Set a **monthly spend cap** in your OpenAI dashboard under *Settings → Limits* as a safety measure.

### Graceful Degradation

If `OPENAI_API_KEY` is not set, the `/api/chat/message` endpoint returns a `503` with a clear message. The chat widget still appears in the UI but displays the error inline — the rest of the application is completely unaffected.

---

## 13. Deployment

### Docker (Self-Hosted)

A `docker-compose.yml` is included for running the full stack locally or on a VPS:

```bash
# Build and start the application
docker compose up --build

# Run database migrations
docker compose exec backend alembic upgrade head
```

This starts:
- **PostgreSQL 16** with health checks
- **FastAPI backend** on port 8002

### Render (Managed Cloud — Pre-Configured)

A `render.yaml` is included with a complete Infrastructure-as-Code configuration for one-click deployment to Render:

- PostgreSQL database provisioned automatically
- `SECRET_KEY` auto-generated by Render
- Single web service running the unified backend + React static build
- `alembic upgrade heads` run automatically at each deploy

**Deploy steps:**
1. Push the repository to GitHub.
2. Connect the repository to Render.
3. Fill in the environment variables in the Render dashboard (Lemon Squeezy keys, SMTP credentials).
4. Deploy.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | **Yes** | JWT signing key — minimum 32 random bytes |
| `DATABASE_URL` | **Yes** (prod) | PostgreSQL connection string |
| `ALLOWED_ORIGINS` | **Yes** (prod) | Comma-separated list of allowed frontend origins |
| `FRONTEND_URL` | **Yes** (prod) | Base URL of the deployed frontend |
| `RESEND_API_KEY` | Recommended | Resend email API key |
| `RESEND_FROM` | Optional | Sender address for Resend |
| `SMTP_HOST` | Optional | SMTP server hostname |
| `SMTP_PORT` | Optional | SMTP port (default: 587) |
| `SMTP_USERNAME` | Optional | SMTP username |
| `SMTP_PASSWORD` | Optional | SMTP app password |
| `LEMONSQUEEZY_API_KEY` | For billing | Lemon Squeezy API key |
| `LEMONSQUEEZY_STORE_ID` | For billing | Lemon Squeezy store ID |
| `LEMONSQUEEZY_VARIANT_ID` | For billing | Pro plan variant ID |
| `LEMONSQUEEZY_WEBHOOK_SECRET` | For billing | Webhook signing secret |
| `OPENAI_API_KEY` | For chatbot | OpenAI API key — get from platform.openai.com |
| `OPENAI_CHAT_MODEL` | Optional | LLM model (default: `gpt-4o-mini`) |
| `LOG_LEVEL` | Optional | Logging level (default: `INFO`) |

---

## 14. Development Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- npm

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Create environment file
copy .env.example .env       # Windows
cp .env.example .env         # macOS / Linux
# Edit .env and set SECRET_KEY to a random 32+ character string

# Run database migrations
alembic upgrade head

# Start the development server
python main.py
```

Backend is available at `http://localhost:8002`  
Swagger UI: `http://localhost:8002/docs`  
ReDoc: `http://localhost:8002/redoc`

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create environment file and configure the API URL
copy .env.example .env       # Windows
cp .env.example .env         # macOS / Linux

# Start the development server
npm start
```

Frontend is available at `http://localhost:3000`

### Running Tests

```bash
cd backend
pytest
```

The test suite uses an in-memory SQLite database and elevated rate limits (`TESTING=true`) to prevent test failures from rate limiting.

### Creating an Admin Account

```bash
cd backend
python make_admin.py <username>
```

---

## 15. Product Roadmap

### Near-Term (Pre-Launch Essentials)

| Item | Priority | Status |
|------|----------|--------|
| Configure Stripe / Lemon Squeezy end-to-end | Critical | Pending |
| Deploy to production server | Critical | Pending |
| Custom domain + HTTPS | Critical | Pending |
| Production database (PostgreSQL) | Critical | Pending |
| Production SMTP / Resend API key | Critical | Pending |

### Growth Features

| Feature | Description |
|---------|-------------|
| Stripe Payment Links | Embed a "Pay Now" link directly in invoice emails |
| 14-day Pro trial | Reduce conversion friction for new signups |
| Annual billing | $99/yr option (31% saving vs monthly) |
| PDF invoice branding | Allow Pro users to upload a logo for PDF invoices |
| Recurring invoice templates | Auto-generate invoices on a configurable schedule |
| Public invoice page | Shareable link for clients to view invoices without email |
| Expense tracking | Log project expenses for full P&L per project |
| Advanced analytics | Monthly revenue trends, top clients, avg hours per project |

### Platform Expansion

| Feature | Description |
|---------|-------------|
| Mobile app | React Native app or installable PWA |
| Team accounts | Agency tier supporting multiple freelancers under one account |
| Multiple currencies | Localised invoicing for international clients |
| Dark / light mode | UI preference toggle |
| Third-party integrations | Zapier, Google Calendar, Toggl import |

---

## Appendix — Project Structure

```
leg_proj3/
├── backend/
│   ├── main.py                     # Application entry point, middleware, router registration
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── alembic.ini
│   ├── make_admin.py               # CLI utility to promote a user to admin
│   ├── app/
│   │   ├── database.py             # SQLAlchemy engine and session factory
│   │   ├── limiter.py              # Rate limiter configuration
│   │   ├── models/                 # SQLAlchemy ORM table definitions
│   │   │   ├── user.py
│   │   │   ├── client.py
│   │   │   ├── project.py
│   │   │   ├── timelog.py
│   │   │   ├── invoice.py
│   │   │   ├── email_verification.py
│   │   │   └── password_reset.py
│   │   ├── schemas/                # Pydantic request/response models
│   │   │   ├── user.py
│   │   │   ├── client.py
│   │   │   ├── project.py
│   │   │   ├── timelog.py
│   │   │   └── invoice.py
│   │   ├── routes/                 # API endpoint handlers
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── clients.py
│   │   │   ├── projects.py
│   │   │   ├── timelog.py
│   │   │   ├── invoices.py
│   │   │   ├── billing.py
│   │   │   └── admin.py
│   │   └── services/               # Business logic layer
│   │       ├── invoice_service.py  # Invoice numbering, calculation, PDF generation
│   │       └── email_service.py    # Resend + SMTP email delivery
│   ├── migrations/                 # Alembic migration versions
│   └── tests/
│       ├── conftest.py
│       └── test_api_flows.py
│
└── frontend/
    ├── package.json
    ├── public/
    │   └── index.html
    └── src/
        ├── App.jsx
        ├── components/
        │   ├── HourStackLogo.jsx
        │   ├── Navbar.jsx
        │   └── Toast.jsx
        ├── pages/
        │   ├── LandingPage.jsx
        │   ├── LoginPage.jsx
        │   ├── RegisterPage.jsx
        │   ├── DashboardPage.jsx
        │   ├── ProjectPage.jsx
        │   ├── ClientsPage.jsx
        │   ├── InvoicePage.jsx
        │   ├── BillingPage.jsx
        │   ├── AdminPage.jsx
        │   ├── ForgotPasswordPage.jsx
        │   ├── ResetPasswordPage.jsx
        │   └── ResendVerificationPage.jsx
        ├── store/                  # Zustand state stores
        └── utils/                  # Axios API client and helpers
```

---

*This document covers the complete HourStack platform as of version 1.0.0. For questions, technical due diligence, or partnership enquiries, refer to the interactive API documentation at `/docs` or contact the development team.*
