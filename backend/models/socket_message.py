from pydantic import BaseModel
from typing import Optional, Any, Literal
from datetime import datetime

class SocketMessage(BaseModel):
    type: Literal["message", "error", "info", "initialize", "loading"]
    content: Any
    timestamp: datetime = datetime.utcnow()
    session_id: Optional[str] = None