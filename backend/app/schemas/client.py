from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ClientBase(BaseModel):
    name: str
    email: str
    rate: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    rate: Optional[str] = None

class ClientResponse(ClientBase):
    id: int
    client_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
