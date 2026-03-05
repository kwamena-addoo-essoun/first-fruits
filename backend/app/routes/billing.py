"""
Lemon Squeezy billing routes — Checkout, Customer Portal redirect, and webhook handler.

Environment variables required:
  LEMONSQUEEZY_API_KEY      — your Lemon Squeezy API key
  LEMONSQUEEZY_STORE_ID     — your store ID (number in dashboard URL)
  LEMONSQUEEZY_VARIANT_ID   — the Variant ID for the Pro plan price
  LEMONSQUEEZY_WEBHOOK_SECRET — webhook signing secret from LS dashboard
  FRONTEND_URL              — base URL of the React app (default: http://localhost:3000)
"""

import hashlib
import hmac
import json
import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.routes.users import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

LS_API_KEY = os.getenv("LEMONSQUEEZY_API_KEY", "")
LS_STORE_ID = os.getenv("LEMONSQUEEZY_STORE_ID", "")
LS_VARIANT_ID = os.getenv("LEMONSQUEEZY_VARIANT_ID", "")
LS_WEBHOOK_SECRET = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

_LS_BASE = "https://api.lemonsqueezy.com/v1"
_LS_HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/vnd.api+json",
}


def _billing_enabled() -> bool:
    return bool(LS_API_KEY and LS_STORE_ID and LS_VARIANT_ID)


def _auth_headers() -> dict:
    return {**_LS_HEADERS, "Authorization": f"Bearer {LS_API_KEY}"}


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/billing/status
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/status")
async def get_billing_status(user: User = Depends(get_current_user)):
    """Return the current user's plan and billing info."""
    return {
        "plan": user.plan or "free",
        "billing_enabled": _billing_enabled(),
        "has_billing_account": bool(user.stripe_customer_id),
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/billing/checkout  — create Lemon Squeezy checkout
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/checkout")
async def create_checkout_session(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Lemon Squeezy checkout and return the redirect URL."""
    if not _billing_enabled():
        raise HTTPException(status_code=503, detail="Billing not configured")

    if user.plan == "pro":
        raise HTTPException(status_code=400, detail="Already on Pro plan")

    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user.email,
                    "custom": {"user_id": str(user.id)},
                },
                "product_options": {
                    "redirect_url": f"{FRONTEND_URL}/billing?success=1",
                },
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": str(LS_STORE_ID)}},
                "variant": {"data": {"type": "variants", "id": str(LS_VARIANT_ID)}},
            },
        }
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{_LS_BASE}/checkouts",
            json=payload,
            headers=_auth_headers(),
            timeout=15.0,
        )

    if res.status_code >= 400:
        logger.error("LS checkout error %d: %s", res.status_code, res.text)
        raise HTTPException(status_code=502, detail="Failed to create checkout")

    checkout_url = res.json()["data"]["attributes"]["url"]
    logger.info("LS checkout created for user %s", user.id)
    return {"url": checkout_url}


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/billing/portal  — redirect to Lemon Squeezy customer portal
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/portal")
async def create_portal_session(user: User = Depends(get_current_user)):
    """Return the Lemon Squeezy customer portal URL for managing the subscription."""
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found. Subscribe first.")

    # Lemon Squeezy customers manage their subscriptions at this URL
    return {"url": "https://app.lemonsqueezy.com/my-orders"}


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/billing/webhook  — Lemon Squeezy webhook (verified by HMAC-SHA256)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/webhook")
async def ls_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Lemon Squeezy subscription events to keep the user's plan in sync."""
    payload = await request.body()
    sig_header = request.headers.get("x-signature", "")

    if LS_WEBHOOK_SECRET:
        computed = hmac.new(
            LS_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(computed, sig_header):
            logger.warning("LS webhook signature verification failed")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
    else:
        logger.warning("LEMONSQUEEZY_WEBHOOK_SECRET not set — skipping signature check.")

    event = json.loads(payload)
    event_name: str = event.get("meta", {}).get("event_name", "")
    data = event.get("data", {})
    attrs = data.get("attributes", {})
    custom_data = event.get("meta", {}).get("custom_data", {})

    logger.info("LS webhook: %s", event_name)

    if event_name in ("subscription_created", "subscription_updated"):
        _sync_subscription(db, data, attrs, custom_data)

    elif event_name in ("subscription_cancelled", "subscription_expired"):
        sub_id = str(data.get("id", ""))
        user = db.query(User).filter(User.stripe_subscription_id == sub_id).first()
        if user:
            user.plan = "free"
            user.stripe_subscription_id = None
            db.commit()
            logger.info("Downgraded user %s to free (LS event: %s)", user.id, event_name)

    return {"received": True}


def _sync_subscription(db: Session, data: dict, attrs: dict, custom_data: dict) -> None:
    """Update a user's plan based on a Lemon Squeezy subscription event."""
    sub_id = str(data.get("id", ""))
    status = attrs.get("status", "")  # active, on_trial, on_grace_period, paused, expired, cancelled
    ls_customer_id = str(attrs.get("customer_id", ""))
    user_id = custom_data.get("user_id")

    # Find user by custom_data first (most reliable), fall back to customer_id
    user = None
    if user_id:
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
        except (ValueError, TypeError):
            pass
    if not user and ls_customer_id:
        user = db.query(User).filter(User.stripe_customer_id == ls_customer_id).first()

    if not user:
        logger.warning("LS event for unknown user (user_id=%s, customer_id=%s)", user_id, ls_customer_id)
        return

    is_active = status in ("active", "on_trial", "on_grace_period")
    user.plan = "pro" if is_active else "free"
    user.stripe_customer_id = ls_customer_id
    user.stripe_subscription_id = sub_id if is_active else None
    db.commit()
    logger.info("User %s plan set to %s (LS status: %s)", user.id, user.plan, status)
