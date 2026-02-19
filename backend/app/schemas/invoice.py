from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InvoiceBase(BaseModel):
    total_hours: float
    hourly_rate: float
    due_date: datetime

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    id: int
    invoice_id: str
    invoice_number: str
    total_amount: float
    status: str
    issue_date: datetime
    paid_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
