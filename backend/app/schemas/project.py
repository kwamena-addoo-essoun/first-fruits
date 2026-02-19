from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    client_id: int
    hourly_rate: float

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    project_id: str
    total_hours: float
    total_earned: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
