import os
import smtplib
import logging
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Resend (preferred — works on Render free tier)
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM = os.getenv("RESEND_FROM", "HourStack <onboarding@resend.dev>")

# SMTP fallback
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "") or SMTP_USERNAME
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8002")

_PLACEHOLDER_VALUES = {"", "your-app-password", "you@gmail.com"}


def _resend_configured() -> bool:
    return bool(RESEND_API_KEY) and RESEND_API_KEY not in _PLACEHOLDER_VALUES


def _smtp_configured() -> bool:
    return (
        bool(SMTP_HOST)
        and SMTP_USERNAME not in _PLACEHOLDER_VALUES
        and SMTP_PASSWORD not in _PLACEHOLDER_VALUES
    )


def _send_via_resend(to_email: str, subject: str, html: str) -> None:
    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json={"from": RESEND_FROM, "to": [to_email], "subject": subject, "html": html},
        timeout=10,
    )
    if response.is_error:
        detail = response.text.strip()
        raise RuntimeError(f"Resend API error {response.status_code}: {detail}")


def _send_via_smtp(to_email: str, subject: str, html: str, text: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    # Port 465 uses implicit SSL; everything else uses STARTTLS
    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())


def send_password_reset_email(to_email: str, token: str) -> None:
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    subject = "Reset your password — HourStack"
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
    text = f"Click the link to reset your password:\n{reset_url}\n\nExpires in 1 hour."

    if _smtp_configured():
        _send_via_smtp(to_email, subject, html, text)
        logger.info("Password reset email sent via SMTP to %s", to_email)
    elif _resend_configured():
        _send_via_resend(to_email, subject, html)
        logger.info("Password reset email sent via Resend to %s", to_email)
    else:
        logger.warning("Email not configured — password reset URL for %s: %s", to_email, reset_url)


def send_verification_email(to_email: str, token: str) -> None:
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
    subject = "Verify your email — HourStack"
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
    text = f"Click the link to verify your email:\n{verify_url}\n\nExpires in 24 hours."

    if _smtp_configured():
        _send_via_smtp(to_email, subject, html, text)
        logger.info("Verification email sent via SMTP to %s", to_email)
    elif _resend_configured():
        _send_via_resend(to_email, subject, html)
        logger.info("Verification email sent via Resend to %s", to_email)
    else:
        logger.warning("Email not configured — verification URL for %s: %s", to_email, verify_url)


def send_invoice_email(invoice, user, client_email: str) -> None:
    from app.services.invoice_service import InvoicePDFGenerator
    from email.mime.base import MIMEBase
    from email import encoders
    import base64

    sender_name = user.company_name or user.username
    subject = f"Invoice {invoice.invoice_number} from {sender_name}"
    due = invoice.due_date.strftime("%B %d, %Y")
    notes_html = f"<p><em>{invoice.notes}</em></p>" if invoice.notes else ""
    html = f"""
    <p>Hi,</p>
    <p>Please find attached invoice <strong>{invoice.invoice_number}</strong>
       for <strong>${invoice.total_amount:,.2f}</strong>.</p>
    <p>Due date: <strong>{due}</strong></p>
    {notes_html}
    <p>Thank you for your business!</p>
    <p style="color:#666;">— {sender_name}</p>
    """

    if _resend_configured():
        try:
            pdf_bytes = InvoicePDFGenerator.generate(invoice, user)
            attachment_b64 = base64.b64encode(pdf_bytes).decode()
            response = httpx.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                json={
                    "from": RESEND_FROM,
                    "to": [client_email],
                    "subject": subject,
                    "html": html,
                    "attachments": [{"filename": f"{invoice.invoice_number}.pdf", "content": attachment_b64}],
                },
                timeout=15,
            )
            response.raise_for_status()
            logger.info("Invoice %s emailed via Resend to %s", invoice.invoice_number, client_email)
        except Exception as exc:
            logger.warning("Resend invoice email failed: %s", exc)
    elif _smtp_configured():
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = client_email
        msg.attach(MIMEText(html, "html"))
        try:
            pdf_bytes = InvoicePDFGenerator.generate(invoice, user)
            attachment = MIMEBase("application", "pdf")
            attachment.set_payload(pdf_bytes)
            encoders.encode_base64(attachment)
            attachment.add_header("Content-Disposition", f'attachment; filename="{invoice.invoice_number}.pdf"')
            msg.attach(attachment)
        except Exception as exc:
            logger.warning("PDF generation failed: %s", exc)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, client_email, msg.as_string())
        logger.info("Invoice %s emailed via SMTP to %s", invoice.invoice_number, client_email)
    else:
        logger.warning("Email not configured — would send invoice %s to %s", invoice.invoice_number, client_email)
