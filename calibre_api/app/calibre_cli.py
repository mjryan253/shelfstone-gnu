import subprocess
import logging
from typing import Tuple

# Configure basic logging
logger = logging.getLogger(__name__)

class CalibreCLIError(Exception):
    """Custom exception for errors related to Calibre CLI operations."""
    def __init__(self, message, stdout=None, stderr=None, returncode=None):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def __str__(self):
        return f"{super().__str__()} (returncode: {self.returncode})\nStderr: {self.stderr}\nStdout: {self.stdout}"


def run_calibre_command(command: list[str], timeout: int = 60) -> Tuple[str, str, int]:
    """
    Runs a generic Calibre CLI command using subprocess.

    Args:
        command: A list of strings representing the command and its arguments
                 (e.g., ['ebook-convert', 'input.txt', 'output.epub']).
        timeout: The timeout in seconds for the command execution.

    Returns:
        A tuple containing (stdout, stderr, returncode) of the executed command.

    Raises:
        FileNotFoundError: If the first element of the command (the Calibre executable) is not found.
        CalibreCLIError: If the command times out or returns a non-zero exit code,
                         or if any other subprocess-related error occurs.
    """
    if not command:
        raise ValueError("Command list cannot be empty.")

    executable_name = command[0]
    logger.info(f"Running Calibre command: {' '.join(command)}")

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,  # We will check the return code manually
            timeout=timeout
        )

        if process.returncode != 0:
            # Log the error but let the caller decide if it's a CalibreCLIError based on context
            logger.warning(
                f"{executable_name} command failed with exit code {process.returncode}."
                f"\nCommand: {' '.join(command)}"
                f"\nStderr: {process.stderr.strip()}"
                f"\nStdout: {process.stdout.strip()}"
            )
            # The decision to raise CalibreCLIError here or let the specific wrapper function
            # interpret the non-zero exit code depends on how granular we want the error handling.
            # For now, any non-zero return code from this generic helper will be an error.
            # Specific wrappers can catch this and provide more context or handle expected non-zero exits.
            # raise CalibreCLIError(
            #     message=f"{executable_name} command failed.",
            #     stdout=process.stdout.strip(),
            #     stderr=process.stderr.strip(),
            #     returncode=process.returncode
            # )

        return process.stdout.strip(), process.stderr.strip(), process.returncode

    except FileNotFoundError:
        logger.error(f"{executable_name} command not found. Ensure Calibre is installed and in your PATH.")
        raise FileNotFoundError(f"{executable_name} command not found. Ensure Calibre is installed and in your PATH.")
    except subprocess.TimeoutExpired:
        logger.error(f"{executable_name} command timed out after {timeout} seconds. Command: {' '.join(command)}")
        raise CalibreCLIError(
            message=f"{executable_name} command timed out.",
            stderr=f"Timeout after {timeout} seconds.",
            returncode=-1 # Using a custom return code for timeout
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred while running {executable_name}: {e}. Command: {' '.join(command)}", exc_info=True)
        raise CalibreCLIError(
            message=f"An unexpected error occurred while running {executable_name}: {str(e)}",
            returncode=-2 # Using a custom return code for other errors
        )

if __name__ == '__main__':
    # Example usage for testing run_calibre_command
    # This assumes 'calibre' or 'ebook-convert' (or other calibre tools) are in PATH

    # Test 1: Get calibre version (should succeed if calibre is installed)
    print("Test 1: Get Calibre version using 'calibre --version'")
    try:
        # Most Calibre tools support --version
        stdout, stderr, retcode = run_calibre_command(['calibre', '--version'])
        if retcode == 0:
            print(f"Success! Output:\n{stdout}")
        else:
            print(f"Command failed with code {retcode}. Stderr: {stderr}\nStdout: {stdout}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except CalibreCLIError as e:
        print(f"CalibreCLIError: {e}")
    print("-" * 20)

    # Test 2: A command that is expected to fail (e.g., invalid command)
    print("Test 2: Run a deliberately failing command 'ebook-convert --non-existent-option'")
    try:
        # Using ebook-convert as it's a common Calibre tool
        stdout, stderr, retcode = run_calibre_command(['ebook-convert', '--non-existent-option'])
        print(f"Command executed. Return code: {retcode}")
        print(f"Stdout:\n{stdout}")
        print(f"Stderr:\n{stderr}")
        if retcode != 0:
            print("Command failed as expected.")
            # Example of raising CalibreCLIError if a non-zero exit is always an error
            # raise CalibreCLIError("Deliberate failure test", stdout, stderr, retcode)
    except FileNotFoundError:
        print("Error: ebook-convert not found. Ensure Calibre is installed.")
    except CalibreCLIError as e:
        print(f"CalibreCLIError (expected for deliberate failure if raised by helper): {e}")
    except Exception as e:
        print(f"Unexpected exception: {e}")
    print("-" * 20)

    # Test 3: Non-existent executable
    print("Test 3: Run a non-existent Calibre command 'nonexistent-calibre-tool --version'")
    try:
        stdout, stderr, retcode = run_calibre_command(['nonexistent-calibre-tool', '--version'])
        print(f"Command executed? Output: {stdout}, Stderr: {stderr}, Code: {retcode}") # Should not reach here
    except FileNotFoundError as e:
        print(f"FileNotFoundError (expected): {e}")
    except CalibreCLIError as e:
        print(f"CalibreCLIError: {e}") # Should be FileNotFoundError
    print("-" * 20)

    # Test 4: Command timeout (requires a command that takes time, or a very short timeout)
    # For a real timeout test, you might need a command that actually hangs or takes long.
    # Here, we simulate with a very short timeout on a command that might take slightly longer than it.
    # 'calibredb list' on a large library could work, or 'ebook-convert' on a large file.
    # For this example, let's just use 'calibre --version' with a tiny timeout to force it.
    # This might not reliably timeout as --version is fast.
    print("Test 4: Command timeout test with 'calibre --version' and 0.001s timeout")
    try:
        # Note: 0.001s is very aggressive and might lead to platform-dependent behavior.
        # A more reliable test might involve a script that sleeps.
        stdout, stderr, retcode = run_calibre_command(['calibre', '--version'], timeout=0.00001)
        print(f"Command executed. Output: {stdout}, Stderr: {stderr}, Code: {retcode}")
    except CalibreCLIError as e:
        if "timed out" in e.args[0]:
            print(f"CalibreCLIError (timeout expected): {e.args[0]}")
        else:
            print(f"CalibreCLIError (unexpected, possibly due to very short timeout): {e}")
    except FileNotFoundError:
        print("Error: calibre not found. Ensure Calibre is installed.")
    except Exception as e:
        print(f"Unexpected exception: {e}")
    print("-" * 20)

    # Test 5: Empty command list
    print("Test 5: Empty command list")
    try:
        run_calibre_command([])
    except ValueError as e:
        print(f"ValueError (expected): {e}")
    print("-" * 20)

    print("Basic tests for run_calibre_command complete.")


# --- Wrapper Functions ---

def get_calibre_version() -> str:
    """
    Gets the installed Calibre version.
    Runs `calibre --version`.

    Returns:
        The Calibre version string.

    Raises:
        CalibreCLIError: If the command fails or returns a non-zero exit code.
        FileNotFoundError: If 'calibre' executable is not found.
    """
    command = ['calibre', '--version']
    stdout, stderr, returncode = run_calibre_command(command)

    if returncode != 0:
        raise CalibreCLIError(
            message="Failed to get Calibre version.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )
    # Example output: "calibre (calibre 6.27.0)\nCopyright Kovid Goyal"
    # Or just "calibre 6.27.0"
    # We need to parse this to get the version number reliably.
    # For now, returning the full stdout. A more robust parsing can be added.
    if "calibre (" in stdout and ")" in stdout: # Format: calibre (calibre X.Y.Z)
        try:
            version_part = stdout.split("calibre (calibre")[1].split(")")[0].strip()
            return version_part
        except IndexError:
            pass # Fallback to returning stdout
    elif stdout.startswith("calibre "): # Format: calibre X.Y.Z
        return stdout.split("calibre ")[1].strip()

    return stdout # Fallback if parsing fails

def ebook_convert(
    input_file: str,
    output_file: str,
    options: Optional[List[str]] = None
) -> str:
    """
    Converts an e-book from one format to another using `ebook-convert`.

    Args:
        input_file: Path to the input e-book file.
        output_file: Path for the converted output e-book file.
        options: A list of additional options for ebook-convert (e.g., ["--authors", "John Doe"]).

    Returns:
        The path to the output_file if conversion is successful.

    Raises:
        CalibreCLIError: If ebook-convert fails.
        FileNotFoundError: If 'ebook-convert' executable or input_file is not found.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    command = ['ebook-convert', input_file, output_file]
    if options:
        command.extend(options)

    stdout, stderr, returncode = run_calibre_command(command, timeout=300) # Conversion can take time

    if returncode != 0:
        # ebook-convert might output useful error messages to stdout or stderr
        raise CalibreCLIError(
            message=f"ebook-convert failed for {input_file} to {output_file}.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    # Check if output file was created (ebook-convert might not error but still fail to produce file)
    if not os.path.exists(output_file):
        raise CalibreCLIError(
            message=f"ebook-convert completed but output file {output_file} was not created.",
            stdout=stdout,
            stderr=stderr, # stderr might contain the reason
            returncode=returncode # Could be 0 if it "succeeded" but didn't create the file for some reason
        )

    logger.info(f"ebook-convert successful: {input_file} -> {output_file}")
    return output_file

def get_ebook_metadata(
    ebook_file_path: str,
    output_opf_file: Optional[str] = None,
    as_json: bool = False,
) -> Union[str, Dict[str, Any]]:
    """
    Reads metadata from a standalone e-book file using `ebook-meta`.
    Can output to an OPF file or return as JSON.

    Args:
        ebook_file_path: Path to the e-book file.
        output_opf_file: Optional. Path to save metadata as an OPF file.
                         If provided, the OPF content is written to this file.
        as_json: If True, attempts to parse the OPF output into a JSON-like dictionary.
                 `output_opf_file` is ignored if `as_json` is True (uses temp OPF).

    Returns:
        If `as_json` is True, returns a dictionary of metadata.
        If `output_opf_file` is provided and `as_json` is False, returns the path to the OPF file.
        Otherwise (neither `output_opf_file` nor `as_json`), returns the raw OPF content as a string.


    Raises:
        CalibreCLIError: If ebook-meta fails.
        FileNotFoundError: If 'ebook-meta' executable or ebook_file_path is not found.
    """
    if not os.path.exists(ebook_file_path):
        raise FileNotFoundError(f"E-book file not found: {ebook_file_path}")

    temp_opf_created = False
    if as_json and not output_opf_file:
        # Create a temporary OPF file for --to-opf if as_json is requested
        # because ebook-meta doesn't directly output JSON.
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".opf", mode="w+") as tmp_opf:
            output_opf_file = tmp_opf.name
            temp_opf_created = True

    command = ['ebook-meta', ebook_file_path]
    if output_opf_file:
        command.extend(['--to-opf', output_opf_file])

    # If neither output_opf_file is given nor as_json is true, ebook-meta prints to stdout.
    # If output_opf_file is given, it prints nothing to stdout.

    stdout, stderr, returncode = run_calibre_command(command)

    if returncode != 0:
        if temp_opf_created and os.path.exists(output_opf_file):
            os.remove(output_opf_file)
        raise CalibreCLIError(
            message=f"ebook-meta failed to read metadata from {ebook_file_path}.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    try:
        if as_json:
            if not output_opf_file: # Should have been created if as_json was true
                raise CalibreCLIError("Internal error: OPF file path missing for JSON conversion.")

            if not os.path.exists(output_opf_file) or os.path.getsize(output_opf_file) == 0:
                 raise CalibreCLIError(
                    message=f"ebook-meta ran but OPF file {output_opf_file} was not created or is empty.",
                    stdout=stdout, stderr=stderr, returncode=returncode
                )

            with open(output_opf_file, 'r', encoding='utf-8') as f:
                opf_content = f.read()

            # Basic OPF to JSON parsing (can be made more robust)
            # This requires an XML parser. Python's built-in xml.etree.ElementTree is good.
            import xml.etree.ElementTree as ET
            metadata_dict = {}
            try:
                root = ET.fromstring(opf_content)
                # Namespace handling is important for OPF files
                ns = {
                    'opf': 'http://www.idpf.org/ २०07/opf',
                    'dc': 'http://purl.org/dc/elements/1.1/'
                }
                metadata_node = root.find('opf:metadata', ns)
                if metadata_node is not None:
                    for child in metadata_node:
                        tag_name = child.tag.split('}')[-1] # Remove namespace
                        if tag_name in metadata_dict:
                            if not isinstance(metadata_dict[tag_name], list):
                                metadata_dict[tag_name] = [metadata_dict[tag_name]]
                            metadata_dict[tag_name].append(child.text)
                        else:
                            metadata_dict[tag_name] = child.text
                    # Handle attributes like scheme for identifiers, role for creators, etc.
                    # For simplicity, this basic parser might miss some nuances.
                return metadata_dict
            except ET.ParseError as e:
                raise CalibreCLIError(f"Failed to parse OPF content from {ebook_file_path}: {e}", stdout=opf_content)

        elif output_opf_file:
            if not os.path.exists(output_opf_file):
                 raise CalibreCLIError(
                    message=f"ebook-meta command ran but OPF file {output_opf_file} was not created.",
                    stdout=stdout, stderr=stderr, returncode=returncode
                )
            return output_opf_file # Return path to the OPF file
        else:
            # If no output_opf_file and not as_json, ebook-meta prints OPF to stdout
            return stdout # Return raw OPF content from stdout
    finally:
        if temp_opf_created and os.path.exists(output_opf_file):
            os.remove(output_opf_file)


def set_ebook_metadata(
    ebook_file_path: str,
    metadata_options: List[str]
) -> str:
    """
    Writes metadata to a standalone e-book file using `ebook-meta`.

    Args:
        ebook_file_path: Path to the e-book file.
        metadata_options: A list of metadata settings, e.g.,
                          ["--title", "New Title", "--authors", "Author Name"].
                          Each option and its value should be separate items if the option takes a value.

    Returns:
        A success message string if metadata is set successfully.

    Raises:
        CalibreCLIError: If ebook-meta fails.
        FileNotFoundError: If 'ebook-meta' executable or ebook_file_path is not found.
    """
    if not os.path.exists(ebook_file_path):
        raise FileNotFoundError(f"E-book file not found: {ebook_file_path}")

    if not metadata_options:
        raise ValueError("metadata_options cannot be empty.")

    command = ['ebook-meta', ebook_file_path] + metadata_options

    stdout, stderr, returncode = run_calibre_command(command)

    if returncode != 0:
        raise CalibreCLIError(
            message=f"ebook-meta failed to set metadata for {ebook_file_path}.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    # ebook-meta usually prints "Metadata changed for..." or "No changes to metadata..."
    # We can return stdout as it often contains a confirmation.
    logger.info(f"ebook-meta set metadata for {ebook_file_path}. Output: {stdout}")
    return stdout if stdout else "Metadata setting command executed."


def ebook_polish(
    ebook_file_path: str,
    output_file_path: Optional[str] = None, # If None, polishes in-place (if supported by format)
    options: Optional[List[str]] = None,
    polish_in_place_if_possible: bool = True # Default behavior of ebook-polish
) -> str:
    """
    Polishes an e-book file using `ebook-polish`.
    Operations can include subsetting fonts, updating metadata from an OPF, etc.

    Args:
        ebook_file_path: Path to the input e-book file (EPUB, AZW3, possibly others).
        output_file_path: Optional path for the polished output file.
                          If None and `polish_in_place_if_possible` is True,
                          ebook-polish will modify the file in-place if the format supports it.
                          If None and `polish_in_place_if_possible` is False, an error might occur
                          or a temporary file might be used by ebook-polish internally.
                          It's safer to provide an output_file_path if not polishing in-place.
        options: A list of additional options for ebook-polish (e.g., ["--subset-fonts"]).
        polish_in_place_if_possible: If True (default) and output_file_path is None, allows
                                     ebook-polish to modify the input file directly.
                                     If False and output_file_path is None, this function might raise
                                     an error as ebook-polish needs an output destination.

    Returns:
        Path to the polished e-book file. If polished in-place, this is ebook_file_path.
        Otherwise, it's output_file_path.

    Raises:
        CalibreCLIError: If ebook-polish fails.
        FileNotFoundError: If 'ebook-polish' executable or ebook_file_path is not found.
        ValueError: If arguments are inconsistent (e.g., no output path when in-place is disallowed).
    """
    if not os.path.exists(ebook_file_path):
        raise FileNotFoundError(f"E-book file not found: {ebook_file_path}")

    command = ['ebook-polish']

    actual_output_path = ebook_file_path # Assume in-place polish initially

    if output_file_path:
        command.extend([ebook_file_path, output_file_path])
        actual_output_path = output_file_path
    elif polish_in_place_if_possible:
        # If output_file_path is None and polish_in_place_if_possible is True,
        # ebook-polish expects the input file path as the first argument, and it will modify it.
        command.append(ebook_file_path)
        # The output path is implicitly the input path.
    else: # output_file_path is None AND polish_in_place_if_possible is False
        # This is problematic. ebook-polish needs an output if not in-place.
        # The CLI usually takes <input_file> <output_file> if not in-place.
        # For safety, let's require an output_file_path if not polishing in-place.
        raise ValueError("output_file_path must be provided if polish_in_place_if_possible is False.")

    if options:
        command.extend(options)

    stdout, stderr, returncode = run_calibre_command(command, timeout=300) # Polishing can take time

    if returncode != 0:
        raise CalibreCLIError(
            message=f"ebook-polish failed for {ebook_file_path}.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    # Verify output file exists
    if not os.path.exists(actual_output_path):
        raise CalibreCLIError(
            message=f"ebook-polish completed but output file {actual_output_path} was not created/found.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    logger.info(f"ebook-polish successful for {ebook_file_path}. Output at: {actual_output_path}")
    return actual_output_path


def fetch_ebook_metadata(
    title: Optional[str] = None,
    authors: Optional[str] = None, # Comma separated string of authors
    isbn: Optional[str] = None,
    ids: Optional[Dict[str, str]] = None, # e.g. {"goodreads": "12345"}
    output_opf_file: Optional[str] = None, # If provided, saves to OPF file
    timeout_seconds: int = 60,
    as_json: bool = False,
) -> Union[str, Dict[str, Any]]:
    """
    Fetches e-book metadata from online sources using `fetch-ebook-metadata`.

    Args:
        title: The title of the book.
        authors: Comma-separated string of author names.
        isbn: ISBN of the book.
        ids: Dictionary of external identifiers (e.g., {'goodreads': '12345'}).
        output_opf_file: Optional. Path to save metadata as an OPF file.
        timeout_seconds: Timeout for the fetch operation.
        as_json: If True, attempts to parse the OPF output into a JSON-like dictionary.
                 `output_opf_file` is used as a temporary location if not provided.

    Returns:
        If `as_json` is True, returns a dictionary of metadata.
        If `output_opf_file` is provided and `as_json` is False, returns the path to the OPF file.
        Otherwise (neither `output_opf_file` nor `as_json`), returns the raw OPF content as a string.

    Raises:
        CalibreCLIError: If fetch-ebook-metadata fails or finds no metadata.
        FileNotFoundError: If 'fetch-ebook-metadata' executable is not found.
        ValueError: If no search criteria (title, authors, isbn, ids) are provided.
    """
    if not (title or authors or isbn or ids):
        raise ValueError("At least one of title, authors, isbn, or ids must be provided for fetching metadata.")

    command = ['fetch-ebook-metadata']
    if title:
        command.extend(['--title', title])
    if authors:
        # fetch-ebook-metadata takes authors one by one with -a or --authors
        # If multiple authors, split and add them.
        for author in authors.split(','):
            command.extend(['--authors', author.strip()])
    if isbn:
        command.extend(['--isbn', isbn])
    if ids:
        for site, site_id in ids.items():
            command.extend(['--identifier', f"{site}:{site_id}"])

    command.extend(['--timeout', str(timeout_seconds)])

    temp_opf_for_json = None
    actual_opf_target = output_opf_file

    if as_json and not output_opf_file:
        import tempfile
        # Create a temporary OPF file for --opf if as_json is requested
        with tempfile.NamedTemporaryFile(delete=False, suffix=".opf", mode="w+") as tmp_opf:
            temp_opf_for_json = tmp_opf.name
            actual_opf_target = temp_opf_for_json

    if actual_opf_target:
        command.extend(['--opf', actual_opf_target])

    # If no actual_opf_target, output is to stdout.

    stdout, stderr, returncode = run_calibre_command(command, timeout=timeout_seconds + 10) # Add buffer to timeout

    try:
        if returncode != 0:
            # fetch-ebook-metadata can return non-zero if metadata not found.
            # stderr often contains "No metadata found" or similar.
            # We should treat "No metadata found" as a specific case, not necessarily a hard error.
            if "No metadata found" in stderr or "No metadata found" in stdout:
                 raise CalibreCLIError(
                    message="No metadata found for the given criteria.",
                    stdout=stdout, stderr=stderr, returncode=returncode
                )
            raise CalibreCLIError(
                message="fetch-ebook-metadata command failed.",
                stdout=stdout, stderr=stderr, returncode=returncode
            )

        if as_json:
            if not actual_opf_target:
                raise CalibreCLIError("Internal error: OPF file path missing for JSON conversion.")
            if not os.path.exists(actual_opf_target) or os.path.getsize(actual_opf_target) == 0:
                raise CalibreCLIError(
                    message=f"fetch-ebook-metadata ran but OPF file {actual_opf_target} was not created or is empty.",
                    stdout=stdout, stderr=stderr, returncode=returncode
                )

            with open(actual_opf_target, 'r', encoding='utf-8') as f:
                opf_content = f.read()

            import xml.etree.ElementTree as ET
            metadata_dict = {}
            try:
                root = ET.fromstring(opf_content)
                ns = {'opf': 'http://www.idpf.org/ २०07/opf', 'dc': 'http://purl.org/dc/elements/1.1/'}
                metadata_node = root.find('opf:metadata', ns)
                if metadata_node is not None:
                    for child in metadata_node:
                        tag_name = child.tag.split('}')[-1]
                        if tag_name in metadata_dict:
                            if not isinstance(metadata_dict[tag_name], list):
                                metadata_dict[tag_name] = [metadata_dict[tag_name]]
                            metadata_dict[tag_name].append(child.text)
                        else:
                            metadata_dict[tag_name] = child.text
                return metadata_dict
            except ET.ParseError as e:
                raise CalibreCLIError(f"Failed to parse OPF content from fetched metadata: {e}", stdout=opf_content)

        elif output_opf_file: # and not as_json
            if not os.path.exists(output_opf_file):
                 raise CalibreCLIError(
                    message=f"fetch-ebook-metadata ran but OPF file {output_opf_file} was not created.",
                    stdout=stdout, stderr=stderr, returncode=returncode
                )
            return output_opf_file
        else: # Not as_json and no output_opf_file, so OPF is in stdout
            if not stdout.strip(): # Should not happen if returncode is 0
                raise CalibreCLIError(
                    message="fetch-ebook-metadata returned success but no OPF content in stdout.",
                    stdout=stdout, stderr=stderr, returncode=returncode
                )
            return stdout
    finally:
        if temp_opf_for_json and os.path.exists(temp_opf_for_json):
            os.remove(temp_opf_for_json)


def web2disk(
    url: str,
    output_recipe_file: str, # .recipe file
    options: Optional[List[str]] = None
) -> str:
    """
    Downloads a website (e.g., a news site) and converts it into an e-book
    by generating a .recipe file using `web2disk`.
    The actual conversion of the recipe to an ebook is done by `ebook-convert`.

    Args:
        url: The URL of the website or article to download.
        output_recipe_file: Path to save the generated .recipe file.
                            Must end with '.recipe'.
        options: A list of additional options for web2disk
                 (e.g., ["--username", "user", "--password", "pass"]).

    Returns:
        The path to the generated .recipe file.

    Raises:
        CalibreCLIError: If web2disk fails.
        FileNotFoundError: If 'web2disk' executable is not found.
        ValueError: If output_recipe_file does not end with '.recipe'.
    """
    if not output_recipe_file.endswith(".recipe"):
        raise ValueError("output_recipe_file must end with '.recipe'")

    command = ['web2disk']
    if options:
        command.extend(options)
    command.extend([url, output_recipe_file])

    stdout, stderr, returncode = run_calibre_command(command, timeout=300) # Downloading can take time

    if returncode != 0:
        raise CalibreCLIError(
            message=f"web2disk failed for URL {url}.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    if not os.path.exists(output_recipe_file) or os.path.getsize(output_recipe_file) == 0:
        raise CalibreCLIError(
            message=f"web2disk completed but recipe file {output_recipe_file} was not created or is empty.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    logger.info(f"web2disk successful. Recipe generated at: {output_recipe_file}")
    return output_recipe_file


# --- Imports needed for the new functions ---
import os
from typing import List, Optional, Union, Dict, Any
# Remove tempfile if it's only used in the __main__ part of the original file
# import tempfile # Used in get_ebook_metadata and fetch_ebook_metadata

# Make sure the logger is available if not already defined at the top
# import logging
# logger = logging.getLogger(__name__) # Assuming it's already configured

# Example usages for new functions (can be expanded for testing)
if __name__ == '__main__':
    # ... (keep existing run_calibre_command tests) ...

    print("\n--- Testing Wrapper Functions ---")

    # Test get_calibre_version
    print("\nTest: Get Calibre Version")
    try:
        version = get_calibre_version()
        print(f"Calibre Version: {version}")
    except Exception as e:
        print(f"Error getting version: {e}")

    # Note: For functions like ebook_convert, ebook_meta, ebook_polish, fetch_ebook_metadata, web2disk,
    # comprehensive tests would require:
    # 1. Sample input files (e.g., test.epub, test.txt).
    # 2. A Calibre installation in the test environment.
    # 3. Assertions on the output files or returned data.
    # 4. Cleanup of any generated files.
    # These are more like integration tests.
    # For now, we'll include placeholder calls to demonstrate structure.

    # Example: ebook_convert (requires dummy files)
    # Create dummy input file for ebook_convert test
    if not os.path.exists("dummy_input.txt"):
        with open("dummy_input.txt", "w") as f:
            f.write("This is a test file for ebook-convert.")

    print("\nTest: ebook-convert (dummy_input.txt to dummy_output.epub)")
    try:
        output_path = ebook_convert("dummy_input.txt", "dummy_output.epub", options=["--authors", "Test Author"])
        print(f"ebook-convert successful. Output: {output_path}")
        if os.path.exists("dummy_output.epub"):
             print("dummy_output.epub created.")
             # os.remove("dummy_output.epub") # Clean up
    except FileNotFoundError as e:
        print(f"File not found (ebook-convert or input): {e}")
    except CalibreCLIError as e:
        print(f"ebook-convert error: {e}")
    finally:
        if os.path.exists("dummy_input.txt"):
            os.remove("dummy_input.txt")
        if os.path.exists("dummy_output.epub"): # Ensure cleanup even on error after creation
            os.remove("dummy_output.epub")


    # Example: get_ebook_metadata (requires a dummy epub)
    # We'd need a minimal valid epub file for a real test.
    # For now, this will likely fail if dummy_output.epub wasn't created or is invalid.
    print("\nTest: get_ebook_metadata (on dummy_output.epub, if it exists and is valid)")
    if os.path.exists("dummy_output.epub"): # Recreate for this test if needed
        # This is not ideal, ebook_convert test should be self-contained
        pass
    else:
        # Quick way to get an EPUB for testing if ebook-convert above didn't run or failed
        # ebook_convert("dummy_input.txt", "dummy_output.epub") # This creates dependency
        print("Skipping get_ebook_metadata test as dummy_output.epub not available.")

    if os.path.exists("dummy_output.epub"): # Check again
        try:
            # Test get metadata as JSON
            metadata_json = get_ebook_metadata("dummy_output.epub", as_json=True)
            print(f"Metadata (JSON) for dummy_output.epub: {metadata_json}")

            # Test get metadata as OPF file
            opf_file = get_ebook_metadata("dummy_output.epub", output_opf_file="dummy_meta.opf")
            print(f"Metadata saved to OPF: {opf_file}")
            if os.path.exists(opf_file):
                # with open(opf_file, "r") as f: print(f.read()) # Print OPF content
                os.remove(opf_file) # Clean up

        except FileNotFoundError as e:
            print(f"File not found during get_ebook_metadata test: {e}")
        except CalibreCLIError as e:
            print(f"get_ebook_metadata error: {e}")
        finally:
            if os.path.exists("dummy_output.epub"): # Clean up the epub used for this test
                 # os.remove("dummy_output.epub") # Let ebook_convert test handle its own cleanup
                 pass

    # Example: set_ebook_metadata (requires a dummy epub that can be modified)
    # Create a fresh dummy epub for this test to avoid interference
    print("\nTest: set_ebook_metadata")
    temp_epub_for_set_meta = "temp_set_meta.epub"
    if not os.path.exists("dummy_input.txt"): # Should have been cleaned up
        with open("dummy_input.txt", "w") as f: f.write("Content for setting metadata.")
    try:
        ebook_convert("dummy_input.txt", temp_epub_for_set_meta)
        if os.path.exists(temp_epub_for_set_meta):
            print(f"Created {temp_epub_for_set_meta} for set_ebook_metadata test.")
            result = set_ebook_metadata(temp_epub_for_set_meta, ["--title", "My Test Title From Pytest"])
            print(f"set_ebook_metadata result: {result}")

            # Verify change (optional, by reading metadata back)
            meta_after_set = get_ebook_metadata(temp_epub_for_set_meta, as_json=True)
            print(f"Metadata after set: {meta_after_set}")
            if meta_after_set.get('title') == "My Test Title From Pytest":
                print("Title successfully updated.")
            else:
                print("Title update verification failed or title not found in parsed metadata.")

    except Exception as e:
        print(f"Error during set_ebook_metadata test: {e}")
    finally:
        if os.path.exists("dummy_input.txt"): os.remove("dummy_input.txt")
        if os.path.exists(temp_epub_for_set_meta): os.remove(temp_epub_for_set_meta)


    # Example: ebook_polish (requires a dummy epub)
    print("\nTest: ebook_polish")
    temp_epub_for_polish = "temp_polish_me.epub"
    polished_output = "temp_polished.epub"
    if not os.path.exists("dummy_input.txt"):
        with open("dummy_input.txt", "w") as f: f.write("Content for polishing.")
    try:
        ebook_convert("dummy_input.txt", temp_epub_for_polish) # Create a source epub
        if os.path.exists(temp_epub_for_polish):
            print(f"Created {temp_epub_for_polish} for ebook_polish test.")
            # Polish with an output file
            result_path = ebook_polish(temp_epub_for_polish, output_file_path=polished_output, options=["--subset-fonts"])
            print(f"ebook_polish (to new file) successful. Output: {result_path}")
            if os.path.exists(polished_output):
                print(f"{polished_output} created.")
                os.remove(polished_output)

            # Polish in-place (be careful with this, test on a copy)
            # For safety, let's copy first then polish in place
            # shutil.copy(temp_epub_for_polish, "temp_polish_inplace_copy.epub")
            # result_inplace = ebook_polish("temp_polish_inplace_copy.epub", options=["--smarten-punctuation"])
            # print(f"ebook_polish (in-place) successful. Output: {result_inplace}")
            # if os.path.exists("temp_polish_inplace_copy.epub"): os.remove("temp_polish_inplace_copy.epub")

    except Exception as e:
        print(f"Error during ebook_polish test: {e}")
    finally:
        if os.path.exists("dummy_input.txt"): os.remove("dummy_input.txt")
        if os.path.exists(temp_epub_for_polish): os.remove(temp_epub_for_polish)
        if os.path.exists(polished_output): os.remove(polished_output) # Ensure cleanup

    # Example: fetch_ebook_metadata (requires network access)
    print("\nTest: fetch_ebook_metadata (for 'The Hobbit' by 'Tolkien')")
    try:
        # Test as JSON
        metadata = fetch_ebook_metadata(title="The Hobbit", authors="J.R.R. Tolkien", as_json=True, timeout_seconds=20)
        print(f"Fetched metadata (JSON): {metadata.get('title', 'N/A Title')} by {metadata.get('creator', 'N/A Author')}")

        # Test as OPF file
        opf_output_path = "fetched_hobbit.opf"
        opf_path = fetch_ebook_metadata(title="The Hobbit", authors="J.R.R. Tolkien", output_opf_file=opf_output_path, timeout_seconds=20)
        print(f"Fetched metadata saved to OPF: {opf_path}")
        if os.path.exists(opf_path):
            # with open(opf_path, "r") as f: print(f.read())
            os.remove(opf_path)

    except CalibreCLIError as e:
        if "No metadata found" in str(e):
            print(f"fetch_ebook_metadata: {e.args[0]}")
        else:
            print(f"fetch_ebook_metadata CalibreCLIError: {e}")
    except FileNotFoundError:
        print("fetch-ebook-metadata tool not found.")
    except Exception as e: # Catch other potential errors like network issues if not wrapped by CalibreCLIError
        print(f"fetch_ebook_metadata error (possibly network): {e}")


    # Example: web2disk (requires network access and a valid URL)
    print("\nTest: web2disk (generates a .recipe file for a URL)")
    recipe_file = "example_site.recipe"
    try:
        # Using a simple, stable page for testing.
        # Make sure this URL is accessible during tests.
        # Example: use a known public domain text page if available.
        # For this test, let's use a wikipedia page.
        # Note: Complex JavaScript-heavy sites might not work well or be slow.
        generated_recipe = web2disk("https://en.wikipedia.org/wiki/EPUB", recipe_file, options=["--max-articles-per-feed", "1"])
        print(f"web2disk successful. Recipe at: {generated_recipe}")
        if os.path.exists(generated_recipe):
            print(f"Recipe file '{generated_recipe}' created. Size: {os.path.getsize(generated_recipe)} bytes.")
            # You could try to convert this recipe with ebook-convert as a further test:
            # ebook_convert(generated_recipe, "wiki_epub_from_recipe.epub")
            os.remove(generated_recipe) # Clean up
    except CalibreCLIError as e:
        print(f"web2disk error: {e}")
    except FileNotFoundError:
        print("web2disk tool not found.")
    except ValueError as e:
        print(f"web2disk ValueError: {e}")
    except Exception as e:
        print(f"web2disk error (possibly network or URL content): {e}")
    finally:
        if os.path.exists(recipe_file): # Ensure cleanup
            os.remove(recipe_file)

    print("\nWrapper function basic tests complete.")


def lrf2lrs(input_lrf_file: str, output_lrs_file: str) -> str:
    """
    Converts an LRF e-book file to an LRS file using `lrf2lrs`.

    Args:
        input_lrf_file: Path to the input LRF file.
        output_lrs_file: Path for the converted output LRS file.

    Returns:
        The path to the output_lrs_file if conversion is successful.

    Raises:
        CalibreCLIError: If lrf2lrs fails.
        FileNotFoundError: If 'lrf2lrs' executable or input_lrf_file is not found.
    """
    if not os.path.exists(input_lrf_file):
        raise FileNotFoundError(f"Input LRF file not found: {input_lrf_file}")

    command = ['lrf2lrs', input_lrf_file, output_lrs_file]
    stdout, stderr, returncode = run_calibre_command(command, timeout=120)

    if returncode != 0:
        raise CalibreCLIError(
            message=f"lrf2lrs failed for {input_lrf_file} to {output_lrs_file}.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    if not os.path.exists(output_lrs_file):
        raise CalibreCLIError(
            message=f"lrf2lrs completed but output file {output_lrs_file} was not created.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    logger.info(f"lrf2lrs successful: {input_lrf_file} -> {output_lrs_file}")
    return output_lrs_file


def lrs2lrf(input_lrs_file: str, output_lrf_file: str) -> str:
    """
    Converts an LRS e-book file to an LRF file using `lrs2lrf`.

    Args:
        input_lrs_file: Path to the input LRS file.
        output_lrf_file: Path for the converted output LRF file.

    Returns:
        The path to the output_lrf_file if conversion is successful.

    Raises:
        CalibreCLIError: If lrs2lrf fails.
        FileNotFoundError: If 'lrs2lrf' executable or input_lrs_file is not found.
    """
    if not os.path.exists(input_lrs_file):
        raise FileNotFoundError(f"Input LRS file not found: {input_lrs_file}")

    command = ['lrs2lrf', input_lrs_file, output_lrf_file]
    stdout, stderr, returncode = run_calibre_command(command, timeout=120)

    if returncode != 0:
        raise CalibreCLIError(
            message=f"lrs2lrf failed for {input_lrs_file} to {output_lrf_file}.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    if not os.path.exists(output_lrf_file):
        raise CalibreCLIError(
            message=f"lrs2lrf completed but output file {output_lrf_file} was not created.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    logger.info(f"lrs2lrf successful: {input_lrs_file} -> {output_lrf_file}")
    return output_lrf_file


# --- calibre-customize wrappers ---

def list_calibre_plugins() -> Dict[str, Any]:
    """
    Lists installed Calibre plugins using `calibre-customize --list-plugins`.
    Parses the output to provide a structured list of plugins.

    Returns:
        A dictionary where keys are plugin names and values are dictionaries
        containing plugin details (version, author, description, etc.).

    Raises:
        CalibreCLIError: If calibre-customize fails or output parsing is unsuccessful.
        FileNotFoundError: If 'calibre-customize' executable is not found.
    """
    command = ['calibre-customize', '--list-plugins']
    stdout, stderr, returncode = run_calibre_command(command)

    if returncode != 0:
        raise CalibreCLIError(
            message="Failed to list Calibre plugins.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    plugins = {}
    # Output is like:
    # Plugin Name 1 (version 1.2.3) by Author Name
    #   Description of plugin 1
    #   (Customization: ...)
    # Plugin Name 2 (version 0.1.0) by Another Author
    #   Description of plugin 2
    #
    # This parsing is very basic and might need adjustment based on exact output format variations.
    current_plugin_name = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue

        # Regex to capture "Plugin Name (version X.Y.Z) by Author"
        # More robust parsing might be needed if format varies.
        # Example: "Action Chains (1.0.0) by calibre"
        # Example: "Adobe Adept Remove (0.1.0) by None" (Author can be None)
        # Example: "Annotations (1.18.0) by David Forrester"
        # Version and Author might be optional or have different formats.
        # A simpler approach: if line doesn't start with whitespace, it's a new plugin header.

        if not line.startswith(' '): # Assuming plugin headers are not indented
            parts = line.split('(')
            plugin_name_full = parts[0].strip()
            current_plugin_name = plugin_name_full
            plugins[current_plugin_name] = {'name': plugin_name_full, 'version': None, 'author': None, 'description_parts': []}

            if len(parts) > 1:
                version_author_part = parts[1].split(')')
                if len(version_author_part) > 0:
                    plugins[current_plugin_name]['version'] = version_author_part[0].strip()
                if " by " in version_author_part[1]:
                     plugins[current_plugin_name]['author'] = version_author_part[1].split(" by ")[1].strip()

        elif current_plugin_name and line: # Indented line, part of current plugin's description
            plugins[current_plugin_name]['description_parts'].append(line)

    # Consolidate description parts
    for name, details in plugins.items():
        if 'description_parts' in details:
            plugins[name]['description'] = "\n".join(details['description_parts']).strip()
            del plugins[name]['description_parts']
            if not plugins[name]['description']: # remove if empty after join
                del plugins[name]['description']


    if not plugins and stdout.strip(): # Parsing failed but there was output
        logger.warning(f"Could not parse plugin list from calibre-customize output, but got output:\n{stdout}")
        # Optionally, return raw output or raise a more specific parsing error.
        # For now, returning empty dict if parsing yields nothing.
    elif not plugins and not stdout.strip(): # No output, no plugins.
        logger.info("No plugins listed by calibre-customize.")


    return plugins


# --- calibre-debug wrappers ---

def run_calibre_debug_test_build(timeout: int = 180) -> str:
    """
    Runs Calibre's build and basic startup test using `calibre-debug --test-build`.
    This can take a few minutes.

    Args:
        timeout: Timeout in seconds for the command.

    Returns:
        The stdout from the command, which usually indicates success or failure of tests.

    Raises:
        CalibreCLIError: If calibre-debug returns a non-zero exit code.
        FileNotFoundError: If 'calibre-debug' executable is not found.
    """
    command = ['calibre-debug', '--test-build']
    # This command can be verbose and take time.
    stdout, stderr, returncode = run_calibre_command(command, timeout=timeout)

    if returncode != 0:
        raise CalibreCLIError(
            message="calibre-debug --test-build failed.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    # Success is usually indicated by "All tests passed" or similar in stdout.
    # The raw stdout is returned for the user to inspect.
    logger.info("calibre-debug --test-build completed.")
    return stdout

# calibre-debug --collect-debug-info might be useful but it creates a zip file.
# The API would need to handle file responses for that.
# For now, focusing on simpler output commands.


if __name__ == '__main__':
    # ... (keep existing run_calibre_command tests and other wrapper tests) ...

    print("\n--- Testing LRF/LRS Conversion Functions ---")
    # These tests require dummy LRF and LRS files, which are not standard text files.
    # Creating valid dummy LRF/LRS for automated testing is complex without specific tools.
    # So, these will likely fail if the tools are called without valid input files.
    # We'll mostly test if the command wrapper can be called.

    print("\nTest: lrf2lrs (dummy_input.lrf to dummy_output.lrs)")
    # Create a dummy empty file, lrf2lrs will fail but tests our wrapper's error handling
    if not os.path.exists("dummy_input.lrf"):
        open("dummy_input.lrf", "w").close()
    try:
        output_path = lrf2lrs("dummy_input.lrf", "dummy_output.lrs")
        print(f"lrf2lrs successful (unexpected for empty file). Output: {output_path}")
        if os.path.exists("dummy_output.lrs"): os.remove("dummy_output.lrs")
    except FileNotFoundError as e:
        print(f"File not found (lrf2lrs or input): {e}")
    except CalibreCLIError as e:
        print(f"lrf2lrs error (expected for empty/invalid file): Code {e.returncode}, Stderr: {e.stderr[:100]}...")
    finally:
        if os.path.exists("dummy_input.lrf"): os.remove("dummy_input.lrf")
        if os.path.exists("dummy_output.lrs"): os.remove("dummy_output.lrs")


    print("\nTest: lrs2lrf (dummy_input.lrs to dummy_output.lrf)")
    if not os.path.exists("dummy_input.lrs"):
        open("dummy_input.lrs", "w").close()
    try:
        output_path = lrs2lrf("dummy_input.lrs", "dummy_output.lrf")
        print(f"lrs2lrf successful (unexpected for empty file). Output: {output_path}")
        if os.path.exists("dummy_output.lrf"): os.remove("dummy_output.lrf")
    except FileNotFoundError as e:
        print(f"File not found (lrs2lrf or input): {e}")
    except CalibreCLIError as e:
        print(f"lrs2lrf error (expected for empty/invalid file): Code {e.returncode}, Stderr: {e.stderr[:100]}...")
    finally:
        if os.path.exists("dummy_input.lrs"): os.remove("dummy_input.lrs")
        if os.path.exists("dummy_output.lrf"): os.remove("dummy_output.lrf")

    print("\n--- Testing Calibre Customize and Debug Functions ---")

    print("\nTest: list_calibre_plugins")
    try:
        plugins = list_calibre_plugins()
        if plugins:
            print(f"Found {len(plugins)} plugins. First few:")
            for i, (name, details) in enumerate(plugins.items()):
                if i < 3: # Print details for a few plugins
                    print(f"  Plugin: {name}, Version: {details.get('version', 'N/A')}, Author: {details.get('author', 'N/A')}")
                    # print(f"    Desc: {details.get('description', '')[:60]}...")
                else:
                    break
        else:
            print("No plugins found or parsing failed.")
    except FileNotFoundError:
        print("calibre-customize tool not found.")
    except CalibreCLIError as e:
        print(f"list_calibre_plugins error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while listing plugins: {e}")


    print("\nTest: run_calibre_debug_test_build")
    # This test can take a long time.
    # Add a flag to skip long tests if needed for quick runs.
    SKIP_LONG_TESTS = os.getenv("SKIP_LONG_TESTS", "false").lower() == "true"
    if SKIP_LONG_TESTS:
        print("Skipping run_calibre_debug_test_build as SKIP_LONG_TESTS is true.")
    else:
        print("Running --test-build (this may take a few minutes)...")
        try:
            output = run_calibre_debug_test_build(timeout=240) # Increased timeout
            print(f"calibre-debug --test-build output (last 200 chars):\n...{output[-200:]}")
            if "All tests passed" in output:
                print("Test build reported success.")
            else:
                print("Test build did not explicitly report 'All tests passed'. Review output.")
        except FileNotFoundError:
            print("calibre-debug tool not found.")
        except CalibreCLIError as e:
            if "timed out" in str(e):
                 print(f"calibre-debug --test-build timed out: {e}")
            else:
                 print(f"calibre-debug --test-build error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during --test-build: {e}")


    print("\nAll wrapper function basic tests complete.")


# --- calibre-smtp wrapper ---

def send_email_with_calibre_smtp(
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: Optional[str] = None,
    # SMTP server configuration - these would ideally come from secure config
    smtp_server: str, # e.g., "smtp.example.com"
    smtp_port: int,   # e.g., 587
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None, # Sensitive!
    smtp_encryption: str = 'tls', # 'tls', 'ssl', or 'none'
    sender_email: Optional[str] = None, # If None, Calibre might use a default or username
    # Calibre specific options
    reply_to_email: Optional[str] = None,
    timeout: int = 60
) -> Tuple[bool, str]:
    """
    Sends an email using `calibre-smtp`.

    Args:
        recipient_email: Email address of the recipient.
        subject: Subject of the email.
        body: Body content of the email.
        attachment_path: Optional path to a file to attach.
        smtp_server: SMTP server hostname or IP.
        smtp_port: SMTP server port.
        smtp_username: Username for SMTP authentication.
        smtp_password: Password for SMTP authentication (highly sensitive).
        smtp_encryption: Encryption method ('tls', 'ssl', 'none').
        sender_email: Email address of the sender.
        reply_to_email: Optional reply-to email address.
        timeout: Command timeout in seconds.

    Returns:
        A tuple (success: bool, message: str).
        `success` is True if calibre-smtp exits with 0, False otherwise.
        `message` contains stdout/stderr from the command.

    Raises:
        FileNotFoundError: If 'calibre-smtp' executable is not found.
        CalibreCLIError: For command execution issues other than non-zero exit for send failure.
                         Note: A failed send that calibre-smtp handles (e.g. auth error) will
                         result in (False, message) rather than raising CalibreCLIError here,
                         as calibre-smtp itself reports the error.
    """
    command = [
        'calibre-smtp',
        '--attachment', attachment_path if attachment_path else "", # Must provide, even if empty
        '--encryption-method', smtp_encryption,
        '--port', str(smtp_port),
        '--relay', smtp_server,
        '--subject', subject,
    ]

    if smtp_username:
        command.extend(['--username', smtp_username])
    if smtp_password:
        # WARNING: Passing passwords on the command line is a security risk.
        # calibre-smtp might have more secure ways (e.g. config files, stdin)
        # but the CLI docs show this option. Use with extreme caution.
        # Consider environment variables or other secure configurations if possible.
        command.extend(['--password', smtp_password])

    if sender_email:
        command.extend(['--from-addr', sender_email]) # Calibre calls this --from-addr
    if reply_to_email:
        command.extend(['--reply-to', reply_to_email])

    # The recipient and body are positional arguments at the end
    command.extend([recipient_email, body])

    # Remove empty attachment argument if not used, as calibre-smtp expects it to be omitted or have a value
    if not attachment_path and '--attachment' in command:
        att_index = command.index('--attachment')
        command.pop(att_index + 1) # remove the empty string value
        command.pop(att_index)     # remove the --attachment flag itself


    stdout, stderr, returncode = run_calibre_command(command, timeout=timeout)

    # calibre-smtp returns 0 on success, non-zero on failure.
    # We don't raise CalibreCLIError for non-zero here, as it's an expected outcome for send failure.
    # Instead, we return a status.
    if returncode == 0:
        logger.info(f"calibre-smtp reported success sending to {recipient_email}. Output: {stdout}")
        return True, stdout if stdout else "Email sent successfully."
    else:
        # Log the full error details for server-side diagnostics
        logger.error(
            f"calibre-smtp failed to send email to {recipient_email}. "
            f"Returncode: {returncode}\nStdout: {stdout}\nStderr: {stderr}"
        )
        # Combine stdout and stderr for the message as either could have error details
        error_message = f"Failed to send email. Return code: {returncode}."
        if stdout:
            error_message += f"\nOutput: {stdout}"
        if stderr:
            error_message += f"\nError details: {stderr}"
        return False, error_message.strip()


# --- ebook-edit wrappers ---

def check_ebook_errors(
    ebook_file_path: str,
    output_format: str = "text", # "text" or "json"
    timeout: int = 180
) -> Union[str, Dict[str, Any]]:
    """
    Checks an e-book (EPUB or AZW3) for errors using `ebook-edit --check-book`.

    Args:
        ebook_file_path: Path to the e-book file (EPUB or AZW3).
        output_format: Desired output format for the error report ('text' or 'json').
        timeout: Command timeout in seconds.

    Returns:
        If output_format is 'json', returns a dictionary parsed from the JSON output.
        If output_format is 'text', returns the raw text output.
        The structure of the JSON can be complex, representing the book's internal structure
        and error reports. An empty dict or specific structure might indicate no errors.

    Raises:
        CalibreCLIError: If ebook-edit fails or if JSON parsing fails when requested.
        FileNotFoundError: If 'ebook-edit' executable or ebook_file_path is not found.
        ValueError: If an unsupported output_format is specified.
    """
    if not os.path.exists(ebook_file_path):
        raise FileNotFoundError(f"E-book file not found: {ebook_file_path}")
    if output_format not in ["text", "json"]:
        raise ValueError("output_format must be 'text' or 'json'.")

    command = ['ebook-edit', '--check-book']
    if output_format == "json":
        command.append('--output-format=json')

    command.append(ebook_file_path)

    # ebook-edit --check-book can be slow for large or complex books.
    stdout, stderr, returncode = run_calibre_command(command, timeout=timeout)

    if returncode != 0:
        # ebook-edit --check-book returns 0 even if errors are found.
        # A non-zero return code usually indicates a more fundamental issue with the command or file.
        raise CalibreCLIError(
            message=f"ebook-edit --check-book command failed for {ebook_file_path}.",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    if output_format == "json":
        if not stdout.strip():
            # If JSON output is empty, it might mean no errors or an issue.
            # The tool usually outputs at least `{"path_to_ebook": []}` for no errors.
            logger.warning(f"ebook-edit --check-book with JSON output returned empty stdout for {ebook_file_path}.")
            return {} # Or raise an error if this is unexpected.

        try:
            # The JSON output is a single JSON object on one line.
            # Example (no errors): {"/path/to/book.epub": []}
            # Example (with errors): {"/path/to/book.epub": [{"level": "error", "msg": "...", ...}]}
            # The key is the book path, value is a list of error objects.
            json_output = json.loads(stdout)
            return json_output
        except json.JSONDecodeError as e:
            raise CalibreCLIError(
                message=f"Failed to parse JSON output from ebook-edit --check-book for {ebook_file_path}: {e}",
                stdout=stdout,
                stderr=stderr, # stderr might contain clues if the tool itself errored before JSON output
                returncode=returncode
            )
    else: # text output
        # Text output can be lengthy. It usually starts with "Checking /path/to/book.epub"
        # and lists errors, or says "No errors/warnings found"
        return stdout


# --- Imports needed for json.loads ---
import json


if __name__ == '__main__':
    # ... (keep existing tests) ...

    print("\n--- Testing Calibre SMTP and Ebook Edit Functions ---")

    # calibre-smtp test - This is difficult to automate without a live SMTP server
    # and exposing credentials. It's best tested manually or with a mock SMTP server.
    print("\nTest: send_email_with_calibre_smtp (SKIPPED - requires live SMTP setup and credentials)")
    # Example of how it *could* be called (DO NOT RUN WITH REAL CREDENTIALS IN AUTOMATED TESTS):
    # try:
    #     # Replace with your actual SMTP server details and a test recipient
    #     # Ensure the SMTP server is configured to allow sending from this script/IP
    #     # BE EXTREMELY CAREFUL WITH smtp_password
    #     success, message = send_email_with_calibre_smtp(
    #         recipient_email="test_recipient@example.com",
    #         subject="Test Email from Calibre API Wrapper",
    #         body="This is a test email sent via calibre-smtp through the Python wrapper.",
    #         attachment_path=None, # Optionally, create a dummy file and provide its path
    #         smtp_server="smtp.gmail.com", # Example, use your actual server
    #         smtp_port=587,
    #         smtp_username="your_email@gmail.com", # Example
    #         smtp_password="YOUR_APP_PASSWORD",    # Example - USE APP PASSWORD IF 2FA ENABLED
    #         smtp_encryption='tls',
    #         sender_email="your_email@gmail.com" # Example
    #     )
    #     if success:
    #         print(f"send_email_with_calibre_smtp reported success: {message}")
    #     else:
    #         print(f"send_email_with_calibre_smtp reported failure: {message}")
    # except FileNotFoundError:
    #     print("calibre-smtp tool not found.")
    # except CalibreCLIError as e: # For issues like timeout before calibre-smtp reports send status
    #     print(f"CalibreCLIError during calibre-smtp test: {e}")
    # except Exception as e:
    #     print(f"An unexpected error occurred during calibre-smtp test: {e}")


    # ebook-edit --check-book test
    # Requires a valid EPUB or AZW3 file. We can try to use one created by ebook-convert.
    print("\nTest: check_ebook_errors (on a dummy EPUB)")
    check_book_epub_path = "check_me.epub"
    # Create a simple text file first
    if not os.path.exists("dummy_for_check.txt"):
        with open("dummy_for_check.txt", "w") as f:
            f.write("This is content for an EPUB to be checked.")

    try:
        # Convert text to EPUB for the test
        ebook_convert("dummy_for_check.txt", check_book_epub_path, options=["--title", "Book For Checking"])
        print(f"Created '{check_book_epub_path}' for check_ebook_errors test.")

        if os.path.exists(check_book_epub_path):
            # Test with JSON output
            print(f"Checking '{check_book_epub_path}' with JSON output...")
            json_report = check_ebook_errors(check_book_epub_path, output_format="json", timeout=120)
            print(f"JSON report (type: {type(json_report)}):")
            if isinstance(json_report, dict) and json_report.get(os.path.abspath(check_book_epub_path)) == []:
                print("  No errors found in JSON report (as expected for basic conversion).")
            elif isinstance(json_report, dict):
                 print(f"  Errors/info found in JSON: {json.dumps(json_report, indent=2)}")
            else:
                print(f"  Unexpected JSON report format or content: {json_report}")


            # Test with text output
            print(f"\nChecking '{check_book_epub_path}' with TEXT output...")
            text_report = check_ebook_errors(check_book_epub_path, output_format="text", timeout=120)
            print("Text report (first 300 chars):")
            print(text_report[:300] + "..." if len(text_report) > 300 else text_report)
            if "No errors or warnings found" in text_report:
                print("  No errors found in text report.")

    except FileNotFoundError as e:
        print(f"File not found (ebook-edit, ebook-convert, or input file): {e}")
    except CalibreCLIError as e:
        print(f"CalibreCLIError during check_ebook_errors test: {e}")
    except ValueError as e:
        print(f"ValueError during check_ebook_errors test: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during check_ebook_errors test: {e}")
    finally:
        if os.path.exists("dummy_for_check.txt"):
            os.remove("dummy_for_check.txt")
        if os.path.exists(check_book_epub_path):
            os.remove(check_book_epub_path)

    print("\nAll wrapper function basic tests complete (including new ones).")
