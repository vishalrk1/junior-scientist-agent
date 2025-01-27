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

DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "gemini": "gemini-pro"
}

AVAILABLE_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
    "gemini": ["gemini-pro", "gemini-pro-vision"]
}

class ProjectSettings(BaseModel):
    context_size: int = Field(default=10, ge=1, le=100)
    max_reports_per_agent: int = Field(default=5, ge=1, le=50)
    auto_save_interval: int = Field(default=300, ge=60, le=3600)
    selected_model: str = Field(default="gpt-4o")

    @classmethod
    def get_defaults(cls, model_provider: str) -> "ProjectSettings":
        return cls(
            context_size=10,
            max_reports_per_agent=5,
            auto_save_interval=300,
            selected_model=DEFAULT_MODELS.get(model_provider, DEFAULT_MODELS['openai'])
        )

    def update(self, new_settings: Dict[str, Any]) -> None:
        for key, value in new_settings.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Project(MongoModel):
    name: str = Field(title="Project Name")
    description: Optional[str] = Field(title="Project Description", default=None)
    model_provider: ModelProviders = Field(title="Model Provider")
    api_key: str = Field(title="API Key")
    status: ProjectStatus = Field(default=ProjectStatus.active)
    dataset: Optional[DatasetSchema] = None
    settings: ProjectSettings = Field(default_factory=lambda: ProjectSettings())
    conversation_ids: List[str] = Field(default_factory=list)
    report_ids: List[str] = Field(default_factory=list)
    current_conversation_id: Optional[str] = None
    project_dir: Optional[str] = None

    def __init__(self, **data):
        if 'settings' not in data:
            data['settings'] = ProjectSettings.get_defaults(
                data.get('model_provider', 'openai')
            )
        elif isinstance(data['settings'], dict):
            data['settings'] = ProjectSettings(**data['settings'])
        super().__init__(**data)

    def update_settings(self, new_settings: Dict[str, Any]):
        """Update project settings while maintaining defaults"""
        self.settings.update(new_settings)
        return self.settings

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
    settings: ProjectSettings
    available_models: List[str] = Field(default_factory=list)

    def __init__(self, **data):
        data["available_models"] = AVAILABLE_MODELS.get(data.get("model_provider"), [])
        super().__init__(**data)

    @classmethod
    def from_db(cls, db_data: dict) -> "ProjectResponse":
        if "settings" not in db_data or not db_data["settings"]:
            db_data["settings"] = ProjectSettings.get_defaults(
                db_data.get("model_provider", "openai")
            ).dict()
        elif isinstance(db_data["settings"], dict):
            default_settings = ProjectSettings.get_defaults(
                db_data.get("model_provider", "openai")
            ).dict()
            default_settings.update(db_data["settings"])
            db_data["settings"] = ProjectSettings(**default_settings)

        if "default_agent_configs" in db_data:
            db_data["default_agent_configs"] = [
                ProjectAgentConfig(**config) if isinstance(config, dict) else config 
                for config in db_data["default_agent_configs"]
            ]
        
        if "available_models" not in db_data:
            provider = db_data.get("model_provider", "openai")
            db_data["available_models"] = AVAILABLE_MODELS.get(provider, [])
        
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
    settings: Optional[ProjectSettings] = None