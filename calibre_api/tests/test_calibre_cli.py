import pytest
import subprocess
from unittest import mock
import os
import json

from calibre_api.app.calibre_cli import (
    run_calibre_command,
    CalibreCLIError,
    get_calibre_version,
    ebook_convert,
    get_ebook_metadata,
    set_ebook_metadata,
    ebook_polish,
    fetch_ebook_metadata,
    web2disk,
    lrf2lrs,
    lrs2lrf,
    list_calibre_plugins,
    run_calibre_debug_test_build,
    send_email_with_calibre_smtp,
    check_ebook_errors,
)

# Mock object for subprocess.CompletedProcess
def mock_completed_process(stdout="", stderr="", returncode=0):
    process = mock.Mock(spec=subprocess.CompletedProcess)
    process.stdout = stdout
    process.stderr = stderr
    process.returncode = returncode
    return process

# --- Tests for run_calibre_command ---

@mock.patch('subprocess.run')
def test_run_calibre_command_success(mock_subproc_run):
    mock_subproc_run.return_value = mock_completed_process(stdout="Success output", returncode=0)
    stdout, stderr, retcode = run_calibre_command(['mytool', '--arg'])
    assert stdout == "Success output"
    assert stderr == ""
    assert retcode == 0
    mock_subproc_run.assert_called_once_with(
        ['mytool', '--arg'], capture_output=True, text=True, check=False, timeout=60
    )

@mock.patch('subprocess.run')
def test_run_calibre_command_failure_returncode(mock_subproc_run):
    mock_subproc_run.return_value = mock_completed_process(stderr="Error output", returncode=1)
    # run_calibre_command itself doesn't raise CalibreCLIError for non-zero, it returns the code.
    # Specific wrappers are expected to check the returncode.
    stdout, stderr, retcode = run_calibre_command(['mytool', '--fail'])
    assert stdout == ""
    assert stderr == "Error output"
    assert retcode == 1


@mock.patch('subprocess.run', side_effect=FileNotFoundError("mytool not found"))
def test_run_calibre_command_file_not_found(mock_subproc_run):
    with pytest.raises(FileNotFoundError, match="mytool command not found"):
        run_calibre_command(['mytool'])

@mock.patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd=['mytool'], timeout=30))
def test_run_calibre_command_timeout(mock_subproc_run):
    with pytest.raises(CalibreCLIError, match="mytool command timed out."):
        run_calibre_command(['mytool'])

def test_run_calibre_command_empty_command_list():
    with pytest.raises(ValueError, match="Command list cannot be empty."):
        run_calibre_command([])

# --- Tests for get_calibre_version ---

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
def test_get_calibre_version_success_simple(mock_run_cmd):
    mock_run_cmd.return_value = ("calibre 6.10.0", "", 0)
    version = get_calibre_version()
    assert version == "6.10.0"
    mock_run_cmd.assert_called_once_with(['calibre', '--version'])

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
def test_get_calibre_version_success_complex(mock_run_cmd):
    mock_run_cmd.return_value = ("calibre (calibre 6.11.0)\nCopyright Kovid Goyal", "", 0)
    version = get_calibre_version()
    assert version == "6.11.0"

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
def test_get_calibre_version_failure(mock_run_cmd):
    mock_run_cmd.return_value = ("", "Error", 1)
    with pytest.raises(CalibreCLIError, match="Failed to get Calibre version."):
        get_calibre_version()

# --- Tests for ebook_convert ---

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists')
def test_ebook_convert_success(mock_os_exists, mock_run_cmd):
    mock_os_exists.side_effect = lambda path: True # Assume all paths exist
    mock_run_cmd.return_value = ("Conversion successful", "", 0)

    result = ebook_convert("input.epub", "output.mobi", options=["--foo", "bar"])

    assert result == "output.mobi"
    mock_os_exists.assert_any_call("input.epub") # First check for input
    mock_os_exists.assert_any_call("output.mobi") # After command, check for output
    mock_run_cmd.assert_called_once_with(
        ['ebook-convert', 'input.epub', 'output.mobi', '--foo', 'bar'], timeout=300
    )

