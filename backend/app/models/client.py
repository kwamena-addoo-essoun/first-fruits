from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import UTC, datetime
import uuid

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    name = Column(String, index=True)
    email = Column(String)
    rate = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    freelancer = relationship("User", back_populates="clients")
    projects = relationship("Project", back_populates="client")
