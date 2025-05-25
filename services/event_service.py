from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from datetime import datetime, timezone
import json

from schemas.event import EventOccurence, EventCreate, EventResponse
from models import EventPermission, Event, EventVersion, EventChangelog, RoleEnum
from services.redis_client import redis_client

from deepdiff import DeepDiff
from dateutil.rrule import rrulestr


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
    

def expand_occurrences_until(event: Event, until: datetime):
    """Expand occurrences of a recurring event up to a given datetime."""
    if event.is_recurring and event.recurrence_pattern:
        start_time = ensure_utc(event.start_time)
        rule = rrulestr(event.recurrence_pattern, dtstart=start_time)
        occurrences = []
        for dt in rule:
            if dt > until:
                break
            occurrences.append(EventOccurence(
                start_time=dt,
                end_time=dt + (event.end_time - event.start_time)
            ))
        return occurrences
    else:
        return [EventOccurence(start_time=event.start_time, end_time=event.end_time)]

def has_event_conflict(db, user_id, start_time, end_time, exclude_event_id=None):
    """
    Returns True if the given time range conflicts with any event (including recurring) for the user.
    """
    # Events owned by the user
    owned_query = db.query(Event).filter(Event.owner_id == user_id)
    # Events shared with the user
    shared_event_ids = db.query(EventPermission.event_id).filter(EventPermission.user_id == user_id)
    shared_query = db.query(Event).filter(Event.id.in_(shared_event_ids))
    # Combine both queries
    query = owned_query.union(shared_query)
    if exclude_event_id:
        query = query.filter(Event.id != exclude_event_id)
    events = query.all()
    for event in events:
        # Expand occurrences up to the end_time of the new/updated event
        for occ in expand_occurrences_until(event, end_time):
            if occ.start_time < end_time and occ.end_time > start_time:
                return True
    return False

    
# Helper function to convert event to dictionary for response
def event_to_dict(event):
    result = {}
    for k, v in event.__dict__.items():
        if k.startswith('_'):
            continue
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result

# Prevent serialization issues with non-serializable objects
def make_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, type):
        return str(obj)
    elif isinstance(obj, list):
        return [make_json_serializable(i) for i in obj]
    else:
        return obj
    
DATETIME_FIELDS = {"start_time", "end_time"}

def assign_version_data_to_event(event, data):
    for key, value in data.items():
        if key in DATETIME_FIELDS and isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                pass
        setattr(event, key, value)


# Create a new event and handle conflicts
def create_event_service(event: EventCreate, db, current_user):
    if event.start_time >= event.end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End time must be after start time")
    
    if has_event_conflict(db, current_user.id, event.start_time, event.end_time):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event time conflicts with an existing event")
    try:
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
        db.flush()  # To get db_event.id

        initial_version = EventVersion(
            event_id=db_event.id,
            version=1,
            data=event_to_dict(db_event),
            changed_by=current_user.id,
            change_note="Initial version"
        )
        db.add(initial_version)

        changelog_entry = EventChangelog(
            event_id=db_event.id,
            version_id=1,
            diff={},
            changed_by=current_user.id,
        )
        db.add(changelog_entry)
        db.commit()
        occurences = expand_occurrences(db_event)
        
        # Invalidate cache for all events of the user
        pattern = f"events:user:{current_user.id}:*"
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)
        
        return EventResponse.model_validate({**db_event.__dict__, "occurences": occurences})
    except SQLAlchemyError as e:
        db.rollback()
        print("Error creating event:", e)
        raise HTTPException(status_code=500, detail="Failed to create event")
    

# Function to create Batch of events
def batch_create_events_service(batch, db, current_user):
    created_events = []
    try:
        # First check for conflicts across all events in the batch
        for event in batch.events:
            if event.start_time >= event.end_time:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End time must be after start time")
            
            if has_event_conflict(db, current_user.id, event.start_time, event.end_time):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Event time conflicts with an existing event: {event.title}")

        for event in batch.events:
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
            db.flush()

            initial_version = EventVersion(
                event_id=db_event.id,
                version=1,
                data=event_to_dict(db_event),
                changed_by=current_user.id,
                change_note="Initial version"
            )
            db.add(initial_version)

            changelog_entry = EventChangelog(
                event_id=db_event.id,
                version_id=1,
                diff={},
                changed_by=current_user.id,
            )
            db.add(changelog_entry)

            occurences = expand_occurrences(db_event)
            created_events.append(EventResponse.model_validate({**db_event.__dict__, "occurences": occurences}))
        db.commit()
        
        # Invalidate cache for all events of the user
        pattern = f"events:user:{current_user.id}:*"
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)
        return created_events
    
    except SQLAlchemyError as e:
        db.rollback()
        print("Error creating events batch:", e)
        raise HTTPException(status_code=500, detail="Failed to create events batch")
    

