from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union

class Book(BaseModel):
    id: int
    title: str
    authors: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    publisher: Optional[str] = None
    pubdate: Optional[str] = None # Assuming date is a string, can be changed to datetime if needed
    isbn: Optional[str] = None
    formats: Optional[List[str]] = Field(default_factory=list)
    comments: Optional[str] = None
    # Add other fields from `calibredb list --fields all` as needed
    # For example:
    author_sort: Optional[str] = None
    cover: Optional[str] = None # Path to cover or URL, TBD based on calibredb output
    identifiers: Optional[dict] = Field(default_factory=dict) # e.g., {"isbn": "123", "doi": "abc"}
    languages: Optional[List[str]] = Field(default_factory=list)
    last_modified: Optional[str] = None # Assuming date is a string
    rating: Optional[Union[int, float]] = None # Calibre supports ratings, often 1-5 or 0-10
    series: Optional[str] = None
    series_index: Optional[float] = None # Can be float e.g. 1.0, 1.5, 2.0
    size: Optional[int] = None # Size in bytes
    uuid: Optional[str] = None

    class Config:
        # Allows to use field names that are not valid Python identifiers
        # by defining an alias (though not strictly needed for the current fields)
        # an_example_field_with_hyphen: Optional[str] = Field(None, alias="an-example-field-with-hyphen")
        pass

class AddBookResponse(BaseModel):
    message: str
    added_book_ids: List[int]
    details: Optional[str] = None

class RemoveBookResponse(BaseModel):
    message: str
    removed_book_id: int
    details: Optional[str] = None

class SetMetadataRequest(BaseModel):
    title: Optional[str] = None
    authors: Optional[List[str]] = None # Will be comma-separated for CLI
    publisher: Optional[str] = None
    pubdate: Optional[str] = None # Expected format e.g., YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
    tags: Optional[List[str]] = None # Will be comma-separated for CLI
    series: Optional[str] = None
    series_index: Optional[float] = None
    isbn: Optional[str] = None
    comments: Optional[str] = None
    rating: Optional[Union[int, float]] = None # Usually 1-5, or 0-10. Calibre uses half-stars (0-10 scale internally for 0-5 stars)

    # Ensure no extra fields are allowed if that's the desired behavior
    # class Config:
    #     extra = "forbid"
    # However, for flexibility, allowing extra might be fine if crud ignores them.
    # For now, let's define what we explicitly support.

class SetMetadataResponse(BaseModel):
    message: str
    book_id: int
    # Potentially include a list of changed fields if --for-machine provides it and it's useful
    # changed_fields: Optional[Dict[str, Any]] = None
    details: Optional[str] = None


# --- General CLI Models ---

class CalibreVersionResponse(BaseModel):
    calibre_version: str
    details: Optional[str] = Field(None, description="Any extra info from the command output, like copyright.")

class EbookConvertRequest(BaseModel):
    output_format: str = Field(..., example="mobi", description="Target e-book format (e.g., 'epub', 'mobi', 'pdf').")
    # Input file will be an UploadFile parameter in the endpoint
    options: Optional[List[str]] = Field(None, description="List of additional ebook-convert options, e.g., ['--authors', 'John Doe']", example=["--embed-font-family", "Arial"])

class EbookConvertResponse(BaseModel):
    message: str
    output_filename: str = Field(description="The name of the converted file, which can be used for downloading.")
    # The file itself will be streamed as a FileResponse from the endpoint directly.

class EbookMetadataGetRequest(BaseModel): # Used as query params for GET endpoint
    # input_file via UploadFile in endpoint
    as_json: bool = Field(True, description="Return metadata as a JSON object. If false, returns raw OPF string or path to OPF file.")
    # output_opf_file: Optional[str] = Field(None, description="If specified and as_json is false, metadata will be saved to this server-side path.")

class EbookMetadataSetRequest(BaseModel):
    # For setting metadata on a standalone file
    # Input file will be an UploadFile parameter in the endpoint
    metadata_options: List[str] = Field(..., description="List of metadata settings for ebook-meta, e.g., ['--title', 'New Title', '--authors', 'Author Name']", example=["--title", "My Awesome Book", "--tags", "Fiction,Adventure"])

class EbookMetadataResponse(BaseModel):
    # For getting or setting metadata on a standalone file
    message: str
    filename: Optional[str] = Field(None, description="Name of the processed file.")
    metadata_content: Optional[Union[str, Dict[str, Any]]] = Field(None, description="OPF content as string, or parsed JSON dictionary if requested (for get), or stdout from set.")
    details: Optional[str] = Field(None, description="Additional details, e.g., path to a saved OPF file or confirmation messages from 'set_metadata'.")


