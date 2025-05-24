from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from models import User
from schemas.response import APIResponse
from schemas.event import EventCreate, EventResponse, EventUpdate, EventBatchCreate
from auth.jwt import get_current_user
from datetime import datetime
from typing import Optional
from services.event_service import (
                                    create_event_service, 
                                    batch_create_events_service,
                                    get_event_service,
                                    list_events_service,
                                    update_event_service,
                                    delete_event_service
                                    )

event_router = APIRouter(prefix="/api/events", tags=["Event Management"])
        
    
# Create a new event
@event_router.post("/", response_model=APIResponse[EventResponse], status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = create_event_service(event, db, current_user)
    return APIResponse(success=True, message="Event created successfully", data=response)


# Create multiple events in a batch
@event_router.post("/batch", response_model=list[EventResponse], status_code=status.HTTP_201_CREATED)
async def create_events_batch(batch: EventBatchCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = batch_create_events_service(batch, db, current_user)
    return APIResponse(success=True, message="Events created successfully", data=response)


# Get an event by ID
@event_router.get("/{id}", response_model=APIResponse[EventResponse])
async def get_event(id:int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    repsonse = get_event_service(id, db, current_user)
    return APIResponse(success=True, message="Event fetched successfully", data=repsonse)


# Get all events for the current user
@event_router.get("/", response_model = APIResponse[list[EventResponse]])
async def list_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of events to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of events to return"),
    is_recurring: Optional[bool] = Query(None, description="Filter by recurring events"),
    search: Optional[str] = Query(None, description="Search by title or description"),
    start_date: Optional[datetime] = Query(None, description="Filter events starting after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events ending before this date"),
):
    response =  list_events_service(db, current_user, skip, limit, is_recurring, search, start_date, end_date)
    return APIResponse(success=True,message="Events fetched successfully",data=response)


# Update an event
@event_router.put("/{id}", response_model=APIResponse[EventResponse])
async def update_event(id: int, event_update: EventUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = update_event_service(id, event_update, db, current_user)
    return APIResponse(success=True, message="Event updated successfully", data=response)


# Delete an event
@event_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return delete_event_service(id, db, current_user)