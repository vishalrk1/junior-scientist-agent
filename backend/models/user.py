from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

from .base_model import MongoModel

class User(MongoModel):
    email: EmailStr = Field(title="Email Address")
    password: str = Field(title="Password")
    name: Optional[str] = Field(title="Name")
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = None
    
    @property
    def collection_name(self) -> str:
        return "users"

class UserResponse(BaseModel):
    id: str
    name: Optional[str]
    email: EmailStr
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]

class UserInDB(User):
    hashed_password: str = Field(title="Hashed Password")
    google_id: Optional[str] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "is_active": True
            }
        }