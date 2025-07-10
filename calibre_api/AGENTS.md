## Agent Instructions for `calibre_api`

This document provides instructions for AI agents working on the `calibre_api` project.

### Project Overview

`calibre_api` is a Python FastAPI application that serves as a wrapper around the `calibredb` command-line tool. It allows users to interact with their Calibre e-book libraries via a RESTful API.

### Prerequisites

1.  **`calibredb` Installation**:
    *   The `calibredb` command-line tool, which is part of the Calibre e-book management software, **must be installed and accessible in the system's PATH**.
    *   You can download Calibre from [https://calibre-ebook.com/download](https://calibre-ebook.com/download).
    *   Verify installation by running `calibredb --version` in your terminal.

2.  **Python Environment**:
    *   Python 3.8 or newer is recommended.
    *   A virtual environment is highly recommended for managing dependencies.

### Setup and Running

1.  **Clone the Repository** (if applicable, or assume code is already present).

2.  **Create and Activate Virtual Environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    Navigate to the `calibre_api` root directory (where `requirements.txt` is located) and run:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Running the FastAPI Application**:
    From the `calibre_api` root directory, run the Uvicorn server:
    ```bash
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *   `app.main:app` refers to the `app` instance of `FastAPI` in `calibre_api/app/main.py`.
    *   `--reload` enables auto-reloading on code changes (for development).
    *   The API will be accessible at `http://localhost:8000`.
    *   Interactive API documentation (Swagger UI) will be at `http://localhost:8000/docs`.
    *   Alternative API documentation (ReDoc) will be at `http://localhost:8000/redoc`.

### Testing

1.  **Install Test Dependencies** (if not already covered by `requirements.txt`, though `pytest` should be included if it's a dev dependency):
    ```bash
    pip install pytest httpx # httpx is used by TestClient
    ```

2.  **Running Tests**:
    From the `calibre_api` root directory, run Pytest:
    ```bash
    python -m pytest tests/
    ```
    Or, if you are in the `calibre_api` directory:
    ```bash
    python -m pytest tests/
    ```
    The tests are located in the `calibre_api/tests/` directory (e.g., `tests/test_main.py`). They use `unittest.mock` to simulate `calibredb` calls, so they do not require an actual Calibre library to be configured for most test cases.

### Interacting with a Calibre Library

*   **Default Library**: If `calibredb` is configured with a default library, the API will use it when no `library_path` is specified.
*   **Specific Library**: To target a specific Calibre library, use the `library_path` query parameter with the API endpoints.
    *   Example: `GET http://localhost:8000/books/?library_path=/path/to/your/calibre/library`
*   **For Manual Testing**:
    *   Ensure you have a Calibre library populated with some books.
    *   You can create one using the Calibre desktop application.
    *   Note the full path to this library (the directory containing `metadata.db` and book folders).

### Code Structure

*   `calibre_api/app/main.py`: Contains the FastAPI application instance and endpoint definitions.
*   `calibre_api/app/models.py`: Defines Pydantic models for data validation and serialization.
*   `calibre_api/app/crud.py`: Contains functions for interacting with the `calibredb` command-line tool (Create, Read, Update, Delete operations - currently focused on Read).
*   `calibre_api/tests/`: Contains Pytest test files.
*   `calibre_api/requirements.txt`: Lists Python package dependencies.
*   `calibre_api/AGENTS.md`: This file.
*   `calibre_api/README.md`: Project documentation for users.

### Important Considerations for Agents

*   **`calibredb` Dependency**: All core functionality relies on `calibredb`. Error handling for `calibredb`'s absence or failures is crucial.
*   **Output Parsing**: `calibredb --for-machine` outputs JSON. The `crud.py` module is responsible for calling `calibredb` and parsing this JSON. Ensure robustness in parsing, especially as `calibredb`'s output structure for all fields can be extensive.
*   **Data Validation**: Pydantic models in `models.py` are used for validating the structure of the data returned by the API. Ensure these models accurately reflect the expected data from `calibredb list --fields all`.
*   **Security**: Be cautious about directly passing user input to shell commands if new functionalities are added. The current implementation uses `subprocess.run` with a list of arguments, which is generally safer than `shell=True`.
*   **Error Handling**: Implement comprehensive error handling for API endpoints, providing clear and appropriate HTTP status codes and error messages.
*   **Dependencies**: Keep `requirements.txt` updated with any new dependencies.
*   **Testing**: Write tests for any new features or bug fixes. Mock external calls to `calibredb` in unit tests.

This document should help you understand the project and contribute effectively. If anything is unclear, please ask for clarification.
