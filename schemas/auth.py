from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True

# class Token(BaseModel):
#     access_token: str
#    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None

class UserWithToken(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str
