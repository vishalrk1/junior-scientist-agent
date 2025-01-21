from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ModelProviders(str, Enum):
    openai = "openai"
    gemini = "gemini"

class Project(BaseModel):
    name: str = Field(title="Project Name")
    description: Optional[str] = Field(title="Project Description")
    provider: ModelProviders = Field(title="Model Provider")
    api_key: str = Field(title="API Key")

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    provider: ModelProviders
    api_key: str
    created_at: datetime