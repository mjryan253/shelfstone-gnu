import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import subprocess
import json

# Adjust import path if necessary based on your project structure
# Assuming your main app is in calibre_api/app/main.py
from calibre_api.app.main import app
from calibre_api.app.crud import CalibredbError

# client = TestClient(app) # Initialize client inside a fixture or test for better isolation

@pytest.fixture(scope="module")
def client():
    # Re-import app here if there are concerns about module caching affecting router state
    # from calibre_api.app.main import app
    # For debugging routing:
    # print("App routes at client fixture creation:")
    # for route in app.routes:
    #     print(f"  Fixture Route: {route.path}, Name: {route.name}, Methods: {getattr(route, 'methods', 'N/A')}")
    return TestClient(app)


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
def test_list_books_success(client, mock_subprocess_run):
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
def test_list_books_success_with_string_parsing(client, mock_subprocess_run):
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
def test_list_books_with_search_and_library_path(client, mock_subprocess_run):
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
def test_list_books_calibredb_not_found(client, mock_subprocess_run):
    # Mock subprocess.run to raise FileNotFoundError
    mock_subprocess_run.side_effect = FileNotFoundError("calibredb not found")

    response = client.get("/books/")
    assert response.status_code == 503 # As defined in main.py for FileNotFoundError
    assert "calibredb command not found" in response.json()["detail"]

@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_calibredb_command_error(client, mock_subprocess_run):
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
def test_list_books_calibredb_json_decode_error(client, mock_subprocess_run):
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
def test_list_books_empty_result_from_calibredb(client, mock_subprocess_run):
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "[]" # Empty list
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.get("/books/")
    assert response.status_code == 200
    assert response.json() == []

@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_calibredb_timeout(client, mock_subprocess_run):
    mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="calibredb list", timeout=1)

    response = client.get("/books/")
    assert response.status_code == 500
    json_response = response.json()
    assert "Error interacting with calibredb" in json_response["detail"]
    assert "calibredb command timed out" in json_response["detail"]

@patch('calibre_api.app.main.list_books') # Patched at main where it's called
def test_list_books_unexpected_error_in_endpoint(client, mock_main_list_books):
    # This tests if the endpoint's generic exception handler works
    # This mock will intercept the call made from within the get_books_endpoint in main.py
    mock_main_list_books.side_effect = Exception("A very unexpected error!")

    response = client.get("/books/")
    assert response.status_code == 500
    json_response = response.json()
    assert "An unexpected server error occurred" in json_response["detail"]
    assert "A very unexpected error!" in json_response["detail"]

# Test for malformed book data from calibredb that fails Pydantic validation in the endpoint
@patch('calibre_api.app.crud.subprocess.run')
def test_list_books_malformed_book_data_from_calibredb(client, mock_subprocess_run):
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


# --- Tests for /books/add/ endpoint ---
from io import BytesIO
from unittest.mock import Mock # Ensure Mock is imported if not already

@patch('calibre_api.app.main.tempfile.mkdtemp', return_value='/tmp/mocktempdir')
@patch('calibre_api.app.main.shutil.copyfileobj')
@patch('calibre_api.app.main.shutil.rmtree')
@patch('calibre_api.app.main.os.path.exists', return_value=True) # Mock os.path.exists for temp file path
@patch('calibre_api.app.crud.os.path.exists', return_value=True) # Mock os.path.exists for book file in crud
@patch('calibre_api.app.crud.subprocess.run')
def test_add_book_endpoint_success(
    client, mock_subprocess_run, mock_crud_os_path_exists, mock_main_os_path_exists,
    mock_rmtree, mock_copyfileobj, mock_mkdtemp
):
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "Added book IDs: 789"
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    file_content = b"fake epub content"
    files = {'file': ('new_book.epub', BytesIO(file_content), 'application/epub+zip')}
    data = {
        'title': 'New Awesome Book',
        'authors': 'A. N. Author',
        'tags': 'epic,fantasy',
        'library_path': '/fakelib'
    }

    response = client.post("/books/add/", files=files, data=data)

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "Book(s) added successfully."
    assert json_response["added_book_ids"] == [789]

    # Check subprocess call
    expected_cmd_part = [
        "calibredb", "add",
        "--with-library", "/fakelib",
        "--metadata", "title:New Awesome Book,authors:A. N. Author,tags:epic,fantasy",
        "--", "/tmp/mocktempdir/new_book.epub" # Assuming mkdtemp returns this and filename is used
    ]
    # We need to check that all elements of expected_cmd_part are in the actual call args
    # The order of metadata items might vary if dicts are used internally before joining.
    # For simplicity, we'll check for substrings for metadata.
    called_args, _ = mock_subprocess_run.call_args
    actual_cmd = called_args[0]

    assert actual_cmd[0:3] == expected_cmd_part[0:3] # calibredb, add, --with-library
    assert actual_cmd[3] == expected_cmd_part[3] # /fakelib
    assert actual_cmd[4] == expected_cmd_part[4] # --metadata
    # Check metadata string contents loosely
    assert "title:New Awesome Book" in actual_cmd[5]
    assert "authors:A. N. Author" in actual_cmd[5]
    assert "tags:epic,fantasy" in actual_cmd[5]
    assert actual_cmd[6] == expected_cmd_part[6] # --
    assert actual_cmd[7] == expected_cmd_part[7] # file path

    mock_mkdtemp.assert_called_once()
    mock_copyfileobj.assert_called_once()
    mock_rmtree.assert_called_once_with('/tmp/mocktempdir')


