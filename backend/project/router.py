import shutil
# POST /projects - Create new project
# GET /projects - List all projects
# GET /projects/{project_id} - Get single project
# PATCH /projects/{project_id} - Update project
# POST /projects/{project_id}/dataset - Add dataset
# DELETE /projects/{project_id} - Delete project

from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from typing import List, Optional
from datetime import datetime
from models.project import (
    Project, ProjectResponse, ProjectUpdate, 
    DatasetSchema, ProjectStatus, ProjectSettings,
    AVAILABLE_MODELS  # Add this import
)
from models.agent import Agent, AgentType, ParameterSchema
from auth.dependencies import get_current_user
from database import Database
from bson import ObjectId
from config import settings
import base64
import pandas as pd
import os

from models.project import ProjectAgentConfig
from models.agent import AgentStatus
from utils.project_setup import setup_project_directory

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
                "settings": ProjectSettings.get_defaults(project.model_provider).model_dump(),
                "default_agent_configs": [config.model_dump() for config in default_agent_configs],
                "available_models": AVAILABLE_MODELS.get(str(project.model_provider), []),
            }

            result = await Database.execute_with_retry(
                projects_collection,
                'insert_one',
                project_data,
                session=session
            )
            
            project_id = str(result.inserted_id)
            try:
                project_dir = setup_project_directory(
                    project_id=project_id,
                    platform=project.model_provider,
                    api_key=project.api_key
                )
                await Database.execute_with_retry(
                    projects_collection,
                    'update_one',
                    {"_id": ObjectId(project_id)},
                    {"$set": {"project_dir": project_dir}},
                    session=session
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to initialize project workspace"
                )

            default_agent_configs = []
            for agent_type, config in DEFAULT_AGENT_CONFIGS.items():
                agent_config = ProjectAgentConfig(
                    agent_type=agent_type,
                    parameters=ParameterSchema(**config["parameters"]),
                    additional_prompt=config.get("additional_prompt")
                )
                default_agent_configs.append(agent_config)

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
            project_data["project_dir"] = project_dir
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
        
    cursor = projects_collection.find(query).sort("created_at", -1)
    projects = await Database.execute_with_retry(
        cursor,
        'to_list',
        length=None
    )
    
    for project in projects:
        if "settings" not in project:
            project["settings"] = ProjectSettings.get_defaults(
                project.get("model_provider", "openai")
            ).dict()
        elif isinstance(project["settings"], dict):
            default_settings = ProjectSettings.get_defaults(
                project.get("model_provider", "openai")
            ).dict()
            default_settings.update(project["settings"])
            project["settings"] = default_settings
        
        provider = project.get("model_provider", "openai")
        project["available_models"] = AVAILABLE_MODELS.get(provider, [])
            
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
    
    if project:
        provider = project.get("model_provider", "openai")
        project["available_models"] = AVAILABLE_MODELS.get(provider, [])
    
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
        encrypted_key = base64.b64encode(project.api_key.encode()).decode()
        update_dict["api_key"] = encrypted_key.decode()
    update_dict["updated_at"] = datetime.utcnow()
    update_dict["last_activity"] = datetime.utcnow()

    await Database.execute_with_retry(
        projects_collection,
        'update_one',
        {"_id": ObjectId(project_id)},
        {"$set": update_dict}
    )
    updated_project = await Database.execute_with_retry(
        projects_collection,
        'find_one',
        {"_id": ObjectId(project_id)}
    )
    return ProjectResponse(**{**updated_project, "id": str(updated_project["_id"])})

@router.patch("/{project_id}/settings")
async def update_project_settings(
    project_id: str,
    settings: ProjectSettings,
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
        raise HTTPException(status_code=404, detail="Project not found")
    
    if settings.selected_model not in AVAILABLE_MODELS[project['model_provider']]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid model for provider {project['model_provider']}"
        )
    
    await Database.execute_with_retry(
        projects_collection,
        'update_one',
        {"_id": ObjectId(project_id)},
        {
            "$set": {
                "settings": settings.dict(),
                "updated_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
        }
    )
    
    return {"settings": settings.dict()}

@router.post("/{project_id}/dataset")
async def add_dataset(
    project_id: str,
    file: UploadFile = File(...),
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

    try:
        project_dir = project.get("project_dir")
        if not project_dir:
            project_dir = setup_project_directory(
                project_id=project_id,
                platform=project["model_provider"],
                api_key=base64.b64decode(project["api_key"]).decode()
            )
            
        data_dir = os.path.join(project_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        file_path = os.path.join(data_dir, file.filename)
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
            
        # Reset file cursor and read CSV
        await file.seek(0)
        df = pd.read_csv(file_path)
        schema = {
            col: str(dtype) for col, dtype in df.dtypes.items()
        }
        
        statistics = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "missing_values": df.isnull().sum().to_dict()
        }
        
        dataset = DatasetSchema(
            name=file.filename,
            path=file_path,
            description=f"Uploaded file: {file.filename}",
            schema=schema,
            statistics=statistics
        )
        
        # Update project with dataset info and return updated project
        updated_project = await Database.execute_with_retry(
            projects_collection,
            'find_one_and_update',
            {"_id": ObjectId(project_id)},
            {
                "$set": {
                    "dataset": dataset.model_dump(),
                    "updated_at": datetime.utcnow(),
                    "last_activity": datetime.utcnow()
                }
            },
            return_document=True
        )
        
        return {
            "message": "Dataset added successfully",
            "dataset": dataset.model_dump(),
            "project": ProjectResponse(**{**updated_project, "id": str(updated_project["_id"])}).model_dump()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing dataset: {str(e)}"
        )

@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    projects_collection = Database.get_projects_collection()
    agents_collection = Database.get_agents_collection()
    
    async with await Database.client.start_session() as session:
        async with session.start_transaction():
            # First get the project to check its directory
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

            if project.get("project_dir"):
                try:
                    shutil.rmtree(project["project_dir"], ignore_errors=True)
                except Exception as e:
                    print(f"Error deleting project directory: {str(e)}")
                    
            await Database.execute_with_retry(
                agents_collection,
                'delete_many',
                {"project_id": project_id},
                session=session
            )
            conversations_collection = await Database.get_collection("conversations")
            await Database.execute_with_retry(
                conversations_collection,
                'delete_many',
                {"project_id": project_id},
                session=session
            )
            result = await Database.execute_with_retry(
                projects_collection,
                'delete_one',
                {"_id": ObjectId(project_id)},
                session=session
            )

            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )
    
    return {"message": "Project and associated resources deleted successfully"}
