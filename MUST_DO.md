# MUST DO — HourStack

Things that must be finished before this is a real, money-making product.

---

## 🔴 Critical (do first)

### 1. Enforce Free Plan Limits on the Backend ✅

- [x] Max **3 active projects** for free users → `403` on `POST /api/projects/` if limit reached
- [x] Max **10 invoices per month** for free users → `403` on `POST /api/invoices/` if limit reached
- [x] Gate **"Email invoice to client"** (`POST /api/invoices/{id}/send`) behind Pro plan only
- [x] Return plan info in relevant API responses so the frontend can show upgrade prompts

### 2. Configure & Test Stripe End-to-End
The plumbing is in place but the keys are empty.

- [ ] Create a Stripe account (if not done) at https://stripe.com
- [ ] Create a **Product** ("HourStack Pro") and a **recurring Price** ($12/mo) in the Stripe Dashboard
- [ ] Add to `backend/.env`:
  ```
  STRIPE_SECRET_KEY=sk_test_...
  STRIPE_PRO_PRICE_ID=price_...
  STRIPE_WEBHOOK_SECRET=whsec_...
  ```
- [ ] Test the full checkout flow locally using the **Stripe CLI**:
  ```
  stripe listen --forward-to localhost:8002/api/billing/webhook
  ```
- [ ] Confirm subscription activates and `users.plan` is set to `"pro"` in the DB
- [ ] Test cancellation via Stripe Customer Portal and confirm plan reverts to `"free"`

### 3. Wire Up Upgrade Prompts in the Frontend ✅
- [x] Show a banner/modal when a free user hits a plan limit (ProjectPage)
- [x] "Email invoice" button shows a 🔒 Pro button → redirects to `/billing` for free users

---

## 🟡 Before Going Live

### 4. Deploy to a Real Server
- [ ] Choose a host: **Railway**, **Render**, or a VPS (DigitalOcean / Hetzner)
- [ ] Set all production env vars (SECRET_KEY, DATABASE_URL, SMTP_*, STRIPE_*, FRONTEND_URL, ALLOWED_ORIGINS)
- [ ] Switch `DATABASE_URL` to **PostgreSQL** (SQLite is not suitable for production)
- [ ] Run `alembic upgrade heads` on the production database
- [ ] Build the React app: `npm run build` (output goes to `frontend/build/`, already served by FastAPI)

### 5. Real Domain Name
- [ ] Buy a domain (e.g., `hourstack.io`) — ~$10/yr on Namecheap / Cloudflare
- [ ] Point DNS to your server
- [ ] Set up **HTTPS** (Let's Encrypt / Cloudflare Proxy)
- [ ] Update `FRONTEND_URL` and `ALLOWED_ORIGINS` in production `.env`
- [ ] Update Stripe Dashboard with the production webhook URL and live keys

### 6. Production SMTP
- [ ] Current config uses a Gmail App Password — fine for small scale
- [ ] For higher volume, switch to **Resend**, **SendGrid**, or **Postmark** (free tiers available)
- [ ] Test: registration email, password reset email, invoice email all arrive correctly

---

## 🟢 Nice to Have (do when live)

- [ ] **Stripe free trial** — offer 14-day Pro trial on signup to improve conversion
- [ ] **Referral / affiliate system** — let users share a link and get a month free
- [ ] **Annual pricing** — $99/yr (save 31%) alongside monthly
- [ ] **PDF invoice branding** — let Pro users upload a logo to appear on invoices
- [ ] **Recurring invoice templates** — auto-generate invoices on a schedule
- [ ] **Expense tracking** — log expenses against projects for full P&L view
- [ ] **Public invoice page** — shareable link for clients to view/pay without email
- [ ] **Stripe Payment Links on invoices** — let clients pay directly from the invoice email
- [ ] **Dark / light mode toggle**
- [ ] **Mobile app** (React Native) — or make the PWA installable
- [ ] **Analytics dashboard** — monthly revenue trend, top clients, avg hours/project
- [ ] **Team accounts** — agency tier with multiple freelancers under one account

---

## 🧹 Tech Debt

- [ ] Write tests for the new billing endpoints (`tests/test_api_flows.py`)
- [ ] Add E2E test for the Stripe webhook handler
- [ ] Add rate limiting to `/api/billing/checkout` and `/api/billing/portal`
- [ ] Review and tighten CORS for production
- [ ] Set up error monitoring (Sentry free tier)
- [ ] Set up uptime monitoring (Better Uptime / UptimeRobot — free)

---

_Last updated: 2 March 2026_
