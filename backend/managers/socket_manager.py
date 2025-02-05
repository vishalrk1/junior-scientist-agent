from fastapi import FastAPI, WebSocket
from datetime import datetime, timedelta
import asyncio
import json
from bson import ObjectId
from typing import Dict, List, Set
from models.socket_message import SocketMessage
from models.rag import ChatMessage, Source
from rag.rag_system import RagSystem
from database import Database

class SocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.rag_systems: Dict[str, RagSystem] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self.last_activity: Dict[str, datetime] = {}  # session_id -> last activity time
        self.cleanup_task = None
        self.session_timeout = timedelta(hours=1)
    
    async def start_cleanup_task(self):
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())

    async def _cleanup_inactive_sessions(self):
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes
            current_time = datetime.utcnow()
            inactive_sessions = [
                session_id for session_id, last_active in self.last_activity.items()
                if current_time - last_active > self.session_timeout
            ]
            for session_id in inactive_sessions:
                await self.cleanup_session(session_id)

    async def cleanup_session(self, session_id: str):
        if session_id in self.active_connections:
            connections = self.active_connections[session_id].copy()
            for websocket in connections:
                await self.disconnect(websocket, session_id)
        
        self.last_activity.pop(session_id, None)
        if session_id in self.rag_systems:
            del self.rag_systems[session_id]
        
        for user_id, sessions in self.user_sessions.items():
            if session_id in sessions:
                sessions.remove(session_id)
                break

    async def connect(self, websocket: WebSocket, session_id: str, rag_system: RagSystem, user_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
            
        self.active_connections[session_id].append(websocket)
        self.rag_systems[session_id] = rag_system
        self.last_activity[session_id] = datetime.utcnow()
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)
        
        initial_messages = [
            ChatMessage(
                role="ai",
                content="👋 Hello! I'm your Document Analysis Assistant.",
                timestamp=datetime.utcnow(),
                source=[]
            ),
            ChatMessage(
                role="ai",
                content="I have gone through your documents and I'm ready to help you with any questions you have.",
                timestamp=datetime.utcnow(),
                source=[]
            )
        ]
        
        collection = await Database.get_collection("rag_sessions")
        await collection.update_one(
            {
                "_id": ObjectId(session_id)
            }, 
            {
                "$push": {"messages": {"$each": [msg.model_dump() for msg in initial_messages]}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )      
        
        for msg in initial_messages:
            await self.send_message(
                websocket,
                SocketMessage(
                    type="initialize",
                    content=msg.dict(),
                    session_id=session_id
                )
            )
    
    async def disconnect(self, websocket: WebSocket, session_id: str):
        await websocket.close()
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                if session_id in self.rag_systems:
                    del self.rag_systems[session_id]
    
    async def send_message(self, websocket: WebSocket, message: SocketMessage):
        await websocket.send_text(message.json())
    
    async def broadcast(self, session_id: str, message: SocketMessage):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await self.send_message(connection, message)
    
    async def send_loading_status(self, session_id: str, is_loading: bool):
        loading_message = SocketMessage(
            type="loading",
            content={"is_loading": is_loading},
            session_id=session_id
        )
        await self.broadcast(session_id, loading_message)

    async def update_activity(self, session_id: str):
        self.last_activity[session_id] = datetime.utcnow()

    async def handle_chat_message(self, websocket: WebSocket, session_id: str, message: str):
        await self.update_activity(session_id)
        try:
            rag_system = self.rag_systems.get(session_id)
            if not rag_system:
                raise ValueError("RAG system not found for this session")
            
            await self.send_loading_status(session_id, True)
            
            response = rag_system.chat(message)
            ai_message = ChatMessage(
                role="ai",
                content=response["answer"],
                source=[Source(title=src["title"], similarity=src["similarity"]) 
                    for src in response["sources"]],
                timestamp=datetime.utcnow()
            )
            user_message = ChatMessage(
                role="user",
                content=message,
                timestamp=datetime.utcnow()
            )
            
            # updating Db with user and AI messages
            collection = await Database.get_collection("rag_sessions")
            await collection.update_one(
                {
                    "_id": ObjectId(session_id)
                }, 
                {
                    "$push": {"messages": {"$each": [user_message.model_dump(), ai_message.model_dump()]}},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            response_message = SocketMessage(
                type="message",
                content=ai_message.model_dump(),
                session_id=session_id
            )
            
            await self.broadcast(session_id, response_message)
            await self.send_loading_status(session_id, False)
            
        except Exception as e:
            await self.send_loading_status(session_id, False)
            error_message = SocketMessage(
                type="error",
                content=str(e),
                session_id=session_id
            )
            await self.send_message(websocket, error_message)