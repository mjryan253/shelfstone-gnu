# Calibre API Endpoints

This document lists the available API endpoints for the Calibre API.

## Endpoints

### `GET /books/`

*   **Description**: Retrieves a list of books from the Calibre library.
*   **Query Parameters**:
    *   `library_path` (optional, string): Path to the Calibre library. If not provided, `calibredb`'s default will be used.
    *   `search` (optional, string): Search query for `calibredb` (e.g., 'title:Dune author:Herbert').

### `POST /books/add/`

*   **Description**: Adds a new book to the Calibre library. The book file is sent as a multipart/form-data upload.
*   **Request Body (multipart/form-data)**:
    *   `file` (required, file): The ebook file to be added.
    *   `library_path` (optional, string): Path to the Calibre library. Uses default if not provided.
    *   `one_book_per_directory` (optional, boolean, default: `False`): If adding from a directory, import only one book.
    *   `duplicates` (optional, boolean, default: `False`): Add the book even if it appears to be a duplicate of an existing book in the library.
    *   `automerge` (optional, boolean, default: `False`): If duplicates are found, automatically merge them with the existing book.
    *   `authors` (optional, string): Comma-separated list of authors to set for the added book (e.g., "Frank Herbert, Kevin J. Anderson").
    *   `title` (optional, string): Title to set for the added book.
    *   `tags` (optional, string): Comma-separated list of tags to set for the added book (e.g., "fiction,sci-fi").
*   **Responses**:
    *   `200 OK`: Book processed successfully. The response body will indicate if the book was added and include its Calibre ID(s).
        ```json
        {
          "message": "Book(s) added successfully.",
          "added_book_ids": [123],
          "details": null
        }
        ```
        Or, if no new book was added (e.g., duplicate ignored):
        ```json
        {
          "message": "Book was processed but no new entries were added to the library.",
          "added_book_ids": [],
          "details": "This can happen if the book is a duplicate and duplicate adding is off, or if the file is invalid."
        }
        ```
    *   `400 Bad Request`: Invalid input, such as the book file not found at the source before upload (less likely with direct upload) or other parameter issues.
    *   `422 Unprocessable Entity`: If required form fields like `file` are missing.
    *   `500 Internal Server Error`: If an error occurs during `calibredb add` execution.
    *   `503 Service Unavailable`: If `calibredb` command is not found.
*   **Example Usage (curl)**:
    ```bash
    curl -X POST "http://localhost:6336/books/add/" \
         -F "file=@/path/to/your/ebook.epub" \
         -F "library_path=/path/to/your/calibre/library" \
         -F "title=My New Book" \
         -F "authors=Author Name" \
         -F "tags=new,unread"
    ```

### `DELETE /books/{book_id}/`

*   **Description**: Removes a book from the Calibre library using its unique Calibre ID. This action is permanent.
*   **Path Parameters**:
    *   `book_id` (required, integer): The ID of the book to be removed.
*   **Query Parameters**:
    *   `library_path` (optional, string): Path to the Calibre library. Uses default if not provided.
*   **Responses**:
    *   `200 OK`: Book removed successfully.
        ```json
        {
          "message": "Book ID 123 removed successfully.",
          "removed_book_id": 123,
          "details": null
        }
        ```
    *   `400 Bad Request`: Invalid input, such as a non-positive book ID or other issues reported by `calibredb` that are not "not found".
    *   `404 Not Found`: If the book with the specified ID does not exist in the library.
    *   `500 Internal Server Error`: If an error occurs during `calibredb remove_books` execution or an unexpected server error.
    *   `503 Service Unavailable`: If `calibredb` command is not found.
*   **Example Usage (curl)**:
    ```bash
    curl -X DELETE "http://localhost:6336/books/123/"
    ```
    With a specific library path:
    ```bash
    curl -X DELETE "http://localhost:6336/books/123/?library_path=/path/to/your/calibre/library"
    ```

### `PUT /books/{book_id}/metadata/`

*   **Description**: Sets or updates metadata for a specific book in the Calibre library. Only the fields provided in the request body will be attempted to be set.
*   **Path Parameters**:
    *   `book_id` (required, integer): The ID of the book whose metadata is to be set.
*   **Query Parameters**:
    *   `library_path` (optional, string): Path to the Calibre library. Uses default if not provided.
*   **Request Body (JSON)**:
    A JSON object containing the metadata fields to update. All fields are optional.
    Example:
    ```json
    {
      "title": "New Updated Title",
      "authors": ["Author One", "Author Two"],
      "tags": ["updated", "fiction", "adventure"],
      "series": "The Great Saga",
      "series_index": 2.0,
      "publisher": "New Publisher Inc.",
      "pubdate": "2023-01-15",
      "isbn": "978-3-16-148410-0",
      "comments": "This book has been updated with new metadata via the API.",
      "rating": 8
    }
    ```
    *   `title` (optional, string)
    *   `authors` (optional, list of strings)
    *   `publisher` (optional, string)
    *   `pubdate` (optional, string - e.g., "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM:SS")
    *   `tags` (optional, list of strings)
    *   `series` (optional, string)
    *   `series_index` (optional, float)
    *   `isbn` (optional, string)
    *   `comments` (optional, string)
    *   `rating` (optional, integer or float - Calibre typically uses a 0-10 scale for 0-5 stars)
*   **Responses**:
    *   `200 OK`: Metadata updated successfully. The response details which fields were reported as changed by `calibredb`.
        ```json
        {
          "message": "Metadata for book ID 123 updated successfully.",
          "book_id": 123,
          "details": "Changes applied: ['title', 'authors', 'tags']"
        }
        ```
        If no actual changes were made (e.g., data submitted was identical to existing data), `details` might reflect this or `calibredb` might return an empty set of changes.
    *   `400 Bad Request`: Invalid input, such as a non-positive book ID, no metadata fields provided, or other issues reported by `calibredb`.
    *   `404 Not Found`: If the book with the specified ID does not exist in the library, or if `calibredb` indicates no changes were made in a way that suggests the book wasn't found.
    *   `422 Unprocessable Entity`: If the request body is not valid JSON or violates model constraints not caught by 400.
    *   `500 Internal Server Error`: If an error occurs during `calibredb set_metadata` execution or an unexpected server error.
    *   `503 Service Unavailable`: If `calibredb` command is not found.
*   **Example Usage (curl)**:
    ```bash
    curl -X PUT "http://localhost:6336/books/123/metadata/?library_path=/path/to/calibre/db" \
         -H "Content-Type: application/json" \
         -d '{
               "title": "A New Title for an Old Book",
               "authors": ["Jane Doe", "John Smith"],
               "tags": ["classic", "updated by api"]
             }'
    ```
