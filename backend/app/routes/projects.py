from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.models.client import Client
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse
from app.routes.users import get_current_user
from typing import List

router = APIRouter()

FREE_PROJECT_LIMIT = 3

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new project"""
    if (user.plan or "free") == "free":
        project_count = db.query(Project).filter(Project.user_id == user.id).count()
        if project_count >= FREE_PROJECT_LIMIT:
            raise HTTPException(
                status_code=403,
                detail=f"Free plan is limited to {FREE_PROJECT_LIMIT} projects. Upgrade to Pro for unlimited projects.",
            )
    if project.client_id is not None:
        client = db.query(Client).filter(Client.id == project.client_id, Client.user_id == user.id).first()
        if not client:
            raise HTTPException(status_code=400, detail="Invalid client_id for current user")

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
async def get_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all projects"""
    projects = db.query(Project).filter(Project.user_id == user.id).all()
    return projects

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project_data: ProjectCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update project"""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_data.client_id is not None:
        client = db.query(Client).filter(Client.id == project_data.client_id, Client.user_id == user.id).first()
        if not client:
            raise HTTPException(status_code=400, detail="Invalid client_id for current user")

    project.client_id = project_data.client_id
    project.name = project_data.name
    project.description = project_data.description
    project.hourly_rate = project_data.hourly_rate
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}")
async def delete_project(project_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a project"""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}
