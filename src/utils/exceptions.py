class BaseScraperException(Exception):
    """Base exception for all scraper-related errors."""
    pass

class NovelNotFoundException(BaseScraperException):
    """Raised when the novel URL is invalid or returns a 404 status."""
    pass

class ScraperParsingException(BaseScraperException):
    """Raised when the site structure has changed and parsing fails (e.g., missing specific tags)."""
    pass

class ChapterLimitException(BaseScraperException):
    """Raised when the requested chapter range is invalid or exceeds limits."""
    pass
