from typing import Dict, Any
from models.rag import Any
from rag.rag_system import RagSystem

class SessionStore:
    _sessions: Dict[str, RagSystem] = {}
    
    @classmethod
    def get_session(cls, session_id: str) -> Any:
        return cls._sessions.get(session_id)
    
    @classmethod
    def set_session(cls, session_id: str, session: RagSystem) -> None:
        cls._sessions[session_id] = session
    
    @classmethod
    def remove_session(cls, session_id: str) -> None:
        cls._sessions.pop(session_id, None)