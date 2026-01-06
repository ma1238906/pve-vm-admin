from typing import Optional, List
from pydantic import BaseModel
from .vm import VM

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    vms: List[VM] = []

    class Config:
        from_attributes = True
