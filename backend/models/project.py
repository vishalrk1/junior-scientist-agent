from pydantic import BaseModel, Field, SecretStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from .base_model import MongoModel
from .agent import AgentType, ParameterSchema
from bson import ObjectId

class ModelProviders(str, Enum):
    openai = "openai"
    gemini = "gemini"

class ProjectStatus(str, Enum):
    active = "active"
    archived = "archived"
    completed = "completed"

class DatasetSchema(BaseModel):
    path: str = Field(title="Dataset Path")
    description: Optional[str] = Field(title="Dataset Description")
    schema: Dict[str, Any] = Field(default_factory=dict, title="Dataset Schema")
    statistics: Dict[str, Any] = Field(default_factory=dict, title="Dataset Statistics")

class ProjectAgentConfig(BaseModel):
    agent_type: AgentType
    parameters: ParameterSchema
    additional_prompt: Optional[str] = None

class Project(MongoModel):
    user_id: str = Field(title="User ID")
    name: str = Field(title="Project Name")
    description: Optional[str] = Field(title="Project Description")
    model_provider: ModelProviders = Field(title="Model Provider")
    api_key: SecretStr = Field(title="API Key")
    dataset: Optional[DatasetSchema] = Field(title="Dataset Information")
    status: ProjectStatus = Field(default=ProjectStatus.active, title="Project Status")
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    default_agent_configs: List[ProjectAgentConfig] = Field(
        default_factory=list,
        title="Default Agent Configurations"
    )
    conversation_ids: List[str] = Field(default_factory=list, title="Associated Conversations")
    report_ids: List[str] = Field(default_factory=list, title="Generated Reports")
    current_conversation_id: Optional[str] = Field(title="Current Active Conversation")
    settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "context_size": 10,
            "max_reports_per_agent": 5,
            "auto_save_interval": 300  # 5 minutes
        }
    )

    @property
    def collection_name(self) -> str:
        return "projects"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Science Project 1",
                "description": "My first science project",
                "model_provider": "openai",
                "status": "active",
                "default_agent_configs": [
                    {
                        "agent_type": "analyzer",
                        "parameters": {
                            "temperature": 0.7,
                            "max_tokens": 2000
                        }
                    }
                ]
            }
        }

class ProjectResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    model_provider: ModelProviders
    dataset: Optional[DatasetSchema]
    status: ProjectStatus
    created_at: datetime
    updated_at: Optional[datetime]
    last_activity: datetime
    default_agent_configs: List[ProjectAgentConfig]
    conversation_ids: List[str]
    report_ids: List[str]
    current_conversation_id: Optional[str]
    settings: Dict[str, Any]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            SecretStr: lambda v: "**********"  # Hide API key in responses
        }

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_provider: Optional[ModelProviders] = None
    api_key: Optional[SecretStr] = None
    dataset: Optional[DatasetSchema] = None
    status: Optional[ProjectStatus] = None