@mock.patch('os.path.exists', return_value=False)
def test_ebook_convert_input_not_found(mock_os_exists):
    with pytest.raises(FileNotFoundError, match="Input file not found: input.epub"):
        ebook_convert("input.epub", "output.mobi")

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists')
def test_ebook_convert_cli_error(mock_os_exists, mock_run_cmd):
    mock_os_exists.return_value = True
    mock_run_cmd.return_value = ("", "CLI Error", 1)
    with pytest.raises(CalibreCLIError, match="ebook-convert failed"):
        ebook_convert("input.epub", "output.mobi")

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists')
def test_ebook_convert_output_file_not_created(mock_os_exists, mock_run_cmd):
    # First os.path.exists for input file is True, second for output file is False
    mock_os_exists.side_effect = [True, False]
    mock_run_cmd.return_value = ("Completed", "", 0) # Command "succeeded"
    with pytest.raises(CalibreCLIError, match="output file output.mobi was not created"):
        ebook_convert("input.epub", "output.mobi")


# --- Tests for get_ebook_metadata ---
# These tests become more complex due to file operations (temp OPF, reading OPF)
# We'll mock os.path.exists, open, os.remove, and xml.etree.ElementTree

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', return_value=True) # Assume ebook file exists
@mock.patch('builtins.open', new_callable=mock.mock_open, read_data='<metadata/>') # Mock open for reading OPF
@mock.patch('xml.etree.ElementTree.fromstring')
@mock.patch('tempfile.NamedTemporaryFile')
@mock.patch('os.remove')
def test_get_ebook_metadata_as_json_success(
    mock_os_remove, mock_tempfile, mock_xml_fromstring, mock_file_open, mock_os_exists, mock_run_cmd
):
    # Setup for temp file used when as_json=True and no output_opf_file
    mock_tmp_file_obj = mock.Mock()
    mock_tmp_file_obj.name = "temp.opf"
    mock_tempfile.return_value.__enter__.return_value = mock_tmp_file_obj

    mock_run_cmd.return_value = ("", "", 0) # ebook-meta --to-opf outputs nothing to stdout

    # Mock XML parsing
    mock_et_root = mock.Mock()
    mock_metadata_node = mock.Mock()
    mock_title_node = mock.Mock()
    mock_title_node.tag = "{http://purl.org/dc/elements/1.1/}title"
    mock_title_node.text = "Test Title"
    mock_metadata_node.findall = mock.Mock(return_value=[mock_title_node]) # Simplified findall
    mock_metadata_node.__iter__ = mock.Mock(return_value=iter([mock_title_node]))

    # Correctly mock finding the metadata node
    # ET's find method needs to be mocked on the root element that fromstring returns
    def find_side_effect(path, ns):
        if path == 'opf:metadata':
            return mock_metadata_node
        return None
    mock_et_root.find = mock.Mock(side_effect=find_side_effect)
    mock_xml_fromstring.return_value = mock_et_root

    # Mock os.path.getsize for the temp OPF file
    with mock.patch('os.path.getsize', return_value=100): # Non-empty file
        result = get_ebook_metadata("book.epub", as_json=True)

    assert result == {"title": "Test Title"}
    mock_run_cmd.assert_called_once_with(['ebook-meta', 'book.epub', '--to-opf', 'temp.opf'])
    mock_file_open.assert_called_with('temp.opf', 'r', encoding='utf-8')
    mock_os_remove.assert_called_with('temp.opf') # Ensure temp file is cleaned up

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', return_value=True)
def test_get_ebook_metadata_as_opf_string_success(mock_os_exists, mock_run_cmd):
    mock_run_cmd.return_value = ("<opf_content/>", "", 0) # ebook-meta prints to stdout
    result = get_ebook_metadata("book.epub", as_json=False, output_opf_file=None)
    assert result == "<opf_content/>"
    mock_run_cmd.assert_called_once_with(['ebook-meta', 'book.epub'])

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', return_value=True)
def test_get_ebook_metadata_to_opf_file_success(mock_os_exists, mock_run_cmd):
    # Command output to file, stdout is empty
    mock_run_cmd.return_value = ("", "", 0)

    result = get_ebook_metadata("book.epub", output_opf_file="meta.opf", as_json=False)

    assert result == "meta.opf"
    mock_run_cmd.assert_called_once_with(['ebook-meta', 'book.epub', '--to-opf', 'meta.opf'])
    # os.path.exists(output_opf_file) is called twice in this path, once for input, once for output.
    # Here, the second call is for "meta.opf" within the wrapper.
    mock_os_exists.assert_any_call("meta.opf")


