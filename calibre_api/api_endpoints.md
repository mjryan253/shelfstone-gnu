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

---

## Calibre General CLI Endpoints

These endpoints provide access to various general-purpose Calibre command-line tools.

### `GET /calibre/version/`

*   **Description**: Retrieves the installed Calibre version. Interfaces with `calibre --version`.
*   **Responses**:
    *   `200 OK`: Successfully retrieved version.
        ```json
        {
          "calibre_version": "6.10.0",
          "details": "calibre (calibre 6.10.0)\nCopyright Kovid Goyal"
        }
        ```
    *   `503 Service Unavailable`: If `calibre` command is not found.
    *   `500 Internal Server Error`: If the command fails unexpectedly.
*   **Example Usage (curl)**:
    ```bash
    curl -X GET "http://localhost:6336/calibre/version/"
    ```

### `POST /ebook/convert/`

*   **Description**: Converts an e-book from one format to another using `ebook-convert`. The input file is uploaded, converted, and the API responds with information about the output file which is stored on the server.
    *Note: This endpoint confirms conversion. A separate mechanism or endpoint would be needed for the client to download the converted file from its server-side temporary location.*
*   **Request Body (multipart/form-data)**:
    *   `input_file` (required, file): The e-book file to be converted.
    *   `request` (required, JSON string for `EbookConvertRequest` model): Contains conversion parameters. Example:
        ```json
        {
          "output_format": "mobi",
          "options": ["--embed-font-family", "Arial", "--authors", "Jules Verne"]
        }
        ```
        When sending with `curl -F`, this JSON payload for `request` part needs to be correctly formatted as a string or read from a file.
        A simpler way if `Form(...)` is used for individual fields of `EbookConvertRequest`:
        *   `output_format` (string, form field): e.g., "epub", "mobi".
        *   `options` (list of strings, form field, can be repeated): e.g., `options=--option1&options=value1`.
*   **Response (`200 OK` - `EbookConvertResponse`)**:
    ```json
    {
      "message": "File converted successfully. It is available on the server.",
      "output_filename": "original_filename.mobi"
    }
    ```
*   **Error Responses**: `404` (file not found), `500` (conversion error), `503` (tool not found).
*   **Example Usage (curl with separate form fields for `EbookConvertRequest`):**
    ```bash
    curl -X POST "http://localhost:6336/ebook/convert/" \
         -F "input_file=@/path/to/your/book.epub" \
         -F "output_format=mobi" \
         -F "options=--authors" \
         -F "options=J.R.R. Tolkien"
    ```
    *(Note: The above curl example assumes `request: EbookConvertRequest = Form(...)` is not used, but individual fields are Forms. If `request` is a single JSON Form field, its content needs to be a stringified JSON as shown in the description.)*
    *Actual implementation uses `request: EbookConvertRequest = Form(...)` which expects a JSON string for the `request` part.*

### `POST /ebook/metadata/get/`

*   **Description**: Reads metadata from a standalone e-book file using `ebook-meta`.
*   **Request Body (multipart/form-data)**:
    *   `input_file` (required, file): The e-book file.
*   **Query Parameters**:
    *   `as_json` (optional, boolean, default: `True`): If `True`, returns metadata as a parsed JSON object. If `False`, returns raw OPF content as a string.
*   **Response (`200 OK` - `EbookMetadataResponse`)**:
    ```json
    {
      "message": "Metadata extracted successfully.",
      "filename": "book.epub",
      "metadata_content": { /* JSON object or OPF string */ }
    }
    ```
*   **Error Responses**: `404`, `500`, `503`.
*   **Example Usage (curl)**:
    ```bash
    curl -X POST "http://localhost:6336/ebook/metadata/get/?as_json=true" \
         -F "input_file=@/path/to/your/book.epub"
    ```

### `POST /ebook/metadata/set/`

*   **Description**: Sets metadata on a standalone e-book file using `ebook-meta`. The modified file is returned directly for download.
*   **Request Body (multipart/form-data)**:
    *   `input_file` (required, file): The e-book file to modify.
    *   `request` (required, JSON string for `EbookMetadataSetRequest` model): Contains metadata options. Example:
        ```json
        {
          "metadata_options": ["--title", "New Awesome Title", "--tags", "Epic,Fantasy"]
        }
        ```
        *(Similar to `/ebook/convert/`, if `request` is a single JSON Form field, its content needs to be a stringified JSON.)*
*   **Response (`200 OK`)**: The modified e-book file is returned directly (`FileResponse`).
*   **Error Responses**: `400` (invalid options), `404`, `500`, `503`.
*   **Example Usage (curl - actual endpoint returns file, so -o is useful):**
    ```bash
    curl -X POST "http://localhost:6336/ebook/metadata/set/" \
         -F "input_file=@/path/to/your/book.epub" \
         -F "request={\"metadata_options\": [\"--title\", \"A Better Title\"]}" \
         -o "modified_book.epub"
    ```

