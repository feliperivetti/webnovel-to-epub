from bs4 import BeautifulSoup
from .base_book import BaseScraper
from src.utils.logger import logger
from src.schemas.novel_schema import BookMetadata, ChapterContent
from src.utils.exceptions import ScraperParsingException

class MyRoyalRoadBook(BaseScraper):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        # SELECTORS CENTRALIZATION
        self._selectors = {
            # Metadata selectors (Main page)
            'meta_header': ('div', {'class': 'row fic-header'}),
            'meta_title': ('h1', {}),
            'meta_author': ('h4', {}),
            'meta_description': ('div', {'class': 'description'}),
            
            # Chapter navigation (Main page table)
            'chap_table_rows': ('tr', {'class': 'chapter-row'}),
            
            # Chapter content (Individual chapter page)
            'chap_title_tag': ('h1', {'class': 'font-white break-word'}),
            'chap_content': ('div', {'class': 'chapter-inner chapter-content'})
        }

    def get_book_metadata(self) -> BookMetadata:
        """Extracts basic book information using the shared session."""
        logger.info(f"[{self.class_name}] Fetching metadata from Royal Road: {self._main_url}")
        
        try:
            response = self._session.get(self._main_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            header = soup.find(*self._selectors['meta_header'])
            if not header:
                logger.error(f"[{self.class_name}] Metadata header not found. Site layout might have changed.")
                raise ScraperParsingException("Could not find the book header. Site layout might have changed.")

            # Cover image extraction
            img_tag = header.find('img')
            cover_link = img_tag.get('src') if img_tag else None
            
            title = header.find(*self._selectors['meta_title']).get_text(strip=True)
            author = header.find(*self._selectors['meta_author']).get_text(strip=True)
            
            desc_tag = soup.find(*self._selectors['meta_description'])
            description = desc_tag.get_text(strip=True) if desc_tag else "No description available."

            logger.info(f"[{self.class_name}] Metadata extracted: '{title}' by '{author}'")

            return BookMetadata(
                book_title=title,
                book_author=author,
                book_description=description,
                book_cover_link=cover_link
            )
        except Exception as e:
            # Raise custom exceptions up, wrap others if needed or let generic bubble up
            logger.error(f"[{self.class_name}] Error fetching metadata: {e}", exc_info=True)
            raise e

    def get_chapters_link(self) -> list:
        # ... (Same implementation, keeping it brief for diff, NO CHANGE needed here ideally but context requires care)
        # Actually this method signature didn't change (returns list), so we can skip replacing it if we target strictly.
        # But to be safe and clean, I will include it or skip it if I can target precisely.
        # Let's replace the whole file content related to methods to be safe.
        
        """Retrieves real chapter links and validates the requested range."""
        logger.info(f"[{self.class_name}] Retrieving chapter list from main page...")
        
        response = self._session.get(self._main_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get all rows from the chapters table
        all_rows = soup.find_all(*self._selectors['chap_table_rows'])
        total_available = len(all_rows)
        logger.info(f"[{self.class_name}] Total chapters available on site: {total_available}")

        # VALIDATION
        if self._start_chapter > total_available:
            logger.error(f"[{self.class_name}] Range error: Start ({self._start_chapter}) > Total ({total_available})")
            raise ValueError(
                f"Requested start chapter ({self._start_chapter}) is greater "
                f"than the total available chapters ({total_available})."
            )

        # Calculate the safe end index
        end_index = min(self._start_chapter + self._chapters_quantity - 1, total_available)
        
        chapter_urls = []
        for i in range(self._start_chapter - 1, end_index):
            relative_url = all_rows[i].get('data-url')
            if relative_url:
                chapter_urls.append(f'https://www.royalroad.com{relative_url}')
        
        logger.info(f"[{self.class_name}] Queued {len(chapter_urls)} chapters for download (Range: {self._start_chapter}-{end_index})")
        return chapter_urls

    def get_chapter_content(self, url: str) -> ChapterContent:
        """Scrapes the title and body text of a specific chapter."""
        # Note: Detailed download logs are handled by the BaseBook executor
        response = self._session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        chapter_title_tag = soup.find(*self._selectors['chap_title_tag'])
        content_div = soup.find(*self._selectors['chap_content'])

        if not content_div:
            logger.warning(f"[{self.class_name}] Content not found for chapter URL: {url}")
            # Identify behavior: raise error or return empty? Base class raises if content empty.
            # We return empty string here, base class will catch.
            content_str = ""
        else:
            # Decode content to string here
            content_str = content_div.decode_contents()

        title = chapter_title_tag.get_text(strip=True) if chapter_title_tag else "Untitled Chapter"

        return ChapterContent(
            title=title,
            content=content_str
        )
    