@mock.patch('os.path.exists', return_value=False)
def test_get_ebook_metadata_input_not_found(mock_os_exists):
    with pytest.raises(FileNotFoundError, match="E-book file not found: book.epub"):
        get_ebook_metadata("book.epub")

# --- Tests for set_ebook_metadata ---

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', return_value=True)
def test_set_ebook_metadata_success(mock_os_exists, mock_run_cmd):
    mock_run_cmd.return_value = ("Metadata changed.", "", 0)
    options = ["--title", "New Title"]
    result = set_ebook_metadata("book.epub", options)
    assert result == "Metadata changed."
    mock_run_cmd.assert_called_once_with(['ebook-meta', 'book.epub'] + options)

@mock.patch('os.path.exists', return_value=True)
def test_set_ebook_metadata_no_options(mock_os_exists):
    with pytest.raises(ValueError, match="metadata_options cannot be empty."):
        set_ebook_metadata("book.epub", [])

# (Add more tests for other wrappers: ebook_polish, fetch_ebook_metadata, web2disk, etc.)
# The structure will be similar: mock os.path.exists, run_calibre_command, and other OS/file ops.

# --- Tests for list_calibre_plugins ---
@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
def test_list_calibre_plugins_success_parsing(mock_run_cmd):
    mock_output = (
        "Plugin Alpha (1.0) by Author A\n"
        "  Description for Alpha.\n"
        "Plugin Beta (2.0.1) by B. Author\n"
        "  Line 1 for Beta.\n"
        "  Line 2 for Beta.\n"
        "NoNamePlugin\n" # Plugin with no version/author info in this format
        "  Just a description."
    )
    mock_run_cmd.return_value = (mock_output, "", 0)
    plugins = list_calibre_plugins()

    assert len(plugins) == 3
    assert "Plugin Alpha" in plugins
    assert plugins["Plugin Alpha"]["version"] == "1.0"
    assert plugins["Plugin Alpha"]["author"] == "Author A"
    assert plugins["Plugin Alpha"]["description"] == "Description for Alpha."

    assert "Plugin Beta" in plugins
    assert plugins["Plugin Beta"]["version"] == "2.0.1"
    assert plugins["Plugin Beta"]["author"] == "B. Author"
    assert plugins["Plugin Beta"]["description"] == "Line 1 for Beta.\nLine 2 for Beta."

    assert "NoNamePlugin" in plugins
    assert plugins["NoNamePlugin"]["version"] is None # Or how your parser handles it
    assert plugins["NoNamePlugin"]["author"] is None
    assert plugins["NoNamePlugin"]["description"] == "Just a description."


@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
def test_list_calibre_plugins_empty_output(mock_run_cmd):
    mock_run_cmd.return_value = ("", "", 0)
    plugins = list_calibre_plugins()
    assert plugins == {}

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
def test_list_calibre_plugins_cli_error(mock_run_cmd):
    mock_run_cmd.return_value = ("", "Error", 1)
    with pytest.raises(CalibreCLIError, match="Failed to list Calibre plugins"):
        list_calibre_plugins()

# --- Tests for run_calibre_debug_test_build ---
@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
def test_run_calibre_debug_test_build_success(mock_run_cmd):
    mock_run_cmd.return_value = ("All tests passed.", "", 0)
    result = run_calibre_debug_test_build(timeout=10) # Short timeout for test
    assert result == "All tests passed."
    mock_run_cmd.assert_called_once_with(['calibre-debug', '--test-build'], timeout=10)

