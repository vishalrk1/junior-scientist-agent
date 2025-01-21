from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    email: EmailStr = Field(title="Email Address")
    password: str = Field(title="Password")
    name: Optional[str] = Field(title="Name")

class UserResponse(BaseModel):
    id: str
    name: Optional[str]
    email: EmailStr
    created_at: datetime

class UserInDB(User):
    hashed_password: str = Field(title="Hashed Password")
    created_at: datetime = Field(title="Created At")