import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid
import json
from datetime import datetime, timedelta

from app.routes.scripting_routes import generation_tasks
from app.models.request_models import ScriptRequest, ScriptEditRequest


@pytest.fixture
def sample_script_id():
    return str(uuid.uuid4())


@pytest.fixture
def sample_script_request():
    return {
        "script_type": "educational",
        "target_audience": "adults",
        "duration_seconds": 120,
        "tone": "informative",
        "style_description": "simple and clear",
        "source_data": "Sample information for the video script"
    }


@pytest.fixture
def sample_script():
    return {
        "_id": str(uuid.uuid4()),
        "scenes": [
            {
                "scene_id": "scene1",
                "time": "00:00-00:30",
                "script": "Introduction to the topic",
                "visual": "Presenter speaking to camera",
                "voiceover": True
            },
            {
                "scene_id": "scene2",
                "time": "00:30-01:00",
                "script": "Detailed explanation",
                "visual": "Animation showing concept",
                "voiceover": True
            }
        ],
        "metadata": {
            "title": "Sample Script",
            "duration": "01:00",
            "target_audience": "adults",
            "tone": "informative",
            "style": "simple"
        },
        "created_at": datetime.utcnow(),
        "updated_at": None
    }


def test_create_script(client, sample_script_request, mock_background_tasks):
    """Test creating a new script"""
    response = client.post("/api/v1/scripts", json=sample_script_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "script_id" in data
    assert data["status"] == "queued"
    assert data["message"] == "Script generation started"
    
    # Check if task was added to in-memory tracking
    assert data["script_id"] in generation_tasks
    assert generation_tasks[data["script_id"]]["status"] == "queued"


def test_get_script_status_queued(client, sample_script_id):
    """Test getting status of a queued script"""
    # Setup in-memory task
    generation_tasks[sample_script_id] = {
        "status": "queued",
        "progress": 0.0
    }
    
    response = client.get(f"/api/v1/scripts/{sample_script_id}/status")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "queued"
    assert data["progress"] == 0.0


def test_get_script_status_in_progress(client, sample_script_id):
    """Test getting status of an in-progress script"""
    # Setup in-memory task
    generation_tasks[sample_script_id] = {
        "status": "in_progress",
        "progress": 0.5
    }
    
    response = client.get(f"/api/v1/scripts/{sample_script_id}/status")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["progress"] == 0.5


def test_get_script_status_not_found(client):
    """Test getting status of a non-existent script"""
    # Use a random UUID that's not in the generation_tasks dict
    random_id = str(uuid.uuid4())
    
    # Ensure the ID is not in the generation_tasks
    if random_id in generation_tasks:
        del generation_tasks[random_id]
    
    response = client.get(f"/api/v1/scripts/{random_id}/status")
    assert response.status_code == 404


def test_get_script(client, sample_script_id, sample_script, mock_script_repository):
    """Test retrieving a script"""
    # Setup: Mock repository to return our sample script
    mock_script_repository.find_one.return_value = sample_script
    
    # Remove from in-memory tracking if it exists
    if sample_script_id in generation_tasks:
        del generation_tasks[sample_script_id]
    
    response = client.get(f"/api/v1/scripts/{sample_script_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["script_id"] == sample_script_id
    assert "script" in data
    assert data["script"]["metadata"]["title"] == "Sample Script"


def test_get_script_in_progress(client, sample_script_id):
    """Test getting a script that's still in progress"""
    # Setup in-memory task as in-progress
    generation_tasks[sample_script_id] = {
        "status": "in_progress", 
        "progress": 0.5
    }
    
    response = client.get(f"/api/v1/scripts/{sample_script_id}")
    assert response.status_code == 202  # Accepted but not complete
    
    # Check that the response indicates processing
    assert "in progress" in response.json()["detail"]


def test_get_script_not_found(client, mock_script_repository):
    """Test getting a non-existent script"""
    # Setup mock to return None
    mock_script_repository.find_one.return_value = None
    
    # Generate a random ID that's not in the generation_tasks
    script_id = str(uuid.uuid4())
    if script_id in generation_tasks:
        del generation_tasks[script_id]
    
    response = client.get(f"/api/v1/scripts/{script_id}")
    assert response.status_code == 404


def test_update_script(client, sample_script_id, sample_script, mock_script_repository):
    """Test updating a script"""
    # Setup: Mock finding and updating the script
    mock_script_repository.find_one.return_value = sample_script
    mock_script_repository.update_one.return_value = True
    
    # Create update request
    update_data = {
        "scenes": [
            {
                "scene_id": "scene1",
                "time": "00:00-00:45",  # Changed timing
                "script": "Updated introduction",  # Changed content
                "visual": "Updated visuals",
                "voiceover": True
            }
        ]
    }
    
    response = client.put(f"/api/v1/scripts/{sample_script_id}", json=update_data)
    assert response.status_code == 200
    
    # Check that the result has the expected fields
    data = response.json()
    assert data["script_id"] == sample_script_id
    assert "script" in data
    assert "message" in data
    assert data["message"] == "Script updated successfully"


def test_update_script_not_found(client, mock_script_repository):
    """Test updating a non-existent script"""
    # Setup mock to return None (not found)
    mock_script_repository.find_one.return_value = None
    
    update_data = {"metadata": {"title": "New Title"}}
    response = client.put(f"/api/v1/scripts/{str(uuid.uuid4())}", json=update_data)
    assert response.status_code == 404


def test_delete_script(client, sample_script_id, sample_script, mock_script_repository):
    """Test deleting a script"""
    # Setup: Mock finding and deleting the script
    mock_script_repository.find_one.return_value = sample_script
    mock_script_repository.delete_one.return_value = True
    
    response = client.delete(f"/api/v1/scripts/{sample_script_id}")
    assert response.status_code == 200
    
    # Check response format
    data = response.json()
    assert data["script_id"] == sample_script_id
    assert data["message"] == "Script deleted successfully"


def test_delete_script_not_found(client, mock_script_repository):
    """Test deleting a non-existent script"""
    # Setup mock to return None (not found)
    mock_script_repository.find_one.return_value = None
    
    response = client.delete(f"/api/v1/scripts/{str(uuid.uuid4())}")
    assert response.status_code == 404


def test_list_scripts(client, mock_script_repository):
    """Test listing all scripts with pagination"""
    # Setup: Mock the find operation and count
    mock_scripts = [
        {
            "_id": str(uuid.uuid4()),
            "metadata": {"title": f"Script {i}"}
        } for i in range(1, 6)
    ]
    
    mock_script_repository.find.return_value = mock_scripts
    mock_script_repository.count_documents.return_value = len(mock_scripts)
    
    response = client.get("/api/v1/scripts?skip=0&limit=5")
    assert response.status_code == 200
    
    data = response.json()
    assert "scripts" in data
    assert len(data["scripts"]) == 5
    assert data["total"] == 5
    assert data["skip"] == 0
    assert data["limit"] == 5