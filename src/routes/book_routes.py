import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.classes.centralnovel_book import MyCentralNovelBook
from src.classes.pandanovel_book import MyPandaNovelBook
from src.classes.royalroad_book import MyRoyalRoadBook

# Define the router with a prefix and tags for better documentation
router = APIRouter(prefix="/books", tags=["Books"])

@router.get("/generate-epub")
def generate_epub(url: str, qty: int = 1, start: int = 1):
    print(f"\n🚀 Starting EPUB generation for {qty} chapters...")
    
    try:
        # Scraper selection based on URL domain
        if "royalroad.com" in url:
            scraper = MyRoyalRoadBook(url, qty, start)
        elif "centralnovel.com" in url:
            scraper = MyCentralNovelBook(url, qty, start)
        elif "pandanovel.com" in url or "novelfire.net" in url:
            scraper = MyPandaNovelBook(url, qty, start)
        else:
            raise HTTPException(status_code=400, detail="Unsupported source URL.")
            
        # The parallel processing occurs inside the base class via create_epub_buffer
        buffer = scraper.create_epub_buffer()

        # --- FILENAME SANITIZATION ---
        # Keep only alphanumeric characters, spaces, dots, and hyphens to avoid HTTP header issues
        filename_raw = f"{scraper.book_title}.epub"
        filename_clean = re.sub(r'[^\w\s.-]', '', filename_raw).strip()
        
        # Fallback if the title becomes empty after cleaning
        if not filename_clean or filename_clean == ".epub":
            filename_clean = "novel_ebook.epub"
        # -----------------------------

        print(f"✅ Download and processing completed successfully!")
        
        # Return the buffer as a stream for the browser to download
        return StreamingResponse(
            buffer,
            media_type="application/epub+zip",
            headers={"Content-Disposition": f"attachment; filename={filename_clean}"}
        )

    except Exception as e:
        print(f"❌ Generation error: {e}")
        # Return a structured error to the API client
        raise HTTPException(status_code=500, detail=str(e))