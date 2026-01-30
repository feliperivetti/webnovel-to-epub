import io
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from src.main import app

from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from src.main import app, verify_internal_token

client = TestClient(app)

# Override the authentication dependency to bypass it during tests
app.dependency_overrides[verify_internal_token] = lambda: {"sub": "test", "action": "generate-epub"}

# Use patch to mock the Service and Scraper
# We need to mock 'src.routes.book_routes.CentralNovelService' or whatever service is being called.
# Since the route logic dynamically selects the service, we'll test the RoyalRoad path.

def test_generate_epub_endpoint(mocker):
    """
    Test the full /books/generate-epub flow with mocked service.
    """
    # 1. Mock the specific Provider Class used in the route
    mock_service_cls = mocker.patch("src.routes.book_routes.RoyalRoadService")
    mock_service = mock_service_cls.return_value
    
    # 2. Mock the scraper instance returned by the service
    mock_scraper = MagicMock()
    # Ensure book_title matches what the route expects for filename generation
    mock_scraper.book_title = "My Test Novel" 
    
    # 3. Mock the create_epub_buffer method to return bytes
    fake_epub_content = b"PK\x03\x04..." # Minimal zip signature approximation
    mock_scraper.create_epub_buffer.return_value = io.BytesIO(fake_epub_content)
    
    # Connect the scraper to the service
    mock_service.get_book_instance.return_value = mock_scraper
    
    # 4. Make the request
    # Since we have JWT auth enabled using Depends(verify_internal_token), 
    # and verifying_internal_token checks API_JWT_SECRET env var.
    # If API_JWT_SECRET is missing, it skips validation (returns "dev" user).
    # Assuming dev environment for tests or we can mock the dependency override.
    
    response = client.get("/books/generate-epub", params={
        "url": "https://www.royalroad.com/fiction/12345/test-novel",
        "qty": 5,
        "start": 1
    })
    
    # 5. Assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/epub+zip"
    assert "My Test Novel.epub" in response.headers["content-disposition"]
    assert response.content == fake_epub_content

def test_generate_epub_invalid_domain():
    """
    Test that an unsupported domain returns 400.
    """
    response = client.get("/books/generate-epub", params={
        "url": "https://unknown-site.com/fiction",
    })
    
    assert response.status_code == 400
    assert "Source not supported" in response.json()['detail']
