from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class EventVersionSchema(BaseModel):
    id: int
    event_id: int
    version: int
    data: dict
    changed_by: int
    changed_at: datetime
    change_note: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v
        }

class EventChangelogSchema(BaseModel):
    id: int
    event_id: int
    version_id: int
    diff: dict
    changed_by: int
    changed_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v
        }

class EventDiffResponse(BaseModel):
    diff: dict

class EventChangelogResponse(BaseModel):
    id: int
    event_id: int
    version_id: int
    diff: dict
    changed_by: int
    changed_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v
        }

class EventDiffResponse(BaseModel):
    diff: Dict[str, Any]