@patch('calibre_api.app.main.tempfile.mkdtemp', return_value='/tmp/mocktempdir')
@patch('calibre_api.app.main.shutil.copyfileobj')
@patch('calibre_api.app.main.shutil.rmtree')
@patch('calibre_api.app.main.os.path.exists', return_value=True)
@patch('calibre_api.app.crud.os.path.exists', return_value=True)
@patch('calibre_api.app.crud.subprocess.run')
def test_add_book_endpoint_no_ids_returned(
    client, mock_subprocess_run, mock_crud_os_path_exists, mock_main_os_path_exists,
    mock_rmtree, mock_copyfileobj, mock_mkdtemp
):
    mock_process = MagicMock()
    mock_process.returncode = 0
    # Simulate calibredb output when a book is recognized as a duplicate and not added,
    # or some other scenario where it succeeds but doesn't report new IDs.
    mock_process.stdout = "No books added"
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    file_content = b"more fake content"
    files = {'file': ('another_book.epub', BytesIO(file_content), 'application/epub+zip')}

    response = client.post("/books/add/", files=files)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "Book was processed but no new entries were added to the library."
    assert json_response["added_book_ids"] == []
    mock_rmtree.assert_called_once_with('/tmp/mocktempdir')


@patch('calibre_api.app.main.tempfile.mkdtemp', return_value='/tmp/mocktempdir')
@patch('calibre_api.app.main.shutil.copyfileobj')
@patch('calibre_api.app.main.shutil.rmtree')
@patch('calibre_api.app.main.os.path.exists', return_value=True)
@patch('calibre_api.app.crud.os.path.exists', return_value=True)
@patch('calibre_api.app.crud.subprocess.run')
def test_add_book_endpoint_calibredb_cli_error(
    client, mock_subprocess_run, mock_crud_os_path_exists, mock_main_os_path_exists,
    mock_rmtree, mock_copyfileobj, mock_mkdtemp
):
    mock_process = MagicMock()
    mock_process.returncode = 1 # Error code
    mock_process.stdout = ""
    mock_process.stderr = "Calibredb exploded!"
    mock_subprocess_run.return_value = mock_process

    file_content = b"error content"
    files = {'file': ('error_book.epub', BytesIO(file_content), 'application/epub+zip')}

    response = client.post("/books/add/", files=files)
    assert response.status_code == 500
    json_response = response.json()
    assert "Error using calibredb add" in json_response["detail"]
    assert "calibredb add command failed with exit code 1" in json_response["detail"]
    mock_rmtree.assert_called_once_with('/tmp/mocktempdir')


@patch('calibre_api.app.main.tempfile.mkdtemp', return_value='/tmp/mocktempdir')
@patch('calibre_api.app.main.shutil.copyfileobj')
@patch('calibre_api.app.main.shutil.rmtree')
@patch('calibre_api.app.crud.add_book') # Mock the whole crud function
def test_add_book_endpoint_calibredb_exec_not_found(
    client, mock_add_book_crud, mock_rmtree, mock_copyfileobj, mock_mkdtemp
):
    # Simulate FileNotFoundError for the calibredb executable itself
    mock_add_book_crud.side_effect = FileNotFoundError("calibredb not found here")

    file_content = b"any content"
    files = {'file': ('any_book.epub', BytesIO(file_content), 'application/epub+zip')}

    response = client.post("/books/add/", files=files)
    assert response.status_code == 503
    json_response = response.json()
    assert "calibredb command not found" in json_response["detail"]
    mock_rmtree.assert_called_once_with('/tmp/mocktempdir')


def test_add_book_endpoint_missing_file_upload(client):
    # No file uploaded, should result in 422 from FastAPI
    # print("Routes available to TestClient in test_add_book_endpoint_missing_file_upload:")
    # for route in client.app.routes:
    #     print(f"  Path: {route.path}, Name: {route.name}, Methods: {getattr(route, 'methods', 'N/A')}")

    response = client.post("/books/add/", data={'title': 'A Book With No File'})
    assert response.status_code == 422 # Unprocessable Entity
    json_response = response.json()
    assert json_response["detail"][0]["loc"] == ["body", "file"]
    assert json_response["detail"][0]["msg"] == "field required"