# --- Tests for send_email_with_calibre_smtp ---
# This one is tricky as it has many arguments and password handling.
@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
def test_send_email_with_calibre_smtp_success(mock_run_cmd):
    mock_run_cmd.return_value = ("Email sent successfully.", "", 0)
    success, message = send_email_with_calibre_smtp(
        recipient_email="to@example.com",
        subject="Test",
        body="Body",
        smtp_server="smtp.host",
        smtp_port=587,
        smtp_username="user",
        smtp_password="pass"
    )
    assert success is True
    assert message == "Email sent successfully."
    expected_cmd_part = ['calibre-smtp', '--encryption-method', 'tls', '--port', '587',
                         '--relay', 'smtp.host', '--subject', 'Test',
                         '--username', 'user', '--password', 'pass',
                         'to@example.com', 'Body']
    # Attachment part is tricky due to exact command formation logic with empty attachment
    # Check if the core parts are there.
    called_args = mock_run_cmd.call_args[0][0]
    assert all(item in called_args for item in expected_cmd_part if item != '--attachment' and item != "")
    assert '--attachment' not in called_args # Since attachment_path was None

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
def test_send_email_with_calibre_smtp_with_attachment(mock_run_cmd):
    mock_run_cmd.return_value = ("Email sent.", "", 0)
    success, _ = send_email_with_calibre_smtp(
        recipient_email="to@example.com", subject="S", body="B", attachment_path="file.zip",
        smtp_server="s", smtp_port=123
    )
    assert success
    called_args = mock_run_cmd.call_args[0][0]
    assert '--attachment' in called_args
    assert 'file.zip' in called_args


@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
def test_send_email_with_calibre_smtp_failure_from_cli(mock_run_cmd):
    mock_run_cmd.return_value = ("", "Auth failed", 1)
    success, message = send_email_with_calibre_smtp(
        recipient_email="to@example.com", subject="S", body="B",
        smtp_server="s", smtp_port=123
    )
    assert success is False
    assert "Auth failed" in message
    assert "Return code: 1" in message


# --- Tests for check_ebook_errors ---
@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', return_value=True)
def test_check_ebook_errors_json_success_no_errors(mock_os_exists, mock_run_cmd):
    # ebook-edit --check-book --output-format=json book.epub
    # Output: {"/abs/path/to/book.epub": []}
    abs_path = os.path.abspath("book.epub")
    mock_run_cmd.return_value = (json.dumps({abs_path: []}), "", 0)

    report = check_ebook_errors("book.epub", output_format="json")

    assert report == {abs_path: []}
    mock_run_cmd.assert_called_once_with(
        ['ebook-edit', '--check-book', '--output-format=json', 'book.epub'], timeout=180
    )

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', return_value=True)
def test_check_ebook_errors_text_success(mock_os_exists, mock_run_cmd):
    mock_run_cmd.return_value = ("No errors found.", "", 0)
    report = check_ebook_errors("book.epub", output_format="text")
    assert report == "No errors found."
    mock_run_cmd.assert_called_once_with(
        ['ebook-edit', '--check-book', 'book.epub'], timeout=180 # No --output-format for text
    )

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', return_value=True)
def test_check_ebook_errors_json_parse_error(mock_os_exists, mock_run_cmd):
    mock_run_cmd.return_value = ("this is not json", "", 0)
    with pytest.raises(CalibreCLIError, match="Failed to parse JSON output"):
        check_ebook_errors("book.epub", output_format="json")

def test_check_ebook_errors_invalid_format(mock_os_exists):
    with pytest.raises(ValueError, match="output_format must be 'text' or 'json'"):
        check_ebook_errors("book.epub", output_format="xml")

# TODO: Add similar tests for ebook_polish, fetch_ebook_metadata, web2disk, lrf2lrs, lrs2lrf
# For functions involving file creation/modification (like ebook_convert, ebook_polish, web2disk, lrf2lrs, lrs2lrf),
# ensure to also mock os.path.exists for the output file check.
# For fetch_ebook_metadata and get_ebook_metadata with as_json=True, also mock tempfile and XML parsing if not already covered.
# Example for ebook_polish
@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', side_effect=lambda p: True) # Mock all path exist checks to True
def test_ebook_polish_success(mock_os_exists, mock_run_cmd):
    mock_run_cmd.return_value = ("Polished.", "", 0)
    result = ebook_polish("book.epub", output_file_path="polished_book.epub", options=["--subset-fonts"])
    assert result == "polished_book.epub"
    mock_run_cmd.assert_called_once_with(
        ['ebook-polish', 'book.epub', 'polished_book.epub', '--subset-fonts'], timeout=300
    )
    # os.path.exists will be called for input and output
    mock_os_exists.assert_any_call("book.epub")
    mock_os_exists.assert_any_call("polished_book.epub")


@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', side_effect=[True, False]) # Input exists, output does not after command
def test_ebook_polish_output_not_created(mock_os_exists, mock_run_cmd):
    mock_run_cmd.return_value = ("Polished.", "", 0) # Command "succeeded"
    with pytest.raises(CalibreCLIError, match="output file polished_book.epub was not created/found"):
        ebook_polish("book.epub", output_file_path="polished_book.epub")

