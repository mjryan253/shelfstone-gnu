# Shelfstone Server

A Python FastAPI application that provides a RESTful API wrapper for various Calibre command-line tools, allowing you to manage e-book libraries, convert formats, edit metadata, and perform other Calibre functions programmatically. This server acts as the backend for the Shelfstone project.

-----

## Features

**Library Management (via `calibredb`):**

  * List books from your Calibre library.
  * Add books to a library.
  * Remove books from a library.
  * Set and update metadata for books in a library.
  * Filter books using Calibre's search syntax.
  * Specify a Calibre library path or use the default.

**General E-book Utilities (via other Calibre CLI tools):**

  * Get installed Calibre version (`calibre --version`).
  * Convert e-books between various formats (`ebook-convert`).
  * Read and write metadata from/to standalone e-book files (`ebook-meta`).
  * Polish e-books: update metadata, subset fonts, smarten punctuation, etc. (`ebook-polish`).
  * Fetch e-book metadata from online sources (`fetch-ebook-metadata`).
  * Generate Calibre recipe files from websites (`web2disk`).
  * Convert LRF files to LRS and vice-versa (`lrf2lrs`, `lrs2lrf`).
  * List installed Calibre plugins (`calibre-customize --list-plugins`).
  * Run Calibre's build and startup self-tests (`calibre-debug --test-build`).
  * Send e-mails with optional attachments via SMTP (`calibre-smtp`).
  * Check e-book files (EPUB, AZW3) for errors (`ebook-edit --check-book`).

-----

