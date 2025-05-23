from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None

class EventBatchCreate(BaseModel):
    events: List[EventCreate]

class EventOccurence(BaseModel):
    start_time: datetime
    end_time: datetime

class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    owner_id: int
    occurences: Optional[list[EventOccurence]] = None

    class Config:
        from_attributes = True

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None