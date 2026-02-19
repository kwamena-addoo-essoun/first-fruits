from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str
    company_name: Optional[str] = None
    hourly_rate: float = 50.0

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True
