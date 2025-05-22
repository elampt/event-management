from sqlalchemy import Column, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base
import enum

class RoleEnum(str, enum.Enum):
    owner = "Owner"
    editor = "Editor"
    viewer = "Viewer"

class EventPermission(Base):
    __tablename__ = "event_permissions"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(Enum(RoleEnum), nullable=False)

    event = relationship("Event", back_populates="permissions")
    user = relationship("User", back_populates="permissions")