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
    name: str = Field(title="Project Name")
    description: Optional[str] = Field(title="Project Description", default=None)
    model_provider: ModelProviders = Field(title="Model Provider")
    api_key: str = Field(title="API Key")  # Changed from SecretStr to str
    status: ProjectStatus = Field(default=ProjectStatus.active)
    dataset: Optional[DatasetSchema] = None
    settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "context_size": 10,
            "max_reports_per_agent": 5,
            "auto_save_interval": 300
        }
    )
    conversation_ids: List[str] = Field(default_factory=list)
    report_ids: List[str] = Field(default_factory=list)
    current_conversation_id: Optional[str] = None

    @property
    def collection_name(self) -> str:
        return "projects"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Science Project 1",
                "description": "My first science project",
                "model_provider": "openai",
                "api_key": "your-api-key-here"
            }
        }

class ProjectResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    model_provider: ModelProviders
    dataset: Optional[DatasetSchema] = None
    status: ProjectStatus = ProjectStatus.active
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_activity: datetime
    default_agent_configs: List[ProjectAgentConfig] = Field(default_factory=list)
    conversation_ids: List[str] = Field(default_factory=list)
    report_ids: List[str] = Field(default_factory=list)
    current_conversation_id: Optional[str] = None
    settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "context_size": 10,
            "max_reports_per_agent": 5,
            "auto_save_interval": 300
        }
    )

    @classmethod
    def from_db(cls, db_data: dict) -> "ProjectResponse":
        if "default_agent_configs" in db_data:
            db_data["default_agent_configs"] = [
                ProjectAgentConfig(**config) if isinstance(config, dict) else config 
                for config in db_data["default_agent_configs"]
            ]
        return cls(**db_data)

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