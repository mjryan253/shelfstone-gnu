import subprocess
import json
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
