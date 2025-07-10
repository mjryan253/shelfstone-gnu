import subprocess
import json
import os # Moved import os to top-level
from typing import List, Dict, Optional, Any

class CalibredbError(Exception):
    """Custom exception for errors related to calibredb operations."""
    def __init__(self, message, stderr=None, returncode=None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode

def list_books(library_path: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lists books from a Calibre library using the calibredb command-line tool.

    Args:
        library_path: Optional path to the Calibre library.
        search_query: Optional search query to filter books.

    Returns:
        A list of dictionaries, where each dictionary represents a book.

    Raises:
        FileNotFoundError: If calibredb command is not found.
        CalibredbError: If calibredb command returns an error or fails to parse output.
    """
    cmd = ["calibredb", "list", "--for-machine"]

    if library_path:
        cmd.extend(["--with-library", library_path])

    # Add all fields to get comprehensive data.
    # Users of this function can then select which fields they care about.
    cmd.extend(["--fields", "all"])

    if search_query:
        cmd.extend(["--search", search_query])

    try:
        # Set a timeout to prevent indefinite hanging if calibredb has issues
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False, # Set to False to handle non-zero exit codes manually
            timeout=60 # 60 seconds timeout
        )

        if process.returncode != 0:
            error_message = f"calibredb command failed with exit code {process.returncode}."
            # Log stderr for debugging if necessary, but don't expose it directly in HTTP responses
            # print(f"Calibredb stderr: {process.stderr}")
            raise CalibredbError(error_message, stderr=process.stderr, returncode=process.returncode)

        if not process.stdout.strip():
            # Handle cases where calibredb returns successfully but with empty output (e.g., no books found)
            return []

        try:
            books_data = json.loads(process.stdout)
            return books_data
        except json.JSONDecodeError as e:
            error_message = f"Failed to parse JSON output from calibredb: {e}"
            # print(f"Problematic calibredb output: {process.stdout}")
            raise CalibredbError(error_message)

    except FileNotFoundError:
        # This occurs if 'calibredb' executable is not in PATH
        raise FileNotFoundError("calibredb command not found. Please ensure Calibre is installed and in your PATH.")
    except subprocess.TimeoutExpired:
        raise CalibredbError("calibredb command timed out.")
    except Exception as e:
        # Catch any other unexpected errors during subprocess execution
        raise CalibredbError(f"An unexpected error occurred while running calibredb: {e}")

def add_book(
    file_path: str,
    library_path: Optional[str] = None,
    one_book_per_directory: bool = False,
    duplicates: bool = False,
    automerge: bool = False,
    authors: Optional[str] = None, # Example: "Author One, Author Two"
    title: Optional[str] = None,
    tags: Optional[str] = None, # Example: "tag1, tag2"
    # Add other metadata options as needed, like isbn, series, etc.
) -> List[int]:
    """
    Adds a book to the Calibre library using the calibredb add command.

    Args:
        file_path: Path to the ebook file to add.
        library_path: Optional path to the Calibre library.
        one_book_per_directory: If True, add only one book per directory.
        duplicates: If True, import duplicate books. Otherwise, they are ignored.
        automerge: Automerge newly added books if they are similar to existing books.
        authors: Set authors for the added book.
        title: Set title for the added book.
        tags: Set tags for the added book.

    Returns:
        A list of Calibre book IDs for the added book(s).
        calibredb add can add multiple books if the file_path is a directory
        or an archive, though this wrapper primarily targets single file additions for now.

    Raises:
        FileNotFoundError: If calibredb command or the book file is not found.
        CalibredbError: If calibredb command returns an error.
        ValueError: If the file_path does not exist.
    """
    # import os # Moved to top-level
    if not os.path.exists(file_path):
        raise ValueError(f"Book file not found at: {file_path}")

    cmd = ["calibredb", "add"]

    if library_path:
        cmd.extend(["--with-library", library_path])
    if one_book_per_directory:
        cmd.append("--one-book-per-directory")
    if duplicates:
        cmd.append("--duplicates")
    if automerge:
        cmd.append("--automerge")

    # Metadata options
    metadata_options = []
    if title:
        metadata_options.append(f"title:{title}")
    if authors:
        metadata_options.append(f"authors:{authors}")
    if tags:
        metadata_options.append(f"tags:{tags}")
    # Add other simple metadata fields here if needed

    if metadata_options:
        cmd.extend(["--metadata", ",".join(metadata_options)])


    # The file path should be the last argument typically, or after --
    cmd.extend(["--", file_path])

    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False, # Handle non-zero exit codes manually
            timeout=120 # Increased timeout for potentially larger files or processing
        )

        if process.returncode != 0:
            error_message = f"calibredb add command failed with exit code {process.returncode}."
            raise CalibredbError(error_message, stderr=process.stderr, returncode=process.returncode)

        # calibredb add typically outputs "Added book IDs: X, Y, Z" or similar.
        # Or just "Added book IDs: X" for a single book.
        # If verbose, it might print more. We need to parse the IDs.
        output = process.stdout.strip()
        added_ids: List[int] = []

        # Example output: "Added book IDs: 123" or "Added book IDs: 123, 456"
        # Sometimes it might just output numbers directly on new lines if multiple files are added from a dir.
        # For now, let's assume the "Added book IDs:" prefix for simplicity.
        # A more robust parsing might be needed depending on actual calibredb versions and verbosity.
        if "Added book IDs:" in output:
            ids_str = output.split("Added book IDs:")[1].strip()
            added_ids = [int(id_str.strip()) for id_str in ids_str.split(',') if id_str.strip().isdigit()]
        elif output.isdigit(): # If it just prints an ID
            added_ids.append(int(output))
        else:
            # If parsing fails, it might be an issue or different output format.
            # For now, we'll raise an error if no IDs are found and output is unexpected.
            # Or it could be that no books were actually added (e.g. duplicate ignored, and --duplicates not set)
            # calibredb add might return 0 even if no book is added due to duplicate filtering.
            # The output string "No books added" can appear.
            if "No books added" in output:
                return [] # No books added, return empty list

            # If we can't parse IDs, and it's not "No books added", it's an unexpected output.
            # However, `calibredb add` might not always output IDs if it's not verbose.
            # Let's assume for now that if returncode is 0, it worked, but IDs might not be easily parseable
            # without specific verbosity flags.
            # The command usually prints the IDs of added books to stdout.
            # If no IDs are found, we should probably indicate this.
            # For now, if we can't parse, we'll return an empty list and log it.
            # A better approach might be to use a specific option for machine-readable output if available,
            # but `calibredb add` doesn't seem to have one like `list --for-machine`.
            print(f"Warning: Could not parse book IDs from calibredb add output: {output}")


        return added_ids

    except FileNotFoundError:
        # This occurs if 'calibredb' executable is not in PATH
        raise FileNotFoundError("calibredb command not found. Please ensure Calibre is installed and in your PATH.")
    except subprocess.TimeoutExpired:
        raise CalibredbError("calibredb add command timed out.")
    except ValueError as ve: # Catch the ValueError from os.path.exists
        raise ve
    except Exception as e:
        raise CalibredbError(f"An unexpected error occurred while running calibredb add: {e}")


def remove_book(book_id: int, library_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Removes a book from the Calibre library using the calibredb remove_books command.

    Args:
        book_id: The ID of the book to remove.
        library_path: Optional path to the Calibre library.

    Returns:
        A dictionary containing the result of the remove operation, typically
        parsed from the JSON output of `calibredb remove_books --for-machine`.
        Example successful output: {"ok": true, "num_removed": 1, "removed_ids": [book_id]}
        Example if book not found: {"ok": false, "num_removed": 0, "removed_ids": [], "errors": [{"id": book_id, "error": "Book not found"}]}


    Raises:
        FileNotFoundError: If calibredb command is not found.
        CalibredbError: If calibredb command returns an error or fails to parse output.
        ValueError: If book_id is not a positive integer.
    """
    if not isinstance(book_id, int) or book_id <= 0:
        raise ValueError("Book ID must be a positive integer.")

    cmd = ["calibredb", "remove_books", "--permanent", "--for-machine", str(book_id)]

    if library_path:
        cmd.extend(["--with-library", library_path])

    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False, # Handle non-zero exit codes manually
            timeout=60
        )

        # calibredb remove_books --for-machine should always return 0 if it runs,
        # even if the book is not found. The success/failure is in the JSON output.
        # However, if it fails for other reasons (e.g. library lock), returncode might be non-zero.
        if process.returncode != 0:
            error_message = f"calibredb remove_books command failed with exit code {process.returncode}."
            raise CalibredbError(error_message, stderr=process.stderr, returncode=process.returncode)

        if not process.stdout.strip():
            # This case should ideally not happen with --for-machine if the command executed.
            raise CalibredbError("calibredb remove_books command returned empty output despite --for-machine.")

        try:
            result_data = json.loads(process.stdout)
            # Example: {"ok": true, "num_removed": 1, "removed_ids": [123]}
            # Example error: {"ok": false, "num_removed": 0, "removed_ids": [], "errors": [{"id": 123, "error": "Book not found"}]}
            # We return the whole dict as it contains useful info.
            return result_data
        except json.JSONDecodeError as e:
            error_message = f"Failed to parse JSON output from calibredb remove_books: {e}. Output: {process.stdout}"
            raise CalibredbError(error_message)

    except FileNotFoundError:
        raise FileNotFoundError("calibredb command not found. Please ensure Calibre is installed and in your PATH.")
    except subprocess.TimeoutExpired:
        raise CalibredbError("calibredb remove_books command timed out.")
    except ValueError as ve: # Catch the ValueError from book_id check
        raise ve
    except Exception as e:
        raise CalibredbError(f"An unexpected error occurred while running calibredb remove_books: {e}")

def set_book_metadata(book_id: int, metadata: 'SetMetadataRequest', library_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Sets metadata for a book in the Calibre library using `calibredb set_metadata`.

    Args:
        book_id: The ID of the book to update.
        metadata: A SetMetadataRequest object containing the metadata to set.
        library_path: Optional path to the Calibre library.

    Returns:
        A dictionary parsed from the JSON output of `calibredb set_metadata --for-machine`.
        An empty dict {} if no changes were made or book not found.
        A dict like {"title": "New Title", "authors": ["New Author"]} if changes were made.

    Raises:
        FileNotFoundError: If calibredb command is not found.
        CalibredbError: If calibredb command returns an error or fails to parse output.
        ValueError: If book_id is not positive or no metadata fields are provided.
    """
    if not isinstance(book_id, int) or book_id <= 0:
        raise ValueError("Book ID must be a positive integer.")

    # from .models import SetMetadataRequest # Avoid circular import if type hint is string
    # This function is type hinted with 'SetMetadataRequest', so it's fine.

    args_to_set = []
    metadata_dict = metadata.model_dump(exclude_unset=True) # Pydantic v2

    if not metadata_dict:
        raise ValueError("No metadata fields provided to set.")

    for field, value in metadata_dict.items():
        if value is None: # Should be excluded by exclude_unset=True, but double check
            continue

        formatted_value = ""
        if field == "authors" or field == "tags":
            if isinstance(value, list):
                formatted_value = ",".join(value)
            else: # Should not happen if Pydantic model is used correctly
                formatted_value = str(value)
        elif field == "rating":
            # Calibre ratings are 0-10 (0-5 stars, half points).
            # Ensure the value is appropriate if specific validation is needed beyond Pydantic.
            # For now, pass it as is.
            formatted_value = str(float(value)) # Ensure it's a float representation
        elif field == "pubdate":
             # calibredb expects YYYY-MM-DD or a full ISO timestamp.
             # Pydantic model has str, so pass as is. Consider date validation/formatting if stricter.
            formatted_value = str(value)
        elif field == "series_index":
            formatted_value = str(float(value))
        else:
            formatted_value = str(value)

        # Escape characters that might interfere with CLI argument parsing if necessary.
        # For simple string:value, direct passing is usually fine.
        # Complex values with spaces or special chars might need quoting by subprocess.run or manual shell escaping.
        # However, calibredb usually handles "field:value with spaces" correctly if passed as a single arg.
        # For now, we assume direct string concatenation is okay for calibredb's parser.
        args_to_set.append(f"{field}:{formatted_value}")


    if not args_to_set:
        # This case should ideally be caught by "No metadata fields provided" earlier.
        # If metadata_dict was populated but all values led to empty formatted_values (unlikely).
        raise ValueError("No valid metadata arguments could be constructed.")

    cmd = ["calibredb", "set_metadata", "--for-machine", str(book_id)] + args_to_set

    if library_path:
        cmd.extend(["--with-library", library_path])

    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60
        )

        if process.returncode != 0:
            # stderr might contain "No book with id X found"
            if "No book with id" in process.stderr and f"id {book_id}" in process.stderr:
                 # Treat as book not found, set_metadata --for-machine outputs {} in this case.
                 # So, the return code non-zero is likely a more severe issue.
                 pass # Let it fall through to JSON parsing, which should be {}

            error_message = f"calibredb set_metadata command failed with exit code {process.returncode}."
            # If stderr indicates book not found, it's not necessarily a CalibredbError for the command itself,
            # but rather for the operation's outcome. However, a non-zero exit code is an error.
            raise CalibredbError(error_message, stderr=process.stderr, returncode=process.returncode)

        if not process.stdout.strip() and process.returncode == 0 :
             # This means book not found or no changes made, as per --for-machine docs (empty object {})
             # It might output nothing or "{}"
             # If it's truly empty string, assume {}
             return {}

        try:
            result_data = json.loads(process.stdout if process.stdout.strip() else "{}")
            # Example successful: {"title": "New Title", "tags": ["new", "tags"]}
            # Example not found / no changes: {}
            return result_data
        except json.JSONDecodeError as e:
            error_message = f"Failed to parse JSON output from calibredb set_metadata: {e}. Output: '{process.stdout}'"
            raise CalibredbError(error_message)

    except FileNotFoundError:
        raise FileNotFoundError("calibredb command not found. Please ensure Calibre is installed and in your PATH.")
    except subprocess.TimeoutExpired:
        raise CalibredbError("calibredb set_metadata command timed out.")
    except ValueError as ve: # From book_id check or no metadata fields
        raise ve
    except Exception as e:
        raise CalibredbError(f"An unexpected error occurred while running calibredb set_metadata: {e}")


if __name__ == '__main__':
    # Example usage (for manual testing)
    # Ensure you have a Calibre library and `calibredb` is in your PATH.
    # You might need to specify --with-library if your default Calibre library isn't set
    # or if you want to target a specific one.
    print("Attempting to list books from default Calibre library...")
    try:
        # Test without library path (uses default Calibre library)
        # books = list_books(search_query="language:eng")

        # To test with a specific library:
        # books = list_books(library_path="/path/to/your/calibre/library", search_query="Foundation")

        # For this example, let's assume there's no default library or it's empty,
        # and we don't specify one, which might lead to an error or empty list
        # depending on the calibredb setup.
        # A more robust test here would involve setting up a known library.

        books = list_books() # This will likely use a default library if configured, or error if not.
                             # For CI/testing, a known library path is better.

        if books:
            print(f"Found {len(books)} books.")
            print("First book details:")
            print(json.dumps(books[0], indent=2))
        else:
            print("No books found or library is empty/not accessible.")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure 'calibredb' is installed and in your system's PATH.")
    except CalibredbError as e:
        print(f"Calibredb Error: {e}")
        if e.stderr:
            print(f"Calibredb Stderr: {e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    print("\nAttempting to list books from a non-existent library (should fail gracefully)...")
    try:
        books = list_books(library_path="/tmp/non_existent_calibre_library_xyz123")
        print(f"Found {len(books)} books.") # Should not reach here if library is truly non-existent
    except CalibredbError as e:
        print(f"Calibredb Error (as expected for non-existent library): {e.args[0]}")
        # Note: The exact error message/code from calibredb for a non-existent library can vary.
        # This test primarily checks if our wrapper handles calibredb's failure.
    except FileNotFoundError as e: # If calibredb itself is not found
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
