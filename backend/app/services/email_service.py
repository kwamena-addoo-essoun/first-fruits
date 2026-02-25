import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "") or SMTP_USERNAME
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8002")


_PLACEHOLDER_VALUES = {"", "your-app-password", "you@gmail.com"}

def _smtp_configured() -> bool:
    """Return True only when all required SMTP credentials look real."""
    return (
        bool(SMTP_HOST)
        and SMTP_USERNAME not in _PLACEHOLDER_VALUES
        and SMTP_PASSWORD not in _PLACEHOLDER_VALUES
    )


def send_password_reset_email(to_email: str, token: str) -> None:
    """Send a password reset email.

    If SMTP is not fully configured, the reset URL is logged at WARNING level so
    developers can use it directly without setting up a mail server.
    """
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"

    if not _smtp_configured():
        logger.warning(
            "SMTP not configured — password reset URL for %s: %s",
            to_email,
            reset_url,
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your password — Freelancer Time Tracker"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    text = (
        f"Click the link below to reset your password:\n{reset_url}\n\n"
        "This link expires in 1 hour. If you didn't request this, ignore this email."
    )
    html = f"""
    <p>Hi,</p>
    <p>Click the button below to reset your password.
       This link expires in <strong>1 hour</strong>.</p>
    <p>
      <a href="{reset_url}"
         style="background:#e67e22;color:white;padding:10px 20px;
                border-radius:4px;text-decoration:none;font-weight:600;">
        Reset Password
      </a>
    </p>
    <p style="color:#999;font-size:0.85rem;">
      If you didn't request a password reset, you can safely ignore this email.
    </p>
    """
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USERNAME:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, to_email, msg.as_string())

    logger.info("Password reset email sent to %s", to_email)


def send_verification_email(to_email: str, token: str) -> None:
    """Send an email verification link.

    If SMTP is not configured, the verification URL is logged so developers
    can verify accounts directly without a mail server.
    """
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"

    if not _smtp_configured():
        logger.warning(
            "SMTP not configured — email verification URL for %s: %s",
            to_email,
            verify_url,
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your email — Freelancer Time Tracker"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    text = (
        f"Click the link below to verify your email address:\n{verify_url}\n\n"
        "This link expires in 24 hours. If you didn't create an account, ignore this email."
    )
    html = f"""
    <p>Hi,</p>
    <p>Thanks for registering! Click the button below to verify your email address.
       This link expires in <strong>24 hours</strong>.</p>
    <p>
      <a href="{verify_url}"
         style="background:#27ae60;color:white;padding:10px 20px;
                border-radius:4px;text-decoration:none;font-weight:600;">
        Verify Email
      </a>
    </p>
    <p style="color:#999;font-size:0.85rem;">
      If you didn't create an account, you can safely ignore this email.
    </p>
    """
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USERNAME:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, to_email, msg.as_string())

    logger.info("Verification email sent to %s", to_email)
