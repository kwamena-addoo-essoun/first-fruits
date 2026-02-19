from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    hourly_rate = Column(Float, default=50.0)
    company_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    clients = relationship("Client", back_populates="freelancer")
    projects = relationship("Project", back_populates="freelancer")
    timelogs = relationship("TimeLog", back_populates="freelancer")
    invoices = relationship("Invoice", back_populates="freelancer")
