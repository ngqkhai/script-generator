from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List


class ScriptResponse(BaseModel):
    """
    Response model for script generation requests
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "script_id": "script_123",
                "status": "completed",
                "message": "Script generated successfully"
            }
        }
    )
    
    script_id: str = Field(..., description="Unique identifier for the generated script")
    status: str = Field(..., description="Status of the script generation (queued, processing, completed, failed)")
    message: Optional[str] = Field(None, description="Optional message providing additional information")


class SceneModel(BaseModel):
    """
    Model representing a single scene in a video script
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scene_id": "scene1",
                "time": "00:00-00:30",
                "script": "Welcome to our video...",
                "visual": "Opening shot of the subject",
                "voiceover": True
            }
        }
    )
    
    scene_id: str
    time: str
    script: str
    visual: str
    voiceover: bool


class ScriptMetadata(BaseModel):
    """
    Model representing script metadata
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Introduction to Quantum Computing",
                "duration": "05:00",
                "target_audience": "general",
                "tone": "informative",
                "style": "modern"
            }
        }
    )
    
    title: str
    duration: str
    target_audience: str
    tone: str
    style: str


class CompleteScriptResponse(BaseModel):
    """
    Response model for a complete script
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "script_id": "script_123",
                "scenes": [
                    {
                        "scene_id": "scene1",
                        "time": "00:00-00:30",
                        "script": "Welcome to our video...",
                        "visual": "Opening shot",
                        "voiceover": True
                    }
                ],
                "metadata": {
                    "title": "Introduction to Quantum Computing",
                    "duration": "05:00",
                    "target_audience": "general",
                    "tone": "informative",
                    "style": "modern"
                },
                "created_at": "2024-02-20T10:00:00Z"
            }
        }
    )
    
    script_id: str
    scenes: List[SceneModel]
    metadata: ScriptMetadata
    created_at: Optional[str] = None