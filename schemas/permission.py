from pydantic import BaseModel
from typing import Optional, List
from models.permission import RoleEnum

class Shareuser(BaseModel):
    user_id: int
    role: RoleEnum

class ShareEventRequest(BaseModel):
    users: List[Shareuser]

class PermissionResponse(BaseModel):
    user_id: int
    role: RoleEnum
    class Config:
        from_attributes = True

class UpdatePermissionRequest(BaseModel):
    role: RoleEnum