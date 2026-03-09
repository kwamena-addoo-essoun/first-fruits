from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import logging
from app.database import get_db
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.models.email_verification import EmailVerificationToken
from app.schemas.user import (
    UserCreate, UserResponse, UserLogin,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from app.limiter import limiter, LOGIN_RATE_LIMIT, REGISTER_RATE_LIMIT, FORGOT_PASSWORD_RATE_LIMIT, RESEND_VERIFICATION_RATE_LIMIT
from app.services.email_service import send_password_reset_email, send_verification_email
from passlib.context import CryptContext
from datetime import UTC, datetime, timedelta
from jose import JWTError, jwt
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
router = APIRouter()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_access_token(user_id: int, is_admin: bool = False) -> str:
    expire = datetime.now(UTC) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": str(user_id), "is_admin": is_admin, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


@router.post("/register", response_model=UserResponse)
@limiter.limit(REGISTER_RATE_LIMIT)
async def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    """Register a new freelancer"""
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password),
        hourly_rate=user.hourly_rate,
        company_name=user.company_name,
        is_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send email verification
    token = secrets.token_urlsafe(32)
    expires = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=24)
    db.add(EmailVerificationToken(user_id=new_user.id, token=token, expires_at=expires))
    db.commit()
    try:
        send_verification_email(new_user.email, token)
    except Exception as exc:
        logger.warning("Failed to send verification email to %s: %s", new_user.email, exc)

    return new_user


@router.post("/login")
@limiter.limit(LOGIN_RATE_LIMIT)
async def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    """Login — rate-limited to prevent brute-force attacks"""
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="EMAIL_NOT_VERIFIED")

    return {"access_token": _create_access_token(user.id, is_admin=user.is_admin), "token_type": "bearer"}


@router.post("/refresh")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    """Exchange a still-valid access token for a fresh 24 h one."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {"access_token": _create_access_token(user.id, is_admin=user.is_admin), "token_type": "bearer"}


@router.post("/forgot-password")
@limiter.limit(FORGOT_PASSWORD_RATE_LIMIT)
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """Request a password reset link.

    Always returns 200 regardless of whether the email exists to prevent
    user-enumeration attacks.
    """
    user = db.query(User).filter(User.email == body.email).first()
    if user:
        # Invalidate any outstanding unused tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,  # noqa: E712
        ).update({"used": True})

        token = secrets.token_urlsafe(32)
        expires = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1)
        db.add(PasswordResetToken(user_id=user.id, token=token, expires_at=expires))
        db.commit()

        try:
            send_password_reset_email(user.email, token)
        except Exception as exc:
            logger.warning("Failed to send password reset email to %s: %s", user.email, exc)

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Apply a password reset using the one-time token from the email link."""
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == body.token,
        PasswordResetToken.used == False,  # noqa: E712
    ).first()

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if datetime.now(UTC).replace(tzinfo=None) > reset_token.expires_at:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    user.hashed_password = hash_password(body.password)
    reset_token.used = True
    db.commit()

    return {"message": "Password reset successful"}


@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify a user's email address using the one-time token from the link."""
    record = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token == token,
        EmailVerificationToken.used == False,  # noqa: E712
    ).first()

    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    if datetime.now(UTC).replace(tzinfo=None) > record.expires_at:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    user = db.query(User).filter(User.id == record.user_id).first()
    user.is_verified = True
    record.used = True
    db.commit()

    return {"message": "Email verified successfully. You can now log in."}


@router.post("/resend-verification")
@limiter.limit(RESEND_VERIFICATION_RATE_LIMIT)
async def resend_verification(
    request: Request,
    body: ForgotPasswordRequest,  # reuse {email} schema
    db: Session = Depends(get_db),
):
    """Resend an email verification link.

    Always returns 200 to prevent user enumeration.
    """
    user = db.query(User).filter(User.email == body.email).first()
    if user and not user.is_verified:
        # Invalidate existing unused tokens
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used == False,  # noqa: E712
        ).update({"used": True})

        token = secrets.token_urlsafe(32)
        expires = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=24)
        db.add(EmailVerificationToken(user_id=user.id, token=token, expires_at=expires))
        db.commit()
        try:
            send_verification_email(user.email, token)
        except Exception as exc:
            logger.warning("Failed to resend verification email to %s: %s", user.email, exc)

    return {"message": "If that email is registered and unverified, a new link has been sent."}
