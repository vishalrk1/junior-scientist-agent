from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .base_model import MongoModel
from .conversation import Conversation

class AgentType(str, Enum):
    analyzer = "analyzer"
    advisor = "advisor"
    planner = "planner"
    coder = "coder"
    
class AgentStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    
class ParameterSchema(BaseModel):
    temperature: float = Field(title="Temperature", default=0.6)
    max_tokens: int = Field(title="Max Tokens", default=2000)

class Agent(MongoModel):
    project_id: str = Field(title="Project ID")
    version: str = Field(title="Agent Version")
    type: AgentType = Field(title="Agent Type")
    status: AgentStatus = Field(title="Agent Status", default=AgentStatus.active)
    parameters: ParameterSchema = Field(title="Agent Parameters")
    additional_prompt: Optional[str] = Field(title="Additional Prompt", default=None)
    is_default: bool = Field(default=False, title="Is Default Configuration")
    context_size: int = Field(default=10)
    last_conversation_id: Optional[str] = Field(default=None)
    last_reports: List[str] = Field(default_factory=list)  # Keep track of recently generated reports
    
    def get_context(self, conversation: Conversation) -> Dict[str, Any]:
        """Get agent's working context from conversation"""
        return {
            'recent_messages': conversation.get_agent_history(self.type),
            'last_reports': self.last_reports,
            'current_conversation': conversation.id if conversation else None
        }
    
    @property
    def collection_name(self) -> str:
        return "agents"
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "project123",
                "version": "0.0.1",
                "type": "analyzer",
                "status": "active",
                "parameters": {
                    "temperature": 0.6,
                    "max_tokens": 2000
                },
                "is_default": False
            }
        }

class AgentResponse(BaseModel):
    id: str
    project_id: str
    version: str
    type: AgentType
    status: AgentStatus
    parameters: ParameterSchema
    additional_prompt: Optional[str]
    is_default: bool
    context_window: int
    memory_key: Optional[str]
    cached_reports: List[str]
    last_conversation_id: Optional[str]
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.timestamp()
        }