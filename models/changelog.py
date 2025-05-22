from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

class EventChangelog(Base):
    __tablename__ = "event_changelog"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    version_id = Column(Integer, ForeignKey("event_versions.id"))
    diff = Column(JSON, nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="changelogs")