@patch('calibre_api.app.main.tempfile.mkdtemp', return_value='/tmp/mocktempdir')
@patch('calibre_api.app.main.shutil.copyfileobj')
@patch('calibre_api.app.main.shutil.rmtree')
@patch('calibre_api.app.crud.add_book')
def test_add_book_endpoint_value_error_from_crud(
    client, mock_add_book_crud, mock_rmtree, mock_copyfileobj, mock_mkdtemp
):
    # For example, if crud.add_book raises ValueError because the temp file path isn't found
    # (though os.path.exists is mocked above, this tests the handler for other ValueErrors from crud)
    mock_add_book_crud.side_effect = ValueError("Specific value error from CRUD")

    file_content = b"value error test"
    files = {'file': ('value.epub', BytesIO(file_content), 'application/epub+zip')}
    response = client.post("/books/add/", files=files)

    assert response.status_code == 400 # As per current main.py handling
    json_response = response.json()
    assert "Specific value error from CRUD" in json_response["detail"]
    mock_rmtree.assert_called_once_with('/tmp/mocktempdir')


# To run these tests:
# Ensure pytest and fastapi[all] are installed
# From the root directory of your project (containing calibre_api folder):
# python -m pytest calibre_api/tests/test_main.py
#
# Or if your current directory is `calibre_api`:
# python -m pytest tests/test_main.py
#
# (Adjust paths as per your actual project structure and how you run pytest)


# --- Tests for DELETE /books/{book_id}/ endpoint ---

@patch('calibre_api.app.crud.subprocess.run')
def test_remove_book_endpoint_success(client, mock_subprocess_run):
    book_id_to_remove = 42
    mock_process = MagicMock()
    mock_process.returncode = 0
    # calibredb remove_books --for-machine output for success
    mock_process.stdout = json.dumps({"ok": True, "num_removed": 1, "removed_ids": [book_id_to_remove]})
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.delete(f"/books/{book_id_to_remove}/")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == f"Book ID {book_id_to_remove} removed successfully."
    assert json_response["removed_book_id"] == book_id_to_remove

    # Check subprocess call
    expected_cmd = ["calibredb", "remove_books", "--permanent", "--for-machine", str(book_id_to_remove)]
    mock_subprocess_run.assert_called_once()
    called_args, _ = mock_subprocess_run.call_args
    assert called_args[0] == expected_cmd

@patch('calibre_api.app.crud.subprocess.run')
def test_remove_book_endpoint_book_not_found(client, mock_subprocess_run):
    book_id_not_found = 999
    mock_process = MagicMock()
    mock_process.returncode = 0 # remove_books --for-machine returns 0 even if book not found
    mock_process.stdout = json.dumps({
        "ok": False,
        "num_removed": 0,
        "removed_ids": [],
        "errors": [{"id": book_id_not_found, "error": "Book not found"}]
    })
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.delete(f"/books/{book_id_not_found}/")
    assert response.status_code == 404 # As per endpoint logic for "not found" error from calibredb
    json_response = response.json()
    assert f"Book with ID {book_id_not_found} not found" in json_response["detail"]

def test_remove_book_endpoint_invalid_book_id(client):
    response = client.delete("/books/0/") # Invalid ID (non-positive)
    assert response.status_code == 400
    assert "Book ID must be a positive integer" in response.json()["detail"]

    response = client.delete("/books/-1/") # Invalid ID
    assert response.status_code == 400
    assert "Book ID must be a positive integer" in response.json()["detail"]

    # Non-integer ID will be caught by FastAPI path param validation (422)
    response = client.delete("/books/abc/")
    assert response.status_code == 422 # Unprocessable Entity from FastAPI

@patch('calibre_api.app.crud.subprocess.run')
def test_remove_book_endpoint_calibredb_cli_error(client, mock_subprocess_run):
    book_id_error = 77
    mock_process = MagicMock()
    mock_process.returncode = 1 # CLI error
    mock_process.stdout = ""
    mock_process.stderr = "Some internal calibredb error during remove"
    mock_subprocess_run.return_value = mock_process

    response = client.delete(f"/books/{book_id_error}/")
    assert response.status_code == 500
    json_response = response.json()
    assert "Error using calibredb remove_books" in json_response["detail"]
    assert "calibredb remove_books command failed with exit code 1" in json_response["detail"]

@patch('calibre_api.app.crud.remove_book') # Mock the whole crud function
def test_remove_book_endpoint_calibredb_exec_not_found(client, mock_remove_book_crud):
    book_id = 88
    # Simulate FileNotFoundError for the calibredb executable itself
    mock_remove_book_crud.side_effect = FileNotFoundError("calibredb (remove) not found")

    response = client.delete(f"/books/{book_id}/")
    assert response.status_code == 503
    json_response = response.json()
    assert "calibredb command not found" in json_response["detail"]

@patch('calibre_api.app.crud.subprocess.run')
def test_remove_book_endpoint_calibredb_json_parse_error(client, mock_subprocess_run):
    book_id_to_remove = 43
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "This is not valid JSON" # Bad output from calibredb
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.delete(f"/books/{book_id_to_remove}/")
    assert response.status_code == 500 # CalibredbError due to JSON parsing
    assert "Failed to parse JSON output from calibredb remove_books" in response.json()["detail"]

