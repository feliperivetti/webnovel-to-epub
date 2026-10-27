import pytest
from pathlib import Path
from src.classes.royalroad_book import MyRoyalRoadBook
from src.utils.exceptions import AntiBotChallengeException

class TestRoyalRoadScraper:

    @pytest.mark.parametrize("method", ["get_book_metadata", "get_chapters_link", "get_chapter_content"])
    def test_anubis_is_not_reported_as_layout_or_chapter_range_error(self, mock_cloudscraper, method):
        _, response = mock_cloudscraper
        response.text = (Path(__file__).parent / "fixtures" / "royalroad_anubis.html").read_text()
        book = MyRoyalRoadBook("https://www.royalroad.com/fiction/123/test", 1, 1)
        args = ("https://www.royalroad.com/fiction/chapter/1",) if method == "get_chapter_content" else ()
        with pytest.raises(AntiBotChallengeException, match="JavaScript proof-of-work"):
            getattr(book, method)(*args)
    
    def test_get_book_metadata(self, mock_cloudscraper, royalroad_toc_html):
        """
        Should correctly extract title, author, and cover from the TOC page.
        """
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = royalroad_toc_html
        
        # Instantiate the book
        book = MyRoyalRoadBook("https://royalroad.com/fiction/123", 10, 1)
        
        metadata = book.get_book_metadata()
        
        # Now accessing attributes, not keys
        assert metadata.book_title == "The Great Test Novel"
        assert metadata.book_author == "Test Author"
        assert metadata.book_cover_link == "https://example.com/cover.jpg"
        
        # Check description content
        desc = metadata.book_description
        assert "This is a" in desc and "test" in desc and "description" in desc

    def test_get_chapters_link(self, mock_cloudscraper, royalroad_toc_html):
        """
        Should correctly extract chapter URLs from the table.
        """
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = royalroad_toc_html
        
        book = MyRoyalRoadBook("https://royalroad.com/fiction/123", 10, 1)
        
        links = book.get_chapters_link()
        
        # We expect 3 chapters based on the fixture
        assert len(links) == 3
        assert links[0] == "https://www.royalroad.com/fiction/12345/chapter/1"
        assert links[2] == "https://www.royalroad.com/fiction/12345/chapter/3"

    def test_get_chapter_content(self, mock_cloudscraper, royalroad_chap_html):
        """
        Should correctly extract title and content from a chapter page.
        """
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = royalroad_chap_html
        
        book = MyRoyalRoadBook("https://royalroad.com/fiction/123", 10, 1)
        
        data = book.get_chapter_content("https://dummy.url")
        
        # Now accessing attributes
        assert data.title == "Chapter 1: The Beginning"
        
        # Content is now a string, not a BS4 Tag
        assert isinstance(data.content, str)
        assert "Once upon a time" in data.content

    def test_start_chapter_validation(self, mock_cloudscraper, royalroad_toc_html):
        """
        Should raise ValueError if start_chapter > total_available.
        """
        mock_scraper, mock_response = mock_cloudscraper
        mock_response.text = royalroad_toc_html
        
        # Requesting start=10 when there are only 3 chapters
        book = MyRoyalRoadBook("https://royalroad.com/fiction/123", 10, 10)
        
        with pytest.raises(ValueError) as excinfo:
            book.get_chapters_link()
        
        assert "Requested start chapter (10) is greater" in str(excinfo.value)
