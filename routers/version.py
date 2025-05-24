from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from models import User
from schemas.response import APIResponse
from auth.jwt import get_current_user
from schemas.version import EventVersionSchema
from services.version_service import get_event_version_service, rollback_event_service

# Retrieve the version history of an event
version_router = APIRouter(prefix="/api/events", tags=["Version History"])
@version_router.get("/{id}/history/{version_id}", response_model=APIResponse[EventVersionSchema])
async def get_event_version(id: int, version_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response =  get_event_version_service(id, version_id, db, current_user)
    return APIResponse(success=True, message="Event version fetched successfully", data=response)


# Rollback to a specific version of an event
@version_router.post("/{id}/rollback/{version_id}", response_model=APIResponse[EventVersionSchema])
async def rollback_event(id: int, version_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = rollback_event_service(id, version_id, db, current_user)
    return APIResponse(success=True, message="Event rolled back successfully", data=response)