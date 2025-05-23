from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import User
from database.connection import get_db
from schemas import UserCreate, UserResponse, LoginRequest, UserWithToken
from auth.jwt import create_access_token, get_current_user
from auth.password import hash_password, verify_password  # Import your password functions
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserWithToken)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == user.username) | (User.email == user.email)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    access_token = create_access_token(data={"user_id": db_user.id})
    user_response = UserResponse.model_validate(db_user)

    return {
        "user": user_response,
        "access_token": access_token, 
        "token_type": "bearer"
        }


@router.post("/login", response_model=UserWithToken)
async def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter((User.email == request.username) | (User.username == request.username)).first()
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"user_id": user.id})
    user_response = UserResponse.model_validate(user)

    return {
        "user": user_response,
        "access_token": access_token, 
        "token_type": "bearer"
        }