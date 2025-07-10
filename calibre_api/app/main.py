from fastapi import FastAPI, HTTPException, Query, File, UploadFile, Form
from typing import List, Optional, Any
import logging
import shutil
import tempfile
import os

from .models import Book, AddBookResponse, RemoveBookResponse, SetMetadataRequest, SetMetadataResponse
from .crud import list_books, add_book, remove_book, set_book_metadata, CalibredbError

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CalibreDB API",
    description="A FastAPI wrapper for the calibredb command-line tool.",
    version="0.1.0",
)

@app.get("/books/", response_model=List[Book])
async def get_books_endpoint(
    library_path: Optional[str] = Query(None, description="Path to the Calibre library. If not provided, calibredb's default will be used."),
    search: Optional[str] = Query(None, description="Search query for calibredb (e.g., 'title:Dune author:Herbert').")
):
    """
    Retrieve a list of books from the Calibre library.
    Uses `calibredb list --for-machine --fields all`.
    """
    try:
        logger.info(f"Received request for books. Library path: '{library_path}', Search: '{search}'")

        # Call the CRUD function to get book data
        books_data = list_books(library_path=library_path, search_query=search)

        # Validate and parse data with Pydantic models
        # Pydantic will raise validation errors if the data doesn't match the Book model
        # For example, if 'id' is missing or 'authors' is not a list.
        # FastAPI handles these Pydantic validation errors automatically and returns a 422 response.

        # However, calibredb --for-machine output is a list of dicts.
        # We need to ensure each dict can be parsed into a Book model.
        # If a field is missing but Optional in Pydantic, it's fine.
        # If a required field (like 'id' or 'title' if not Optional) is missing, Pydantic will error.

        validated_books: List[Book] = []
        for book_dict in books_data:
            try:
                # Ensure 'authors' and 'tags' are lists if they exist and are strings
                # (calibredb sometimes returns comma-separated strings for these)
                # This preprocessing step might be better placed in the crud layer or a dedicated parsing function.
                if 'authors' in book_dict and isinstance(book_dict['authors'], str):
                    book_dict['authors'] = [a.strip() for a in book_dict['authors'].split(',')] if book_dict['authors'] else []

                if 'tags' in book_dict and isinstance(book_dict['tags'], str):
                    book_dict['tags'] = [t.strip() for t in book_dict['tags'].split(',')] if book_dict['tags'] else []

                if 'formats' in book_dict and isinstance(book_dict['formats'], str):
                     book_dict['formats'] = [f.strip() for f in book_dict['formats'].split(',')] if book_dict['formats'] else []

                if 'languages' in book_dict and isinstance(book_dict['languages'], str):
                     book_dict['languages'] = [lang.strip() for lang in book_dict['languages'].split(',')] if book_dict['languages'] else []

                validated_books.append(Book(**book_dict))
            except Exception as e: # Catch Pydantic validation errors or other issues per book
                logger.error(f"Error parsing book data: {book_dict}. Error: {e}", exc_info=True)
                # Optionally, skip this book or raise an error for the whole request
                # For now, we'll be strict and raise an error if any book fails validation.
                # This could be changed to skip problematic books and return valid ones.
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing book data from calibredb. Problematic book: {book_dict.get('title', 'Unknown title')}. Error: {str(e)}"
                )

        logger.info(f"Successfully retrieved and validated {len(validated_books)} books.")
        return validated_books

    except FileNotFoundError as e:
        logger.error(f"calibredb not found: {e}", exc_info=True)
        raise HTTPException(
            status_code=503, # Service Unavailable
            detail="calibredb command not found. Ensure Calibre is installed and in your PATH."
        )
    except CalibredbError as e:
        logger.error(f"CalibredbError: {e.args[0]}. Return code: {e.returncode}. Stderr: {e.stderr}", exc_info=True)
        detail_message = f"Error interacting with calibredb: {e.args[0]}"
        # Potentially include parts of e.stderr if it's safe and useful, or log it for internal review.
        raise HTTPException(
            status_code=500, # Or 400/404 depending on error type
            detail=detail_message
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred in /books/ endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected server error occurred: {str(e)}"
        )

