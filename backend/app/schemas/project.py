from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    client_id: Optional[int] = None
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

    model_config = ConfigDict(from_attributes=True)
