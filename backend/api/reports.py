from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import pickle
from pathlib import Path

from backend.models.report import Report
from backend.auth.dependencies import get_current_user
from backend.database import Database

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/{project_id}")
async def get_project_reports(
    project_id: str,
    agent_type: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get all reports for a project"""
    reports_coll = await Database.get_collection("reports")
    query = {"project_id": project_id}
    if agent_type:
        query["agent_type"] = agent_type
        
    reports = await reports_coll.find(query).to_list(length=100)
    return reports

@router.get("/{report_id}/content")
async def get_report_content(
    report_id: str,
    current_user = Depends(get_current_user)
):
    """Get report content from file system"""
    reports_coll = await Database.get_collection("reports")
    report = await reports_coll.find_one({"_id": report_id})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    try:
        with open(report["file_path"], 'rb') as f:
            content = pickle.load(f)
        return {
            "metadata": report["metadata"],
            "content": content,
            "summary": report.get("summary")
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error loading report: {str(e)}"
        )
