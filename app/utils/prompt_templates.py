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
    base_prompt = """You are a professional video script generator. Create a detailed video script for the following requirements.

IMPORTANT INSTRUCTIONS:
1. You must respond with ONLY a valid JSON object
2. Do NOT use markdown formatting (no ```json or ``` markers)
3. Do NOT include any explanations or additional text
4. The response must be a single, valid JSON object

Requirements:
"""
    
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
    
    if request.language:
        base_prompt += f"Language: {request.language}\n"

    # Add source data if provided
    if data:
        base_prompt += f"\nSource Data:\n{data}\n"
    
    # Output format instructions
    duration_text = f"{request.duration_seconds} seconds" if request.duration_seconds else "an appropriate duration"
    
    output_format = f"""
Required JSON Structure:
{{
  "scenes": [
    {{
      "scene_id": "scene1",
      "time": "00:00-00:30",
      "script": "The script text for this scene...",
      "visual": "Detailed visual description for image generation...",
      "voiceover": true
    }}
  ],
  "metadata": {{
    "title": "Video Title",
    "duration": "MM:SS",
    "target_audience": "Description of target audience",
    "tone": "The tone of the video",
    "style": "The visual style"
  }}
}}

Instructions:
1. Divide {duration_text} into 4-8 logical scenes with appropriate timing
2. Make the script engaging and impactful for the target audience
3. The visual descriptions should be detailed enough to generate compelling images
4. Return ONLY the JSON object, no other text or explanation
5. Ensure the JSON is valid and properly formatted
6. Do NOT use markdown formatting or code blocks
7. The response must be a single, valid JSON object that can be parsed directly
8. The language of the script should be {request.language}
"""
    
    return base_prompt + output_format