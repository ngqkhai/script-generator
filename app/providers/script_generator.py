import uuid
import logging
import asyncio
import time
from datetime import datetime

from app.models.request_models import ScriptRequest
from app.providers.gemini_service import GeminiService
from app.utils.prompt_templates import get_script_prompt_with_data

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Service for generating video scripts"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScriptGenerator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.gemini_service = GeminiService()
        self._initialized = True
    
    async def generate_script(self, request: ScriptRequest) -> dict:
        """Generate a complete video script based on the request
        
        Args:
            request: The script generation request
            
        Returns:
            Dict containing the generated script
        """
        start_time = time.time()
        
        # Create prompt with source data if provided
        prompt = get_script_prompt_with_data(request, request.source_data)
        
        # Get audience type and tone if provided
        audience_type = request.target_audience if request.target_audience else None
        tone = request.tone if request.tone else None
        
        # Generate structured script using Gemini
        structured_script = await self.gemini_service.generate_structured_script(
            prompt=prompt,
            audience_type=audience_type,
            tone=tone
        )
        
        # Add creation timestamp
        structured_script["created_at"] = datetime.utcnow()
        
        logger.info(f"Script generated in {time.time() - start_time:.2f} seconds")
        return structured_script