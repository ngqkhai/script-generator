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
    script = script_repository.find_one(script_id)
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
    script = script_repository.find_one(script_id)
    if script:
        return {
            "script_id": script_id,
            "script": script
        }
    else:
        raise HTTPException(status_code=404, detail="Script not found")


@router.put("/scripts/{script_id}", response_model=Dict[str, Any])
async def update_script(script_id: str, edit_request: ScriptEditRequest):
    """Edit an existing script, allowing updates to individual scenes"""
    # Check if script exists
    existing_script = script_repository.find_one(script_id)
    if not existing_script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Prepare update data
    update_data = {
        "updated_at": datetime.utcnow()
    }
    
    # Handle specific scene updates if provided
    if edit_request.scene_updates:
        # Get current scenes from the existing script
        current_scenes = existing_script.get("scenes", [])
        
        # Create a dictionary for quick lookup of scene updates by scene_id
        scene_updates_dict = {update.scene_id: update for update in edit_request.scene_updates}
        
        # Update only the specified scenes in the current scenes array
        for i, scene in enumerate(current_scenes):
            scene_id = scene.get("scene_id")
            if scene_id in scene_updates_dict:
                # Get the update for this scene
                scene_update = scene_updates_dict[scene_id]
                
                # Create a dict with only the non-None fields from the update
                update_dict = {k: v for k, v in scene_update.dict().items() 
                              if k != "scene_id" and v is not None}
                
                # Apply updates to the scene
                current_scenes[i].update(update_dict)
        
        # Add scenes array to update data, but DO NOT use $set operator here
        # as we're using the repository pattern
        update_data["scenes"] = current_scenes
    
    # Update metadata if provided
    if edit_request.metadata:
        update_data["metadata"] = edit_request.metadata
    
    # Update the script
    success = script_repository.update_one(script_id, update_data)
    if success:
        # Get the updated script
        updated_script = script_repository.find_one(script_id)
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
    existing_script = script_repository.find_one(script_id)
    if not existing_script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Delete the script
    success = script_repository.delete_one(script_id)
    if success:
        # Also remove from in-memory tracking if present
        if script_id in generation_tasks:
            del generation_tasks[script_id]
            
        return {
            "script_id": script_id,
            "message": "Script deleted successfully"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to delete script")


@router.get("/scripts", response_model=Dict[str, Any])
async def list_scripts(skip: int = 0, limit: int = 10):
    """List all generated scripts with pagination"""
    scripts = script_repository.find(skip=skip, limit=limit)
    total = script_repository.count_documents()
    
    return {
        "scripts": scripts,
        "total": total,
        "skip": skip,
        "limit": limit
    }


async def generate_script_in_background(script_id: str, request: ScriptRequest):
    """Background task to generate a script"""
    try:
        # Update status to in-progress
        generation_tasks[script_id] = {
            "status": "in_progress",
            "progress": 0.1
        }
        
        # Generate script
        script = await script_generator.generate_script(request)
        
        # Update progress
        generation_tasks[script_id] = {
            "status": "finalizing",
            "progress": 0.9
        }
        
        # Add generated script to database
        script["_id"] = script_id  # Use the same ID we generated
        script_repository.insert_one(script)
        
        # Update final status
        generation_tasks[script_id] = {
            "status": "completed",
            "progress": 1.0
        }
        
        # Clean up task after some time (keep status for a while for clients to check)
        await asyncio.sleep(300)  # 5 minutes
        if script_id in generation_tasks:
            del generation_tasks[script_id]
            
    except Exception as e:
        logger.error(f"Error generating script {script_id}: {str(e)}")
        # Update status to error
        generation_tasks[script_id] = {
            "status": "error",
            "progress": 0,
            "error": str(e)
        }