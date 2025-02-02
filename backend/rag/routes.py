import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from typing import List
from bson import ObjectId
from io import BytesIO

from models.rag import RagSession, Chat, Source, RagSessionResonse
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
        session_dict = {
            "user_id": data.user_id,
            "api_key": data.api_key,
            "title": data.title,
            "description": data.description,
            "documents": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "chats": [],
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
    
    print(rag_system)

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
    question: str,
    user = Depends(get_current_user)
):
    """Chat with a RAG session"""
    collection = await Database.get_collection("rag_sessions")
    session_doc = await collection.find_one({
        "_id": ObjectId(session_id), 
        "user_id": user.id
    })
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = RagSession.parse_obj(session_doc)

    rag_system = RAG_SESSIONS.get(session_id)
    if not rag_system:
        raise HTTPException(status_code=400, detail="Session not initialized")

    try:
        response = rag_system.chat(question)
        
        # Save chat to session
        chat = Chat(
            question=question,
            answer=response["answer"],
            sources=[Source(title=src) for src in response["sources"]]
        )
        session.chats.append(chat)
        await session.save()
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
