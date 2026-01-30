import asyncio
import tempfile
import os
import re
import json
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from src.services.centralnovel_service import CentralNovelService
from src.services.novelsbr_service import NovelsBrService
from src.services.pandanovel_service import PandaNovelService
from src.services.royalroad_service import RoyalRoadService

from src.utils.exceptions import NovelNotFoundException, ScraperParsingException, ChapterLimitException

from src.services.registry import ScraperRegistry
from src.utils.logger import logger
from src.config import get_settings
from src.services.task_manager import TaskManager
from src.services.epub_builder import EpubBuilder


router = APIRouter(prefix="/books", tags=["Books"])
settings = get_settings()

# --- BACKGROUND WORKER ---

async def background_epub_generation(task_id: str, url: str, qty: int, start: int):
    """
    Background task that performs scraping and epub generation.
    Updates status in TaskManager.
    """
    logger.info(f"[{task_id}] Background task started.")
    
    # Define a sync callback wrapper to update async TaskManager
    # Because BaseScraper is sync, we might need a way to run async code.
    # Actually, TaskManager methods are async. We can use asyncio.run or run_in_executor wrapper 
    # BUT running asyncio.run inside a loop inside a thread is tricky.
    # Simpler: The callback updates a local variable or calls a non-async helper,
    # OR we make TaskManager methods sync-friendly or fire-and-forget.
    # Let's make a sync wrapper for the callback.
    
    def sync_progress_callback(pct: int):
        # Fire and forget update (or simple sync update if TaskManager allows)
        # Since we are in an async function (background_epub_generation), 
        # but the scraper runs synchronously... 
        # Ideally we run scraper in a threadpool to not block the event loop.
        pass

    try:
        service_class = ScraperRegistry.get_service(url)
        if not service_class:
            await TaskManager.fail_task(task_id, "Unsupported domain.")
            return

        logger.info(f"[{task_id}] Step 2: Loop")
        # Run the heavy synchronous blocking work in a thread
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        def blocking_scraping():
             # We need a way to call async update_progress from this sync thread
            def update_progress_bridge(pct):
                # Schedule the async update in the main loop
                asyncio.run_coroutine_threadsafe(
                    TaskManager.update_progress(task_id, pct), 
                    loop
                )

            service = service_class()
            scraper = service.get_book_instance(url, qty, start)
            return scraper.scrape_novel(progress_callback=update_progress_bridge)

        logger.info(f"[{task_id}] Step 3: Run Executor")
        # Execute scraping in thread pool
        novel_data = await loop.run_in_executor(None, blocking_scraping)
        
        logger.info(f"[{task_id}] Step 4: Build EPUB")
        # Build EPUB
        await TaskManager.update_progress(task_id, 98)
        result_buffer = EpubBuilder.create_epub(novel_data)
        
        logger.info(f"[{task_id}] Step 5: Save File")
        # We use delete=False so we can serve it later.
        # It's important to cleanup later.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub", mode="wb") as tmp:
            if isinstance(result_buffer, bytes):
                tmp.write(result_buffer)
            else:
                tmp.write(result_buffer.getbuffer())
            tmp_path = tmp.name
            
        # Filename
        book_title = novel_data.metadata.book_title
        filename_raw = f"{book_title}.epub"
        filename_clean = re.sub(r'[^\w\s.-]', '', filename_raw).strip() or "novel.epub"
        
        await TaskManager.complete_task(task_id, tmp_path, filename_clean)
        logger.info(f"[{task_id}] Task finished successfully.")

    except Exception as e:
        logger.error(f"[{task_id}] Task failed: {e}", exc_info=True)
        await TaskManager.fail_task(task_id, str(e))


# --- ENDPOINTS ---

@router.post("/generate", status_code=202)
async def start_generation_task(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="The full URL of the novel series"),
    qty: int = Query(default=1, ge=1, le=settings.MAX_CHAPTERS_LIMIT, description="Number of chapters to download"),
    start: int = Query(default=1, ge=1, description="Starting chapter number")
):
    """
    Starts the EPUB generation process in the background.
    Returns a Task ID to track progress.
    """
    # Quick Validation
    if not ScraperRegistry.get_service(url):
         raise HTTPException(status_code=400, detail="Unsupported domain.")

    task_id = await TaskManager.create_task()
    
    # Add to Background Tasks
    background_tasks.add_task(background_epub_generation, task_id, url, qty, start)
    
    return {"task_id": task_id, "message": "Generation started", "status_url": f"/books/events/{task_id}"}


@router.get("/events/{task_id}")
async def get_progress_events(request: Request, task_id: str):
    """
    SSE Endpoint. Streams progress updates for a given task.
    """
    async def event_generator():
        # Check initial validity
        if not TaskManager.get_task(task_id):
            yield {
                "event": "error",
                "data": json.dumps({"message": "Task not found"})
            }
            return

        last_status = None
        last_progress = -1

        while True:
            # If client disconnects
            if await request.is_disconnected():
                break

            task = TaskManager.get_task(task_id)
            if not task:
                break
                
            status = task["status"]
            progress = task["progress"]
            
            # Yield update if something changed
            if status != last_status or progress != last_progress:
                payload = {
                    "status": status, 
                    "progress": progress
                }
                
                if status == "completed":
                    payload["download_url"] = f"/books/download/{task_id}"
                
                if status == "failed":
                    payload["error"] = task.get("error")
                
                yield {
                    "event": "update",
                    "data": json.dumps(payload)
                }
                
                last_status = status
                last_progress = progress

            if status in ["completed", "failed"]:
                break
            
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@router.get("/download/{task_id}")
async def download_book(task_id: str, background_tasks: BackgroundTasks):
    """
    Downloads the generated file and schedules cleanup.
    """
    task = TaskManager.get_task(task_id)
    if not task or task["status"] != "completed":
        raise HTTPException(status_code=404, detail="File not ready or task not found.")
        
    file_path = task.get("file_path")
    filename = task.get("filename", "novel.epub")
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="File lost on server.")

    # Schedule cleanup after response is sent
    # We delay cleanup a bit or just rely on OS temp cleanup if we were purely temp.
    # Since we use NamedTemporaryFile with delete=False, we MUST manual clean.
    # BackgroundTasks runs AFTER response.
    background_tasks.add_task(TaskManager.cleanup_task, task_id)
    
    return FileResponse(
        path=file_path, 
        filename=filename, 
        media_type="application/epub+zip",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )