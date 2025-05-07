import pytest
from unittest.mock import patch, MagicMock
import asyncio
from datetime import datetime

from app.providers.script_generator import ScriptGenerator
from app.models.request_models import ScriptRequest


@pytest.fixture
def mock_gemini_service():
    with patch("app.providers.gemini_service.GeminiService") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        
        # Mock the generate_structured_script method to make it async
        async def mock_generate(*args, **kwargs):
            return {
                "scenes": [
                    {
                        "scene_id": "scene1",
                        "time": "00:00-00:30",
                        "script": "Test script content",
                        "visual": "Visual description",
                        "voiceover": True
                    }
                ],
                "metadata": {
                    "title": "Test Video",
                    "duration": "00:30",
                    "target_audience": "general",
                    "tone": "informative",
                    "style": "simple"
                }
            }
        
        mock_instance.generate_structured_script = mock_generate
        yield mock_instance


@pytest.fixture
def script_generator(mock_gemini_service):
    # Reset singleton instance for testing
    ScriptGenerator._instance = None
    ScriptGenerator._initialized = False
    with patch.object(ScriptGenerator, "__init__", return_value=None):
        generator = ScriptGenerator()
        generator._initialized = True
        generator.gemini_service = mock_gemini_service
        yield generator


@pytest.fixture
def sample_script_request():
    return ScriptRequest(
        script_type="educational",
        target_audience="adults",
        duration_seconds=120,
        tone="informative",
        style_description="simple and clear",
        source_data="Sample information for the video script"
    )


@pytest.mark.asyncio
async def test_generate_script(script_generator, sample_script_request):
    """Test the script generation process with mocked prompt utils"""
    with patch("app.providers.script_generator.get_script_prompt_with_data") as mock_prompt:
        mock_prompt.return_value = "Test prompt"
        
        result = await script_generator.generate_script(sample_script_request)
        
        # Check the result has the expected structure
        assert "scenes" in result
        assert "metadata" in result
        assert "created_at" in result  # Timestamp should be added


@pytest.mark.asyncio
async def test_generate_script_without_optional_fields(script_generator):
    """Test script generation with minimal request fields"""
    with patch("app.providers.script_generator.get_script_prompt_with_data") as mock_prompt:
        mock_prompt.return_value = "Test prompt"
        
        request = ScriptRequest(script_type="educational")
        
        result = await script_generator.generate_script(request)
        
        # Check result structure
        assert "scenes" in result
        assert "metadata" in result
        assert "created_at" in result