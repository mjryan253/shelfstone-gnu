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
