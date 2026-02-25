from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional
from datetime import datetime

class InvoiceCreate(BaseModel):
    due_date: datetime
    # Link to existing data (auto-computes hours/rate from project timelogs)
    client_id: Optional[int] = None
    project_id: Optional[int] = None
    notes: Optional[str] = None
    # Manual override (required when project_id is not provided)
    total_hours: Optional[float] = None
    hourly_rate: Optional[float] = None

    @model_validator(mode="after")
    def check_hours_or_project(self):
        if self.project_id is None:
            if self.total_hours is None or self.hourly_rate is None:
                raise ValueError("total_hours and hourly_rate are required when project_id is not provided")
        return self

class InvoiceResponse(BaseModel):
    id: int
    invoice_id: str
    invoice_number: str
    total_hours: float
    hourly_rate: float
    total_amount: float
    status: str
    due_date: datetime
    issue_date: datetime
    paid_date: Optional[datetime] = None
    created_at: datetime
    client_id: Optional[int] = None
    project_id: Optional[int] = None
    client_name: Optional[str] = None
    project_name: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
