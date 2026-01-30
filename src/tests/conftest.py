import os
import pytest
from unittest.mock import MagicMock

# Define paths to fixtures
FIXTURES_DIR = os.path.dirname(os.path.abspath(__file__)) + "/fixtures"

@pytest.fixture
def royalroad_toc_html():
    with open(f"{FIXTURES_DIR}/royalroad_toc.html", "r", encoding="utf-8") as f:
        return f.read()

@pytest.fixture
def royalroad_chap_html():
    with open(f"{FIXTURES_DIR}/royalroad_chap.html", "r", encoding="utf-8") as f:
        return f.read()

@pytest.fixture
def mock_cloudscraper(mocker):
    """
    Mock cloudscraper to avoid real network requests.
    """
    mock_scraper = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_scraper.get.return_value = mock_response
    
    # Patch the create_scraper function where it is used
    mocker.patch("cloudscraper.create_scraper", return_value=mock_scraper)
    
    return mock_scraper, mock_response