@patch('calibre_api.app.crud.subprocess.run')
def test_remove_book_endpoint_calibredb_ok_false_no_specific_error(client, mock_subprocess_run):
    book_id_to_remove = 44
    mock_process = MagicMock()
    mock_process.returncode = 0
    # Calibredb reports ok:false but doesn't give a specific error message for the ID in the "errors" list
    mock_process.stdout = json.dumps({"ok": False, "num_removed": 0, "removed_ids": [], "errors": []})
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.delete(f"/books/{book_id_to_remove}/")
    assert response.status_code == 500 # Endpoint treats this as a server-side/calibredb tool issue
    assert f"Calibredb failed to remove book ID {book_id_to_remove}, reason unspecified" in response.json()["detail"]

@patch('calibre_api.app.crud.subprocess.run')
def test_remove_book_endpoint_calibredb_ok_true_but_not_removed(client, mock_subprocess_run):
    book_id_to_remove = 45
    mock_process = MagicMock()
    mock_process.returncode = 0
    # Calibredb reports ok:true but doesn't list the ID as removed or num_removed is 0
    mock_process.stdout = json.dumps({"ok": True, "num_removed": 0, "removed_ids": []})
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.delete(f"/books/{book_id_to_remove}/")
    assert response.status_code == 404 # Endpoint treats this as "not found or already removed"
    assert f"Book with ID {book_id_to_remove} not found or already removed" in response.json()["detail"]


# --- Tests for PUT /books/{book_id}/metadata/ endpoint ---

@patch('calibre_api.app.crud.subprocess.run')
def test_set_metadata_endpoint_success(client, mock_subprocess_run):
    book_id_to_update = 123
    update_payload = {
        "title": "New Title",
        "authors": ["Author A", "Author B"],
        "tags": ["updated", "test"],
        "rating": 8 # Corresponds to 4 stars
    }
    # Expected output from `calibredb set_metadata --for-machine` if changes are made
    mock_calibredb_output = {"title": "New Title", "authors": ["Author A", "Author B"], "tags": ["updated", "test"], "rating": 8}

    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = json.dumps(mock_calibredb_output)
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.put(f"/books/{book_id_to_update}/metadata/", json=update_payload)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == f"Metadata for book ID {book_id_to_update} updated successfully."
    assert json_response["book_id"] == book_id_to_update
    assert "Changes applied: " in json_response["details"]
    for key in update_payload.keys():
        assert key in json_response["details"] # Check that all updated keys are mentioned

    # Check subprocess call arguments
    mock_subprocess_run.assert_called_once()
    called_args_list = mock_subprocess_run.call_args[0][0] # Get the list of cmd arguments
    assert str(book_id_to_update) in called_args_list
    assert "title:New Title" in called_args_list
    assert "authors:Author A,Author B" in called_args_list # Check comma separation
    assert "tags:updated,test" in called_args_list
    assert "rating:8.0" in called_args_list # crud formats rating as float string


@patch('calibre_api.app.crud.subprocess.run')
def test_set_metadata_endpoint_book_not_found_or_no_changes(client, mock_subprocess_run):
    book_id_not_found = 999
    update_payload = {"title": "Attempted Update"}
    # `calibredb set_metadata --for-machine` returns {} if book not found or no changes made
    mock_calibredb_output = {}

    mock_process = MagicMock()
    mock_process.returncode = 0 # Exit code is 0 even if book not found
    mock_process.stdout = json.dumps(mock_calibredb_output)
    mock_process.stderr = "" # Or sometimes "No book with id 999 found" but exit code is still 0.
    mock_subprocess_run.return_value = mock_process

    response = client.put(f"/books/{book_id_not_found}/metadata/", json=update_payload)
    # Current endpoint logic raises 404 if update_result is empty from crud
    assert response.status_code == 404
    assert f"Book with ID {book_id_not_found} not found, or no metadata was actually changed" in response.json()["detail"]


def test_set_metadata_endpoint_invalid_book_id(client):
    response = client.put("/books/0/metadata/", json={"title": "Test"})
    assert response.status_code == 400
    assert "Book ID must be a positive integer" in response.json()["detail"]

    # Non-integer ID caught by FastAPI path param validation
    response = client.put("/books/abc/metadata/", json={"title": "Test"})
    assert response.status_code == 422


def test_set_metadata_endpoint_no_metadata_provided(client):
    book_id = 1
    response = client.put(f"/books/{book_id}/metadata/", json={}) # Empty payload
    assert response.status_code == 400
    assert "No metadata fields provided" in response.json()["detail"]


@patch('calibre_api.app.crud.subprocess.run')
def test_set_metadata_endpoint_calibredb_cli_error(client, mock_subprocess_run):
    book_id_error = 77
    update_payload = {"title": "Error Update"}
    mock_process = MagicMock()
    mock_process.returncode = 1 # CLI error
    mock_process.stdout = ""
    mock_process.stderr = "calibredb exploded during set_metadata"
    mock_subprocess_run.return_value = mock_process

    response = client.put(f"/books/{book_id_error}/metadata/", json=update_payload)
    assert response.status_code == 500
    json_response = response.json()
    assert "Error using calibredb set_metadata" in json_response["detail"]
    assert "calibredb set_metadata command failed with exit code 1" in json_response["detail"]