# Example for fetch_ebook_metadata
@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('xml.etree.ElementTree.fromstring')
@mock.patch('tempfile.NamedTemporaryFile')
@mock.patch('os.remove')
@mock.patch('builtins.open', new_callable=mock.mock_open, read_data='<metadata><dc:title>Fetched Title</dc:title></metadata>')
@mock.patch('os.path.exists', return_value=True) # For temp OPF file
@mock.patch('os.path.getsize', return_value=100) # For temp OPF file
def test_fetch_ebook_metadata_as_json_success(
    mock_os_getsize, mock_os_exists, mock_file_open, mock_os_remove, mock_tempfile, mock_xml_fromstring, mock_run_cmd
):
    mock_tmp_file_obj = mock.Mock()
    mock_tmp_file_obj.name = "fetched_temp.opf"
    mock_tempfile.return_value.__enter__.return_value = mock_tmp_file_obj

    mock_run_cmd.return_value = ("", "", 0) # Command outputs to OPF file

    mock_et_root = mock.Mock()
    mock_metadata_node = mock.Mock()
    mock_title_node = mock.Mock()
    mock_title_node.tag = "{http://purl.org/dc/elements/1.1/}title" # Note: actual ns might vary slightly based on ET version or OPF specifics
    mock_title_node.text = "Fetched Title"
    mock_metadata_node.__iter__ = mock.Mock(return_value=iter([mock_title_node]))
    def find_side_effect(path, ns):
        if path == 'opf:metadata': return mock_metadata_node
        return None
    mock_et_root.find = mock.Mock(side_effect=find_side_effect)
    mock_xml_fromstring.return_value = mock_et_root

    result = fetch_ebook_metadata(title="Some Book", as_json=True)
    assert result == {"title": "Fetched Title"}
    mock_run_cmd.assert_called_once() # Check specific args if needed
    args, _ = mock_run_cmd.call_args
    assert args[0][:3] == ['fetch-ebook-metadata', '--title', 'Some Book']
    assert '--opf' in args[0]
    assert args[0][args[0].index('--opf') + 1] == "fetched_temp.opf"


@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
def test_fetch_ebook_metadata_no_results(mock_run_cmd):
    mock_run_cmd.return_value = ("", "No metadata found for query", 1) # Or specific error code/stderr
    with pytest.raises(CalibreCLIError, match="No metadata found for the given criteria."):
        fetch_ebook_metadata(title="Unknown Book")

# Example for web2disk
@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', side_effect=lambda p: True if p.endswith(".recipe") else False) # Output .recipe exists
@mock.patch('os.path.getsize', return_value=1)
def test_web2disk_success(mock_os_getsize, mock_os_exists, mock_run_cmd):
    mock_run_cmd.return_value = ("Recipe generated", "", 0)
    result = web2disk("http://example.com", "out.recipe")
    assert result == "out.recipe"
    mock_run_cmd.assert_called_once_with(
        ['web2disk', 'http://example.com', 'out.recipe'], timeout=300
    )

def test_web2disk_invalid_recipe_filename():
    with pytest.raises(ValueError, match="output_recipe_file must end with '.recipe'"):
        web2disk("http://example.com", "out.txt")

# Example for LRF converters (lrf2lrs, lrs2lrf)
@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', side_effect=lambda p: True)
def test_lrf2lrs_success(mock_os_exists, mock_run_cmd):
    mock_run_cmd.return_value = ("", "", 0)
    result = lrf2lrs("in.lrf", "out.lrs")
    assert result == "out.lrs"
    mock_run_cmd.assert_called_once_with(['lrf2lrs', 'in.lrf', 'out.lrs'], timeout=120)

@mock.patch('calibre_api.app.calibre_cli.run_calibre_command')
@mock.patch('os.path.exists', side_effect=lambda p: True)
def test_lrs2lrf_success(mock_os_exists, mock_run_cmd):
    mock_run_cmd.return_value = ("", "", 0)
    result = lrs2lrf("in.lrs", "out.lrf")
    assert result == "out.lrf"
    mock_run_cmd.assert_called_once_with(['lrs2lrf', 'in.lrs', 'out.lrf'], timeout=120)
