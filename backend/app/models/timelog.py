from sqlalchemy import Column, Integer, DateTime, ForeignKey, Float, String, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import UTC, datetime
import uuid

class TimeLog(Base):
    __tablename__ = "timelogs"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)   # NULL while timer is running
    hours = Column(Float, nullable=True)          # NULL while timer is running
    description = Column(Text, nullable=True)
    is_invoiced = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    freelancer = relationship("User", back_populates="timelogs")
    project = relationship("Project", back_populates="timelogs")
