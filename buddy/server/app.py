from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import shutil
import os
import yaml
from datetime import datetime
from pathlib import Path

from buddy.model import load_model
from buddy.agents import AdviseAgent, AnalyzerAgent, PlannerAgent
from buddy.utils import dataframe_validator, print_in_box, ask_text
from buddy.workflow.base import base

app = FastAPI(
    title="Data Buddy API",
    description="API for interacting with Data Science Buddy agents",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DatasetRequest(BaseModel):
    data_path: str
    requirements: Optional[str] = None

class AnalysisResponse(BaseModel):
    dataset_hash: str
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class RequirementRequest(BaseModel):
    dataset_hash: str
    requirements: str

class PlanRequest(BaseModel):
    dataset_hash: str
    model_suggestion: Optional[str] = None

class UpdateAdvisorRequest(BaseModel):
    dataset_hash: str
    question: str

class UpdatePlanRequest(BaseModel):
    dataset_hash: str
    changes: Dict[str, Any]

class ProjectCreate(BaseModel):
    name: str
    platform: str = "openai"
    api_key: Optional[str] = None

class DatasetUpload(BaseModel):
    project_name: str
    
class ProjectResponse(BaseModel):
    name: str
    status: str
    config_path: str

active_sessions = {}
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)

def get_project_path(project_name: str) -> Path:
    return PROJECTS_DIR / project_name

def get_project_config(project_name: str) -> dict:
    config_path = get_project_path(project_name) / ".databuddy" / "config.yml"
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Project configuration not found")
    with open(config_path) as f:
        return yaml.safe_load(f)

