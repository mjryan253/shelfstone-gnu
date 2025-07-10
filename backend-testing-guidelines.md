# How to Run Pytest Tests for the Calibre API Wrapper

This document provides instructions on how to run the automated tests for the Calibre API wrapper using Pytest.

## Prerequisites

1.  **Python Environment**: Ensure you have a Python environment (Python 3.8+ recommended). Using a virtual environment is highly recommended.
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

2.  **Install Dependencies**: Install `pytest` and other necessary packages. The API uses FastAPI.
    ```bash
    pip install pytest "fastapi[all]"
    ```
    (If there's a `requirements-dev.txt` or similar, use that instead: `pip install -r requirements-dev.txt`)

3.  **Calibre Installation (Optional but Recommended for some tests)**:
    *   While many tests use mocking to simulate `calibredb` CLI interactions, having Calibre installed and `calibredb` in your system's PATH can be useful for understanding the underlying tool's behavior or for running tests that might eventually perform real interactions (though current tests are designed to be isolated).
    *   If `calibredb` is not in the PATH, tests that *don't* fully mock the subprocess call for `calibredb` might fail with a `FileNotFoundError` (which some tests are designed to expect and handle).

## Running Tests

1.  **Navigate to the Root Directory**: Open your terminal and navigate to the root directory of the `calibre_api` project (the directory containing the `calibre_api` folder and this `RUNNING_TESTS.md` file, if it's placed at the root).

2.  **Execute Pytest**:
    You can run pytest using the Python module execution:
    ```bash
    python -m pytest
    ```
    Or, if `pytest` is directly available in your PATH (common within virtual environments after installation):
    ```bash
    pytest
    ```

    Pytest will automatically discover and run tests in files named `test_*.py` or `*_test.py`. For this project, the tests are primarily in `calibre_api/tests/test_main.py`.

3.  **Verbose Output (Optional)**:
    To get more detailed output, including print statements from tests and test names as they run:
    ```bash
    python -m pytest -s -v
    ```
    or
    ```bash
    pytest -s -v
    ```

## Interpreting Output

*   `.` indicates a test that passed.
*   `F` indicates a test that failed.
*   `E` indicates a test that encountered an error during execution (not a failed assertion).
*   `s` indicates a test that was skipped.
*   `x` indicates a test that was expected to fail and did (xfail).
*   `X` indicates a test that was expected to fail but passed (xpass).

Pytest will provide a summary at the end, detailing the number of passed, failed, errored, and skipped tests, along with tracebacks for any failures or errors.

## Troubleshooting

*   **Module Not Found Errors**: If you get `ModuleNotFoundError` (e.g., for `calibre_api.app.main`), ensure you are running `pytest` from the correct root directory that allows Python to find the `calibre_api` package. Your `PYTHONPATH` should implicitly include the current directory if running from the project root.
*   **Fixture Not Found Errors**: If tests report "fixture '...' not found", ensure the fixture is correctly defined (e.g., with `@pytest.fixture`) and that test functions needing the fixture list it as a parameter.
*   **Dependency Issues**: Ensure all dependencies listed in `requirements.txt` (or similar, including development dependencies) are installed in your active Python environment.

By following these steps, you should be able to execute the test suite and verify the functionality of the Calibre API wrapper.
