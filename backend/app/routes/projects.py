from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse
from app.routes.users import get_current_user
from typing import List

router = APIRouter()

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, token: str, db: Session = Depends(get_db)):
    """Create a new project"""
    user = get_current_user(token, db)
    
    db_project = Project(
        user_id=user.id,
        client_id=project.client_id,
        name=project.name,
        description=project.description,
        hourly_rate=project.hourly_rate
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(token: str, db: Session = Depends(get_db)):
    """Get all projects"""
    user = get_current_user(token, db)
    projects = db.query(Project).filter(Project.user_id == user.id).all()
    return projects

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project_data: ProjectCreate, token: str, db: Session = Depends(get_db)):
    """Update project"""
    user = get_current_user(token, db)
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.name = project_data.name
    project.hourly_rate = project_data.hourly_rate
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
