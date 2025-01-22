# POST /projects - Create new project
# GET /projects - List all projects
# GET /projects/{project_id} - Get single project
# PATCH /projects/{project_id} - Update project
# POST /projects/{project_id}/dataset - Add dataset
# DELETE /projects/{project_id} - Delete project

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime
from models.project import (
    Project, ProjectResponse, ProjectUpdate, 
    DatasetSchema, ProjectStatus
)
from models.agent import Agent, AgentType, ParameterSchema
from auth.dependencies import get_current_user
from database import Database
from bson import ObjectId
from config import settings
import base64

from models.project import ProjectAgentConfig
from models.agent import AgentStatus

DEFAULT_AGENT_CONFIGS = {
    AgentType.analyzer: {
        "parameters": {"temperature": 0.6, "max_tokens": 2000},
    },
    AgentType.advisor: {
        "parameters": {"temperature": 0.6, "max_tokens": 1500},
    },
    AgentType.planner: {
        "parameters": {"temperature": 0.6, "max_tokens": 1000},
    },
    AgentType.coder: {
        "parameters": {"temperature": 0.6, "max_tokens": 2500},
        "additional_prompt": "Generate and explain code"
    }
}

router = APIRouter()

@router.post("", response_model=ProjectResponse)
async def create_project(project: Project, current_user: dict = Depends(get_current_user)):
    projects_collection = Database.get_projects_collection()
    agents_collection = Database.get_agents_collection()
    
    async with await Database.client.start_session() as session:
        async with session.start_transaction():
            now = datetime.utcnow()
            
            # Create agent configs first
            default_agent_configs = []
            for agent_type, config in DEFAULT_AGENT_CONFIGS.items():
                agent_config = ProjectAgentConfig(
                    agent_type=agent_type,
                    parameters=ParameterSchema(**config["parameters"]),
                    additional_prompt=config.get("additional_prompt")
                )
                default_agent_configs.append(agent_config)

            project_data = {
                "name": project.name,
                "description": project.description,
                "model_provider": project.model_provider,
                "api_key": base64.b64encode(project.api_key.encode()).decode(),
                "user_id": str(current_user["_id"]),
                "created_at": now,
                "updated_at": now,
                "last_activity": now,
                "status": ProjectStatus.active,
                "conversation_ids": [],
                "report_ids": [],
                "current_conversation_id": None,
                "settings": {
                    "context_size": 10,
                    "max_reports_per_agent": 5,
                    "auto_save_interval": 300
                },
                "default_agent_configs": [config.model_dump() for config in default_agent_configs]
            }

            # Insert project
            result = await Database.execute_with_retry(
                projects_collection,
                'insert_one',
                project_data,
                session=session
            )
            
            project_id = str(result.inserted_id)
            
            # Create agent instances
            agents_to_create = []
            for agent_type, config in DEFAULT_AGENT_CONFIGS.items():
                agent_data = {
                    "project_id": project_id,
                    "type": agent_type,
                    "version": "1.0.0",
                    "parameters": config["parameters"],
                    "additional_prompt": config.get("additional_prompt"),
                    "is_default": True,
                    "status": AgentStatus.active
                }
                agents_to_create.append(agent_data)

            if agents_to_create:
                await Database.execute_with_retry(
                    agents_collection,
                    'insert_many',
                    agents_to_create,
                    session=session
                )

            project_data["id"] = project_id
            return ProjectResponse(**project_data)

@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    current_user: dict = Depends(get_current_user),
    status: Optional[ProjectStatus] = None
):
    projects_collection = Database.get_projects_collection()
    query = {"user_id": str(current_user["_id"])}
    if status:
        query["status"] = status
        
    cursor = projects_collection.find(query).sort("last_activity", -1)
    projects = await Database.execute_with_retry(
        cursor,
        'to_list',
        length=None
    )
    
    return [ProjectResponse(**{**project, "id": str(project["_id"])}) for project in projects]

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    projects_collection = Database.get_projects_collection()
    
    project = await Database.execute_with_retry(
        projects_collection,
        'find_one',
        {
            "_id": ObjectId(project_id),
            "user_id": str(current_user["_id"])
        }
    )
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return ProjectResponse(**{**project, "id": str(project["_id"])})

@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user)
):
    projects_collection = Database.get_projects_collection()
    project = await Database.execute_with_retry(
        projects_collection,
        'find_one',
        {
            "_id": ObjectId(project_id),
            "user_id": str(current_user["_id"])
        }
    )
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    update_dict = update_data.model_dump(exclude_unset=True)
    if "api_key" in update_dict:
        encrypted_key = fernet.encrypt(update_dict["api_key"].get_secret_value().encode())
        update_dict["api_key"] = encrypted_key.decode()
    
    update_dict["updated_at"] = datetime.utcnow()
    update_dict["last_activity"] = datetime.utcnow()
    
    # Update project
    await Database.execute_with_retry(
        projects_collection,
        'update_one',
        {"_id": ObjectId(project_id)},
        {"$set": update_dict}
    )
    
    # Get updated project
    updated_project = await Database.execute_with_retry(
        projects_collection,
        'find_one',
        {"_id": ObjectId(project_id)}
    )
    
    return ProjectResponse(**{**updated_project, "id": str(updated_project["_id"])})

@router.post("/{project_id}/dataset")
async def add_dataset(
    project_id: str,
    dataset: DatasetSchema,
    current_user: dict = Depends(get_current_user)
):
    projects_collection = Database.get_projects_collection()
    project = await Database.execute_with_retry(
        projects_collection,
        'find_one',
        {
            "_id": ObjectId(project_id),
            "user_id": str(current_user["_id"])
        }
    )
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update project with dataset
    await Database.execute_with_retry(
        projects_collection,
        'update_one',
        {"_id": ObjectId(project_id)},
        {
            "$set": {
                "dataset": dataset.model_dump(),
                "updated_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Dataset added successfully"}

@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    projects_collection = Database.get_projects_collection()
    
    result = await Database.execute_with_retry(
        projects_collection,
        'delete_one',
        {
            "_id": ObjectId(project_id),
            "user_id": str(current_user["_id"])
        }
    )
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return {"message": "Project deleted successfully"}
