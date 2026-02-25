from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.routes.users import get_current_user
from typing import List

router = APIRouter()

@router.post("/", response_model=ClientResponse)
async def create_client(client: ClientCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a new client"""
    db_client = Client(
        user_id=user.id,
        name=client.name,
        email=client.email,
        rate=client.rate
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.get("/", response_model=List[ClientResponse])
async def get_clients(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all clients"""
    clients = db.query(Client).filter(Client.user_id == user.id).all()
    return clients

@router.delete("/{client_id}")
async def delete_client(client_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a client"""
    client = db.query(Client).filter(Client.id == client_id, Client.user_id == user.id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    db.delete(client)
    db.commit()
    return {"message": "Client deleted"}

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: int, data: ClientUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update a client"""
    client = db.query(Client).filter(Client.id == client_id, Client.user_id == user.id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if data.name is not None:
        client.name = data.name
    if data.email is not None:
        client.email = data.email
    if data.rate is not None:
        client.rate = data.rate

    db.add(client)
    db.commit()
    db.refresh(client)
    return client
