import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from typing import List
from bson import ObjectId
from io import BytesIO

from models.rag import RagSession, ChatMessage, Source, RagSessionResonse
from rag.rag_system import RagSystem
from auth.dependencies import get_current_user
from database import Database

router = APIRouter()
RAG_SESSIONS = {}  # In-memory store of active RAG systems

@router.post("/session", response_model=RagSessionResonse)
async def create_session(
    data: RagSession,
    user = Depends(get_current_user)
): 
    try:
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
        
        session_dict = {
            "user_id": data.user_id,
            "api_key": data.api_key,
            "title": data.title,
            "description": data.description,
            "documents": [],
            "messages": [msg.dict() for msg in initial_messages],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "settings": data.settings
        }

        collection = await Database.get_collection("rag_sessions")
        result = await collection.insert_one(session_dict)
        
        session_dict["_id"] = str(result.inserted_id)
        session = RagSession.parse_obj(session_dict)
        
        RAG_SESSIONS[str(session.id)] = RagSystem(
            api_key=data.api_key,
            session_id=str(session.id)
        )
        
        return session.to_response()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.post("/{session_id}/upload")
async def upload_files(
    session_id: str,
    files: List[UploadFile] = File(...),
    user = Depends(get_current_user)
):
    print("User: ", user)
    collection = await Database.get_collection("rag_sessions")
    session_doc = await collection.find_one({
        "_id": ObjectId(session_id), 
        "user_id": str(user["_id"])
    })
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    session = RagSession.parse_obj(session_doc)

    rag_system = RAG_SESSIONS.get(session_id)
    if not rag_system:
        rag_system = RagSystem(
            api_key=session.api_key,
            session_id=session_id
        )
        RAG_SESSIONS[session_id] = rag_system

    try:
        processed_files = []
        total_chunks = 0
        for file in files:
            content = await file.read()
            file_obj = BytesIO(content)
            file_obj.name = file.filename
            chunks = rag_system.process_one_file(file_obj)
            total_chunks += len(chunks)
            processed_files.append(file.filename)
            await file.seek(0)

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

@router.post("/{session_id}/chat")
async def chat(
    session_id: str,
    data: dict = Body(...),  # Change this line
    user = Depends(get_current_user)
):
    """Chat with a RAG session"""
    message = data.get("message")  # Extract message from request body
    print(">>> USer Query: ", message)
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
    print(">>> Session Found: ", session)

    rag_system = RAG_SESSIONS.get(session_id)
    if not rag_system:
        raise HTTPException(status_code=400, detail="Session not initialized")

    try:
        user_message = ChatMessage(
            role="user",
            content=message,
            timestamp=datetime.utcnow()
        )
        
        response = rag_system.chat(message)
        print(">>> AI Response: ", response)
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
