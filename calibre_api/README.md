# CalibreDB API

A Python FastAPI application that provides a RESTful API wrapper for the `calibredb` command-line tool, allowing you to interact with your Calibre e-book libraries programmatically.

## Features

*   List books from your Calibre library.
*   Filter books using Calibre's search syntax.
*   Specify a Calibre library path or use the default.
*   JSON output for easy integration with other applications.

## Requirements

*   **Calibre**: The Calibre e-book management software must be installed, and the `calibredb` command-line tool must be accessible in your system's PATH.
    *   Download Calibre: [https://calibre-ebook.com/download](https://calibre-ebook.com/download)
*   **Python**: Python 3.8 or newer.

## Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/mjryan253/shelfstone-gnu.git 
    cd calibre_api
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

## Running the Application

Once the setup is complete, you can run the FastAPI application using Uvicorn:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 6336
```

*   The API will be available at `http://localhost:6336`.
*   Interactive API documentation (Swagger UI) can be accessed at `http://localhost:6336/docs`.
*   Alternative API documentation (ReDoc) can be accessed at `http://localhost:6336/redoc`.

## API Endpoints

### List Books

*   **Endpoint**: `GET /books/`
*   **Description**: Retrieves a list of books from the Calibre library. It uses `calibredb list --for-machine --fields all` internally to fetch comprehensive book data.
*   **Query Parameters**:
    *   `library_path` (optional, string): The absolute path to your Calibre library directory (the one containing `metadata.db`). If not provided, `calibredb` will attempt to use its default configured library.
        *   Example: `/books/?library_path=/Users/yourname/Calibre%20Library`
    *   `search` (optional, string): A search query string in Calibre's search syntax to filter the books.
        *   Example: `/books/?search=title:Dune%20author:Herbert`
        *   Example: `/books/?search=tags:"science fiction"`
*   **Success Response (200 OK)**:
    A JSON array of book objects. Each book object contains fields like `id`, `title`, `authors`, `tags`, `publisher`, `pubdate`, `isbn`, `formats`, `comments`, etc.
    ```json
    [
      {
        "id": 1,
        "title": "Dune",
        "authors": ["Frank Herbert"],
        "tags": ["Science Fiction", "Classic"],
        "publisher": "Chilton Books",
        "pubdate": "1965-08-01T00:00:00+00:00",
        "isbn": "9780441172719",
        "formats": ["EPUB", "MOBI"],
        "comments": "A masterpiece of science fiction.",
        "author_sort": "Herbert, Frank",
        "cover": "/path/to/calibre/library/Frank Herbert/Dune (1)/cover.jpg",
        "identifiers": {"isbn": "9780441172719"},
        "languages": ["eng"],
        "last_modified": "2023-10-26T10:00:00+00:00",
        "rating": 5,
        "series": "Dune Saga",
        "series_index": 1.0,
        "size": 1024000,
        "uuid": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
      },
      // ... more books
    ]
    ```
*   **Error Responses**:
    *   `422 Unprocessable Entity`: If query parameters are invalid.
    *   `500 Internal Server Error`: If there's an issue with `calibredb` execution (e.g., command error, JSON parsing failure) or an unexpected server error.
    *   `503 Service Unavailable`: If the `calibredb` command is not found (indicating Calibre might not be installed or not in PATH).

## Development and Testing

(This section is more for contributors)

### Running Tests

Ensure you have `pytest` installed (`pip install pytest`). From the `calibre_api` root directory:

```bash
python -m pytest tests/
```

Tests are located in the `tests/` directory and use mocking to simulate `calibredb` calls, so they generally don't require a live Calibre library.

## Future Enhancements

*   Endpoints for other `calibredb` actions (e.g., getting metadata for a single book, adding books, exporting books).
*   More sophisticated error handling and status codes.
*   Authentication/Authorization for accessing the API.

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details (if one exists).
(Note: No `LICENSE` file has been created in this session.)
