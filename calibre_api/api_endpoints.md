# Calibre API Endpoints

This document lists the available API endpoints for the Calibre API.

## Endpoints

### `GET /books/`

*   **Description**: Retrieves a list of books from the Calibre library.
*   **Query Parameters**:
    *   `library_path` (optional, string): Path to the Calibre library. If not provided, `calibredb`'s default will be used.
    *   `search` (optional, string): Search query for `calibredb` (e.g., 'title:Dune author:Herbert').
