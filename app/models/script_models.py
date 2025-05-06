from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
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
    scene_id: str
    time: str  # Format: "MM:SS-MM:SS"
    script: str
    visual: str
    voiceover: bool = True


class ScriptMetadata(BaseModel):
    """Metadata for the script"""
    title: str
    duration: str  # Format: "MM:SS"
    target_audience: str
    tone: str
    style: str
    key_points: List[str]
    data_sources: Optional[List[str]] = None


class VideoScript(BaseModel):
    """Complete video script model"""
    id: Optional[str] = None
    scenes: List[Scene]
    metadata: ScriptMetadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class DataRequest(BaseModel):
    """Model for requesting data from the collector service"""
    request_id: str
    topic: str
    requirements: Dict[str, Any]


class DataResponse(BaseModel):
    """Model for data received from collector service"""
    request_id: str
    status: str
    payload: Dict[str, Any]