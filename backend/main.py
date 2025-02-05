from buddy.agents import AnalyzerAgent
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from api import workflow
from database import Database
from auth.router import router as auth_router
from project.router import router as project_router
from agent.router import router as agents_router
from rag.routes import router as rag_router
from models.socket_message import SocketMessage
from managers.socket_manager import SocketManager
from session_store import RAG_SESSIONS
from auth.dependencies import get_current_user

MAX_CONNECTIONS_PER_USER = 5

@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.connect_db()
    await socket_manager.start_cleanup_task()
    yield
    await Database.close_db()

app = FastAPI(title="Junior Data Scientist Agent API", lifespan=lifespan)

@app.get("/health")
async def health_check():
    if await Database.check_connection():
        return {"status": "healthy", "database": "connected"}
    raise HTTPException(status_code=503, detail="Database connection failed")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socket_manager = SocketManager()

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(project_router, prefix="/projects", tags=["Projects"])
app.include_router(agents_router, prefix="/api", tags=["agents"])
app.include_router(rag_router, prefix="/rag", tags=["RAG"])
app.include_router(workflow.router, prefix="/workflow")

@app.websocket("/ws/{session_id}/chat")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str, 
    token: str = None
):
    if not token:
        await websocket.close(code=4001, reason="No authentication token provided")
        return
        
    try:
        user = await get_current_user(token)
        print("User: ", user)
    except HTTPException:
        await websocket.close(code=4001, reason="Invalid authentication token")
        return
        
    user_id = str(user["_id"])
    
    if (user_id in socket_manager.user_sessions and 
        len(socket_manager.user_sessions[user_id]) >= MAX_CONNECTIONS_PER_USER):
        await websocket.close(code=4001, reason="Too many active sessions")
        return
    
    try:
        rag_system = RAG_SESSIONS.get(session_id)
        if not rag_system:
            await websocket.close(code=4000, reason="Invalid session")
            return
            
        await socket_manager.connect(websocket, session_id, rag_system, user_id)
        
        try:
            while True:
                data = await websocket.receive_json()
                if "message" in data:
                    await socket_manager.handle_chat_message(
                        websocket, 
                        session_id, 
                        data["message"]
                    )
                elif data.get("type") == "ping":
                    await socket_manager.update_activity(session_id)
                    await websocket.send_json({"type": "pong"})
                    
        except WebSocketDisconnect:
            await socket_manager.disconnect(websocket, session_id)
            
    except Exception as e:
        error_message = SocketMessage(
            type="error",
            content=str(e),
            session_id=session_id
        )
        await socket_manager.send_message(websocket, error_message)
    finally:
        await socket_manager.disconnect(websocket, session_id)
