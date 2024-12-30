from pydantic import BaseModel, EmailStr
from typing import Optional

class UserModel(BaseModel):
    class Config:
        orm_mode = True

class UserCreate(UserModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class UserLogin(UserModel):
    email:EmailStr
    password: str
    
class UserUpdate(UserModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserProfile(UserModel):
    first_name: str
    last_name: str
    email: EmailStr
    