class EbookPolishRequest(BaseModel):
    # Input file will be an UploadFile parameter in the endpoint
    output_filename_suffix: Optional[str] = Field("_polished", description="Suffix to append to the original filename for the output. e.g., '_polished'. If not provided, a default might be used or in-place polish attempted if format supports.")
    # output_format: Optional[str] = Field(None, description="If polish should also convert, specify format. Typically polish retains format.")
    options: Optional[List[str]] = Field(None, description="List of ebook-polish options, e.g., ['--subset-fonts', '--smarten-punctuation']", example=["--upgrade-book", "--jacket"])
    # polish_in_place_if_possible: bool = True # This logic is primarily handled in the wrapper based on output_filename strategy

class EbookPolishResponse(BaseModel):
    message: str
    output_filename: str = Field(description="The name of the polished file.")
    # File itself will be streamed as a FileResponse.

class FetchMetadataQueryRequest(BaseModel): # Can be used for query parameters or as part of a JSON body
    title: Optional[str] = Field(None, example="The Lord of the Rings")
    authors: Optional[str] = Field(None, description="Comma-separated string of author names.", example="J.R.R. Tolkien")
    isbn: Optional[str] = Field(None, example="978-0618640157")
    ids: Optional[Dict[str, str]] = Field(None, description="Dictionary of external identifiers.", example={"goodreads": "33"})
    as_json: bool = Field(True, description="Return metadata as a JSON object. If false, returns raw OPF string.")
    # output_opf_file: Optional[str] = Field(None, description="Server-side path to save OPF. Not typically exposed directly in API request.")

class FetchMetadataResponse(BaseModel):
    message: str
    search_criteria: Dict[str, Any]
    metadata: Optional[Union[Dict[str, Any], str]] = Field(None, description="Fetched metadata as JSON dict or OPF string.")
    details: Optional[str] = Field(None, description="Any additional details from the fetch operation.")


class WebToDiskRequest(BaseModel):
    url: str = Field(..., example="https://www.gutenberg.org/files/1342/1342-h/1342-h.htm") # Example: Pride and Prejudice
    # output_recipe_filename will be generated by server to avoid path issues, or taken from request if simple name
    options: Optional[List[str]] = Field(None, description="List of web2disk options.", example=["--max-articles-per-feed", "1"])

class WebToDiskResponse(BaseModel):
    message: str
    recipe_filename: str = Field(description="Name of the generated .recipe file.")
    # Recipe file itself will be streamed as a FileResponse.


class LrfConversionRequest(BaseModel):
    # input_file via UploadFile
    # output_filename will be determined based on input filename + new extension
    pass # No specific fields needed in request body if output name is derived

class LrfConversionResponse(BaseModel):
    message: str
    output_filename: str
    # File via FileResponse


class PluginListResponse(BaseModel):
    message: str
    count: int
    plugins: Dict[str, Any] = Field(description="Dictionary of installed plugins and their details.")

class DebugTestBuildResponse(BaseModel):
    message: str
    output: str = Field(description="Full stdout from the 'calibre-debug --test-build' command.")

class SmtpSendRequest(BaseModel):
    recipient_email: str = Field(..., example="recipient@example.com")
    subject: str = Field(..., example="Hello from Calibre API")
    body: str = Field(..., example="This is the body of the email.")
    # attachment will be an UploadFile parameter in the endpoint
    smtp_server: str = Field(..., example="smtp.example.com")
    smtp_port: int = Field(..., example=587)
    smtp_username: Optional[str] = Field(None, example="user@example.com")
    smtp_password: Optional[str] = Field(None, description="SMTP password. This is sensitive and should be handled with care by the client and server.")
    smtp_encryption: str = Field("tls", example="tls", description="Encryption method: 'tls', 'ssl', or 'none'.", pattern="^(tls|ssl|none)$")
    sender_email: Optional[str] = Field(None, example="sender@example.com", description="Sender's email address.")
    reply_to_email: Optional[str] = Field(None, example="replyto@example.com", description="Reply-To email address.")

class SmtpSendResponse(BaseModel):
    success: bool
    message: str
    details: Optional[str] = Field(None, description="Additional details or error messages from the SMTP operation.")


class EbookCheckRequest(BaseModel): # Can be used as query parameters for endpoint with file upload
    # input_file via UploadFile in endpoint
    output_format: str = Field("json", example="json", description="Desired report format: 'json' or 'text'.", pattern="^(json|text)$")

class EbookCheckResponse(BaseModel):
    message: str
    filename: str = Field(description="Name of the checked file.")
    report_format: str
    report: Union[str, Dict[str, Any]] = Field(description="The error report, either as a text string or a JSON object/dictionary.")