### `POST /ebook/polish/`

*   **Description**: Polishes an e-book (e.g., subsets fonts, updates metadata) using `ebook-polish`. The polished file is returned for download.
*   **Request Body (multipart/form-data)**:
    *   `input_file` (required, file): The e-book to polish.
    *   `output_filename_suffix` (optional, string, default: `_polished`): Suffix for the output filename.
    *   `options` (optional, list of strings, can be repeated): e.g., `options=--subset-fonts&options=--smarten-punctuation`.
*   **Response (`200 OK`)**: The polished e-book file (`FileResponse`).
*   **Error Responses**: `400`, `404`, `500`, `503`.
*   **Example Usage (curl):**
    ```bash
    curl -X POST "http://localhost:6336/ebook/polish/" \
         -F "input_file=@/path/to/your/book.epub" \
         -F "output_filename_suffix=_beta" \
         -F "options=--subset-fonts" \
         -o "polished_book.epub"
    ```

### `GET /ebook/metadata/fetch/`

*   **Description**: Fetches e-book metadata from online sources using `fetch-ebook-metadata`.
*   **Query Parameters**:
    *   `title` (optional, string)
    *   `authors` (optional, string, comma-separated)
    *   `isbn` (optional, string)
    *   `as_json` (optional, boolean, default: `True`): Returns JSON if `True`, else OPF string.
*   **Response (`200 OK` - `FetchMetadataResponse`)**:
    ```json
    {
      "message": "Metadata fetched successfully.",
      "search_criteria": {"title": "The Hobbit", "authors": "J.R.R. Tolkien", "isbn": null},
      "metadata": { /* JSON object or OPF string */ }
    }
    ```
    If no metadata found, `message` indicates this and `metadata` may be `null`.
*   **Error Responses**: `400`, `500`, `503`.
*   **Example Usage (curl)**:
    ```bash
    curl -X GET "http://localhost:6336/ebook/metadata/fetch/?title=The%20Hobbit&authors=J.R.R.%20Tolkien"
    ```

### `POST /web2disk/generate-recipe/`

*   **Description**: Generates a Calibre `.recipe` file from a URL using `web2disk`. The `.recipe` file is returned for download.
*   **Request Body (JSON - `WebToDiskRequest`)**:
    ```json
    {
      "url": "https://www.example.com/article",
      "options": ["--max-articles-per-feed", "1"]
    }
    ```
*   **Response (`200 OK`)**: The generated `.recipe` file (`FileResponse`).
*   **Error Responses**: `400`, `500`, `503`.
*   **Example Usage (curl):**
    ```bash
    curl -X POST "http://localhost:6336/web2disk/generate-recipe/" \
         -H "Content-Type: application/json" \
         -d '{"url": "https://en.wikipedia.org/wiki/EPUB", "options": ["--max-articles-per-feed", "1"]}' \
         -o "generated_site.recipe"
    ```

### `POST /ebook/convert/lrf-to-lrs/`

*   **Description**: Converts an LRF e-book file to LRS format. Returns the LRS file.
*   **Request Body (multipart/form-data)**:
    *   `input_file` (required, file): The LRF file.
*   **Response (`200 OK`)**: The LRS file (`FileResponse`).
*   **Error Responses**: `404`, `500`, `503`.
*   **Example Usage (curl):**
    ```bash
    curl -X POST "http://localhost:6336/ebook/convert/lrf-to-lrs/" \
         -F "input_file=@/path/to/your/book.lrf" \
         -o "book.lrs"
    ```

### `POST /ebook/convert/lrs-to-lrf/`

*   **Description**: Converts an LRS e-book file to LRF format. Returns the LRF file.
*   **Request Body (multipart/form-data)**:
    *   `input_file` (required, file): The LRS file.
*   **Response (`200 OK`)**: The LRF file (`FileResponse`).
*   **Error Responses**: `404`, `500`, `503`.
*   **Example Usage (curl):**
    ```bash
    curl -X POST "http://localhost:6336/ebook/convert/lrs-to-lrf/" \
         -F "input_file=@/path/to/your/book.lrs" \
         -o "book.lrf"
    ```

### `GET /calibre/plugins/`

*   **Description**: Lists installed Calibre plugins using `calibre-customize --list-plugins`.
*   **Response (`200 OK` - `PluginListResponse`)**:
    ```json
    {
      "message": "Successfully retrieved plugin list.",
      "count": 5,
      "plugins": {
        "Plugin Name 1": {"name": "Plugin Name 1", "version": "1.0", "author": "Author A"},
        "Plugin Name 2": {"name": "Plugin Name 2", "version": "1.2", "author": "Author B", "description": "Does something cool."}
        // ... more plugins
      }
    }
    ```
