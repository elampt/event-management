from schemas.version import EventChangelogSchema, EventDiffResponse
from schemas.response import APIResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from models import User
from auth.jwt import get_current_user
from typing import List
from services.changelog_service import get_event_changelog_service, get_event_diff_service

changelog_router = APIRouter(prefix="/api/events", tags=["Changelog & Diff"])


# Get chronological history of changes made to an event
@changelog_router.get("/{id}/changelog", response_model=APIResponse[List[EventChangelogSchema]])
async def get_event_changelog(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = get_event_changelog_service(id, db, current_user)
    return APIResponse(success=True, message="Changelog fetched successfully", data=response)


# Get the diff between two versions of an event
@changelog_router.get("/{id}/diff/{version_id1}/{version_id2}", response_model=APIResponse[EventDiffResponse])
async def get_event_diff(id: int, version_id1: int, version_id2: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = get_event_diff_service(id, version_id1, version_id2, db, current_user)
    return APIResponse(success=True, message="Event diff fetched successfully", data=response)