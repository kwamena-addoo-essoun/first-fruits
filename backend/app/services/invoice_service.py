from sqlalchemy.orm import Session
from app.models.timelog import TimeLog
from app.models.project import Project
from datetime import datetime

class TimeTrackingService:
    @staticmethod
    def calculate_hours(start_time: datetime, end_time: datetime) -> float:
        """Calculate hours between two times"""
        delta = end_time - start_time
        return delta.total_seconds() / 3600

    @staticmethod
    def get_project_stats(db: Session, project_id: int) -> dict:
        """Get total hours and earnings for a project"""
        timelogs = db.query(TimeLog).filter(TimeLog.project_id == project_id).all()
        project = db.query(Project).filter(Project.id == project_id).first()
        
        total_hours = sum(log.hours for log in timelogs)
        total_earned = total_hours * project.hourly_rate if project else 0
        
        return {"total_hours": total_hours, "total_earned": total_earned}

class InvoiceService:
    @staticmethod
    def generate_invoice_number(user_id: int, invoice_count: int) -> str:
        """Generate unique invoice number"""
        return f"INV-{user_id}-{invoice_count + 1:04d}"

    @staticmethod
    def calculate_invoice_total(total_hours: float, hourly_rate: float) -> float:
        """Calculate invoice total"""
        return round(total_hours * hourly_rate, 2)