## Requirements

  * **Calibre**: The Calibre e-book management software must be installed. All Calibre command-line tools used by the API (e.g., `calibredb`, `ebook-convert`, `ebook-meta`, etc.) must be accessible in your system's `PATH`.
      * Download Calibre: [https://calibre-ebook.com/download](https://calibre-ebook.com/download)
  * **Python**: Python 3.8 or newer.

-----

## Setup

1.  **Clone the Repository**:

    ```bash
    git clone https://github.com/mjryan253/shelfstone-gnu.git
    cd shelfstone-gnu/calibre_api
    ```

2.  **Create and Activate a Virtual Environment** (recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

-----

## Running the Application

Once the setup is complete, you can run the FastAPI application using Uvicorn (ensure you are in the `calibre_api` directory):

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 6336
```

The Shelfstone Server API will be available at `http://localhost:6336` (internally) and typically accessed via the main application's Nginx proxy (e.g., `http://localhost:6464/api/`).
Interactive API documentation (Swagger UI) for the direct service can be accessed at `http://localhost:6336/docs`.
Alternative API documentation (ReDoc) can be accessed at `http://localhost:6336/redoc`.

-----

## API Endpoints

The API is broadly divided into two categories:

  * **Calibre Library Management (`/books/*`)**: Endpoints that interact with a Calibre library database using `calibredb`.
  * **General Calibre CLI Utilities (`/calibre/*`, `/ebook/*`)**: Endpoints that wrap other Calibre command-line tools for various e-book operations.

For detailed information on each endpoint, including request/response models and examples, please refer to the API Endpoints Documentation or explore the interactive Swagger UI at `/docs` and ReDoc at `/redoc` when the application is running.

Below is a summary of the available endpoint groups and their functionalities:

### Calibre Library Management (`/books/*`)

These endpoints use `calibredb` to interact with your Calibre library.

  * `GET /books/`: List books from the library. Supports searching and specifying library path.
  * `POST /books/add/`: Add a new book to the library.
  * `DELETE /books/{book_id}/`: Remove a book from the library by its ID.
  * `PUT /books/{book_id}/metadata/`: Set or update metadata for a specific book in the library.

### General Calibre CLI Utilities

These endpoints wrap various other Calibre command-line tools.

#### Calibre Version & Control:

  * `GET /calibre/version/`: Get the installed Calibre version (`calibre --version`).
  * `GET /calibre/plugins/`: List installed Calibre plugins (`calibre-customize --list-plugins`).
  * `POST /calibre/debug/test-build/`: Run Calibre's build and startup self-tests (`calibre-debug --test-build`).
  * `POST /calibre/send-email/`: Send an email via SMTP using `calibre-smtp`.

#### E-book Conversion & File Operations:

  * `POST /ebook/convert/`: Convert an e-book file to another format (`ebook-convert`).
  * `POST /ebook/convert/lrf-to-lrs/`: Convert LRF to LRS (`lrf2lrs`).
  * `POST /ebook/convert/lrs-to-lrf/`: Convert LRS to LRF (`lrs2lrf`).

#### E-book Metadata (Standalone Files):

  * `POST /ebook/metadata/get/`: Read metadata from a standalone e-book file (`ebook-meta`).
  * `POST /ebook/metadata/set/`: Write metadata to a standalone e-book file (`ebook-meta`).
  * `GET /ebook/metadata/fetch/`: Fetch metadata for a book from online sources (`fetch-ebook-metadata`).

#### E-book Content & Structure:

  * `POST /ebook/polish/`: Polish an e-book (e.g., subset fonts, update cover) (`ebook-polish`).
  * `POST /ebook/check/`: Check an e-book file for errors (`ebook-edit --check-book`).
  * `POST /web2disk/generate-recipe/`: Create a Calibre recipe file from a website URL (`web2disk`). The recipe can then be used with `ebook-convert` to create an e-book.

-----

## Development and Testing

(This section is more for contributors)

### Running Tests

Ensure you have `pytest` installed (`pip install pytest`). From the `calibre_api` root directory:

```bash
python -m pytest tests/
```

Tests are located in the `tests/` directory.

  * `test_main.py` contains integration tests for the FastAPI endpoints, mocking the underlying `calibre_cli.py` calls.
  * `test_calibre_cli.py` contains unit tests for the Calibre CLI wrapper functions, mocking `subprocess.run` and filesystem operations.

These tests generally do not require a live Calibre installation to run, as external calls are mocked.

**Note on Testing Environment:**

The tests are designed to run in an environment where the Calibre command-line tools are *not* installed. This is to ensure that the tests are not dependent on a specific Calibre version and that they can be run in a CI/CD environment without a full Calibre installation.

If you are running the tests in an environment where Calibre *is* installed, you may see some tests fail. This is because the tests mock the `subprocess.run` function to simulate the behavior of the Calibre command-line tools. If the tools are actually present, the mocks may not behave as expected.

To run the tests in an environment with Calibre installed, you will need to set the `SKIP_LONG_TESTS` environment variable to `true`. This will skip the tests that are known to be problematic in an environment with Calibre installed.

```bash
SKIP_LONG_TESTS=true python -m pytest tests/
```

-----

## Future Enhancements

  * **Enhanced File Handling**: Implement robust temporary file management, potentially using background tasks for cleanup after `FileResponse` streams. Provide clear mechanisms for clients to download files generated by `POST` requests (e.g., via unique IDs or dedicated download endpoints).
  * **Asynchronous Operations**: For long-running Calibre commands (e.g., complex conversions, large test builds), consider implementing asynchronous task handling (e.g., using Celery or FastAPI's `BackgroundTasks` for longer processes) with status polling endpoints.
  * **Configuration Management**: Externalize configurations, especially for sensitive data like SMTP server details (e.g., via environment variables or configuration files).
  * **Security**: Implement authentication and authorization, especially if the API is exposed externally.
  * **`calibre-server` Integration**: Evaluate useful, non-conflicting ways to interact with `calibre-server` functionalities via the API if any are identified.
  * **More `ebook-edit` Features**: Explore wrapping more non-interactive sub-commands of `ebook-edit` if they provide utility through an API.

-----

## Contributing

Contributions are welcome\! Please feel free to open an issue or submit a pull request.

-----

## License

This project is licensed under the MIT License - see the `LICENSE` file for details (if one exists).
(Note: No `LICENSE` file has been created in this session.)