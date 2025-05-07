import pytest
from fastapi.testclient import TestClient
import os
from unittest.mock import patch, MagicMock

from app import create_app

# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_variables():
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "mock_api_key",
        "GEMINI_MODEL": "gemini-pro",
        "MONGODB_URL": "mongodb://localhost:27017",
        "MONGODB_DB": "test_scripts_db"
    }):
        yield


@pytest.fixture
def test_app():
    app = create_app()
    return app


@pytest.fixture
def client(test_app):
    with TestClient(test_app) as client:
        yield client


@pytest.fixture(autouse=True)
def mock_script_repository():
    """Mock the script repository used in routes"""
    with patch('app.routes.scripting_routes.script_repository') as mock:
        # Configure mock repository methods
        mock.find_one.return_value = None
        mock.insert_one.return_value = True
        mock.update_one.return_value = True
        mock.delete_one.return_value = True
        mock.find.return_value = []
        mock.count_documents.return_value = 0
        
        yield mock


@pytest.fixture(autouse=True)
def mock_script_generator():
    """Mock the script generator used in routes"""
    with patch('app.routes.scripting_routes.script_generator') as mock_gen:
        # Mock the async generate_script method
        async def mock_generate(request):
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
        
        mock_gen.generate_script = mock_generate
        yield mock_gen


@pytest.fixture(autouse=True)
def mock_background_tasks():
    """Mock the background task function"""
    with patch('app.routes.scripting_routes.generate_script_in_background') as mock_task:
        yield mock_task