import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import subprocess
import json

# Adjust import path if necessary based on your project structure
# Assuming your main app is in calibre_api/app/main.py
from calibre_api.app.main import app
from calibre_api.app.crud import CalibredbError

client = TestClient(app)

# Sample successful calibredb output
SAMPLE_CALIBREDB_JSON_OUTPUT_ALL_FIELDS = [
    {
        "id": 1,
        "title": "Dune",
        "authors": ["Frank Herbert"], # Assuming model expects list
        "publisher": "Chilton Books",
        "pubdate": "1965-08-01T00:00:00+00:00",
        "isbn": "9780441172719",
        "formats": ["EPUB", "MOBI"], # Assuming model expects list
        "tags": ["Science Fiction", "Classic"], # Assuming model expects list
        "comments": "A masterpiece of science fiction.",
        "author_sort": "Herbert, Frank",
        "cover": "/path/to/cover1.jpg", # Example path
        "identifiers": {"isbn": "9780441172719", "goodreads": "12345"},
        "languages": ["eng"], # Assuming model expects list
        "last_modified": "2023-10-26T10:00:00+00:00",
        "rating": 5,
        "series": "Dune Saga",
        "series_index": 1.0,
        "size": 1024000, # Bytes
        "uuid": "some-uuid-1"
    },
    {
        "id": 2,
        "title": "Project Hail Mary",
        "authors": ["Andy Weir"],
        "publisher": "Ballantine Books",
        "pubdate": "2021-05-04T00:00:00+00:00",
        "isbn": "9780593135204",
        "formats": ["EPUB"],
        "tags": ["Science Fiction", "Hard Sci-Fi"],
        "comments": "An astronaut on a solo mission.",
        "author_sort": "Weir, Andy",
        "cover": "/path/to/cover2.jpg",
        "identifiers": {"isbn": "9780593135204"},
        "languages": ["eng"],
        "last_modified": "2023-10-25T12:00:00+00:00",
        "rating": 4,
        "series": None,
        "series_index": None,
        "size": 800000,
        "uuid": "some-uuid-2"
    }
]

# Sample calibredb output where authors/tags are comma-separated strings
SAMPLE_CALIBREDB_JSON_OUTPUT_STRINGS = [
    {
        "id": 1,
        "title": "Dune",
        "authors": "Frank Herbert, Another Author",
        "publisher": "Chilton Books",
        "pubdate": "1965-08-01T00:00:00+00:00",
        "isbn": "9780441172719",
        "formats": "EPUB, MOBI",
        "tags": "Science Fiction, Classic, Space Opera",
        "comments": "A masterpiece of science fiction.",
        "languages": "eng, fra"
        # Other fields omitted for brevity but should be there for full Book model validation
    }
]


@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_success(mock_subprocess_run):
    # Mock subprocess.run to return a successful response
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = json.dumps(SAMPLE_CALIBREDB_JSON_OUTPUT_ALL_FIELDS)
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.get("/books/")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["title"] == "Dune"
    assert response_data[0]["authors"] == ["Frank Herbert"] # Check if correctly parsed
    assert response_data[1]["title"] == "Project Hail Mary"

    # Check if calibredb was called with expected default arguments
    mock_subprocess_run.assert_called_once_with(
        ["calibredb", "list", "--for-machine", "--fields", "all"],
        capture_output=True, text=True, check=False, timeout=60
    )

@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_success_with_string_parsing(mock_subprocess_run):
    # Mock subprocess.run to return a successful response with comma-separated strings
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = json.dumps(SAMPLE_CALIBREDB_JSON_OUTPUT_STRINGS)
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.get("/books/")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["title"] == "Dune"
    assert response_data[0]["authors"] == ["Frank Herbert", "Another Author"]
    assert response_data[0]["tags"] == ["Science Fiction", "Classic", "Space Opera"]
    assert response_data[0]["formats"] == ["EPUB", "MOBI"]
    assert response_data[0]["languages"] == ["eng", "fra"]


