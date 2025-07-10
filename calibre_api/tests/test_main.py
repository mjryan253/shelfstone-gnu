import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import subprocess
import json

# Adjust the import path according to your project structure
from calibre_api.main import app

client = TestClient(app)

@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock_run:
        yield mock_run

def test_list_books_success(mock_subprocess_run):
    # Mock successful calibredb command
    mock_output = [{"id": 1, "title": "Test Book 1", "authors": "Author A"}]
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps(mock_output), stderr="", returncode=0, check_returncode=lambda: None
    )

    response = client.get("/books")
    assert response.status_code == 200
    assert response.json() == mock_output
    mock_subprocess_run.assert_called_once_with(
        ["calibredb", "list", "--for-machine"], capture_output=True, text=True, check=True
    )

def test_list_books_with_query_params(mock_subprocess_run):
    # Mock successful calibredb command with query parameters
    mock_output = [{"id": 2, "title": "Searched Book", "authors": "Author B"}]
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps(mock_output), stderr="", returncode=0, check_returncode=lambda: None
    )

    response = client.get("/books?search=test&limit=10&sort_by=title")
    assert response.status_code == 200
    assert response.json() == mock_output
    mock_subprocess_run.assert_called_once_with(
        ["calibredb", "list", "--for-machine", "--search", "test", "--limit", "10", "--sort-by", "title"],
        capture_output=True, text=True, check=True
    )

def test_list_books_calibredb_called_process_error(mock_subprocess_run):
    # Mock calibredb command failing with CalledProcessError
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="calibredb list --for-machine", stderr="calibredb error"
    )

    response = client.get("/books")
    assert response.status_code == 500
    assert "calibredb command failed: calibredb error" in response.json()["detail"]

def test_list_books_file_not_found_error(mock_subprocess_run):
    # Mock calibredb command raising FileNotFoundError
    mock_subprocess_run.side_effect = FileNotFoundError("calibredb not found")

    response = client.get("/books")
    assert response.status_code == 500
    assert "calibredb command not found" in response.json()["detail"]

def test_list_books_json_decode_error(mock_subprocess_run):
    # Mock calibredb command returning invalid JSON
    mock_subprocess_run.return_value = MagicMock(
        stdout="not a json string", stderr="", returncode=0, check_returncode=lambda: None
    )

    response = client.get("/books")
    assert response.status_code == 500
    assert "Failed to parse calibredb output" in response.json()["detail"]

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Calibre API"}
