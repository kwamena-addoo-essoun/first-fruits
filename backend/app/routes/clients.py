from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientResponse
from app.routes.users import get_current_user
from typing import List

router = APIRouter()

@router.post("/", response_model=ClientResponse)
async def create_client(client: ClientCreate, token: str, db: Session = Depends(get_db)):
    """Add a new client"""
    user = get_current_user(token, db)
    
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
async def get_clients(token: str, db: Session = Depends(get_db)):
    """Get all clients"""
    user = get_current_user(token, db)
    clients = db.query(Client).filter(Client.user_id == user.id).all()
    return clients

@router.delete("/{client_id}")
async def delete_client(client_id: int, token: str, db: Session = Depends(get_db)):
    """Delete a client"""
    user = get_current_user(token, db)
    client = db.query(Client).filter(Client.id == client_id, Client.user_id == user.id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    db.delete(client)
    db.commit()
    return {"message": "Client deleted"}
