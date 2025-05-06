from typing import Optional
from pydantic import BaseModel

class ScriptRequest(BaseModel):
    """Request with only the fields specified by the user - no required fields"""
    script_type: Optional[str] = None
    target_audience: Optional[str] = None
    duration_seconds: Optional[int] = None
    tone: Optional[str] = None
    style_description: Optional[str] = None
    source_data: Optional[str] = None  # This will contain the "Data" field

class ScriptEditRequest(BaseModel):
    """Request model for editing a script"""
    scenes: Optional[list] = None
    metadata: Optional[dict] = None