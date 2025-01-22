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
from cryptography.fernet import Fernet
from config import settings

router = APIRouter()
fernet = Fernet(settings.ENCRYPTION_KEY.encode())

@router.post("", response_model=ProjectResponse)
async def create_project(project: Project, current_user: dict = Depends(get_current_user)):
    projects_collection = Database.get_projects_collection()
    agents_collection = Database.get_agents_collection()
    
    async with await Database.client.start_session() as session:
        async with session.start_transaction():
            project_data = project.model_dump()
            project_data["user_id"] = str(current_user["_id"])
            project_data["created_at"] = datetime.utcnow()
            project_data["last_activity"] = datetime.utcnow()

            encrypted_key = fernet.encrypt(project_data["api_key"].get_secret_value().encode())
            project_data["api_key"] = encrypted_key.decode()

            result = await Database.execute_with_retry(
                projects_collection,
                'insert_one',
                project_data,
                session=session
            )
            
            project_id = str(result.inserted_id)

            # Create default agents for the project
            default_agents = []
            for agent_type in AgentType:
                agent_config = next(
                    (config for config in project.default_agent_configs 
                     if config.agent_type == agent_type), 
                    None
                )
                
                agent_data = {
                    "project_id": project_id,
                    "type": agent_type,
                    "version": "1.0.0",
                    "parameters": agent_config.parameters.model_dump() if agent_config else ParameterSchema().model_dump(),
                    "additional_prompt": agent_config.additional_prompt if agent_config else None,
                    "is_default": True
                }
                default_agents.append(Agent(**agent_data))

            if default_agents:
                await Database.execute_with_retry(
                    agents_collection,
                    'insert_many',
                    [agent.dict() for agent in default_agents],
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
    
    # Build query
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