@app.post("/books/add/", response_model=AddBookResponse)
async def add_book_endpoint(
    file: UploadFile = File(...),
    library_path: Optional[str] = Form(None),
    one_book_per_directory: bool = Form(False),
    duplicates: bool = Form(False), # Add new books even if they appear to be duplicates of existing books.
    automerge: bool = Form(False), # If duplicates are found, auto-merge them.
    authors: Optional[str] = Form(None), # Comma-separated
    title: Optional[str] = Form(None),
    tags: Optional[str] = Form(None) # Comma-separated
):
    """
    Add a book to the Calibre library.
    The book file is uploaded and then processed by `calibredb add`.
    """
    # Create a temporary directory to store the uploaded file
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        logger.info(f"Received request to add book: {file.filename}. Library path: '{library_path}'")

        # Save the uploaded file to the temporary path
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Uploaded file '{file.filename}' saved to temporary path: {temp_file_path}")

        # Call the CRUD function to add the book
        added_ids = add_book(
            file_path=temp_file_path,
            library_path=library_path,
            one_book_per_directory=one_book_per_directory,
            duplicates=duplicates,
            automerge=automerge,
            authors=authors,
            title=title,
            tags=tags
        )

        if added_ids:
            logger.info(f"Book(s) added successfully with ID(s): {added_ids}")
            return AddBookResponse(
                message="Book(s) added successfully.",
                added_book_ids=added_ids
            )
        else:
            logger.info(f"Book '{file.filename}' was not added (e.g., duplicate ignored, or other reason).")
            return AddBookResponse(
                message="Book was processed but no new entries were added to the library.",
                added_book_ids=[],
                details="This can happen if the book is a duplicate and duplicate adding is off, or if the file is invalid."
            )

    except FileNotFoundError as e: # For calibredb executable not found
        logger.error(f"calibredb not found: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="calibredb command not found. Ensure Calibre is installed.")
    except ValueError as e: # For book file not found (should be caught by os.path.exists in crud)
        logger.error(f"ValueError during book add: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except CalibredbError as e:
        logger.error(f"CalibredbError during add: {e.args[0]}. Stderr: {e.stderr}", exc_info=True)
        detail = f"Error using calibredb add: {e.args[0]}"
        if e.stderr and "No such file or directory" in e.stderr and library_path:
             detail = f"Error with Calibre library path '{library_path}'. Please ensure it is correct. Calibredb: {e.args[0]}"
        raise HTTPException(status_code=500, detail=detail)
    except Exception as e:
        logger.error(f"An unexpected error occurred in /books/add/ endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")
    finally:
        # Clean up: remove the temporary directory and its contents
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Temporary directory '{temp_dir}' cleaned up.")

@app.delete("/books/{book_id}/", response_model=RemoveBookResponse)
async def remove_book_endpoint(
    book_id: int,
    library_path: Optional[str] = Query(None, description="Path to the Calibre library. If not provided, calibredb's default will be used.")
):
    """
    Remove a book from the Calibre library by its ID.
    Uses `calibredb remove_books --permanent --for-machine <id>`.
    """
    try:
        logger.info(f"Received request to remove book ID: {book_id}. Library path: '{library_path}'")

        if book_id <= 0: # Basic validation, crud layer also validates.
            raise HTTPException(status_code=400, detail="Book ID must be a positive integer.")

        # Call the CRUD function to remove the book
        remove_result = remove_book(book_id=book_id, library_path=library_path)

        if remove_result.get("ok") and remove_result.get("num_removed", 0) > 0 and book_id in remove_result.get("removed_ids", []):
            logger.info(f"Book ID: {book_id} removed successfully.")
            return RemoveBookResponse(
                message=f"Book ID {book_id} removed successfully.",
                removed_book_id=book_id
            )
        else:
            # Handle cases where the book was not found or another error occurred based on remove_result
            error_detail = "Failed to remove book."
            errors = remove_result.get("errors", [])
            if errors and isinstance(errors, list) and errors[0].get("id") == book_id:
                error_msg_from_calibre = errors[0].get('error', 'Unknown reason')
                error_detail = f"Failed to remove book ID {book_id}: {error_msg_from_calibre}."
                logger.warning(error_detail)
                if "not found" in error_msg_from_calibre.lower():
                     raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found in the library.")
                # Other specific errors from calibredb might warrant a 400 or 500
                raise HTTPException(status_code=400, detail=error_detail)
            elif not remove_result.get("ok"): # General failure if no specific error message for the ID
                 logger.error(f"Calibredb 'remove_books' reported 'ok: false' for book ID {book_id} with no specific error entry. Result: {remove_result}")
                 raise HTTPException(status_code=500, detail=f"Calibredb failed to remove book ID {book_id}, reason unspecified in errors list.")
            else: # ok: true, but book not in removed_ids or num_removed is 0.
                logger.warning(f"Book ID {book_id} not effectively removed despite 'ok: true'. Result: {remove_result}")
                raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found or already removed.")

    except ValueError as e: # From crud validation (book_id <=0) or our own check.
        logger.warning(f"ValueError in remove_book_endpoint for ID {book_id}: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e: # For calibredb executable not found
        logger.error(f"calibredb not found: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="calibredb command not found. Ensure Calibre is installed.")
    except CalibredbError as e:
        logger.error(f"CalibredbError during remove for ID {book_id}: {e.args[0]}. Stderr: {e.stderr}", exc_info=True)
        detail = f"Error using calibredb remove_books for ID {book_id}: {e.args[0]}"
        raise HTTPException(status_code=500, detail=detail)
    except HTTPException: # Re-raise HTTPExceptions we've already crafted
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred in /books/remove/ endpoint for ID {book_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")

# Example of how to run for local development:
# uvicorn calibre_api.app.main:app --reload --port 6336
# or python -m uvicorn calibre_api.app.main:app --reload --port 6336

@app.put("/books/{book_id}/metadata/", response_model=SetMetadataResponse)
async def set_book_metadata_endpoint(
    book_id: int,
    metadata_update: SetMetadataRequest,
    library_path: Optional[str] = Query(None, description="Path to the Calibre library. If not provided, calibredb's default will be used.")
):
    """
    Set metadata for a specific book in the Calibre library.
    Uses `calibredb set_metadata --for-machine <ID> field:value ...`.
    Only fields provided in the request body will be updated.
    """
    try:
        logger.info(f"Received request to set metadata for book ID: {book_id}. Library path: '{library_path}'. Data: {metadata_update.model_dump(exclude_unset=True)}")

        if book_id <= 0:
            raise HTTPException(status_code=400, detail="Book ID must be a positive integer.")

        if not metadata_update.model_dump(exclude_unset=True):
             raise HTTPException(status_code=400, detail="No metadata fields provided in the request.")

        # Call the CRUD function to set metadata
        # set_book_metadata now returns the JSON output from --for-machine
        # which is {} if book not found / no changes, or {"field": "new_value", ...} if changes made.
        update_result = set_book_metadata(
            book_id=book_id,
            metadata=metadata_update,
            library_path=library_path
        )

        if not update_result: # Empty dict {} means book not found or no actual changes made by calibredb
            # To differentiate, we might need to check if the book exists first,
            # or rely on calibredb's behavior (it typically errors if book ID is invalid but {} if valid ID but no such book)
            # For now, if calibredb set_metadata returns {}, we'll assume "not found or no effective change".
            # A more robust way would be to list the book first, but that's more overhead.
            # The crud function might raise CalibredbError if returncode is non-zero and stderr indicates "No book with id".
            # Let's assume if we reach here with an empty dict, it's likely "not found or no change".
            logger.warning(f"No metadata changes reported by calibredb for book ID {book_id}. This might mean the book was not found or data was identical.")
            # Consider returning 404 if we are sure book not found, or 200/304 if no change but book exists.
            # For simplicity, if calibredb doesn't error but returns {}, let's treat as "no effective change".
            # If the crud layer already raised an error for "book not found" (e.g. non-zero exit from CLI), that's handled by CalibredbError.
            # If `set_metadata` returns {} because the book ID is valid but doesn't exist in the DB, that's a "not found" scenario.
            # The current crud.set_book_metadata returns {} if stdout is empty (book not found) or if JSON is {} (no changes)
            # This ambiguity needs careful handling.
            # If `calibredb set_metadata` runs successfully (exit 0) but outputs `{}`, it means the book was not found OR no actual changes were applied.
            # We should try to be more specific.
            # Let's try listing the book first to confirm existence if update_result is {}. This adds an extra call.
            # Alternative: check stderr from set_metadata if it hints at "No book with id".
            # The crud function `set_book_metadata` already tries to handle some of this.
            # If `process.returncode != 0` and stderr contains "No book with id", it now just passes and returns {}.
            # So an empty dict from crud means either "not found" or "no changes needed".

            # To improve: The crud function could return a more structured object or tuple,
            # e.g., (success_status_enum, data_or_error_message)

            # For now, let's assume an empty `update_result` means the book wasn't found or no metadata was changed.
            # If the goal is to confirm an update, an empty result is not a successful update.
            # If no fields were actually changed (e.g. submitted data was same as existing), calibredb might return {}.
            # This could be a 200 OK with a message "No changes applied" or 404 if we can confirm "not found".
            # The crud.set_book_metadata's behavior with non-zero exit code + "No book with id" in stderr (which then returns {})
            # means we can't easily distinguish "not found" from "no actual change" just from an empty dict here if exit code was 0.

            # Let's assume for now: if result is empty, we say "not found or no changes".
            # A more robust solution would be for crud to better signal "not found".
            # If the CalibredbError from crud specifically said "No book with id X found", it would be a 500 here.
            # This means if we get here with {}, and no CalibredbError was raised, the book *likely* exists but no fields changed.
            # However, `calibredb set_metadata --for-machine` for a non-existent ID returns {} and exit code 0.
            # This is the tricky part.

            # Simplification: If calibredb set_metadata (exit 0) results in {}, assume book not found for API purposes.
            # This makes the API stricter: you must provide changes that *can* be applied to an *existing* book.
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found, or no metadata was actually changed by calibredb.")

        logger.info(f"Metadata for book ID: {book_id} updated successfully. Changes: {update_result}")
        return SetMetadataResponse(
            message=f"Metadata for book ID {book_id} updated successfully.",
            book_id=book_id,
            details=f"Changes applied: {list(update_result.keys())}" if update_result else "No specific changes reported by calibredb (or book not found)."
        )

    except ValueError as e: # From crud validation or our own checks.
        logger.warning(f"ValueError in set_book_metadata_endpoint for ID {book_id}: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e: # For calibredb executable not found
        logger.error(f"calibredb not found: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="calibredb command not found. Ensure Calibre is installed.")
    except CalibredbError as e:
        logger.error(f"CalibredbError during set_metadata for ID {book_id}: {e.args[0]}. Stderr: {e.stderr}", exc_info=True)
        detail = f"Error using calibredb set_metadata for ID {book_id}: {e.args[0]}"
        if e.stderr and "No book with id" in e.stderr and f"id {book_id}" in e.stderr:
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found in the library.")
        raise HTTPException(status_code=500, detail=detail)
    except HTTPException: # Re-raise HTTPExceptions we've already crafted
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred in /books/metadata/ endpoint for ID {book_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")

# Example of how to run for local development:
# uvicorn calibre_api.app.main:app --reload --port 6336
# Ensure calibredb is in PATH and you have a calibre library.
# Test with:
# http://localhost:6336/books/
# http://localhost:6336/books/?search=science%20fiction
# http://localhost:6336/books/?library_path=/path/to/your/calibre/library
# http://localhost:6336/docs for Swagger UI
# http://localhost:6336/redoc for ReDoc UI
