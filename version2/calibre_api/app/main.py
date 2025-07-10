from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional, Any
import logging

from .models import Book
from .crud import list_books, CalibredbError

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
        # Consider the nature of the error. If it's due to a bad search query from user, could be 400.
        # If it's a library access issue, could be 500 or specific codes.
        # For now, a general 500 for calibredb operational issues.
        detail_message = f"Error interacting with calibredb: {e.args[0]}"
        if e.stderr: # Optionally include stderr if it's safe and useful for the client
            # Be cautious about exposing raw stderr directly.
            # detail_message += f" Details: {e.stderr}"
            pass
        raise HTTPException(
            status_code=500,
            detail=detail_message
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred in /books/ endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected server error occurred: {str(e)}"
        )

# Example of how to run for local development:
# uvicorn calibre_api.app.main:app --reload --port 6336
# or python -m uvicorn calibre_api.app.main:app --reload --port 6336
# Ensure calibredb is in PATH and you have a calibre library.
# Test with:
# http://localhost:6336/books/
# http://localhost:6336/books/?search=science%20fiction
# http://localhost:6336/books/?library_path=/path/to/your/calibre/library
# http://localhost:6336/docs for Swagger UI
# http://localhost:6336/redoc for ReDoc UI
