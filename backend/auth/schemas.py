from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

class GoogleAuthRequest(BaseModel):
    token: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)