@patch('calibre_api.app.crud.subprocess.run')
def test_set_metadata_endpoint_calibredb_cli_error_book_not_found_in_stderr(client, mock_subprocess_run):
    book_id_error = 78
    update_payload = {"title": "Error Update"}
    mock_process = MagicMock()
    mock_process.returncode = 1 # CLI error
    mock_process.stdout = "" # Important: set_metadata might return non-zero with "No book with id" in stderr
    mock_process.stderr = f"No book with id {book_id_error} found"
    mock_subprocess_run.return_value = mock_process

    response = client.put(f"/books/{book_id_error}/metadata/", json=update_payload)
    # The endpoint logic now specifically checks for this stderr message if CalibredbError is raised
    assert response.status_code == 404
    assert f"Book with ID {book_id_error} not found in the library" in response.json()["detail"]


@patch('calibre_api.app.crud.set_book_metadata') # Mock the whole crud function
def test_set_metadata_endpoint_calibredb_exec_not_found(client, mock_set_metadata_crud):
    book_id = 88
    update_payload = {"title": "Any Update"}
    mock_set_metadata_crud.side_effect = FileNotFoundError("calibredb (set_metadata) not found")

    response = client.put(f"/books/{book_id}/metadata/", json=update_payload)
    assert response.status_code == 503
    assert "calibredb command not found" in response.json()["detail"]


@patch('calibre_api.app.crud.subprocess.run')
def test_set_metadata_endpoint_json_parse_error(client, mock_subprocess_run):
    book_id = 89
    update_payload = {"title": "JSON Error Test"}
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "Not JSON" # Invalid JSON from calibredb
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process

    response = client.put(f"/books/{book_id}/metadata/", json=update_payload)
    assert response.status_code == 500 # CalibredbError due to JSON parsing in CRUD
    assert "Failed to parse JSON output from calibredb set_metadata" in response.json()["detail"]


# --- Tests for New CLI Endpoints ---
# We'll need to mock functions from calibre_api.app.calibre_cli
# And potentially os, tempfile, shutil if those are used directly in endpoints before calling cli wrappers

# Mock for calibre_cli functions
# Each test will patch the specific calibre_cli function it's testing against for that endpoint.

# Test GET /calibre/version/
@patch('calibre_api.app.main.calibre_cli.get_calibre_version')
def test_get_calibre_version_endpoint(mock_get_version, client):
    mock_get_version.return_value = "6.15.0"
    response = client.get("/calibre/version/")
    assert response.status_code == 200
    assert response.json() == {"calibre_version": "6.15.0", "details": None}

    mock_get_version.return_value = "calibre (calibre 6.15.0)\nCopyright Kovid Goyal"
    response = client.get("/calibre/version/")
    assert response.status_code == 200
    assert response.json() == {"calibre_version": "6.15.0", "details": "calibre (calibre 6.15.0)\nCopyright Kovid Goyal"}


@patch('calibre_api.app.main.calibre_cli.get_calibre_version', side_effect=FileNotFoundError("calibre not found"))
def test_get_calibre_version_endpoint_not_found(mock_get_version, client):
    response = client.get("/calibre/version/")
    assert response.status_code == 503
    assert "Calibre command not found" in response.json()["detail"]

@patch('calibre_api.app.main.calibre_cli.get_calibre_version', side_effect=CalibredbError("CLI failed")) # Using CalibredbError as a stand-in for CalibreCLIError for now
def test_get_calibre_version_endpoint_cli_error(mock_get_version, client):
    # Adjust if CalibreCLIError is distinct and used in calibre_cli
    from calibre_api.app.calibre_cli import CalibreCLIError # Ensure this is the correct error type
    mock_get_version.side_effect = CalibreCLIError("CLI failed", stderr="details")
    response = client.get("/calibre/version/")
    assert response.status_code == 500
    assert "Failed to get Calibre version: CLI failed" in response.json()["detail"]


