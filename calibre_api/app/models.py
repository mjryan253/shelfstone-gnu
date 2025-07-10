from pydantic import BaseModel, Field
from typing import List, Optional, Union

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
