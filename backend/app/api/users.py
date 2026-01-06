from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models import user as user_model
from app.schemas import user as user_schema
from app.core import security

router = APIRouter()

@router.get("/", response_model=List[user_schema.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: user_model.User = Depends(deps.get_current_active_superuser),
):
    users = db.query(user_model.User).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=user_schema.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: user_schema.UserCreate,
    current_user: user_model.User = Depends(deps.get_current_active_superuser),
):
    user = db.query(user_model.User).filter(user_model.User.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = user_model.User(
        username=user_in.username,
        hashed_password=security.get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", response_model=user_schema.User)
def delete_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_superuser),
):
    user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.username == "admin":
         raise HTTPException(status_code=400, detail="Cannot delete default admin user")
         
    db.delete(user)
    db.commit()
    return user

@router.get("/me", response_model=user_schema.User)
def read_user_me(
    current_user: user_model.User = Depends(deps.get_current_active_user),
):
    return current_user
