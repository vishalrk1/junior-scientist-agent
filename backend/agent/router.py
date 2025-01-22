from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime
from models.agent import Agent, AgentResponse, AgentType, ParameterSchema
from models.project import Project
from auth.dependencies import get_current_user
from database import Database
from bson import ObjectId

router = APIRouter()

@router.get("/projects/{project_id}/agents", response_model=List[AgentResponse])
async def list_project_agents(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    agents_collection = Database.get_agents_collection()
    projects_collection = Database.get_projects_collection()
    project = await Database.execute_with_retry(
        projects_collection,
        'find_one',
        {"_id": ObjectId(project_id), "user_id": str(current_user["_id"])}
    )
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    agents = await Database.execute_with_retry(
        agents_collection,
        'find',
        {"project_id": project_id}
    ).to_list(length=None)
    
    return [AgentResponse(**{**agent, "id": str(agent["_id"])}) for agent in agents]

@router.patch("/projects/{project_id}/agents/{agent_type}", response_model=AgentResponse)
async def update_project_agent(
    project_id: str,
    agent_type: AgentType,
    parameters: ParameterSchema,
    current_user: dict = Depends(get_current_user)
):
    agents_collection = Database.get_agents_collection()
    projects_collection = Database.get_projects_collection()
    project = await Database.execute_with_retry(
        projects_collection,
        'find_one',
        {"_id": ObjectId(project_id), "user_id": str(current_user["_id"])}
    )
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    agent = await Database.execute_with_retry(
        agents_collection,
        'find_one_and_update',
        {
            "project_id": project_id,
            "type": agent_type
        },
        {
            "$set": {
                "parameters": parameters.dict(),
                "updated_at": datetime.utcnow(),
                "is_default": False
            }
        },
        return_document=True
    )
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return AgentResponse(**{**agent, "id": str(agent["_id"])})

@router.post("/projects/{project_id}/agents/{agent_type}/reset", response_model=AgentResponse)
async def reset_agent_to_default(
    project_id: str,
    agent_type: AgentType,
    current_user: dict = Depends(get_current_user)
):
    """Reset agent parameters to project defaults"""
    agents_collection = Database.get_agents_collection()
    projects_collection = Database.get_projects_collection()
    project = await Database.execute_with_retry(
        projects_collection,
        'find_one',
        {"_id": ObjectId(project_id), "user_id": str(current_user["_id"])}
    )
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get default config from project
    default_config = next(
        (config for config in project["default_agent_configs"] 
         if config["agent_type"] == agent_type),
        None
    )
    
    if not default_config:
        default_config = {"parameters": ParameterSchema().dict()}
    
    # Update agent with default parameters
    agent = await Database.execute_with_retry(
        agents_collection,
        'find_one_and_update',
        {
            "project_id": project_id,
            "type": agent_type
        },
        {
            "$set": {
                "parameters": default_config["parameters"],
                "additional_prompt": default_config.get("additional_prompt"),
                "is_default": True,
                "updated_at": datetime.utcnow()
            }
        },
        return_document=True
    )
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return AgentResponse(**{**agent, "id": str(agent["_id"])})
