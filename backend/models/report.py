from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

from .base_model import MongoModel
from .agent import AgentType

class ReportType(str, Enum):
    data_analysis = "data_analysis"
    model_evaluation = "model_evaluation"
    feature_importance = "feature_importance"
    performance_metrics = "performance_metrics"
    code_snippet = "code_snippet"
    visualization = "visualization"
    recommendation = "recommendation"

class ReportStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class Report(MongoModel):
    project_id: str = Field(title="Project ID")
    agent_type: AgentType = Field(title="Agent Type")
    file_path: str = Field(title="Report File Path")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    conversation_id: Optional[str] = None
    
    @property
    def collection_name(self) -> str:
        return "reports"
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "project123",
                "agent_type": "analyzer",
                "file_path": "/reports/analysis_123.pkl",
                "metadata": {"dataset": "iris.csv"},
                "summary": "Analysis of iris dataset"
            }
        }
