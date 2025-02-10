from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from typing import List
from bson import ObjectId

from auth.dependencies import get_current_user
from database import Database
from session_store import SessionStore

from models.rag import RagSession, ChatMessage, Source, RagSessionResonse, SettingsConfig
from rag.rag_system import RagSystem

router = APIRouter()

@router.post("/session", response_model=RagSessionResonse)
async def create_session(
    data: RagSession,
    user = Depends(get_current_user)
): 
    try:
        settings = SettingsConfig()
        session_dict = {
            "user_id": data.user_id,
            "api_key": data.api_key,
            "title": data.title,
            "description": data.description,
            "documents": [],
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "settings": settings.__dict__
        }

        collection = await Database.get_collection("rag_sessions")
        result = await collection.insert_one(session_dict)
        session_id = str(result.inserted_id)
        session_dict["_id"] = session_id
        
        rag_system = RagSystem(
            api_key=data.api_key,
            session_id=session_id,
            settings=settings
        )
        
        SessionStore.set_session(session_id, rag_system)
        session = RagSession.parse_obj(session_dict)
        return session.to_response()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.post("/{session_id}/upload")
async def upload_files(
    session_id: str,
    files: List[UploadFile] = File(...),
    user = Depends(get_current_user)
):
    collection = await Database.get_collection("rag_sessions")
    session_doc = await collection.find_one({
        "_id": ObjectId(session_id), 
        "user_id": str(user["_id"])
    })
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    session = RagSession.parse_obj(session_doc)

    rag_system = SessionStore.get_session(session_id)
    if not rag_system:
        rag_system = RagSystem(
            api_key=session.api_key,
            session_id=session_id,
            settings=session.settings
        )
        SessionStore.set_session(session_id, rag_system)

    try:
        processed_files = []
        for file in files:
            processed_files.append(file.filename)
        
        total_chunks = await rag_system.process_files(files)
        print(f"Processed {len(files)} files into {total_chunks} chunks")

        await collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$push": {"documents": {"$each": processed_files}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return {"message": f"Processed {len(files)} files into {total_chunks} chunks"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_chat_history(user = Depends(get_current_user)):
    collection = await Database.get_collection("rag_sessions")
    cursor = collection.find({"user_id": str(user["_id"])})
    sessions = []
    async for session in cursor:
        sessions.append(RagSession.parse_obj(session).to_response())
    return sessions[::-1]

@router.get("/session/{session_id}", response_model=RagSessionResonse)
async def get_session(
    session_id: str,
    user = Depends(get_current_user)
):
    collection = await Database.get_collection("rag_sessions")
    session_doc = await collection.find_one({
        "_id": ObjectId(session_id), 
        "user_id": str(user["_id"])
    })
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = RagSession.parse_obj(session_doc)
    return session.to_response()

@router.post("/{session_id}/chat")
async def chat(
    session_id: str,
    data: dict = Body(...),
    user = Depends(get_current_user)
):
    message = data.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    collection = await Database.get_collection("rag_sessions")
    session_doc = await collection.find_one({
        "_id": ObjectId(session_id), 
        "user_id": str(user["_id"])
    })
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = RagSession.parse_obj(session_doc)

    rag_system = SessionStore.get_session(session_id)
    if not rag_system:
        raise HTTPException(status_code=400, detail="Session not initialized")

    try:
        user_message = ChatMessage(
            role="user",
            content=message,
            timestamp=datetime.utcnow()
        )
        
        response = rag_system.chat(message)
        ai_message = ChatMessage(
            role="ai",
            content=response["answer"],
            source=[Source(title=src["title"], similarity=src["similarity"]) 
                   for src in response["sources"]],
            timestamp=datetime.utcnow()
        )
        
        await collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$push": {
                    "messages": {
                        "$each": [user_message.dict(), ai_message.dict()]
                    }
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return {
            "message": ai_message.content,
            "sources": ai_message.source
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{session_id}/settings", response_model=RagSessionResonse)
async def update_settings(
    session_id: str,
    settings: SettingsConfig,
    user = Depends(get_current_user)
):
    collection = await Database.get_collection("rag_sessions")
    session_doc = await collection.find_one({
        "_id": ObjectId(session_id), 
        "user_id": str(user["_id"])
    })
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not settings.validate_weights():
        raise HTTPException(
            status_code=400, 
            detail="Invalid settings: weights must sum to 1.0"
        )
    
    try:
        await collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "settings": settings.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        rag_system = SessionStore.get_session(session_id)
        if rag_system:
            rag_system.update_settings(settings)
        
        updated_doc = await collection.find_one({"_id": ObjectId(session_id)})
        session = RagSession.parse_obj(updated_doc)
        return session.to_response()
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update settings: {str(e)}"
        )

