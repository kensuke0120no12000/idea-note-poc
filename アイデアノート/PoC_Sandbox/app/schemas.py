from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

# ベースモデル
class EventLogIn(BaseModel):
    event_type: str
    raw_event: Dict[str, Any]
    notes: Optional[str] = None

# DBから読みだした際のモデル
class EventLogOut(EventLogIn):
    id: int
    timestamp: datetime
    status: str

    model_config = ConfigDict(from_attributes=True) 