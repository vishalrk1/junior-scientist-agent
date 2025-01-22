from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

from .base_model import MongoModel
from .conversation import MessageType

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
    type: ReportType = Field(title="Report Type")
    name: str = Field(title="Report Name")
    description: Optional[str] = Field(title="Report Description")
    status: ReportStatus = Field(default=ReportStatus.pending)
    data: Dict[str, Any] = Field(default_factory=dict)
    file_path: Optional[str] = Field(title="File Path for Stored Report")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generated_by: MessageType = Field(title="Agent Type that Generated Report")
    conversation_id: Optional[str] = Field(title="Related Conversation ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def collection_name(self) -> str:
        return "reports"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
