from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.invoice import Invoice
from app.models.timelog import TimeLog
from app.models.project import Project
from app.models.client import Client
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.routes.users import get_current_user
from app.services.invoice_service import InvoiceService, InvoicePDFGenerator
from app.services.email_service import send_invoice_email
from typing import List
from datetime import UTC, datetime

router = APIRouter()


@router.post("/", response_model=InvoiceResponse)
async def create_invoice(
    invoice: InvoiceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate invoice, optionally auto-computing hours from a project's uninvoiced timelogs."""
    total_hours = invoice.total_hours
    hourly_rate = invoice.hourly_rate
    client_name = None
    project_name = None
    resolved_client_id = invoice.client_id

    # ── Project-based auto-computation ──────────────────────────────────────
    if invoice.project_id is not None:
        project = db.query(Project).filter(
            Project.id == invoice.project_id, Project.user_id == user.id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        uninvoiced_logs = (
            db.query(TimeLog)
            .filter(TimeLog.project_id == project.id, TimeLog.is_invoiced == 0)
            .all()
        )
        if not uninvoiced_logs:
            raise HTTPException(
                status_code=400,
                detail="No uninvoiced time logs found for this project",
            )

        total_hours = round(sum(log.hours for log in uninvoiced_logs), 4)
        hourly_rate = invoice.hourly_rate or project.hourly_rate
        project_name = project.name

        if project.client_id:
            resolved_client_id = project.client_id
            client = db.query(Client).filter(Client.id == project.client_id).first()
            if client:
                client_name = client.name

    # ── Client name snapshot (manual invoice with explicit client_id) ────────
    if client_name is None and invoice.client_id is not None:
        client = db.query(Client).filter(
            Client.id == invoice.client_id, Client.user_id == user.id
        ).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        client_name = client.name

    total_amount = InvoiceService.calculate_invoice_total(total_hours, hourly_rate)
    invoice_count = db.query(Invoice).filter(Invoice.user_id == user.id).count()
    invoice_number = InvoiceService.generate_invoice_number(user.id, invoice_count)

    db_invoice = Invoice(
        user_id=user.id,
        client_id=resolved_client_id,
        project_id=invoice.project_id,
        invoice_number=invoice_number,
        client_name=client_name,
        project_name=project_name,
        notes=invoice.notes,
        total_hours=total_hours,
        hourly_rate=hourly_rate,
        total_amount=total_amount,
        due_date=invoice.due_date,
    )
    db.add(db_invoice)

    if invoice.project_id is not None:
        for log in uninvoiced_logs:
            log.is_invoiced = 1

    db.commit()
    db.refresh(db_invoice)
    return db_invoice


@router.get("/earnings/summary")
async def get_earnings_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get earnings summary"""
    invoices = db.query(Invoice).filter(Invoice.user_id == user.id).all()
    total_invoiced = sum(inv.total_amount for inv in invoices)
    paid = sum(inv.total_amount for inv in invoices if inv.status == "paid")
    pending = total_invoiced - paid
    return {
        "total_invoiced": round(total_invoiced, 2),
        "paid": round(paid, 2),
        "pending": round(pending, 2),
        "invoice_count": len(invoices),
    }


@router.get("/", response_model=List[InvoiceResponse])
async def get_invoices(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all invoices"""
    invoices = db.query(Invoice).filter(Invoice.user_id == user.id).all()
    return invoices


@router.put("/{invoice_id}/status")
async def update_invoice_status(
    invoice_id: int,
    status: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update invoice status"""
    allowed_statuses = {"draft", "sent", "paid"}
    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400, detail=f"status must be one of: {', '.join(sorted(allowed_statuses))}"
        )
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.user_id == user.id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.status = status
    if status == "paid":
        invoice.paid_date = datetime.now(UTC)

    db.add(invoice)
    db.commit()
    return {"message": f"Invoice status updated to {status}"}


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.user_id == user.id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted"}


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download invoice as a PDF file"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.user_id == user.id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        pdf_bytes = InvoicePDFGenerator.generate(invoice, user)
    except RuntimeError as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(e))  # pragma: no cover

    filename = f"{invoice.invoice_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{invoice_id}/send")
async def send_invoice_to_client(
    invoice_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Email the invoice PDF directly to the client."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.user_id == user.id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Resolve the client email
    client_email: str | None = None
    if invoice.client_id:
        client = db.query(Client).filter(Client.id == invoice.client_id).first()
        if client:
            client_email = client.email

    if not client_email:
        raise HTTPException(
            status_code=400,
            detail="No client email on file. Attach a client with an email address to this invoice first.",
        )

    try:
        send_invoice_email(invoice, user, client_email)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {exc}")

    # Auto-advance status to 'sent' if still a draft
    if invoice.status == "draft":
        invoice.status = "sent"
        db.commit()

    return {"message": f"Invoice {invoice.invoice_number} sent to {client_email}"}
