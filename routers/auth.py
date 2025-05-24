from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import User
from database.connection import get_db
from schemas import UserCreate, UserResponse, LoginRequest, UserWithToken
from auth.jwt import create_access_token, get_current_user
from auth.password import hash_password, verify_password  # Import your password functions
from fastapi.security import OAuth2PasswordRequestForm
from services.auth_service import register_service, login_service

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@auth_router.post("/register", response_model=UserWithToken)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    return register_service(user, db)


@auth_router.post("/login", response_model=UserWithToken)
async def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login_service(request, db)