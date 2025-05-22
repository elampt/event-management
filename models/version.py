from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

class EventVersion(Base):
    __tablename__ = "event_versions"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    version = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    change_note = Column(String)

    event = relationship("Event", back_populates="versions")