# Test POST /ebook/convert/
# This endpoint is tricky because it's meant to return a FileResponse if fully implemented,
# but the current main.py returns JSON. We'll test the JSON response.
@patch('calibre_api.app.main.tempfile.gettempdir', return_value="/mocked_temp")
@patch('calibre_api.app.main.os.path.join', lambda *args: "/".join(args)) # Simple mock for os.path.join
@patch('calibre_api.app.main.shutil.copyfileobj')
@patch('calibre_api.app.main.os.remove')
@patch('calibre_api.app.main.calibre_cli.ebook_convert')
def test_ebook_convert_endpoint_json_response(mock_ebook_convert, mock_os_remove, mock_copyfileobj, mock_gettempdir, client):
    mock_ebook_convert.return_value = "/mocked_temp/convert_out_test_book.mobi" # Path to converted file

    file_content = b"dummy epub content"
    # Prepare form data for EbookConvertRequest
    form_data = {'output_format': 'mobi', 'options': json.dumps(['--authors', 'Test Author'])}

    # Send request with file and form data
    # Note: FastAPI TestClient expects options to be sent multiple times if it's a List[str] from Form.
    # If EbookConvertRequest is a single Form field expecting JSON string, this is different.
    # The current endpoint has `request: EbookConvertRequest = Form(...)`
    # This is unusual. Normally, you'd have individual Form fields or a JSON body (if not for files).
    # For `Form(EbookConvertRequest)`, FastAPI expects the client to send a JSON string for the `request` field.

    response = client.post(
        "/ebook/convert/",
        files={'input_file': ('test_book.epub', BytesIO(file_content), 'application/epub+zip')},
        data={'request': json.dumps({'output_format': 'mobi', 'options': ['--authors', 'Test Author']})}
    )

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["message"] == "File converted successfully. It is available on the server."
    assert json_data["output_filename"] == "test_book.mobi"

    # Assert that calibre_cli.ebook_convert was called correctly
    # Path construction for temp_input_path and temp_output_path involves uuid, so exact match is hard.
    # Check that it was called, and relevant options are present.
    mock_ebook_convert.assert_called_once()
    call_args = mock_ebook_convert.call_args[1] # Get keyword arguments
    assert call_args['input_file'].startswith("/mocked_temp/convert_in_")
    assert call_args['output_file'].startswith("/mocked_temp/convert_out_")
    assert call_args['options'] == ['--authors', 'Test Author']

    mock_os_remove.assert_called_once() # For temp_input_path


