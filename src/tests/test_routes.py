import io
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from src.main import app, verify_internal_token
from src.schemas.novel_schema import Novel, BookMetadata, Chapter

client = TestClient(app)

# Override the authentication dependency to bypass it during tests
app.dependency_overrides[verify_internal_token] = lambda: {"sub": "test", "action": "generate-epub"}

def test_generate_epub_endpoint(mocker):
    """
    Test the full /books/generate-epub flow with mocked service and builder.
    """
    # 1. Mock the specific Provider Class used in the route
    mock_service_cls = mocker.patch("src.routes.book_routes.RoyalRoadService")
    mock_service = mock_service_cls.return_value
    
    # 2. Mock the scraper instance returned by the service
    mock_scraper = MagicMock()
    mock_service.get_book_instance.return_value = mock_scraper
    
    # 3. Mock scraper.scrape_novel() to return a valid Novel object
    mock_novel = Novel(
        metadata=BookMetadata(
            book_title="My Test Novel", 
            book_author="Test Author", 
            book_description="Desc"
        ), 
        chapters=[Chapter(index=1, title="Ch1", content="<p>Content</p>")]
    )
    mock_scraper.scrape_novel.return_value = mock_novel
    
    # 4. Mock EpubBuilder to return a byte buffer
    fake_epub_content = b"PK\x03\x04..." # Minimal zip signature
    mock_builder = mocker.patch("src.routes.book_routes.EpubBuilder")
    mock_builder.create_epub.return_value = io.BytesIO(fake_epub_content)
    
    # Connect the scraper to the service
    mock_service.get_book_instance.return_value = mock_scraper
    
    # 5. Make the request
    response = client.get("/books/generate-epub", params={
        "url": "https://www.royalroad.com/fiction/12345/test-novel",
        "qty": 5,
        "start": 1
    })
    
    # 6. Assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/epub+zip"
    assert "My Test Novel.epub" in response.headers["content-disposition"]
    assert response.content == fake_epub_content
    
    # Verify calls
    mock_scraper.scrape_novel.assert_called_once()
    mock_builder.create_epub.assert_called_once_with(mock_novel)

def test_generate_epub_invalid_domain():
    """
    Test that an unsupported domain returns 400.
    """
    response = client.get("/books/generate-epub", params={
        "url": "https://unknown-site.com/fiction",
    })
    
    assert response.status_code == 400
    assert "Source not supported" in response.json()['detail']
