from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.invoice import Invoice
from app.models.timelog import TimeLog
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.routes.users import get_current_user
from app.services.invoice_service import InvoiceService
from typing import List
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=InvoiceResponse)
async def create_invoice(invoice: InvoiceCreate, token: str, db: Session = Depends(get_db)):
    """Generate invoice"""
    user = get_current_user(token, db)
    
    total_amount = InvoiceService.calculate_invoice_total(invoice.total_hours, invoice.hourly_rate)
    invoice_count = db.query(Invoice).filter(Invoice.user_id == user.id).count()
    invoice_number = InvoiceService.generate_invoice_number(user.id, invoice_count)
    
    db_invoice = Invoice(
        user_id=user.id,
        invoice_number=invoice_number,
        total_hours=invoice.total_hours,
        hourly_rate=invoice.hourly_rate,
        total_amount=total_amount,
        due_date=invoice.due_date
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

@router.get("/", response_model=List[InvoiceResponse])
async def get_invoices(token: str, db: Session = Depends(get_db)):
    """Get all invoices"""
    user = get_current_user(token, db)
    invoices = db.query(Invoice).filter(Invoice.user_id == user.id).all()
    return invoices

@router.put("/{invoice_id}/status")
async def update_invoice_status(invoice_id: int, status: str, token: str, db: Session = Depends(get_db)):
    """Update invoice status"""
    user = get_current_user(token, db)
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.user_id == user.id).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.status = status
    if status == "paid":
        invoice.paid_date = datetime.utcnow()
    
    db.add(invoice)
    db.commit()
    return {"message": f"Invoice status updated to {status}"}

@router.get("/earnings/summary")
async def get_earnings_summary(token: str, db: Session = Depends(get_db)):
    """Get earnings summary"""
    user = get_current_user(token, db)
    invoices = db.query(Invoice).filter(Invoice.user_id == user.id).all()
    
    total_invoiced = sum(inv.total_amount for inv in invoices)
    paid = sum(inv.total_amount for inv in invoices if inv.status == "paid")
    pending = total_invoiced - paid
    
    return {
        "total_invoiced": total_invoiced,
        "paid": paid,
        "pending": pending,
        "invoice_count": len(invoices)
    }
