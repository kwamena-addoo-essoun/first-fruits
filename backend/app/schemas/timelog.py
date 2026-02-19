from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TimeLogBase(BaseModel):
    project_id: int
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None

class TimeLogCreate(TimeLogBase):
    pass

class TimeLogResponse(TimeLogBase):
    id: int
    log_id: str
    hours: float
    is_invoiced: int
    created_at: datetime

    class Config:
        from_attributes = True
