import io
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
    # Since we use Registry now, we mock valid return from ScraperRegistry.get_service
    mock_service_cls = MagicMock()
    mocker.patch("src.services.registry.ScraperRegistry.get_service", return_value=mock_service_cls)
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
    
    # 5. Make the request (POST now)
    response = client.post("/books/generate", params={
        "url": "https://www.royalroad.com/fiction/12345/test-novel",
        "qty": 5,
        "start": 1
    })
    
    # 6. Assertions for Task Start
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert "status_url" in data
    
    # We do NOT verify mock_scraper calls here because they happen in background task
    # and might not have run yet. Integration test (test_sse.py) covers execution.

def test_generate_epub_invalid_domain():
    """
    Test that an unsupported domain returns 400.
    """
    response = client.post("/books/generate", params={
        "url": "https://unknown-site.com/fiction",
    })
    
    assert response.status_code == 400
    assert "Unsupported domain" in response.json()['detail']
