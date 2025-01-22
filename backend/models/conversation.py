from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from .base_model import MongoModel

class MessageType(str, Enum):
    user = "user"
    analyzer = "analyzer"
    advisor = "advisor"
    planner = "planner"
    coder = "coder"

class Message(BaseModel):
    type: MessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    report_id: Optional[str] = Field(default=None)
    agent_id: Optional[str] = Field(default=None)
    
class Conversation(MongoModel):
    project_id: str = Field(title="Project ID")
    messages: List[Message] = Field(default_factory=list)
    active_agents: List[str] = Field(default_factory=list)  # List of agent IDs
    context_size: int = Field(default=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_recent_messages(self, count: int = None) -> List[Message]:
        if count is None:
            count = self.context_size
        return self.messages[-count:]
    
    def get_agent_history(self, agent_type: MessageType, count: int = None) -> List[Message]:
        if count is None:
            count = self.context_size
        agent_messages = [m for m in self.messages if m.type == agent_type]
        return agent_messages[-count:]
    
    @property
    def collection_name(self) -> str:
        return "conversations"