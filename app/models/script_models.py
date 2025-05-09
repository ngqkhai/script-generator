from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class ScriptType(str, Enum):
    EDUCATIONAL = "educational"
    PRODUCT = "product"
    TUTORIAL = "tutorial"
    DOCUMENTARY = "documentary"
    ADVERTISEMENT = "advertisement"
    SHORT_FORM = "short_form"


class AudienceType(str, Enum):
    CHILDREN = "children"
    TEENS = "teens"
    ADULTS = "adults"
    SENIORS = "seniors"
    PROFESSIONALS = "professionals"
    GENERAL = "general"


class ToneType(str, Enum):
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    HUMOROUS = "humorous"
    SERIOUS = "serious"
    INSPIRING = "inspiring"
    INFORMATIVE = "informative"


class Scene(BaseModel):
    """Model representing a single scene in the script"""
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
    time: str  # Format: "MM:SS-MM:SS"
    script: str
    visual: str
    voiceover: bool = True


class ScriptMetadata(BaseModel):
    """Metadata for the script"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Introduction to Quantum Computing",
                "duration": "05:00",
                "target_audience": "general",
                "tone": "informative",
                "style": "modern",
                "key_points": ["Quantum bits", "Superposition", "Entanglement"],
                "data_sources": ["wikipedia.org", "research-paper.pdf"]
            }
        }
    )
    
    title: str
    duration: str  # Format: "MM:SS"
    target_audience: str
    tone: str
    style: str
    key_points: List[str]
    data_sources: Optional[List[str]] = None


class VideoScript(BaseModel):
    """Complete video script model"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "script_123",
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
                    "style": "modern",
                    "key_points": ["Quantum bits", "Superposition"],
                    "data_sources": ["wikipedia.org"]
                },
                "created_at": "2024-02-20T10:00:00Z",
                "updated_at": "2024-02-20T10:30:00Z"
            }
        }
    )
    
    id: Optional[str] = None
    scenes: List[Scene]
    metadata: ScriptMetadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class DataRequest(BaseModel):
    """Model for requesting data from the collector service"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "req_123",
                "topic": "quantum computing",
                "requirements": {
                    "depth": "intermediate",
                    "sources": ["academic", "technical"]
                }
            }
        }
    )
    
    request_id: str
    topic: str
    requirements: Dict[str, Any]


class DataResponse(BaseModel):
    """Model for data received from collector service"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "req_123",
                "status": "completed",
                "payload": {
                    "content": "Quantum computing is a type of computing...",
                    "sources": ["wikipedia.org", "research-paper.pdf"]
                }
            }
        }
    )
    
    request_id: str
    status: str
    payload: Dict[str, Any]