@app.post("/api/initialize", response_model=Dict[str, str])
async def initialize_session(background_tasks: BackgroundTasks):
    """Initialize a new session with the agents"""
    try:
        model = load_model(work_dir=".", model=None)
        session_id = str(len(active_sessions) + 1)
        
        active_sessions[session_id] = {
            "model": model,
            "analyzer": AnalyzerAgent(model),
            "advisor": AdviseAgent(model),
            "planner": PlannerAgent(model),
            "websocket": None
        }
        
        return {"session_id": session_id, "status": "initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_dataset(request: DatasetRequest, session_id: str):
    """Analyze the dataset using the AnalyzerAgent"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        df = dataframe_validator(request.data_path)
        analyzer = active_sessions[session_id]["analyzer"]
        result = analyzer.analyze_data(df)
        
        return {
            "dataset_hash": result.dataset_hash,
            "results": [r.__dict__ for r in result.results],
            "metadata": result.metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/advise")
async def get_advice(request: RequirementRequest, session_id: str):
    """Get advice from the AdvisorAgent"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        advisor = active_sessions[session_id]["advisor"]
        result = advisor.chat(request.requirements)
        return {"advice": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/plan")
async def create_plan(request: PlanRequest, session_id: str):
    """Generate ML plan using the PlannerAgent"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        planner = active_sessions[session_id]["planner"]
        plan = planner.generate_plan(model_or_algorithm=request.model_suggestion)
        return {"plan": plan.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle CSV file uploads"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"filename": filename, "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/advisor/update")
async def update_advisor_report(request: UpdateAdvisorRequest, session_id: str):
    """Update advisor report through continued interaction"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        advisor = active_sessions[session_id]["advisor"]
        result = advisor.chat(request.question)
        updated_report = advisor.json_report
        ws = active_sessions[session_id]["websocket"]

        if ws:
            await ws.send_json({
                "type": "advisor_update",
                "data": updated_report
            })
            
        return {"advice": result, "report": updated_report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/planner/update")
async def update_plan_report(request: UpdatePlanRequest, session_id: str):
    """Update planner report with modifications"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        planner = active_sessions[session_id]["planner"]
        updated_plan = await handle_planner_action(
            planner, 
            "plan", 
            {"model_suggestion": request.changes.get("model_suggestion")}
        )
        
        # Notify connected WebSocket clients
        ws = active_sessions[session_id]["websocket"]
        if ws:
            await ws.send_json({
                "type": "plan_update",
                "data": updated_plan
            })
            
        return updated_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """Create a new Data Buddy project"""
    try:
        project_dir = get_project_path(project.name)
        config_dir = project_dir / ".databuddy"
        config_dir.mkdir(parents=True, exist_ok=True)

        config = {
            "platform": project.platform,
            "api_key": project.api_key
        }
        
        config_path = config_dir / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        return ProjectResponse(
            name=project.name,
            status="created",
            config_path=str(config_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_name}/upload")
async def upload_dataset(
    project_name: str,
    file: UploadFile = File(...),
    config: dict = Depends(get_project_config)
):
    """Upload dataset to a specific project"""
    try:
        project_dir = get_project_path(project_name)
        data_dir = project_dir / "data"
        data_dir.mkdir(exist_ok=True)

        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")

        file_path = data_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "filename": file.filename,
            "path": str(file_path),
            "project": project_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_name}/analyze")
async def analyze_project(
    project_name: str,
    dataset_path: str,
    requirements: Optional[str] = None,
    config: dict = Depends(get_project_config)
):
    """Analyze a project's dataset"""
    try:
        model = load_model(str(get_project_path(project_name)), None)
        analyzer = AnalyzerAgent(model)
        advisor = AdviseAgent(model)
        planner = PlannerAgent(model)

        df = dataframe_validator(dataset_path)
        analysis_result = analyzer.analyze_data(df)
        advice = None
        if requirements:
            advice = advisor.chat(requirements)

        return {
            "analysis": {
                "dataset_hash": analysis_result.dataset_hash,
                "results": [r.__dict__ for r in analysis_result.results],
                "metadata": analysis_result.metadata
            },
            "advice": advice
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    try:
        if session_id not in active_sessions:
            await websocket.close(code=4000, reason="Invalid session")
            return

        await websocket.accept()
        active_sessions[session_id]["websocket"] = websocket

        while True:
            try:
                data = await websocket.receive_json()
                
                if data["type"] == "chat":
                    if data["agent"] == "advisor":
                        result = await handle_advisor_chat(
                            active_sessions[session_id]["advisor"],
                            data["message"]
                        )
                    elif data["agent"] == "planner":
                        result = await handle_planner_chat(
                            active_sessions[session_id]["planner"],
                            data["message"]
                        )
                    else:
                        result = {"error": "Invalid agent type"}
                    
                    await websocket.send_json({
                        "type": f"{data['agent']}_response",
                        "data": result
                    })
                
                elif data["type"] == "improve_report":
                    if data["agent"] == "advisor":
                        result = await handle_advisor_improvement(
                            active_sessions[session_id]["advisor"],
                            data["suggestions"]
                        )
                    elif data["agent"] == "planner":
                        result = await handle_planner_improvement(
                            active_sessions[session_id]["planner"],
                            data["suggestions"]
                        )
                    else:
                        result = {"error": "Invalid agent type"}
                    
                    await websocket.send_json({
                        "type": f"{data['agent']}_improvement",
                        "data": result
                    })

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    finally:
        # Cleanup session
        if session_id in active_sessions:
            active_sessions[session_id]["websocket"] = None

async def handle_advisor_chat(advisor: AdviseAgent, message: str) -> dict:
    """Handle chat messages for the advisor agent"""
    try:
        result = advisor.chat(message)
        return {
            "response": result,
            "report": advisor.json_report
        }
    except Exception as e:
        return {"error": str(e)}

async def handle_planner_chat(planner: PlannerAgent, message: dict) -> dict:
    """Handle chat messages for the planner agent"""
    try:
        if message.get("action") == "generate":
            plan = planner.generate_plan(
                model_or_algorithm=message.get("model_suggestion")
            )
            return {"plan": plan.__dict__}
        elif message.get("action") == "improve":
            improved_plan = planner.chat(message.get("current_plan"))
            return {"plan": improved_plan.__dict__}
    except Exception as e:
        return {"error": str(e)}

async def handle_advisor_improvement(advisor: AdviseAgent, suggestions: str) -> dict:
    """Handle report improvement requests for the advisor agent"""
    try:
        improved_report = advisor.chat(suggestions)
        return {
            "improved_report": improved_report,
            "json_report": advisor.json_report
        }
    except Exception as e:
        return {"error": str(e)}

async def handle_planner_improvement(planner: PlannerAgent, suggestions: dict) -> dict:
    """Handle plan improvement requests for the planner agent"""
    try:
        if suggestions.get("model_suggestion"):
            improved_plan = planner.generate_plan(
                model_or_algorithm=suggestions["model_suggestion"]
            )
        else:
            current_plan = suggestions.get("current_plan")
            improved_plan = planner.chat(current_plan)
        
        return {"improved_plan": improved_plan.__dict__}
    except Exception as e:
        return {"error": str(e)}

async def handle_planner_action(planner: PlannerAgent, action: str, params: dict) -> dict:
    """Handle planner actions and return results"""
    try:
        if action == "plan":
            plan = planner.generate_plan(
                model_or_algorithm=params.get("model_suggestion")
            )
            return {"plan": plan.__dict__}
        elif action == "improve":
            improved_plan = planner.chat(params.get("current_plan"))
            return {"plan": improved_plan.__dict__}
        else:
            raise ValueError(f"Unknown action: {action}")
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/projects/{project_name}/reports")
async def get_project_reports(project_name: str):
    """Get all reports for a project"""
    try:
        project_dir = get_project_path(project_name)
        reports_dir = project_dir / "analysis_reports"
        
        if not reports_dir.exists():
            return {"reports": []}

        reports = []
        for report_file in reports_dir.glob("*.json"):
            with open(report_file) as f:
                report_data = json.load(f)
                reports.append({
                    "filename": report_file.name,
                    "data": report_data
                })

        return {"reports": reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/projects/{project_name}")
async def delete_project(project_name: str):
    """Delete a project"""
    try:
        project_dir = get_project_path(project_name)
        if project_dir.exists():
            shutil.rmtree(project_dir)
        return {"status": "deleted", "project": project_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(PROJECTS_DIR, exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    for session_id, session in active_sessions.items():
        if session["websocket"]:
            await session["websocket"].close()
    active_sessions.clear()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)