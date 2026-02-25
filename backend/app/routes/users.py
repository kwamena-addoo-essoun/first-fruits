from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"

def get_token_from_header(authorization: str = Header(None)) -> str:
    """Extract token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    return parts[1]

def get_current_user(token: str = Depends(get_token_from_header), db: Session = Depends(get_db)) -> User:
    """Get authenticated user"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile"""
    return user

@router.put("/me", response_model=UserResponse)
async def update_me(data: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update current user profile"""
    from app.routes.auth import hash_password
    if data.company_name is not None:
        user.company_name = data.company_name
    if data.hourly_rate is not None:
        user.hourly_rate = data.hourly_rate
    if data.password is not None:
        user.hashed_password = hash_password(data.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
