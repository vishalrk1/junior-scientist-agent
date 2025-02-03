from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import Field, BaseModel
from .base_model import MongoModel
from bson import ObjectId

class Source(BaseModel):
    title: str = Field(..., description="Title of the source document")
    similarity: float = Field(..., description="Similarity score of the source")
    
class ChatMessage(BaseModel):
    role: Literal['ai', 'user'] = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    source: Optional[List[Source]] = Field(None, description="Source of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "role": "ai",
                "content": "Hello! How can I help you today?",
                "timestamp": "2024-01-20T12:00:00"
            }
        }

class RagSession(MongoModel):
    id: Optional[str] = Field(default=None, alias="_id")
    api_key: Optional[str] = Field(None, description="API key for the RAG session")
    user_id: str = Field(..., description="ID of the user who owns this session")
    title: str = Field(..., description="Title of the RAG session")
    description: Optional[str] = Field(None, description="Description of the session")
    messages: List[ChatMessage] = Field(default_factory=list)  # Changed from chats to messages
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    documents: List[str] = Field(default_factory=list, description="List of document titles used in this session")
    settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "temperature": 0.85,
            "max_context_length": 2000,
            "similarity_threshold": 0.4,
        }
    )
    
    @property
    def collection_name(self) -> str:
        return "rag_sessions"
    
    def to_response(self) -> 'RagSessionResonse':
        return RagSessionResonse(
            id=str(self.id) if self.id else None,
            title=self.title,
            description=self.description,
            messages=self.messages,
            created_at=self.created_at,
            updated_at=self.updated_at,
            documents=self.documents,
            settings=self.settings
        )

    @classmethod
    def parse_obj(cls, obj):
        if "_id" in obj and isinstance(obj["_id"], ObjectId):
            obj["_id"] = str(obj["_id"])
        return super().parse_obj(obj)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }

class RagSessionResonse(BaseModel):
    id: str = Field(..., description="ID of the RAG session")
    title: str = Field(..., description="Title of the RAG session")
    description: Optional[str] = Field(None, description="Description of the session")
    messages: List[ChatMessage] = Field(default_factory=list)  # Changed from chats to messages
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    documents: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "temperature": 0.7,
            "max_context_length": 4000,
            "similarity_threshold": 0.4,
        }
    )

    class Config:
        schema_extra = {
            "example": {
                "id": "60c7b6d2b5f3f1f4b6f9b3e1",
                "title": "Sample RAG Session",
                "description": "This is a sample RAG session",
                "messages": [
                    {
                        "role": "ai",
                        "content": "Hello! How can I help you today?",
                        "timestamp": "2024-01-20T12:00:00"
                    },
                    {
                        "role": "user",
                        "content": "Can you analyze this document for me?",
                        "timestamp": "2024-01-20T12:00:05"
                    }
                ],
                "created_at": "2024-01-20T12:00:00",
                "updated_at": "2024-01-20T12:00:05",
                "documents": ["sample_document.pdf"],
                "settings": {
                    "temperature": 0.7,
                    "max_context_length": 4000,
                    "similarity_threshold": 0.4,
                }
            }
        }