from fastapi import HTTPException, status
from models import User
from schemas import UserCreate, UserResponse, UserWithToken
from auth.jwt import create_access_token
from auth.password import hash_password, verify_password

# Service to handle user authentication and registration
def register_service(user, db):
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

# Service to handle user login
def login_service(request, db):
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