@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_with_search_and_library_path(mock_subprocess_run):
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = json.dumps([SAMPLE_CALIBREDB_JSON_OUTPUT_ALL_FIELDS[0]]) # Return only one book
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    library_p = "/test/library"
    search_q = "title:Dune"
    response = client.get(f"/books/?library_path={library_p}&search={search_q}")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["title"] == "Dune"

    mock_subprocess_run.assert_called_once_with(
        ["calibredb", "list", "--for-machine", "--with-library", library_p, "--fields", "all", "--search", search_q],
        capture_output=True, text=True, check=False, timeout=60
    )

@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_calibredb_not_found(mock_subprocess_run):
    # Mock subprocess.run to raise FileNotFoundError
    mock_subprocess_run.side_effect = FileNotFoundError("calibredb not found")

    response = client.get("/books/")
    assert response.status_code == 503 # As defined in main.py for FileNotFoundError
    assert "calibredb command not found" in response.json()["detail"]

@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_calibredb_command_error(mock_subprocess_run):
    # Mock subprocess.run to simulate a command error
    mock_process = MagicMock()
    mock_process.returncode = 1 # Non-zero exit code
    mock_process.stdout = ""
    mock_process.stderr = "Some calibredb error"
    mock_subprocess_run.return_value = mock_process

    response = client.get("/books/")
    assert response.status_code == 500
    json_response = response.json()
    assert "Error interacting with calibredb" in json_response["detail"]
    # Check if the specific error message is part of the detail
    assert "calibredb command failed with exit code 1" in json_response["detail"]


@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_calibredb_json_decode_error(mock_subprocess_run):
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "This is not JSON" # Invalid JSON output
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.get("/books/")
    assert response.status_code == 500
    json_response = response.json()
    assert "Error interacting with calibredb" in json_response["detail"]
    assert "Failed to parse JSON output from calibredb" in json_response["detail"]

@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_empty_result_from_calibredb(mock_subprocess_run):
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "[]" # Empty list
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.get("/books/")
    assert response.status_code == 200
    assert response.json() == []

@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_calibredb_timeout(mock_subprocess_run):
    mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="calibredb list", timeout=1)

    response = client.get("/books/")
    assert response.status_code == 500
    json_response = response.json()
    assert "Error interacting with calibredb" in json_response["detail"]
    assert "calibredb command timed out" in json_response["detail"]

@patch('calibre_api.app.crud.list_books') # Mocking at the crud level for this test
def test_list_books_unexpected_error_in_endpoint(mock_list_books):
    # This tests if the endpoint's generic exception handler works
    mock_list_books.side_effect = Exception("A very unexpected error!")

    response = client.get("/books/")
    assert response.status_code == 500
    json_response = response.json()
    assert "An unexpected server error occurred" in json_response["detail"]
    assert "A very unexpected error!" in json_response["detail"]

# Test for malformed book data from calibredb that fails Pydantic validation in the endpoint
@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_malformed_book_data_from_calibredb(mock_subprocess_run):
    malformed_book_data = [
        {
            # "id": 1, # Missing required 'id' field
            "title": "Book with missing ID",
            "authors": ["Author"],
        }
    ]
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = json.dumps(malformed_book_data)
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.get("/books/")
    # The current implementation in main.py raises a 500 if any book fails validation.
    # FastAPI would return 422 if the response_model validation fails directly,
    # but here we iterate and parse, then raise HTTPException.
    assert response.status_code == 500
    json_response = response.json()
    assert "Error processing book data from calibredb" in json_response["detail"]
    # Pydantic v2 error message for missing field: "Field required"
    assert "Field required" in json_response["detail"] or "missing" in json_response["detail"].lower() # More general check for missing field
    assert "id" in json_response["detail"] # Check that the problematic field is mentioned.

# To run these tests:
# Ensure pytest and fastapi[all] are installed
# From the root directory of your project (containing calibre_api folder):
# python -m pytest calibre_api/tests/test_main.py
#
# Or if your current directory is `calibre_api`:
# python -m pytest tests/test_main.py
#
# (Adjust paths as per your actual project structure and how you run pytest)
