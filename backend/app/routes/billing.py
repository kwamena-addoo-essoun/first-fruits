"""
Stripe billing routes — Checkout, Customer Portal, and webhook handler.

Environment variables required:
  STRIPE_SECRET_KEY      — your Stripe secret key (sk_test_… / sk_live_…)
  STRIPE_WEBHOOK_SECRET  — webhook signing secret from Stripe dashboard
  STRIPE_PRO_PRICE_ID    — the Price ID for the Pro subscription plan
  FRONTEND_URL           — base URL of the React app (default: http://localhost:3000)
"""

import json
import logging
import os

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.routes.users import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

stripe.api_key = STRIPE_SECRET_KEY


def _billing_enabled() -> bool:
    return bool(STRIPE_SECRET_KEY and STRIPE_PRO_PRICE_ID)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/billing/status  — current subscription state
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
# POST /api/billing/checkout  — create Stripe Checkout session
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/checkout")
async def create_checkout_session(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session and return the redirect URL."""
    if not _billing_enabled():
        raise HTTPException(status_code=503, detail="Billing not configured")

    if user.plan == "pro":
        raise HTTPException(status_code=400, detail="Already on Pro plan")

    # Create or reuse the Stripe customer record
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={"user_id": str(user.id), "username": user.username},
        )
        user.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{"price": STRIPE_PRO_PRICE_ID, "quantity": 1}],
        mode="subscription",
        success_url=f"{FRONTEND_URL}/billing?success=1",
        cancel_url=f"{FRONTEND_URL}/billing?canceled=1",
        metadata={"user_id": str(user.id)},
    )

    logger.info("Checkout session created for user %s", user.id)
    return {"url": session.url}


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/billing/portal  — create Stripe Customer Portal session
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/portal")
async def create_portal_session(user: User = Depends(get_current_user)):
    """Create a Stripe Customer Portal session for managing the subscription."""
    if not _billing_enabled():
        raise HTTPException(status_code=503, detail="Billing not configured")

    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found. Subscribe first.")

    portal = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{FRONTEND_URL}/billing",
    )

    return {"url": portal.url}


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/billing/webhook  — Stripe webhook (no auth, verified by signature)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe lifecycle events to keep the user's plan in sync."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError:
            logger.warning("Webhook signature verification failed")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
    else:
        # Dev mode — accept unsigned events (never do this in production!)
        logger.warning("STRIPE_WEBHOOK_SECRET not set — accepting unsigned webhook. NOT safe for production.")
        event = json.loads(payload)

    event_type: str = event["type"]
    data = event["data"]["object"]
    logger.info("Stripe webhook: %s", event_type)

    # Subscription activated or updated
    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        _sync_subscription(db, data)

    # Subscription cancelled / expired
    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.plan = "free"
            user.stripe_subscription_id = None
            db.commit()
            logger.info("Downgraded user %s to free (subscription deleted)", user.id)

    return {"received": True}


def _sync_subscription(db: Session, subscription: dict) -> None:
    """Update a user's plan based on a Stripe subscription object."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")  # active, trialing, past_due, canceled, etc.
    sub_id = subscription.get("id")

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.warning("Received subscription event for unknown customer %s", customer_id)
        return

    is_active = status in ("active", "trialing")
    user.plan = "pro" if is_active else "free"
    user.stripe_subscription_id = sub_id if is_active else None
    db.commit()
    logger.info("User %s plan set to %s (subscription status: %s)", user.id, user.plan, status)
