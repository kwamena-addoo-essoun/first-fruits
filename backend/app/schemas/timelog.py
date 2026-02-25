from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class TimeLogCreate(BaseModel):
    project_id: int
    start_time: Optional[datetime] = None   # defaults to now if omitted
    end_time: Optional[datetime] = None     # omit to start a live timer
    description: Optional[str] = None

class TimeLogUpdate(BaseModel):
    project_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None

class TimeLogResponse(BaseModel):
    id: int
    log_id: str
    project_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    hours: Optional[float] = None
    description: Optional[str] = None
    is_invoiced: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
