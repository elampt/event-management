from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from models import Event, User
from schemas.event import EventCreate, EventResponse, EventOccurence, EventUpdate, EventBatchCreate
from auth.jwt import get_current_user
from dateutil.rrule import rrulestr
from datetime import timedelta, timezone
from typing import Optional

router = APIRouter(prefix="/api/events", tags=["Event Management"])

# Function to ensure that the datetime is in UTC
def ensure_utc(dt):
    if dt.tzinfo is None:
        # Assume naive datetimes are UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

# Function to expand occurrences of a recurring event
def expand_occurrences(event: Event, count: int = 10):
    if event.is_recurring and event.recurrence_pattern:
        start_time = ensure_utc(event.start_time)
        rule = rrulestr(event.recurrence_pattern, dtstart=start_time)
        # Generate up to `count` occurences
        occurrences = []
        for dt in list(rule[:count]):
            occurrences.append(EventOccurence(
                start_time=dt,
                end_time=dt + (event.end_time - event.start_time)
            ))
        return occurrences
    else:
        return [EventOccurence(start_time=event.start_time, end_time=event.end_time)]
    
    
# Create a new event
@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_event = Event(
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        location=event.location,
        is_recurring=event.is_recurring,
        recurrence_pattern=event.recurrence_pattern,
        owner_id=current_user.id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    # Expand occurrences if the event is recurring
    occurences = expand_occurrences(db_event)
    return EventResponse.model_validate({**db_event.__dict__, "occurences": occurences})


# Create multiple events in a batch
@router.post("/batch", response_model=list[EventResponse], status_code=status.HTTP_201_CREATED)
async def create_events_batch(batch: EventBatchCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    created_events = []
    for event in batch.events:
        db_event = Event(
            title = event.title,
            description = event.description,
            start_time = event.start_time,
            end_time = event.end_time,
            location = event.location,
            is_recurring = event.is_recurring,
            recurrence_pattern = event.recurrence_pattern,
            owner_id = current_user.id
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        occurences = expand_occurrences(db_event)
        created_events.append(EventResponse.model_validate({**db_event.__dict__, "occurences": occurences}))
    return created_events


# Get an event by ID
@router.get("/{id}", response_model=EventResponse)
async def get_event(id:int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_event = db.query(Event).filter(Event.id == id).first()
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    if db_event.owner_id != current_user.id:
        # Optionally, check for explicit permission here
        # permission = db.query(EventPermission).filter_by(event_id=event_id, user_id=current_user.id).first()
        # if not permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have to access this event")
    
    occurences = expand_occurrences(db_event)
    return EventResponse.model_validate({**db_event.__dict__, "occurences": occurences})


# Get all events for the current user
@router.get("/", response_model = list[EventResponse])
async def list_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of events to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of events to return"),
    is_recurring: Optional[bool] = Query(None, description="Filter by recurring events"),
    search: Optional[str] = Query(None, description="Search by title or description")
):
    query = db.query(Event).filter(Event.owner_id == current_user.id)
    # Need to include other permissions logic here

    if is_recurring is not None:
        query = query.filter(Event.is_recurring == is_recurring)
    if search:
        query = query.filter(
            (Event.title.ilike(f"%{search}%")) | 
            (Event.description.ilike(f"%{search}%"))
        )
    events = query.offset(skip).limit(limit).all()

    if not events:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No events found")
    return [
        EventResponse.model_validate({**event.__dict__, "occurences": expand_occurrences(event)})
        for event in events
    ]


# Update an event
@router.put("/{id}", response_model=EventResponse)
async def update_event(id: int, event_update: EventUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_event = db.query(Event).filter(Event.id == id).first()
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if db_event.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to update this event")
    
    # Update the event with the new values provided (Allows for partial updates)
    update_data = event_update.model_dump(exclude_unset=True) # Get only the fields that were provided, convert to dict
    for key, value in update_data.items():
        setattr(db_event, key, value)
    db.commit()
    db.refresh(db_event)
    occurences = expand_occurrences(db_event)
    return EventResponse.model_validate({**db_event.__dict__, "occurences": occurences})


# Delete an event
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_event = db.query(Event).filter(Event.id == id).first()
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if db_event.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to delete this event")
    
    db.delete(db_event)
    db.commit()
    return {"detail": "Event deleted successfully"}