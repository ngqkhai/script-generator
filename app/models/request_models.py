from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, ConfigDict

class ScriptRequest(BaseModel):
    """Request with only the fields specified by the user - no required fields"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "script_type": "educational",
                "target_audience": "general",
                "duration_seconds": "Medium (3-5 mins)",
                "tone": "informative",
                "style_description": "Modern and engaging",
                "language": "en",
                "content": "Sample content for script generation"
            }
        }
    )
    
    script_type: Optional[str] = None
    target_audience: Optional[str] = None
    duration_seconds: Optional[str] = None
    tone: Optional[str] = None
    style_description: Optional[str] = None
    language: Optional[str] = None
    content: Optional[str] = None  # This will contain the "Data" field

class SceneUpdate(BaseModel):
    """Model for updating a specific scene in a script"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scene_id": "scene1",
                "time": "00:00-00:30",
                "script": "Updated script content",
                "visual": "Updated visual description",
                "voiceover": True
            }
        }
    )
    
    scene_id: str  # ID of the scene to update (e.g., "scene1", "scene2")
    time: Optional[str] = None
    script: Optional[str] = None
    visual: Optional[str] = None
    voiceover: Optional[bool] = None
    # Add any other scene fields that might be updated

class ScriptEditRequest(BaseModel):
    """Model for editing an existing script"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metadata": {
                    "title": "Updated Title",
                    "duration": "05:00"
                },
                "scene_updates": [
                    {
                        "scene_id": "scene1",
                        "script": "Updated script content"
                    }
                ]
            }
        }
    )
    
    metadata: Optional[Dict[str, Any]] = None
    scenes: Optional[List[Dict[str, Any]]] = None  # Keep for backward compatibility
    scene_updates: Optional[List[SceneUpdate]] = None  # New field for updating specific scenes