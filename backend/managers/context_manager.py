from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from backend.models.conversation import Conversation, Message
from backend.models.agent import AgentType
from backend.database import Database

class ContextManager:
    def __init__(self, project_id: str, context_window: int = 10):
        self.project_id = project_id
        self.context_window = context_window
        self.conversation_cache: Dict[str, List[Message]] = {}
        self.agent_contexts: Dict[AgentType, Dict[str, Any]] = {}
        
    async def load_conversation_context(self, conversation_id: str) -> List[Message]:
        """Load conversation context from database"""
        if conversation_id in self.conversation_cache:
            return self.conversation_cache[conversation_id]

        conv_coll = await Database.get_collection("conversations")
        conversation = await conv_coll.find_one({"_id": conversation_id})
        
        if not conversation:
            return []
            
        messages = conversation.get("messages", [])[-self.context_window:]
        self.conversation_cache[conversation_id] = messages
        return messages

    async def get_agent_context(self, agent_type: AgentType, conversation_id: str) -> Dict[str, Any]:
        """Get context for specific agent type"""
        if agent_type not in self.agent_contexts:
            self.agent_contexts[agent_type] = {}

        key = f"{conversation_id}_{agent_type.value}"
        if key in self.agent_contexts[agent_type]:
            return self.agent_contexts[agent_type][key]

        # Load agent-specific messages
        messages = await self.load_conversation_context(conversation_id)
        agent_messages = [m for m in messages if m.type == agent_type]
        
        # Load related reports
        reports_coll = await Database.get_collection("reports")
        recent_reports = await reports_coll.find({
            "project_id": self.project_id,
            "agent_type": agent_type.value,
            "created_at": {"$gt": datetime.utcnow() - timedelta(days=7)}
        }).limit(5).to_list(length=5)

        context = {
            "recent_messages": agent_messages,
            "recent_reports": recent_reports,
            "conversation_id": conversation_id
        }
        
        self.agent_contexts[agent_type][key] = context
        return context

    async def update_context(self, message: Message, conversation_id: str):
        """Update context with new message"""
        if conversation_id in self.conversation_cache:
            self.conversation_cache[conversation_id].append(message)
            if len(self.conversation_cache[conversation_id]) > self.context_window:
                self.conversation_cache[conversation_id].pop(0)

        # Update agent context
        key = f"{conversation_id}_{message.type.value}"
        if message.type in self.agent_contexts and key in self.agent_contexts[message.type]:
            self.agent_contexts[message.type][key]["recent_messages"].append(message)

    async def clear_cache(self):
        """Clear context caches"""
        self.conversation_cache.clear()
        self.agent_contexts.clear()
