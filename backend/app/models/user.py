from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    GUEST = "guest"
    MEMBER = "member"
    MENTOR = "mentor"
    ADMIN = "admin"

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: UserRole = UserRole.GUEST

class UserCreate(UserBase):
    email: EmailStr
    name: str

class UserUpdate(UserBase):
    pass

class UserInDB(UserBase):
    id: str
    created_at: str
    last_active: str

    class Config:
        orm_mode = True