# Function to get event by ID with permission checks
def get_event_service(id, db, current_user):
    cache_key = f"event:{id}:user:{current_user.id}"
    cached = redis_client.get(cache_key)
    if cached:
        # Deserialize the cached data
        return EventResponse.model_validate(json.loads(cached))
    
    db_event = db.query(Event).filter(Event.id == id).first()
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    if db_event.owner_id != current_user.id:
        permission = db.query(EventPermission).filter_by(event_id=id, user_id=current_user.id).first()
        if not permission:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have to access this event")
    
    occurences = expand_occurrences(db_event)
    event_response = EventResponse.model_validate({**db_event.__dict__, "occurences": occurences})
    # Cache the event response for 5 minutes
    redis_client.setex(cache_key, 300, event_response.model_dump_json())  # Cache for 5 minutes
    return event_response


# Function to get all events with optional filters
def list_events_service(db, current_user, skip, limit, is_recurring, search, start_date, end_date):
    cache_key = f"events:user:{current_user.id}:skip:{skip}:limit:{limit}:recurring:{is_recurring}:search:{search}:start_date:{start_date}:end_date:{end_date}"
    cached = redis_client.get(cache_key)
    
    if cached:
        # Deserialize the cached data
        return [EventResponse.model_validate(event) for event in json.loads(cached)]
    
    # Events owned by the current user
    owned_query = db.query(Event).filter(Event.owner_id == current_user.id)
    # Events shared with the current user
    shared_event_ids = db.query(EventPermission.event_id).filter(EventPermission.user_id == current_user.id)
    shared_query = db.query(Event).filter(Event.id.in_(shared_event_ids))

    # Combine both queries
    query = owned_query.union(shared_query)

    if is_recurring is not None:
        query = query.filter(Event.is_recurring == is_recurring)
    if search:
        query = query.filter(
            (Event.title.ilike(f"%{search}%")) | 
            (Event.description.ilike(f"%{search}%"))
        )

    # Filter by start and end dates
    if start_date:
        query = query.filter(Event.start_time >= start_date)
    if end_date:
        query = query.filter(Event.end_time <= end_date)

    events = query.offset(skip).limit(limit).all()

    if not events:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No events found")
    return [
        EventResponse.model_validate({**event.__dict__, "occurences": expand_occurrences(event)})
        for event in events
    ]


# Function to update an existing event
def update_event_service(id, event_update, db, current_user):
    db_event = db.query(Event).filter(Event.id == id).first()
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if db_event.owner_id != current_user.id:
        permission = db.query(EventPermission).filter_by(event_id=id, user_id=current_user.id, role=RoleEnum.editor).first()
        if not permission:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to update this event")
    try:
        update_data = event_update.model_dump(exclude_unset=True)
        if "start_time" in update_data or "end_time" in update_data:
            new_start = update_data.get("start_time", db_event.start_time)
            new_end = update_data.get("end_time", db_event.end_time)
            if new_start >= new_end:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End time must be after start time")
            if has_event_conflict(db, current_user.id, new_start, new_end, exclude_event_id=id):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event time conflicts with an existing event")
        for key, value in update_data.items():
            setattr(db_event, key, value)
        db.flush()
        latest_version = db.query(EventVersion).filter_by(event_id=id).order_by(EventVersion.version.desc()).first()
        next_version_number = (latest_version.version if latest_version else 0) + 1
        new_version = EventVersion(
            event_id=id,
            version=next_version_number,
            data=event_to_dict(db_event),
            changed_by=current_user.id,
            change_note="Updated event"
        )
        db.add(new_version)
        diff = DeepDiff(latest_version.data, new_version.data, ignore_order=True).to_dict() if latest_version else {}
        diff = make_json_serializable(diff)
        changelog_entry = EventChangelog(
            event_id=id,
            version_id=new_version.id,
            diff=diff,
            changed_by=current_user.id,
        )
        db.add(changelog_entry)
        db.commit()
        occurences = expand_occurrences(db_event)

        # Invalidate cache for all events of the user
        pattern = f"events:user:{current_user.id}:*"
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)

        return EventResponse.model_validate({**db_event.__dict__, "occurences": occurences})
    except SQLAlchemyError as e:
        db.rollback()
        print("Error updating event:", e)
        raise HTTPException(status_code=500, detail="Failed to update event")
    

# Function to delete an event
def delete_event_service(id, db, current_user):
    db_event = db.query(Event).filter(Event.id == id).first()
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if db_event.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to delete this event")
    
    db.delete(db_event)
    db.commit()

    # Invalidate cache for all events of the user
    pattern = f"events:user:{current_user.id}:*"
    for key in redis_client.scan_iter(pattern):
        redis_client.delete(key)

    return {"detail": "Event deleted successfully"}