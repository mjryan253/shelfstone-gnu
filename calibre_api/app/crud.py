import json
import os
from typing import List, Dict, Optional, Any

# Use the centralized CalibreCLIError and run_calibre_command
from .calibre_cli import CalibreCLIError, run_calibre_command
# We can make CalibredbError a specialized version of CalibreCLIError or just use CalibreCLIError directly.
# For now, let's define it as a subclass to maintain specificity if desired,
# but it could also be an alias or replaced by CalibreCLIError.

class CalibredbError(CalibreCLIError):
    """Custom exception for errors related to calibredb operations,
    inheriting from the general CalibreCLIError."""
    def __init__(self, message, stdout=None, stderr=None, returncode=None):
        # Ensure constructor matches CalibreCLIError or adapt as needed.
        # CalibreCLIError takes: message, stdout=None, stderr=None, returncode=None
        super().__init__(message, stdout=stdout, stderr=stderr, returncode=returncode)


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

    # FileNotFoundError and CalibreCLIError (for timeout) are handled by run_calibre_command
    stdout, stderr, returncode = run_calibre_command(cmd, timeout=60)

    if returncode != 0:
        error_message = f"calibredb list command failed with exit code {returncode}."
        raise CalibredbError(error_message, stdout=stdout, stderr=stderr, returncode=returncode)

    if not stdout.strip():
        # Handle cases where calibredb returns successfully but with empty output (e.g., no books found)
        return []

    try:
        books_data = json.loads(stdout)
        return books_data
    except json.JSONDecodeError as e:
        error_message = f"Failed to parse JSON output from calibredb list: {e}"
        # Include stdout in the error for debugging, as it contains the problematic text
        raise CalibredbError(error_message, stdout=stdout, stderr=stderr, returncode=returncode)


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

    # FileNotFoundError and CalibreCLIError (for timeout) are handled by run_calibre_command
    stdout, stderr, returncode = run_calibre_command(cmd, timeout=120)

    if returncode != 0:
        error_message = f"calibredb add command failed with exit code {returncode}."
        raise CalibredbError(error_message, stdout=stdout, stderr=stderr, returncode=returncode)

    # calibredb add typically outputs "Added book IDs: X, Y, Z" or similar.
    # Or just "Added book IDs: X" for a single book.
    # If verbose, it might print more. We need to parse the IDs.
    output_str = stdout.strip() # Use stdout from run_calibre_command
    added_ids: List[int] = []

    if "Added book IDs:" in output_str:
        ids_str_part = output_str.split("Added book IDs:")[1].strip()
        added_ids = [int(id_val.strip()) for id_val in ids_str_part.split(',') if id_val.strip().isdigit()]
    elif output_str.isdigit(): # If it just prints an ID
        added_ids.append(int(output_str))
    else:
        if "No books added" in output_str:
            return [] # No books added, return empty list

        # Log if output is unexpected and no IDs parsed
        # This situation might occur if calibredb add has different output formats
        # or if no IDs are printed despite success (e.g. not verbose enough).
        # For now, we assume if IDs are not in the expected format and it's not "No books added",
        # it's an empty result for added IDs unless an error code was already raised.
        if returncode == 0: # Command succeeded but output not recognized for ID parsing
            # Consider logging this as a warning if a logger is available/configured
            print(f"Warning: Could not parse book IDs from calibredb add output: {output_str}")
            # Return empty list as we couldn't confirm any IDs were added from the output.
            # This maintains the function signature but signals no specific IDs found.
            return []
            # Alternatively, if any non-ID-containing output on success is an error for this function:
            # raise CalibredbError("Failed to parse book IDs from successful calibredb add output.", stdout=stdout, stderr=stderr, returncode=returncode)


    return added_ids


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

    # FileNotFoundError and CalibreCLIError (for timeout) are handled by run_calibre_command
    stdout, stderr, returncode = run_calibre_command(cmd, timeout=60)

    # calibredb remove_books --for-machine should always return 0 if it runs,
    # even if the book is not found. The success/failure is in the JSON output.
    # However, if it fails for other reasons (e.g. library lock), returncode might be non-zero.
    if returncode != 0:
        error_message = f"calibredb remove_books command failed with exit code {returncode}."
        raise CalibredbError(error_message, stdout=stdout, stderr=stderr, returncode=returncode)

    if not stdout.strip():
        # This case should ideally not happen with --for-machine if the command executed.
        # If it does, it's an unexpected state.
        raise CalibredbError(
            "calibredb remove_books command returned empty stdout despite --for-machine.",
            stdout=stdout, stderr=stderr, returncode=returncode
        )

    try:
        result_data = json.loads(stdout)
        return result_data
    except json.JSONDecodeError as e:
        error_message = f"Failed to parse JSON output from calibredb remove_books: {e}. Output: {stdout}"
        raise CalibredbError(error_message, stdout=stdout, stderr=stderr, returncode=returncode)


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

    # FileNotFoundError and CalibreCLIError (for timeout) are handled by run_calibre_command
    stdout, stderr, returncode = run_calibre_command(cmd, timeout=60)

    if returncode != 0:
        # Check if stderr indicates "No book with id X found", even with non-zero exit.
        # Some calibredb versions/operations might exit non-zero for this.
        # However, the primary expectation for `set_metadata --for-machine` is exit 0
        # and empty JSON `{}` if book not found or no changes.
        # A non-zero exit usually means a more fundamental problem with the command execution itself.
        if "No book with id" in stderr and f"id {book_id}" in stderr:
            # If this specific error occurs with a non-zero exit, it's still a failure,
            # but we might treat it as "not found" leading to {} if that's desired.
            # However, run_calibre_command's contract implies non-zero is an execution problem.
            # For now, let any non-zero exit be a CalibredbError indicating command failure.
            # The specific wrappers or endpoint logic can then inspect stderr if needed.
            pass # Let the generic error be raised below.

        error_message = f"calibredb set_metadata command failed with exit code {returncode}."
        raise CalibredbError(error_message, stdout=stdout, stderr=stderr, returncode=returncode)

    # If command execution was successful (returncode == 0):
    if not stdout.strip():
        # This means book not found or no changes made, as per --for-machine docs (empty object {})
        # It might output nothing or "{}"
        return {}

    try:
        result_data = json.loads(stdout) # `stdout` should be "{}" if empty or no changes
        return result_data
    except json.JSONDecodeError as e:
        error_message = f"Failed to parse JSON output from calibredb set_metadata: {e}. Output: '{stdout}'"
        raise CalibredbError(error_message, stdout=stdout, stderr=stderr, returncode=returncode)


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
