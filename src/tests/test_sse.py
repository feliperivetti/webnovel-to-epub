import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from src.main import app, verify_internal_token
from src.services.task_manager import TaskManager
from unittest.mock import MagicMock, AsyncMock
import nest_asyncio

nest_asyncio.apply()

# Override auth for testing
app.dependency_overrides[verify_internal_token] = lambda: {"sub": "test", "action": "generate-epub"}

@pytest.fixture
def mock_scrapers(mocker):
    # Mock Registry to return a mock class
    mock_service_cls = MagicMock()
    mock_scraper = MagicMock()
    
    # Mock scrape_novel to be compatible with threadpool
    # It just needs to return a dummy novel data
    from src.schemas.novel_schema import Novel, BookMetadata, Chapter
    mock_novel = Novel(
        metadata=BookMetadata(book_title="Async Test", book_author="Me", book_description="Desc"),
        chapters=[Chapter(index=1, title="Ch1", content="Text")]
    )
    mock_scraper.scrape_novel.return_value = mock_novel
    
    mock_service_cls.return_value.get_book_instance.return_value = mock_scraper
    mocker.patch("src.services.registry.ScraperRegistry.get_service", return_value=mock_service_cls)
    return mock_scraper

@pytest.mark.asyncio
async def test_full_sse_flow(mock_scrapers, mocker):
    """
    Integration test for the async task flow:
    1. POST /generate -> get task_id
    2. GET /events/{task_id} -> stream updates
    3. GET /download/{task_id} -> download file
    """
    
    # 1. Start Task
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/books/generate", params={
            "url": "https://royalroad.com/fiction/123",
            "qty": 1, 
            "start": 1
        })
    
    assert response.status_code == 202
    data = response.json()
    task_id = data["task_id"]
    assert "task_id" in data
    
    # 2. Consume SSE Events
    # We need to wait a bit for background task to finish or we manually trigger it?
    # Since we use FastAPI TestClient/AsyncClient, background tasks run in the event loop.
    # We poll the SSE endpoint.
    
    events = []
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        async with ac.stream("GET", f"/books/events/{task_id}") as response:
             async for line in response.aiter_lines():
                 if line.startswith("data:"):
                     import json
                     payload = json.loads(line[6:])
                     events.append(payload)
                     if payload.get("status") in ["completed", "failed"]:
                         break
    
    # Verify we got events
    assert len(events) > 0
    final_event = events[-1]
    
    error_msg = final_event.get("error", "Unknown error")
    assert final_event["status"] == "completed", f"Task Failed: {error_msg}"
    assert "download_url" in final_event
    
    # 3. Download
    download_url = final_event["download_url"]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        dl_response = await ac.get(download_url)
        
    assert dl_response.status_code == 200
    assert dl_response.headers["content-type"] == "application/epub+zip"
    
    # Cleanup mocked file if real one created? 
    # TaskManager uses tempfile, logic should handle it.
