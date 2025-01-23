from fastapi import APIRouter, HTTPException, WebSocket, Depends
from typing import Dict, Any, List
from pydantic import BaseModel

from backend.managers.workflow_manager import WorkflowManager
from backend.models.project import Project, ProjectStatus
from backend.models.conversation import Conversation, Message
from backend.auth.dependencies import get_current_user
from backend.database import Database

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
    conv_coll = await Database.get_collection("conversations")
    conversation = await conv_coll.find_one({"project_id": project_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.websocket("/{project_id}/ws")
async def workflow_websocket(websocket: WebSocket, project_id: str):
    await websocket.accept()
    
    workflow = WorkflowManager(project_id)
    await workflow.initialize()
    
    try:
        while True:
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
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "data": {"message": str(e)}
        })
    finally:
        await websocket.close()
