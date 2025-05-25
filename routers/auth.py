from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas import UserCreate, UserWithToken
from models import User
from auth.jwt import get_current_user
from schemas.response import APIResponse
from fastapi.security import OAuth2PasswordRequestForm
from services.auth_service import register_service, login_service, refresh_token_service, logout_service

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# User registration endpoint
@auth_router.post("/register", response_model=APIResponse[UserWithToken])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    response = register_service(user, db)
    return APIResponse(success=True, message="User registered successfully", data=response)

# User login endpoint
@auth_router.post("/login", response_model=APIResponse[UserWithToken])
async def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    response = login_service(request, db)
    return APIResponse(success=True, message="User logged in successfully", data=response)

# Refresh token endpoint
@auth_router.post("/refresh", response_model=APIResponse[UserWithToken])
async def refresh_token(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = refresh_token_service(current_user, db)
    return APIResponse(success=True, message="Token refreshed successfully", data=response)

# Logout endpoint
@auth_router.post("/logout", response_model=APIResponse[dict])
async def logout(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logout_service(current_user, db)
    return APIResponse(success=True, message="User logged out successfully", data={})