*   **Error Responses**: `500`, `503`.
*   **Example Usage (curl)**:
    ```bash
    curl -X GET "http://localhost:6336/calibre/plugins/"
    ```

### `POST /calibre/debug/test-build/`

*   **Description**: Runs Calibre's build and basic startup test using `calibre-debug --test-build`. This can take several minutes.
*   **Query Parameters**:
    *   `timeout` (optional, integer, default: 180): Timeout in seconds for the command.
*   **Response (`200 OK` - `DebugTestBuildResponse`)**:
    ```json
    {
      "message": "Calibre debug --test-build completed. All tests passed.",
      "output": "calibre version: 6.10.0\nPython version: ... \nAll tests passed"
    }
    ```
*   **Error Responses**: `408` (timeout), `500`, `503`.
*   **Example Usage (curl)**:
    ```bash
    curl -X POST "http://localhost:6336/calibre/debug/test-build/?timeout=240"
    ```

### `POST /calibre/send-email/`

*   **Description**: Sends an email using `calibre-smtp`. SMTP server details must be provided in the request.
*   **Request Body (multipart/form-data for file, JSON for SmtpSendRequest part)**:
    *   `request` (required, JSON string for `SmtpSendRequest` model): Contains email details and SMTP configuration. Example:
        ```json
        {
          "recipient_email": "test@example.com",
          "subject": "API Test Email",
          "body": "Hello from the Calibre API!",
          "smtp_server": "smtp.mailprovider.com",
          "smtp_port": 587,
          "smtp_username": "user@example.com",
          "smtp_password": "your_password",
          "smtp_encryption": "tls",
          "sender_email": "user@example.com"
        }
        ```
    *   `attachment_file` (optional, file): A file to attach to the email.
*   **Response (`200 OK` - `SmtpSendResponse`)**:
    ```json
    {
      "success": true,
      "message": "Email sent successfully.",
      "details": null
    }
    ```
    If sending fails, `success` will be `false` and `message` (and `details`) will contain error information.
*   **Error Responses**: `500`, `503`.
*   **Example Usage (curl):**
    ```bash
    # Prepare SmtpSendRequest JSON payload, e.g., in a file named smtp_payload.json
    # Contents of smtp_payload.json:
    # { "recipient_email": "recipient@example.com", "subject": "Test", "body": "Test body",
    #   "smtp_server": "your.smtp.server", "smtp_port": 587, "smtp_username": "user", "smtp_password": "password",
    #   "smtp_encryption": "tls", "sender_email": "sender@example.com" }

    # Without attachment:
    curl -X POST "http://localhost:6336/calibre/send-email/" \
         -H "Content-Type: multipart/form-data" \
         -F "request=<smtp_payload.json;type=application/json"

    # With attachment:
    curl -X POST "http://localhost:6336/calibre/send-email/" \
         -H "Content-Type: multipart/form-data" \
         -F "request=<smtp_payload.json;type=application/json" \
         -F "attachment_file=@/path/to/your/attachment.pdf"
    ```
    *(Note: The `SmtpSendRequest` is sent as a JSON part in a multipart/form-data request. The `request=<payload.json` syntax in curl is one way to send a JSON file as a form part. Adjust based on your client library.)*
    *Actual implementation uses `request: SmtpSendRequest = Body(...)` alongside `attachment_file: UploadFile = File(None)`. This means FastAPI expects the JSON payload for `SmtpSendRequest` to be in the request body, and `attachment_file` as a separate part if `Content-Type` is `multipart/form-data`. If only JSON is sent (no file), `Content-Type` should be `application/json` for `request`.*
    *A cleaner way for mixed data is often to have distinct Form fields for SmtpSendRequest's simple fields and a File field.*

### `POST /ebook/check/`

*   **Description**: Checks an e-book (EPUB or AZW3) for errors using `ebook-edit --check-book`.
*   **Request Body (multipart/form-data)**:
    *   `input_file` (required, file): The e-book file to check.
*   **Query Parameters**:
    *   `output_format` (optional, string, default: `json`): Report format, 'json' or 'text'.
*   **Response (`200 OK` - `EbookCheckResponse`)**:
    ```json
    {
      "message": "Ebook check completed.",
      "filename": "book.epub",
      "report_format": "json",
      "report": { /* JSON report object or text string */ }
    }
    ```
*   **Error Responses**: `400`, `404`, `500`, `503`.
*   **Example Usage (curl):**
    ```bash
    curl -X POST "http://localhost:6336/ebook/check/?output_format=json" \
         -F "input_file=@/path/to/your/book.epub"
    ```
