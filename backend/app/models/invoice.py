from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    invoice_number = Column(String, unique=True)
    total_hours = Column(Float)
    hourly_rate = Column(Float)
    total_amount = Column(Float)
    status = Column(String, default="draft")  # draft, sent, paid
    
    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    paid_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    freelancer = relationship("User", back_populates="invoices")
