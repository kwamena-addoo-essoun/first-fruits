from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.timelog import TimeLog
from app.models.project import Project
from app.schemas.timelog import TimeLogCreate, TimeLogResponse
from app.routes.users import get_current_user
from app.services.invoice_service import TimeTrackingService
from typing import List

router = APIRouter()

@router.post("/", response_model=TimeLogResponse)
async def create_timelog(timelog: TimeLogCreate, token: str, db: Session = Depends(get_db)):
    """Log work time"""
    user = get_current_user(token, db)
    
    hours = TimeTrackingService.calculate_hours(timelog.start_time, timelog.end_time)
    
    db_timelog = TimeLog(
        user_id=user.id,
        project_id=timelog.project_id,
        start_time=timelog.start_time,
        end_time=timelog.end_time,
        hours=hours,
        description=timelog.description
    )
    db.add(db_timelog)
    
    # Update project totals
    project = db.query(Project).filter(Project.id == timelog.project_id).first()
    if project:
        project.total_hours += hours
        project.total_earned += hours * project.hourly_rate
        db.add(project)
    
    db.commit()
    db.refresh(db_timelog)
    return db_timelog

@router.get("/", response_model=List[TimeLogResponse])
async def get_timelogs(token: str, db: Session = Depends(get_db)):
    """Get all time logs"""
    user = get_current_user(token, db)
    timelogs = db.query(TimeLog).filter(TimeLog.user_id == user.id).all()
    return timelogs

@router.get("/project/{project_id}", response_model=List[TimeLogResponse])
async def get_project_timelogs(project_id: int, token: str, db: Session = Depends(get_db)):
    """Get time logs for a project"""
    user = get_current_user(token, db)
    timelogs = db.query(TimeLog).filter(
        TimeLog.user_id == user.id,
        TimeLog.project_id == project_id
    ).all()
    return timelogs

@router.delete("/{timelog_id}")
async def delete_timelog(timelog_id: int, token: str, db: Session = Depends(get_db)):
    """Delete a time log"""
    user = get_current_user(token, db)
    timelog = db.query(TimeLog).filter(TimeLog.id == timelog_id, TimeLog.user_id == user.id).first()
    
    if not timelog:
        raise HTTPException(status_code=404, detail="Time log not found")
    
    db.delete(timelog)
    db.commit()
    return {"message": "Time log deleted"}
