import pytest
from unittest.mock import patch
import requests
from src.classes.base_book import BaseScraper
from src.schemas.novel_schema import BookMetadata, ChapterContent

# Create a concrete implementation of BaseScraper for testing
class MockScraper(BaseScraper):
    def get_book_metadata(self):
        return BookMetadata(book_title="Test Book", book_cover_link=None)
    
    def get_chapters_link(self):
        return ["http://test.com/1", "http://test.com/2"]
    
    def get_chapter_content(self, url):
        # This will be mocked by the framework, but we need the method structure
        return ChapterContent(title="Test Chapter", content="<p>Content</p>")

@pytest.fixture
def mock_scraper():
    return MockScraper("http://test.com", 1, 1)

def test_retry_on_429_recover(mock_scraper):
    """
    Test that the scraper retries on 429 Too Many Requests and eventually succeeds.
    """
    url = "http://test.com/chapter1"
    
    # Create a mock response for 429
    mock_429 = requests.Response()
    mock_429.status_code = 429
    
    # Create a mock response for 200 (Success)
    mock_200 = ChapterContent(title="Success", content="Body")
    
    # We mock get_chapter_content directly to simulate the return logic
    # BUT wait, _fetch_with_retry calls get_chapter_content.
    # If get_chapter_content performs the request, we should mock requests.Session.get inside it?
    # Actually, BaseScraper._fetch_with_retry calls self.get_chapter_content(url)
    # The actual request happens INSIDE the concrete implementation of get_chapter_content.
    # So we should mock get_chapter_content to raise HTTPError first, then return success.
    
    error_429 = requests.exceptions.HTTPError(response=mock_429)
    
    with patch.object(mock_scraper, 'get_chapter_content', side_effect=[error_429, mock_200]):
        # Also patch time.sleep to avoid waiting during test
        with patch('time.sleep') as mock_sleep:
            result = mock_scraper._fetch_with_retry(url, max_retries=3)
            
            # Assertions
            assert result.title == "Success"
            assert mock_sleep.called
            # Verify it was called with the backoff time (we'll check if it was called at least once)
            assert mock_sleep.call_count == 1

def test_retry_on_429_fail(mock_scraper):
    """
    Test that the scraper raises error after max retries if 429 persists.
    """
    url = "http://test.com/chapter1"
    mock_429 = requests.Response()
    mock_429.status_code = 429
    error_429 = requests.exceptions.HTTPError(response=mock_429)
    
    with patch.object(mock_scraper, 'get_chapter_content', side_effect=[error_429, error_429, error_429]):
        with patch('time.sleep'):
            with pytest.raises(requests.exceptions.HTTPError):
                mock_scraper._fetch_with_retry(url, max_retries=3)
