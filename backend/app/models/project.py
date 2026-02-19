from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    hourly_rate = Column(Float)
    is_active = Column(Boolean, default=True)
    total_hours = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    freelancer = relationship("User", back_populates="projects")
    client = relationship("Client", back_populates="projects")
    timelogs = relationship("TimeLog", back_populates="project")
