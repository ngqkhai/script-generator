from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel

class ScriptRequest(BaseModel):
    """Request with only the fields specified by the user - no required fields"""
    script_type: Optional[str] = None
    target_audience: Optional[str] = None
    duration_seconds: Optional[int] = None
    tone: Optional[str] = None
    style_description: Optional[str] = None
    source_data: Optional[str] = None  # This will contain the "Data" field

class SceneUpdate(BaseModel):
    scene_id: str  # ID of the scene to update (e.g., "scene1", "scene2")
    time: Optional[str] = None
    script: Optional[str] = None
    visual: Optional[str] = None
    voiceover: Optional[bool] = None
    # Add any other scene fields that might be updated

class ScriptEditRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = None
    scenes: Optional[List[Dict[str, Any]]] = None  # Keep for backward compatibility
    scene_updates: Optional[List[SceneUpdate]] = None  # New field for updating specific scenes