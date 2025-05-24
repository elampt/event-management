from fastapi import APIRouter, Depends, status
from database.connection import get_db
from sqlalchemy.orm import Session
from models import Event, User
from schemas.permission import ShareEventRequest, PermissionResponse, UpdatePermissionRequest
from auth.jwt import get_current_user
from services.collaboration_service import share_event_service, get_event_permissions_service, update_user_permission_service, remove_user_permission_service

router = APIRouter(prefix="/api/events", tags=["Collaboration"])

# Share an event with another user
@router.post("/{id}/share", response_model=list[PermissionResponse])
async def share_event(id: int, share_req: ShareEventRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return share_event_service(id, share_req, db, current_user)

# List all permissions for an event
@router.get("/{id}/permissions", response_model=list[PermissionResponse])
async def get_event_permissions(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_event_permissions_service(id, db, current_user)
    
# Update an existing permission for a user for an event
@router.put("/{id}/permissions/{user_id}", response_model=PermissionResponse)
async def update_user_permission(
    id: int,
    user_id: int, 
    update_req: UpdatePermissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_user_permission_service(id, user_id, update_req, db, current_user)

# Remove a user's permission for an event
@router.delete("/{id}/permissions/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_permission(
    id: int,
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return remove_user_permission_service(id, user_id, db, current_user)