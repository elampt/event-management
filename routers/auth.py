from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas import UserCreate, UserWithToken
from schemas.response import APIResponse
from fastapi.security import OAuth2PasswordRequestForm
from services.auth_service import register_service, login_service

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@auth_router.post("/register", response_model=APIResponse[UserWithToken])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    response = register_service(user, db)
    return APIResponse(success=True, message="User registered successfully", data=response)


@auth_router.post("/login", response_model=APIResponse[UserWithToken])
async def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    response = login_service(request, db)
    return APIResponse(success=True, message="User logged in successfully", data=response)