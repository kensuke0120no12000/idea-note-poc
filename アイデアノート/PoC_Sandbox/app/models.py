from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base

class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String, index=True)
    raw_event = Column(JSON)
    status = Column(String, default="processed") # "processed", "error", "pending"
    notes = Column(String, nullable=True) 