from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional

from src.utils.constants import API_CONFIG

# --- SEARCH SCHEMAS ---

class NovelSearchResult(BaseModel):
    """Schema for a single novel search result item."""
    title: str = Field(..., example="Shadow Slave")
    url: str = Field(..., example="https://royalroad.com/fiction/12345/novel")
    cover: Optional[str] = Field(None, example="https://cdn.com/cover.jpg")
    chapters_count: Optional[str] = Field("N/A", example="1500 Chapters")


class SearchResponse(BaseModel):
    """Schema for the complete search response."""
    source: str
    results_count: int
    results: List[NovelSearchResult]


# --- DOWNLOAD / EPUB SCHEMAS ---

class EpubRequest(BaseModel):
    """
    Schema for EPUB generation request. 
    Useful if you decide to change from GET to POST later.
    """
    url: HttpUrl
    qty: int = Field(default=1, ge=1, le=API_CONFIG["MAX_CHAPTERS_LIMIT"], description="Quantity of chapters to download")
    start: int = Field(default=1, ge=1, description="Starting chapter number")


class BookMetadata(BaseModel):
    """Schema for the book metadata extracted before/during generation."""
    book_title: str
    book_author: str
    book_description: str
    book_cover_link: Optional[str] = None


# --- ERROR SCHEMAS ---

class ErrorMessage(BaseModel):
    """Standardized error message schema."""
    detail: str


# --- INTERNAL DATA MODELS (SRP) ---

class ChapterContent(BaseModel):
    """Raw scraped chapter content without index."""
    title: str
    content: str  # HTML string

class Chapter(BaseModel):
    """Represents a single chapter's content."""
    index: int
    title: str
    content: str  # HTML content

class Novel(BaseModel):
    """Represents the complete novel data ready for export."""
    metadata: BookMetadata
    chapters: List[Chapter]
    cover_image_bytes: Optional[bytes] = None  # Raw bytes of the cover image