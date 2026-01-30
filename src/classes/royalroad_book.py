from bs4 import BeautifulSoup
from .base_book import BaseScraper
from src.utils.logger import logger


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

    def get_book_metadata(self) -> dict:
        """Extracts basic book information using the shared session."""
        logger.info(f"[{self.class_name}] Fetching metadata from Royal Road: {self._main_url}")
        
        try:
            response = self._session.get(self._main_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            header = soup.find(*self._selectors['meta_header'])
            if not header:
                logger.error(f"[{self.class_name}] Metadata header not found. Site layout might have changed.")
                raise ValueError("Could not find the book header.")

            # Cover image extraction
            img_tag = header.find('img')
            cover_link = img_tag.get('src') if img_tag else None
            
            title = header.find(*self._selectors['meta_title']).get_text(strip=True)
            author = header.find(*self._selectors['meta_author']).get_text(strip=True)

            logger.info(f"[{self.class_name}] Metadata extracted: '{title}' by '{author}'")

            return {
                'book_title': title,
                'book_author': author,
                'book_description': soup.find(*self._selectors['meta_description']) or "No description available.",
                'book_cover_link': cover_link
            }
        except Exception as e:
            logger.error(f"[{self.class_name}] Error fetching metadata: {e}", exc_info=True)
            raise e

    def get_chapters_link(self) -> list:
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

    def get_chapter_content(self, url: str) -> dict:
        """Scrapes the title and body text of a specific chapter."""
        # Note: Detailed download logs are handled by the BaseBook executor
        response = self._session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        chapter_title_tag = soup.find(*self._selectors['chap_title_tag'])
        content_div = soup.find(*self._selectors['chap_content'])

        if not content_div:
            logger.warning(f"[{self.class_name}] Content not found for chapter URL: {url}")

        return {    
            'chapter_title': chapter_title_tag.get_text(strip=True) if chapter_title_tag else "Untitled Chapter",
            'main_content': content_div 
        }
    