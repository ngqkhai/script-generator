from typing import Optional
from app.models.request_models import ScriptRequest


def get_script_prompt_with_data(request: ScriptRequest, data: Optional[str] = None) -> str:
    """Generate a prompt using only the fields that exist in the request
    
    Args:
        request: Script generation request
        data: Optional raw text data
        
    Returns:
        Formatted prompt string
    """
    # Start with base prompt - no required fields
    base_prompt = "You are a professional video script generator. Create a detailed video script for the following requirements:\n\n"
    
    # Only add fields that exist in the request
    if request.script_type:
        base_prompt += f"Type: {request.script_type}\n"
        
    if request.target_audience:
        base_prompt += f"Target Audience: {request.target_audience}\n"
        
    if request.duration_seconds:
        base_prompt += f"Duration: {request.duration_seconds} seconds\n"
        
    if request.tone:
        base_prompt += f"Tone: {request.tone}\n"
        
    if request.style_description:
        base_prompt += f"Style: {request.style_description}\n"
    
    # Add source data if provided
    if data:
        base_prompt += f"\nSource Data:\n{data}\n"
    
    # Output format instructions
    duration_text = f"{request.duration_seconds} seconds" if request.duration_seconds else "an appropriate duration"
    
    output_format = f"""
    Create a JSON structure with the following format:
    {{
      "scenes": [
        {{
          "scene_id": "unique_identifier",
          "time": "MM:SS-MM:SS",
          "script": "The script text for this scene...",
          "visual": "Detailed visual description for image generation...",
          "voiceover": true or false
        }},
        // Additional scenes...
      ],
      "metadata": {{
        "title": "Title for the video",
        "duration": "MM:SS",
        "target_audience": "Description of target audience",
        "tone": "The tone of the video",
        "style": "The visual style"
      }}
    }}
    
    Divide {duration_text} into 4-8 logical scenes with appropriate timing.
    Make the script engaging and impactful for the target audience.
    The visual descriptions should be detailed enough to generate compelling images.
    
    ONLY RETURN THE JSON STRUCTURE, NO OTHER TEXT.
    """
    
    return base_prompt + output_format