# Test POST /ebook/metadata/get/
@patch('calibre_api.app.main.tempfile.gettempdir', return_value="/mocked_temp")
@patch('calibre_api.app.main.os.path.join', lambda *args: "/".join(args))
@patch('calibre_api.app.main.shutil.copyfileobj')
@patch('calibre_api.app.main.os.remove')
@patch('calibre_api.app.main.calibre_cli.get_ebook_metadata')
def test_get_ebook_metadata_endpoint(mock_get_meta, mock_os_remove, mock_copyfileobj, mock_gettempdir, client):
    mock_get_meta.return_value = {"title": "Test Book", "authors": ["Author"]} # JSON output

    response = client.post(
        "/ebook/metadata/get/?as_json=true",
        files={'input_file': ('book.epub', BytesIO(b"content"), 'application/epub+zip')}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["message"] == "Metadata extracted successfully."
    assert json_data["filename"] == "book.epub"
    assert json_data["metadata_content"] == {"title": "Test Book", "authors": ["Author"]}
    mock_get_meta.assert_called_once()
    call_args = mock_get_meta.call_args[1]
    assert call_args['ebook_file_path'].startswith("/mocked_temp/meta_in_")
    assert call_args['as_json'] is True


# Test POST /ebook/metadata/set/ (returns FileResponse)
@patch('calibre_api.app.main.tempfile.gettempdir', return_value="/mocked_temp")
@patch('calibre_api.app.main.os.path.join', lambda *args: "/".join(args))
@patch('calibre_api.app.main.shutil.copyfileobj')
# @patch('calibre_api.app.main.os.remove') # FileResponse handles its own lifecycle for temp files passed as objects
@patch('calibre_api.app.main.calibre_cli.set_ebook_metadata')
@patch('calibre_api.app.main.FileResponse') # Mock FileResponse to check its args
def test_set_ebook_metadata_endpoint(mock_file_response_cls, mock_set_meta, mock_copyfileobj, mock_gettempdir, client):
    mock_set_meta.return_value = "Metadata changed." # stdout from CLI tool

    # Mock the actual FileResponse object that would be created
    mock_file_response_instance = MagicMock()
    mock_file_response_cls.return_value = mock_file_response_instance

    response = client.post(
        "/ebook/metadata/set/",
        files={'input_file': ('book_to_mod.epub', BytesIO(b"epub data"), 'application/epub+zip')},
        data={'request': json.dumps({'metadata_options': ['--title', 'Updated']})}
    )
    assert response.status_code == 200 # Assuming FileResponse returns 200 by default

    # Verify FileResponse was called correctly
    mock_file_response_cls.assert_called_once()
    fr_call_args = mock_file_response_cls.call_args[1]
    assert fr_call_args['path'].startswith("/mocked_temp/meta_set_")
    assert fr_call_args['filename'] == 'book_to_mod.epub'

    # Verify calibre_cli.set_ebook_metadata was called
    mock_set_meta.assert_called_once()
    cli_call_args = mock_set_meta.call_args[1]
    assert cli_call_args['ebook_file_path'].startswith("/mocked_temp/meta_set_")
    assert cli_call_args['metadata_options'] == ['--title', 'Updated']


# Test POST /ebook/polish/
@patch('calibre_api.app.main.tempfile.gettempdir', return_value="/mocked_temp")
@patch('calibre_api.app.main.os.path.join', lambda *args: "/".join(args))
@patch('calibre_api.app.main.shutil.copyfileobj')
@patch('calibre_api.app.main.os.remove') # For temp_input_path
@patch('calibre_api.app.main.calibre_cli.ebook_polish')
@patch('calibre_api.app.main.FileResponse')
def test_ebook_polish_endpoint(mock_file_response_cls, mock_ebook_polish, mock_os_remove, mock_copyfileobj, mock_gettempdir, client):
    mock_ebook_polish.return_value = "/mocked_temp/polish_out_polished_book.epub" # Path to polished file
    mock_file_response_instance = MagicMock()
    mock_file_response_cls.return_value = mock_file_response_instance

    response = client.post(
        "/ebook/polish/",
        files={'input_file': ('book.epub', BytesIO(b"content"), 'application/epub+zip')},
        data={'output_filename_suffix': '_superpolished', 'options': ['--subset-fonts']} # options must be sent one by one or as JSON string
    )
    assert response.status_code == 200
    mock_file_response_cls.assert_called_once()
    fr_call_args = mock_file_response_cls.call_args[1]
    assert fr_call_args['path'] == "/mocked_temp/polish_out_polished_book.epub"
    assert fr_call_args['filename'] == 'book_superpolished.epub'

    mock_ebook_polish.assert_called_once()
    cli_call_args = mock_ebook_polish.call_args[1]
    assert cli_call_args['ebook_file_path'].startswith("/mocked_temp/polish_in_")
    assert cli_call_args['output_file_path'].startswith("/mocked_temp/polish_out_")
    assert cli_call_args['options'] == ['--subset-fonts']


# Test GET /ebook/metadata/fetch/
@patch('calibre_api.app.main.calibre_cli.fetch_ebook_metadata')
def test_fetch_ebook_metadata_endpoint(mock_fetch_meta, client):
    mock_fetch_meta.return_value = {"title": "Fetched Book", "source": "online"}
    response = client.get("/ebook/metadata/fetch/?title=Test&authors=Author")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["message"] == "Metadata fetched successfully."
    assert json_data["metadata"] == {"title": "Fetched Book", "source": "online"}
    mock_fetch_meta.assert_called_with(title="Test", authors="Author", isbn=None, as_json=True)

@patch('calibre_api.app.main.calibre_cli.fetch_ebook_metadata', side_effect=CalibreCLIError("No metadata found", stderr="details"))
def test_fetch_ebook_metadata_endpoint_no_results(mock_fetch_meta, client):
    response = client.get("/ebook/metadata/fetch/?title=Unknown")
    assert response.status_code == 200 # Specific handling for "No metadata found"
    json_data = response.json()
    assert json_data["message"] == "No metadata found for the given criteria."
    assert json_data["metadata"] is None


# Test POST /web2disk/generate-recipe/
@patch('calibre_api.app.main.tempfile.gettempdir', return_value="/mocked_temp")
@patch('calibre_api.app.main.os.path.join', lambda *args: "/".join(args))
# @patch('calibre_api.app.main.os.remove') # FileResponse with BackgroundTask for cleanup
@patch('calibre_api.app.main.calibre_cli.web2disk')
@patch('calibre_api.app.main.FileResponse')
def test_web2disk_generate_recipe_endpoint(mock_file_response_cls, mock_web2disk, mock_gettempdir, client):
    mock_web2disk.return_value = "/mocked_temp/recipe_example_com_page.recipe"
    mock_file_response_instance = MagicMock()
    mock_file_response_cls.return_value = mock_file_response_instance

    payload = {"url": "http://example.com/page", "options": ["--max-articles-per-feed", "1"]}
    response = client.post("/web2disk/generate-recipe/", json=payload)

    assert response.status_code == 200
    mock_file_response_cls.assert_called_once()
    fr_call_args = mock_file_response_cls.call_args[1]
    assert fr_call_args['path'] == "/mocked_temp/recipe_example_com_page.recipe"
    assert fr_call_args['filename'] == "example_com_page.recipe" # Check derived filename

    mock_web2disk.assert_called_once_with(
        url="http://example.com/page",
        output_recipe_file=mock.ANY, # Temp path is dynamic
        options=["--max-articles-per-feed", "1"]
    )
    assert mock_web2disk.call_args[1]['output_recipe_file'].endswith("_example_com_page.recipe")


# Test LRF converters
@patch('calibre_api.app.main.tempfile.gettempdir', return_value="/mocked_temp")
@patch('calibre_api.app.main.os.path.join', lambda *args: "/".join(args))
@patch('calibre_api.app.main.shutil.copyfileobj')
@patch('calibre_api.app.main.os.remove')
@patch('calibre_api.app.main.calibre_cli.lrf2lrs')
@patch('calibre_api.app.main.FileResponse')
def test_lrf_to_lrs_endpoint(mock_file_response_cls, mock_lrf2lrs, mock_os_remove, mock_copyfileobj, mock_gettempdir, client):
    mock_lrf2lrs.return_value = "/mocked_temp/lrf2lrs_out_book.lrs"
    mock_file_response_instance = MagicMock()
    mock_file_response_cls.return_value = mock_file_response_instance

    response = client.post(
        "/ebook/convert/lrf-to-lrs/",
        files={'input_file': ('book.lrf', BytesIO(b"lrf"), 'application/octet-stream')}
    )
    assert response.status_code == 200
    mock_file_response_cls.assert_called_once_with(
        path="/mocked_temp/lrf2lrs_out_book.lrs",
        filename="book.lrs",
        media_type="application/octet-stream",
        headers=mock.ANY
    )
    mock_lrf2lrs.assert_called_once()


# Test GET /calibre/plugins/
@patch('calibre_api.app.main.calibre_cli.list_calibre_plugins')
def test_list_plugins_endpoint(mock_list_plugins, client):
    mock_list_plugins.return_value = {"PluginA": {"version": "1.0"}}
    response = client.get("/calibre/plugins/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["message"] == "Successfully retrieved plugin list."
    assert json_data["count"] == 1
    assert json_data["plugins"] == {"PluginA": {"version": "1.0"}}


# Test POST /calibre/debug/test-build/
@patch('calibre_api.app.main.calibre_cli.run_calibre_debug_test_build')
def test_debug_test_build_endpoint(mock_run_test_build, client):
    mock_run_test_build.return_value = "All tests passed."
    response = client.post("/calibre/debug/test-build/?timeout=30")
    assert response.status_code == 200
    json_data = response.json()
    assert "All tests passed" in json_data["message"]
    assert json_data["output"] == "All tests passed."
    mock_run_test_build.assert_called_with(timeout=30)


# Test POST /calibre/send-email/
@patch('calibre_api.app.main.tempfile.gettempdir', return_value="/mocked_temp")
@patch('calibre_api.app.main.os.path.join', lambda *args: "/".join(args))
@patch('calibre_api.app.main.shutil.copyfileobj')
@patch('calibre_api.app.main.os.remove')
@patch('calibre_api.app.main.calibre_cli.send_email_with_calibre_smtp')
def test_send_email_endpoint(mock_send_email, mock_os_remove, mock_copyfileobj, mock_gettempdir, client):
    mock_send_email.return_value = (True, "Email sent successfully.")
    email_payload = {
        "recipient_email": "to@example.com", "subject": "Hi", "body": "There",
        "smtp_server": "s", "smtp_port": 123, "smtp_encryption": "tls"
    }
    # Test without attachment
    response = client.post("/calibre/send-email/", json=email_payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["message"] == "Email sent successfully."
    mock_send_email.assert_called_with(
        recipient_email="to@example.com", subject="Hi", body="There",
        smtp_server="s", smtp_port=123, smtp_encryption="tls",
        attachment_path=None, smtp_username=None, smtp_password=None, # Defaults
        sender_email=None, reply_to_email=None
    )

    # Test with attachment
    mock_send_email.reset_mock()
    mock_send_email.return_value = (True, "Email sent with attachment.")
    response = client.post(
        "/calibre/send-email/",
        files={'attachment_file': ('attach.txt', BytesIO(b"attach"), 'text/plain')},
        # When files are present, other payload needs to be in 'data' and might need careful formatting
        # For simplicity, assume the SmtpSendRequest is sent as a JSON string part if client supports it.
        # Or define individual Form fields. The current endpoint `request: SmtpSendRequest = Body(...)`
        # implies Content-Type: application/json for the main payload, which conflicts with multipart/form-data for files.
        # This endpoint structure needs review for mixed JSON body and file.
        # A common way is all Form fields, or a JSON string part for the main model.
        # Let's assume the test client sends SmtpSendRequest as a 'request' part for this test to proceed.
        # This would require `request: SmtpSendRequest = Form(...)` or similar in endpoint.
        # Given `Body(...)`, this test for attachment + JSON body is complex with TestClient.
        # Skipping the attachment part of this specific test due to ambiguity of mixed Body and File.
        # The unit test for calibre_cli.send_email_with_calibre_smtp covers attachment logic.


# Test POST /ebook/check/
@patch('calibre_api.app.main.tempfile.gettempdir', return_value="/mocked_temp")
@patch('calibre_api.app.main.os.path.join', lambda *args: "/".join(args))
@patch('calibre_api.app.main.shutil.copyfileobj')
@patch('calibre_api.app.main.os.remove')
@patch('calibre_api.app.main.calibre_cli.check_ebook_errors')
def test_check_ebook_endpoint(mock_check_errors, mock_os_remove, mock_copyfileobj, mock_gettempdir, client):
    abs_path = os.path.abspath("book.epub") # Path key in JSON report is absolute
    mock_check_errors.return_value = {abs_path: []} # No errors

    response = client.post(
        "/ebook/check/?output_format=json",
        files={'input_file': ('book.epub', BytesIO(b"content"), 'application/epub+zip')}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["message"] == "Ebook check completed."
    assert json_data["filename"] == "book.epub"
    assert json_data["report_format"] == "json"
    assert json_data["report"] == {abs_path: []}

    mock_check_errors.assert_called_once()
    cli_call_args = mock_check_errors.call_args[1]
    assert cli_call_args['ebook_file_path'].startswith("/mocked_temp/check_ebook_in_")
    assert cli_call_args['output_format'] == "json"
