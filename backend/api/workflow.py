from fastapi import APIRouter, HTTPException, WebSocket, Depends, Query, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
from jwt import InvalidTokenError
import jwt
import logging

logger = logging.getLogger(__name__)

from models.agent import Agent
from models.conversation import Conversation, Message
from auth.dependencies import get_current_user
from managers.workflow_manager import WorkflowManager
from auth.jwt import verify_token
from database import Database
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from utils.project_setup import setup_project_directory

router = APIRouter(prefix="/workflow", tags=["workflow"])

class WorkflowRequest(BaseModel):
    dataset_path: str
    requirements: str = None

class WorkflowResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any] = None

@router.post("/{project_id}/analyze")
async def analyze_dataset(
    project_id: str,
    request: WorkflowRequest,
    current_user = Depends(get_current_user)
):
    workflow = WorkflowManager(project_id)
    await workflow.initialize()
    
    try:
        report_path = await workflow.run_analysis(request.dataset_path)
        return WorkflowResponse(
            status="success",
            message="Analysis completed",
            data={"report_path": report_path}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/advice")
async def get_advice(
    project_id: str,
    request: WorkflowRequest,
    current_user = Depends(get_current_user)
):
    workflow = WorkflowManager(project_id)
    await workflow.initialize()
    
    try:
        advice = await workflow.get_advice(request.requirements)
        return WorkflowResponse(
            status="success",
            message="Advice generated",
            data={"advice": advice}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/plan")
async def generate_plan(
    project_id: str,
    current_user = Depends(get_current_user)
):
    workflow = WorkflowManager(project_id)
    await workflow.initialize()
    
    try:
        plan = await workflow.generate_plan()
        return WorkflowResponse(
            status="success",
            message="Plan generated",
            data={"plan": plan}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}/conversation")
async def get_conversation(
    project_id: str,
    current_user = Depends(get_current_user)
):
    try:
        # First check if project exists and user has access
        projects_collection = Database.get_projects_collection()
        project = await projects_collection.find_one({
            "_id": ObjectId(project_id),
            "user_id": str(current_user["_id"])
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Get conversation collection
        conv_coll = await Database.get_collection("conversations")
        
        # Try to find existing conversation
        conversation = await conv_coll.find_one({"project_id": project_id})
        
        if not conversation:
            # Create initial conversation if none exists
            conversation = {
                "project_id": project_id,
                "messages": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await conv_coll.insert_one(conversation)
            conversation["_id"] = result.inserted_id
            
            # Update project with conversation reference
            await projects_collection.update_one(
                {"_id": ObjectId(project_id)},
                {
                    "$set": {
                        "current_conversation_id": str(result.inserted_id),
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"conversation_ids": str(result.inserted_id)}
                }
            )

        return {
            "messages": conversation.get("messages", []),
            "id": str(conversation["_id"]),
            "project_id": project_id,
            "created_at": conversation.get("created_at"),
            "updated_at": conversation.get("updated_at")
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation: {str(e)}"
        )

@router.websocket("/{project_id}/ws")
async def workflow_websocket(
    websocket: WebSocket,
    project_id: str,
    token: Optional[str] = Query(None)
):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        await websocket.accept()
        
        try:
            # Verify token
            user = verify_token(token)
            if not user:
                logger.error(f"Invalid token for WebSocket connection")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            # Verify project access
            projects_collection = Database.get_projects_collection()
            project = await projects_collection.find_one({
                "_id": ObjectId(project_id),
                "user_id": str(user.get("id"))  # Ensure user_id is string
            })
            
            if not project:
                logger.error(f"Project access denied for user {user.get('id')}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            workflow = WorkflowManager(project_id)
            await workflow.initialize()
            
            while True:
                try:
                    data = await websocket.receive_json()
                    if data["type"] == "analyze":
                        report_path = await workflow.run_analysis(data["dataset_path"])
                        await websocket.send_json({
                            "type": "analysis_complete",
                            "data": {"report_path": report_path}
                        })
                    elif data["type"] == "advice":
                        advice = await workflow.get_advice(data["requirements"])
                        await websocket.send_json({
                            "type": "advice_complete",
                            "data": {"advice": advice}
                        })
                    elif data["type"] == "plan":
                        plan = await workflow.generate_plan()
                        await websocket.send_json({
                            "type": "plan_complete",
                            "data": {"plan": plan}
                        })
                    elif data.get("type") == "system" and data.get("messages"):
                        # Save initial messages to conversation
                        conv_coll = await Database.get_collection("conversations")
                        conversation = await conv_coll.find_one({"project_id": project_id})
                        
                        if not conversation:
                            # Create new conversation with project reference
                            conversation = {
                                "project_id": project_id,
                                "messages": [],
                                "created_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow()
                            }
                            result = await conv_coll.insert_one(conversation)
                            conversation_id = result.inserted_id
                            
                            # Update project with conversation reference
                            await Database.get_projects_collection().update_one(
                                {"_id": ObjectId(project_id)},
                                {
                                    "$set": {"current_conversation_id": str(conversation_id)},
                                    "$push": {"conversation_ids": str(conversation_id)}
                                }
                            )
                        else:
                            conversation_id = conversation["_id"]

                        # Add messages to conversation
                        messages_to_add = []
                        for msg in data["messages"]:
                            message = {
                                "id": str(ObjectId()),
                                "type": msg["type"],
                                "content": msg["content"],
                                "timestamp": datetime.utcnow(),
                                "dataset": msg.get("dataset")
                            }
                            messages_to_add.append(message)
                            # Send message to client
                            await websocket.send_json({
                                "type": "message",
                                "messageType": msg["type"],
                                "content": msg["content"],
                                "dataset": msg.get("dataset")
                            })

                        # Update conversation in database
                        await conv_coll.update_one(
                            {"_id": conversation_id},
                            {
                                "$push": {"messages": {"$each": messages_to_add}},
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)}
                    })

        except jwt.InvalidTokenError:
            logger.error("Invalid token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        if not websocket.client_state.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
