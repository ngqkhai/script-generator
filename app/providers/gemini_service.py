import google.generativeai as genai
from typing import Dict, Any, Optional
import json
import asyncio
import logging
import re

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google's Gemini API"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self._initialized = True
    
    async def generate_structured_script(self, 
                                        prompt: str, 
                                        audience_type: Optional[str] = None,
                                        tone: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured script output using Gemini API
        
        Args:
            prompt: The formatted prompt for script generation
            audience_type: Target audience type for personalization (optional)
            tone: Desired tone for the script (optional)
            
        Returns:
            Dict containing the structured script
        """
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192
        )
        
        # Enhance prompt with audience-specific instructions if provided
        enhanced_prompt = prompt
        if audience_type and tone:
            audience_instructions = self._get_audience_instructions(audience_type, tone)
            enhanced_prompt = f"{prompt}\n\n{audience_instructions}"
        
        try:
            logger.info("Sending prompt to Gemini API")
            logger.debug(f"Prompt: {enhanced_prompt}")
            
            # Generate content asynchronously
            response = await asyncio.to_thread(
                self.model.generate_content,
                enhanced_prompt,
                generation_config=generation_config
            )
            
            logger.info("Received response from Gemini API")
            
            # Parse the response as JSON
            if hasattr(response, 'candidates') and response.candidates:
                json_text = response.candidates[0].content.parts[0].text
                logger.debug(f"Raw response text: {json_text}")
                try:
                    # Remove markdown code block formatting if present
                    json_text = re.sub(r'^```json\s*', '', json_text)
                    json_text = re.sub(r'\s*```$', '', json_text)
                    return json.loads(json_text)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from response: {str(e)}")
                    logger.error(f"Invalid JSON text: {json_text}")
                    # Fallback to text parsing
                    return self._extract_json_from_text(json_text)
            else:
                # Fallback to text parsing if structured response fails
                text_content = response.text
                logger.debug(f"Fallback response text: {text_content}")
                return self._extract_json_from_text(text_content)
                
        except Exception as e:
            logger.error(f"Error generating script with Gemini API: {str(e)}")
            raise ValueError(f"Failed to generate script: {str(e)}")
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response if structured output fails
        
        Args:
            text: Text response from Gemini API
            
        Returns:
            Extracted JSON as dict
        """
        try:
            # Find JSON block
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                logger.debug(f"Extracted JSON string: {json_str}")
                return json.loads(json_str)
            
            logger.error("No JSON block found in response")
            logger.debug(f"Full text: {text}")
            raise ValueError("No valid JSON found in response")
        except Exception as e:
            logger.error(f"Failed to extract JSON from response: {str(e)}")
            logger.debug(f"Failed text: {text}")
            raise ValueError(f"Failed to parse script structure: {str(e)}")
    
    def _get_audience_instructions(self, audience_type: str, tone: str) -> str:
        """Get personalized instructions based on audience type
        
        Args:
            audience_type: Target audience type
            tone: Desired tone
            
        Returns:
            String with audience-specific instructions
        """
        tone_instructions = {
            "casual": "Maintain a conversational, friendly tone throughout the script.",
            "professional": "Maintain a formal, authoritative tone throughout the script.",
            "humorous": "Incorporate appropriate humor and light-hearted elements throughout the script.",
            "serious": "Maintain a serious, straightforward tone appropriate for weighty topics.",
            "inspiring": "Use language that motivates and uplifts throughout the script.",
            "informative": "Focus on clear, educational delivery of information throughout the script."
        }
        
        tone_instruction = tone_instructions.get(tone.lower(), "")
        
        return f"{tone_instruction}\n\nReturn ONLY a valid JSON response matching the exact structure requested."