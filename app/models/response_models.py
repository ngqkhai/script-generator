from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class ScriptResponse(BaseModel):
    """
    Response model for script generation requests
    """
    script_id: str = Field(..., description="Unique identifier for the generated script")
    status: str = Field(..., description="Status of the script generation (queued, processing, completed, failed)")
    message: Optional[str] = Field(None, description="Optional message providing additional information")


class SceneModel(BaseModel):
    """
    Model representing a single scene in a video script
    """
    scene_id: str
    time: str
    script: str
    visual: str
    voiceover: bool


class ScriptMetadata(BaseModel):
    """
    Model representing script metadata
    """
    title: str
    duration: str
    target_audience: str
    tone: str
    style: str


class CompleteScriptResponse(BaseModel):
    """
    Response model for a complete script
    """
    script_id: str
    scenes: List[SceneModel]
    metadata: ScriptMetadata
    created_at: Optional[str] = None