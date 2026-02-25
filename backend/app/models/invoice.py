from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import UTC, datetime
import uuid

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"))
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    invoice_number = Column(String, unique=True)
    # Snapshot of names at invoice creation time (survive client/project renames)
    client_name = Column(String, nullable=True)
    project_name = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    total_hours = Column(Float)
    hourly_rate = Column(Float)
    total_amount = Column(Float)
    status = Column(String, default="draft")  # draft, sent, paid
    
    issue_date = Column(DateTime, default=lambda: datetime.now(UTC))
    due_date = Column(DateTime)
    paid_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    freelancer = relationship("User", back_populates="invoices")
    client = relationship("Client", foreign_keys=[client_id])
    project = relationship("Project", foreign_keys=[project_id])
