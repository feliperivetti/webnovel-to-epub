import re
import io
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.services.centralnovel_service import CentralNovelService
from src.services.novelsbr_service import NovelsBrService
from src.services.pandanovel_service import PandaNovelService
from src.services.royalroad_service import RoyalRoadService

from src.utils.constants import API_CONFIG
from src.utils.logger import logger


router = APIRouter(prefix="/books", tags=["Books"])


from src.services.epub_builder import EpubBuilder

# ... imports ...


@router.get("/generate-epub")
def generate_epub(
    url: str = Query(..., description="The full URL of the novel series"),
    qty: int = Query(default=1, ge=1, le=API_CONFIG["MAX_CHAPTERS_LIMIT"], description="Number of chapters to download"),
    start: int = Query(default=1, ge=1, description="Starting chapter number")
):
    """
    Identifies the source novel site, scrapes the content, 
    and returns a generated EPUB file as a stream.
    """
    logger.info(f"🚀 Initializing EPUB generation | URL: {url} | Qty: {qty} | Start: {start}")
    
    # 1. Map domains to Service Classes
    providers = {
        "centralnovel.com": CentralNovelService,
        "novels-br.com": NovelsBrService,
        "pandanovel.co": PandaNovelService,
        "novelfire.net": PandaNovelService,
        "royalroad.com": RoyalRoadService
    }

    # 2. Identify the correct provider
    service_class = None
    for domain, cls in providers.items():
        if domain in url.lower():
            service_class = cls
            break

    if not service_class:
        logger.warning(f"⚠️ Unsupported domain requested: {url}")
        raise HTTPException(
            status_code=400, 
            detail="Source not supported. Supported domains: royalroad.com, centralnovel.com, pandanovel.co, novelfire.net"
        )

    try:
        # 3. Instantiate the service and get the book scraper instance
        service = service_class()
        scraper = service.get_book_instance(url, qty, start)

        # 4. Scrape Data (SRP: Scraper only returns data)
        novel_data = scraper.scrape_novel()
        
        # 5. Build EPUB (SRP: Builder only acts on data)
        result_buffer = EpubBuilder.create_epub(novel_data)

        # Handle both raw bytes and BytesIO objects to avoid "bytes-like object required" error
        if isinstance(result_buffer, bytes):
            final_stream = io.BytesIO(result_buffer)
        else:
            # If it's already a BytesIO object, ensure cursor is at the start
            final_stream = result_buffer
            final_stream.seek(0)
            
        # 6. Filename Sanitization
        book_title = novel_data.metadata.book_title
        filename_raw = f"{book_title}.epub"
        # Keep alphanumeric, spaces, dots, and hyphens
        filename_clean = re.sub(r'[^\w\s.-]', '', filename_raw).strip()
        
        if not filename_clean or filename_clean == ".epub":
            filename_clean = "novel_ebook.epub"

        logger.info(f"✅ EPUB successfully generated: '{filename_clean}'")
        
        # 6. Return as a stream
        return StreamingResponse(
            final_stream,
            media_type="application/epub+zip",
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename_clean}\"",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )

    except Exception as e:
        # exc_info=True captures the full stack trace in the log file
        logger.error(f"❌ Generation failed for {url}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while generating the book: {str(e)}"
        )
    