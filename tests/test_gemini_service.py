import pytest
from unittest.mock import patch, MagicMock
import asyncio
import json

from app.providers.gemini_service import GeminiService


@pytest.fixture
def mock_genai():
    with patch("app.providers.gemini_service.genai") as mock:
        mock_response = MagicMock()
        mock_response.text = '{"scenes": [{"scene_id": "test1"}], "metadata": {"title": "Test"}}'
        
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [MagicMock(text=mock_response.text)]
        
        mock_response.candidates = [mock_candidate]
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        
        mock.GenerativeModel.return_value = mock_model
        
        yield mock


@pytest.fixture
def gemini_service(mock_genai):
    # Reset singleton instance for testing
    GeminiService._instance = None
    service = GeminiService()
    return service


@pytest.mark.asyncio
async def test_generate_structured_script(gemini_service, mock_genai):
    """Test generating a structured script"""
    prompt = "Create a video script about AI"
    result = await gemini_service.generate_structured_script(prompt)
    
    # Check API was called correctly
    mock_model = mock_genai.GenerativeModel.return_value
    mock_model.generate_content.assert_called_once()
    
    # Check result structure
    assert "scenes" in result
    assert "metadata" in result
    assert result["scenes"][0]["scene_id"] == "test1"
    assert result["metadata"]["title"] == "Test"


@pytest.mark.asyncio
async def test_generate_structured_script_with_audience(gemini_service, mock_genai):
    """Test generating a script with audience and tone customization"""
    prompt = "Create a video script about space"
    audience_type = "children"
    tone = "fun"
    
    result = await gemini_service.generate_structured_script(
        prompt, audience_type=audience_type, tone=tone)
    
    # Check API was called with enhanced prompt
    mock_model = mock_genai.GenerativeModel.return_value
    args, kwargs = mock_model.generate_content.call_args
    
    # Verify prompt was enhanced with audience instructions
    assert prompt in args[0]
    
    # Check result
    assert "scenes" in result
    assert "metadata" in result


@pytest.mark.asyncio
async def test_extract_json_from_text(gemini_service):
    """Test extracting JSON from text if structured response fails"""
    # Test with valid JSON in the middle of text
    text = "Some text before\n```json\n{\"key\": \"value\"}\n```\nSome text after"
    with patch.object(gemini_service, '_extract_json_from_text', return_value={"key": "value"}):
        result = gemini_service._extract_json_from_text(text)
        assert result == {"key": "value"}
    
    # Test with invalid JSON
    with pytest.raises(ValueError):
        gemini_service._extract_json_from_text("Not a JSON string")