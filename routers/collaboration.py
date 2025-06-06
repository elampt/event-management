from fastapi import APIRouter, Depends, status
from database.connection import get_db
from sqlalchemy.orm import Session
from models import Event, User
from schemas.response import APIResponse
from schemas.permission import ShareEventRequest, PermissionResponse, UpdatePermissionRequest
from auth.jwt import get_current_user
from services.collaboration_service import share_event_service, get_event_permissions_service, update_user_permission_service, remove_user_permission_service

collaboration_router = APIRouter(prefix="/api/events", tags=["Collaboration"])

# Share an event with another user
@collaboration_router.post("/{id}/share", response_model=APIResponse[list[PermissionResponse]])
async def share_event(id: int, share_req: ShareEventRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = share_event_service(id, share_req, db, current_user)
    return APIResponse(success=True, message="Event shared successfully", data=response)

# List all permissions for an event
@collaboration_router.get("/{id}/permissions", response_model=APIResponse[list[PermissionResponse]])
async def get_event_permissions(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = get_event_permissions_service(id, db, current_user)
    return APIResponse(success=True, message="Event permissions fetched successfully", data=response)
    
# Update an existing permission for a user for an event
@collaboration_router.put("/{id}/permissions/{user_id}", response_model=APIResponse[PermissionResponse])
async def update_user_permission(
    id: int,
    user_id: int, 
    update_req: UpdatePermissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    response = update_user_permission_service(id, user_id, update_req, db, current_user)
    return APIResponse(success=True, message="Permission updated successfully", data=response)

# Remove a user's permission for an event
@collaboration_router.delete("/{id}/permissions/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_permission(
    id: int,
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return remove_user_permission_service(id, user_id, db, current_user)