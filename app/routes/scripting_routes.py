from fastapi import APIRouter, HTTPException, BackgroundTasks
from bson.objectid import ObjectId
import uuid
from typing import Dict, Any
import logging
from datetime import datetime
import asyncio

from app.models.request_models import ScriptRequest, ScriptEditRequest
from app.providers.script_generator import ScriptGenerator
from app.repositories.script_repository import ScriptRepository

router = APIRouter()
script_generator = ScriptGenerator()
script_repository = ScriptRepository()

# In-memory tracking of generation jobs
generation_tasks = {}

logger = logging.getLogger(__name__)


@router.post("/scripts", response_model=Dict[str, Any])
async def create_script(request: ScriptRequest, background_tasks: BackgroundTasks):
    """Create a new video script"""
    # Generate a unique ID for this script
    script_id = str(uuid.uuid4())
    
    # Store initial status
    generation_tasks[script_id] = {
        "status": "queued",
        "progress": 0.0
    }
    
    # Add script generation to background tasks
    background_tasks.add_task(
        generate_script_in_background,
        script_id,
        request
    )
    
    return {
        "script_id": script_id,
        "status": "queued",
        "message": "Script generation started"
    }


@router.get("/scripts/{script_id}/status")
async def get_script_status(script_id: str):
    """Get the status of a script generation job"""
    # Check in-memory task status first
    if script_id in generation_tasks:
        return generation_tasks[script_id]
    
    # If not in tasks, check if it exists in the repository
    script = script_repository.find_by_id(script_id)
    if script:
        return {
            "status": "completed",
            "progress": 1.0
        }
    
    # If not found anywhere, return 404
    raise HTTPException(status_code=404, detail="Script not found")


@router.get("/scripts/{script_id}", response_model=Dict[str, Any])
async def get_script(script_id: str):
    """Get a generated script by ID"""
    # Check if still in generation
    if script_id in generation_tasks:
        status = generation_tasks[script_id]["status"]
        if status != "completed":
            raise HTTPException(
                status_code=202,
                detail=f"Script generation in progress. Status: {status}"
            )
    
    # Get from repository
    script = script_repository.find_by_id(script_id)
    if script:
        return {
            "script_id": script_id,
            "script": script
        }
    else:
        raise HTTPException(status_code=404, detail="Script not found")


@router.put("/scripts/{script_id}", response_model=Dict[str, Any])
async def update_script(script_id: str, edit_request: ScriptEditRequest):
    """Edit an existing script"""
    # Check if script exists
    existing_script = script_repository.find_by_id(script_id)
    if not existing_script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Prepare update data
    update_data = {
        "updated_at": datetime.utcnow()
    }
    
    # Update scenes if provided
    if edit_request.scenes:
        update_data["scenes"] = edit_request.scenes
    
    # Update metadata if provided
    if edit_request.metadata:
        update_data["metadata"] = edit_request.metadata
    
    # Update the script
    success = script_repository.update(script_id, update_data)
    if success:
        # Get the updated script
        updated_script = script_repository.find_by_id(script_id)
        return {
            "script_id": script_id,
            "script": updated_script,
            "message": "Script updated successfully"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to update script")


@router.delete("/scripts/{script_id}", response_model=Dict[str, Any])
async def delete_script(script_id: str):
    """Delete a script by ID"""
    # Check if script exists
    script = script_repository.find_by_id(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Delete the script
    success = script_repository.delete(script_id)
    if success:
        return {
            "script_id": script_id,
            "message": "Script deleted successfully"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to delete script")


@router.get("/scripts", response_model=Dict[str, Any])
async def list_scripts(limit: int = 10, skip: int = 0, search: str = None):
    """List all scripts with optional searching"""
    # Prepare filter
    filter_criteria = {}
    if search:
        filter_criteria["$text"] = {"$search": search}
    
    # Get scripts from repository
    scripts = script_repository.list(filter_criteria, limit, skip)
    
    return {
        "count": len(scripts),
        "scripts": scripts
    }


async def generate_script_in_background(script_id: str, request: ScriptRequest):
    """Background task to generate a script"""
    try:
        # Update status to processing
        generation_tasks[script_id] = {
            "status": "processing",
            "progress": 0.1
        }
        
        # Update progress for processing
        generation_tasks[script_id]["progress"] = 0.3
        logger.info(f"Generating script {script_id}")
        
        # Generate the script
        script = await script_generator.generate_script(request)
        
        # Update progress during generation
        generation_tasks[script_id]["progress"] = 0.8
        logger.info(f"Script {script_id} generation complete, saving to database")
        
        # Store the script in the repository
        script_repository.save({**script, "_id": ObjectId(script_id)})
        
        # Mark as completed
        generation_tasks[script_id] = {
            "status": "completed",
            "progress": 1.0
        }
        logger.info(f"Script {script_id} saved to database and ready for retrieval")
        
    except Exception as e:
        logger.error(f"Error generating script {script_id}: {str(e)}")
        # Mark as failed
        generation_tasks[script_id] = {
            "status": "failed",
            "progress": 0,
            "error": str(e)
        }