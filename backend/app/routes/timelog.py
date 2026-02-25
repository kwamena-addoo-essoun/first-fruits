from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.timelog import TimeLog
from app.models.project import Project
from app.models.user import User
from app.schemas.timelog import TimeLogCreate, TimeLogUpdate, TimeLogResponse
from app.routes.users import get_current_user
from app.services.invoice_service import TimeTrackingService
from typing import List
from datetime import UTC, datetime

router = APIRouter()


def _update_project_totals(project: Project, delta_hours: float) -> None:
    """Add delta_hours (can be negative) to a project's running totals."""
    project.total_hours = max(0.0, (project.total_hours or 0.0) + delta_hours)
    project.total_earned = max(0.0, (project.total_earned or 0.0) + delta_hours * project.hourly_rate)


@router.post("/", response_model=TimeLogResponse)
async def create_timelog(
    timelog: TimeLogCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log work time. Omit end_time to start a live timer."""
    project = db.query(Project).filter(
        Project.id == timelog.project_id, Project.user_id == user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check no timer is already running on this project
    if timelog.end_time is None:
        active = db.query(TimeLog).filter(
            TimeLog.user_id == user.id, TimeLog.end_time == None  # noqa: E711
        ).first()
        if active:
            raise HTTPException(
                status_code=400, detail="A timer is already running. Stop it before starting a new one."
            )

    start = timelog.start_time or datetime.now(UTC)
    hours = None
    if timelog.end_time is not None:
        hours = TimeTrackingService.calculate_hours(start, timelog.end_time)
        if hours <= 0:
            raise HTTPException(status_code=400, detail="end_time must be after start_time")
        _update_project_totals(project, hours)
        db.add(project)

    db_timelog = TimeLog(
        user_id=user.id,
        project_id=timelog.project_id,
        start_time=start,
        end_time=timelog.end_time,
        hours=hours,
        description=timelog.description,
    )
    db.add(db_timelog)
    db.commit()
    db.refresh(db_timelog)
    return db_timelog


@router.get("/active", response_model=TimeLogResponse)
async def get_active_timer(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get the currently running timer (if any). Returns 404 if none running."""
    active = db.query(TimeLog).filter(
        TimeLog.user_id == user.id, TimeLog.end_time == None  # noqa: E711
    ).first()
    if not active:
        raise HTTPException(status_code=404, detail="No active timer")
    return active


@router.patch("/{timelog_id}/stop", response_model=TimeLogResponse)
async def stop_timer(
    timelog_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stop a running timer — sets end_time to now and computes hours."""
    timelog = db.query(TimeLog).filter(
        TimeLog.id == timelog_id, TimeLog.user_id == user.id
    ).first()
    if not timelog:
        raise HTTPException(status_code=404, detail="Time log not found")
    if timelog.end_time is not None:
        raise HTTPException(status_code=400, detail="Timer is not running")

    end = datetime.now(UTC).replace(tzinfo=None)  # naive UTC to match SQLite storage
    hours = TimeTrackingService.calculate_hours(timelog.start_time, end)
    timelog.end_time = end
    timelog.hours = hours

    project = db.query(Project).filter(
        Project.id == timelog.project_id, Project.user_id == user.id
    ).first()
    if project:
        _update_project_totals(project, hours)
        db.add(project)

    db.add(timelog)
    db.commit()
    db.refresh(timelog)
    return timelog


@router.put("/{timelog_id}", response_model=TimeLogResponse)
async def update_timelog(
    timelog_id: int,
    data: TimeLogUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Edit an existing (completed) time log."""
    timelog = db.query(TimeLog).filter(
        TimeLog.id == timelog_id, TimeLog.user_id == user.id
    ).first()
    if not timelog:
        raise HTTPException(status_code=404, detail="Time log not found")
    if timelog.end_time is None:
        raise HTTPException(status_code=400, detail="Cannot edit a running timer — stop it first")

    old_hours = timelog.hours or 0.0
    project = db.query(Project).filter(
        Project.id == timelog.project_id, Project.user_id == user.id
    ).first()

    if data.description is not None:
        timelog.description = data.description
    if data.start_time is not None:
        timelog.start_time = data.start_time
    if data.end_time is not None:
        timelog.end_time = data.end_time
    if data.project_id is not None and data.project_id != timelog.project_id:
        new_project = db.query(Project).filter(
            Project.id == data.project_id, Project.user_id == user.id
        ).first()
        if not new_project:
            raise HTTPException(status_code=404, detail="New project not found")
        if project:
            _update_project_totals(project, -old_hours)
            db.add(project)
        timelog.project_id = data.project_id
        project = new_project

    # Recompute hours from (possibly updated) start/end
    new_hours = TimeTrackingService.calculate_hours(timelog.start_time, timelog.end_time)
    if new_hours <= 0:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    hours_delta = new_hours - (old_hours if data.project_id is None else 0.0)
    timelog.hours = new_hours
    if project:
        _update_project_totals(project, hours_delta)
        db.add(project)

    db.add(timelog)
    db.commit()
    db.refresh(timelog)
    return timelog


@router.get("/", response_model=List[TimeLogResponse])
async def get_timelogs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all time logs"""
    timelogs = db.query(TimeLog).filter(TimeLog.user_id == user.id).all()
    return timelogs


@router.get("/project/{project_id}", response_model=List[TimeLogResponse])
async def get_project_timelogs(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get time logs for a project"""
    timelogs = db.query(TimeLog).filter(
        TimeLog.user_id == user.id, TimeLog.project_id == project_id
    ).all()
    return timelogs


@router.delete("/{timelog_id}")
async def delete_timelog(
    timelog_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a time log"""
    timelog = db.query(TimeLog).filter(
        TimeLog.id == timelog_id, TimeLog.user_id == user.id
    ).first()
    if not timelog:
        raise HTTPException(status_code=404, detail="Time log not found")

    project = db.query(Project).filter(
        Project.id == timelog.project_id, Project.user_id == user.id
    ).first()
    if project and timelog.hours:
        _update_project_totals(project, -timelog.hours)
        db.add(project)

    db.delete(timelog)
    db.commit()
    return {"message": "Time log deleted"}

