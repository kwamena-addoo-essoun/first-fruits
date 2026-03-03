from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import UTC, datetime
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
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Billing / subscription
    plan = Column(String, default="free", nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    clients = relationship("Client", back_populates="freelancer", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="freelancer", cascade="all, delete-orphan")
    timelogs = relationship("TimeLog", back_populates="freelancer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="freelancer", cascade="all, delete-orphan")
