import pytest
from app.utils.prompt_templates import get_script_prompt_with_data
from app.models.request_models import ScriptRequest


def test_prompt_with_all_fields():
    """Test prompt generation with all fields provided"""
    request = ScriptRequest(
        script_type="educational",
        target_audience="adults",
        duration_seconds=120,
        tone="informative",
        style_description="simple and clear",
        content="Sample data for script"
    )
    
    prompt = get_script_prompt_with_data(request, "Additional source data")
    
    # Check that all fields are included in prompt
    assert "Type: educational" in prompt
    assert "Target Audience: adults" in prompt
    assert "Duration: 120 seconds" in prompt
    assert "Tone: informative" in prompt
    assert "Style: simple and clear" in prompt
    assert "Source Data:" in prompt
    assert "Additional source data" in prompt
    assert "JSON structure" in prompt


def test_prompt_with_minimal_fields():
    """Test prompt generation with minimal fields"""
    request = ScriptRequest(script_type="tutorial")
    
    prompt = get_script_prompt_with_data(request)
    
    # Check that only provided fields are included
    assert "Type: tutorial" in prompt
    assert "Target Audience:" not in prompt
    assert "Duration:" not in prompt
    assert "Tone:" not in prompt
    assert "Style:" not in prompt
    assert "Source Data:" not in prompt
    assert "an appropriate duration" in prompt  # Default duration text
    assert "JSON structure" in prompt


def test_prompt_with_some_fields():
    """Test prompt generation with some fields"""
    request = ScriptRequest(
        script_type="advertisement",
        tone="humorous",
        style_description="energetic and fun"
    )
    
    prompt = get_script_prompt_with_data(request)
    
    # Check that only provided fields are included
    assert "Type: advertisement" in prompt
    assert "Tone: humorous" in prompt
    assert "Style: energetic and fun" in prompt
    assert "Target Audience:" not in prompt
    assert "Duration:" not in prompt
    assert "Source Data:" not in prompt


def test_prompt_with_data():
    """Test prompt generation with source data"""
    request = ScriptRequest(script_type="documentary")
    source_data = "Facts about climate change: The global temperature has risen by 1.1°C since the pre-industrial era."
    
    prompt = get_script_prompt_with_data(request, source_data)
    
    # Check that source data is included
    assert "Type: documentary" in prompt
    assert "Source Data:" in prompt
    assert source_data in prompt