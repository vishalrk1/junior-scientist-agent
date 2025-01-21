from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from .schemas import (
    TokenResponse, PasswordResetRequest, PasswordReset,
    GoogleAuthRequest, ChangePasswordRequest
)
from auth.utils import create_access_token, pwd_context, generate_reset_token
from auth.dependencies import get_current_user
from auth.oauth import verify_google_token

from database import Database
from datetime import datetime
from bson import ObjectId

from config import settings
from models.user import User, UserResponse, UserInDB

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user: User):
    users_collection = Database.get_users_collection()

    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_dict = user.model_dump()
    user_dict["hashed_password"] = pwd_context.hash(user.password)
    user_dict["created_at"] = datetime.utcnow()
    del user_dict["password"]
    
    result = await users_collection.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    
    return UserResponse(**user_dict)

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users_collection = Database.get_users_collection()
    user = await users_collection.find_one({"email": form_data.username})
    
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/google", response_model=TokenResponse)
async def google_login(request: GoogleAuthRequest):
    try:
        google_user = await verify_google_token(request.token)
        
        users_collection = Database.get_users_collection()
        user = await users_collection.find_one({"email": google_user["email"]})
        
        if not user:
            user_data = {
                "email": google_user["email"],
                "name": google_user.get("name"),
                "created_at": datetime.utcnow(),
                "google_id": google_user["sub"],
            }
            result = await users_collection.insert_one(user_data)
        access_token = create_access_token(data={"sub": google_user["email"]})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        name=current_user.get("name"),
        created_at=current_user["created_at"]
    )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Successfully logged out"}