from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.email_verification import EmailVerificationToken
from app.models.password_reset import PasswordResetToken
from app.routes.users import get_current_user
from app.services.email_service import send_password_reset_email, FRONTEND_URL
from datetime import UTC, datetime, timedelta
import secrets
import os

router = APIRouter()

BOOTSTRAP_SECRET = os.getenv("BOOTSTRAP_SECRET", "")


@router.post("/bootstrap-admin")
def bootstrap_admin(
    email: str,
    secret: str,
    db: Session = Depends(get_db),
):
    """One-time endpoint to promote a user to admin using a shared secret.
    Set BOOTSTRAP_SECRET env var in Render, call once, then remove it."""
    if not BOOTSTRAP_SECRET or secret != BOOTSTRAP_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = True
    user.is_verified = True
    db.commit()
    return {"message": f"{user.username} is now admin and verified"}


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency — 403 for non-admins."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/users")
def list_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List all registered users."""
    users = db.query(User).order_by(User.created_at).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "company_name": u.company_name,
            "hourly_rate": u.hourly_rate,
            "is_admin": u.is_admin,
            "is_verified": u.is_verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Delete a user and all their data."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Manually remove token rows (no ORM cascade configured there)
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete()
    db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"message": f"User {user.username} deleted"}


@router.patch("/users/{user_id}/verify")
def verify_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Manually mark a user's email as verified."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    db.commit()
    return {"username": user.username, "is_verified": True}


@router.delete("/users")
def delete_all_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Delete all non-admin users and their related token rows."""
    users_to_delete = db.query(User).filter(User.is_admin == False, User.id != admin.id).all()  # noqa: E712
    deleted_count = 0

    for user in users_to_delete:
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete()
        db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).delete()
        db.delete(user)
        deleted_count += 1

    db.commit()
    return {"message": f"Deleted {deleted_count} users", "deleted_count": deleted_count}


@router.post("/users/{user_id}/toggle-admin")
def toggle_admin(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Promote or demote a user's admin status."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own admin status")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = not user.is_admin
    db.commit()
    return {"username": user.username, "is_admin": user.is_admin}


@router.post("/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Force a password reset for a user; always returns the reset URL."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Invalidate any existing unused tokens
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,  # noqa: E712
    ).update({"used": True})

    token = secrets.token_urlsafe(32)
    expires = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=24)
    db.add(PasswordResetToken(user_id=user.id, token=token, expires_at=expires))
    db.commit()

    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"

    email_sent = False
    try:
        send_password_reset_email(user.email, token)
        email_sent = True
    except Exception:
        pass

    return {
        "message": f"Password reset token generated for {user.username}",
        "reset_url": reset_url,
        "email_sent": email_sent,
    }
