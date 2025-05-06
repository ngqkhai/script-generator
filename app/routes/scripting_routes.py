from fastapi import APIRouter, HTTPException, Depends
from app.models.request_models import ScriptRequest
from app.models.response_models import ScriptResponse
from app.providers.script_generator import ScriptGenerator
from app.repositories.script_repository import ScriptRepository
from typing import Dict, Any
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Create dependencies (will be replaced in tests)
def get_script_repository():
    return ScriptRepository()  # Now instantiated at call time, not at import time

def get_script_generator():
    return ScriptGenerator()  # Similarly, instantiated at call time

@router.post("/scripts", response_model=ScriptResponse)
async def create_script(
    request: ScriptRequest,
    script_repository: ScriptRepository = Depends(get_script_repository),
    script_generator: ScriptGenerator = Depends(get_script_generator)
):
    """
    Create a new video script based on request parameters
    """
    try:
        logger.info(f"Received script generation request for type: {request.script_type}")
        
        # Queue the script generation job (or generate it directly if simple)
        script_data = await script_generator.generate_script(request)
        
        # Save to database
        script_id = script_repository.save(script_data)
        
        # Return response with script ID
        return ScriptResponse(
            script_id=script_id,
            status="queued"  # or "completed" if generated directly
        )
        
    except Exception as e:
        logger.error(f"Error creating script: {e}")
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")

@router.get("/scripts/{script_id}")
async def get_script(
    script_id: str,
    script_repository: ScriptRepository = Depends(get_script_repository)
):
    """
    Get a script by ID
    """
    try:
        script = script_repository.get_by_id(script_id)
        
        if not script:
            raise HTTPException(status_code=404, detail=f"Script with ID {script_id} not found")
            
        return script
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving script: {e}")
        raise HTTPException(status_code=500, detail=f"Could not retrieve script: {str(e)}")