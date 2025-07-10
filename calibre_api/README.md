# Calibre API

This FastAPI application provides an API wrapper around the `calibredb` command-line tool.

## Setup

1.  **Install Calibre:**
    Make sure you have Calibre installed on your system and `calibredb` is accessible in your system's PATH. You can download Calibre from [https://calibre-ebook.com/download](https://calibre-ebook.com/download).

2.  **Create a Python virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

To run the FastAPI application, use Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Documentation

Once the application is running, you can access the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.

Alternatively, you can view the ReDoc documentation at `http://127.0.0.1:8000/redoc`.

## API Endpoints

### `GET /books`

Lists books from your Calibre library.

**Query Parameters:**

*   `search` (optional, string): Filters books by a search query. This is passed directly to `calibredb list --search`. For example, `title:"The Hitchhiker's Guide"` or `author:Adams`.
*   `limit` (optional, integer): Limits the number of books returned. This is passed to `calibredb list --limit`.
*   `sort_by` (optional, string): Specifies the field to sort the books by. This is passed to `calibredb list --sort-by`. Common fields include `title`, `authors`, `pubdate`, `last_modified`.

**Example Usage:**

*   `GET /books` - Lists all books.
*   `GET /books?search=author:Asimov` - Lists all books by Isaac Asimov.
*   `GET /books?limit=10&sort_by=title` - Lists the first 10 books, sorted by title.

**Responses:**

*   `200 OK`: Returns a JSON array of book objects.
    ```json
    [
        {
            "id": 1,
            "title": "Some Book Title",
            "authors": "Author Name",
            "formats": ["EPUB", "MOBI"],
            "isbn": "9781234567890",
            "publisher": "Some Publisher",
            "rating": 5,
            "tags": ["Fiction", "Sci-Fi"],
            "series": "Some Series",
            "series_index": 1.0,
            "author_sort": "Name, Author",
            "comments": "A great read.",
            "cover": "/path/to/library/Author Name/Some Book Title (1)/cover.jpg",
            "last_modified": "2023-10-27T10:00:00+00:00",
            "pubdate": "2020-01-15T00:00:00+00:00",
            "size": 1234567,
            "uuid": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
        }
        // ... more books
    ]
    ```
*   `500 Internal Server Error`: If `calibredb` command fails, cannot be found, or if its output cannot be parsed.
    ```json
    {
        "detail": "calibredb command failed: [error message from calibredb]"
    }
    ```
    or
    ```json
    {
        "detail": "calibredb command not found. Make sure Calibre is installed and in your PATH."
    }
    ```
    or
    ```json
    {
        "detail": "Failed to parse calibredb output."
    }
    ```

### `GET /`

Returns a welcome message.

**Responses:**

*   `200 OK`:
    ```json
    {
        "message": "Welcome to the Calibre API"
    }
    ```

## Development

### Running Tests

To run the unit tests:

```bash
python -m pytest
```
Make sure you are in the `calibre_api` directory or specify the path to the tests.

```bash
python -m pytest calibre_api/tests/test_main.py
```
