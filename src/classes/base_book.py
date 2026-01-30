import io, os, random, time
import cloudscraper
import concurrent.futures
from abc import ABC, abstractmethod
from dotenv import load_dotenv

from src.utils.constants import API_CONFIG, EPUB_STRINGS
from src.utils.logger import logger
from src.schemas.novel_schema import Novel, Chapter, BookMetadata

class BaseScraper(ABC):
    def __init__(self, main_url: str, chapters_quantity: int, start_chapter: int):
        # Load variables from .env file into os.environ
        load_dotenv()
        
        self._main_url = main_url
        self._chapters_quantity = chapters_quantity
        self._start_chapter = start_chapter
        
        # Identify which subclass is running
        self.class_name = self.__class__.__name__
        
        # Initialize cloudscraper
        self._session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        # Proxy configuration
        proxy_url = os.environ.get("PROXY_URL")
        if proxy_url:
            self._session.proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            logger.info(f"[{self.class_name}] Proxy enabled from environment.")
        else:
            logger.warning(f"[{self.class_name}] No proxy detected. Using direct server IP.")
        
        self.book_title = "Unknown Title"
        logger.debug(f"[{self.class_name}] Instance initialized for: {main_url}")

    @abstractmethod
    def get_book_metadata(self) -> dict: 
        """Must return a dict compatible with BookMetadata."""
        pass

    @abstractmethod
    def get_chapters_link(self) -> list: 
        """Must return a list of URLs for the chapters."""
        pass

    @abstractmethod
    def get_chapter_content(self, url: str) -> dict: 
        """Must return a dict with chapter_title and main_content (BeautifulSoup node)."""
        pass

    def _fetch_with_retry(self, url: str, max_retries: int = 3):
        """Internal helper to fetch chapter content with exponential backoff."""
        for i in range(max_retries):
            try:
                data = self.get_chapter_content(url)
                if not data or not data.get('main_content'):
                    raise ValueError("Main content is empty or not found.")
                return data
            except Exception as e:
                if i < max_retries - 1:
                    wait_time = (2 ** i) * 5 + random.uniform(1, 2)
                    logger.warning(f"[{self.class_name}] Retry {i+1}/{max_retries} for: {url} | Error: {e} | Waiting {wait_time:.2f}s")
                    time.sleep(wait_time)
                    continue
                logger.error(f"[{self.class_name}] Max retries reached for: {url}")
                raise e

    def scrape_novel(self) -> Novel:
        """Main process to orchestrate scraping and return a Novel object."""
        start_time = time.time()
        logger.info(f"[{self.class_name}] Starting Scrape for: {self._main_url}")

        # 1. Metadata Extraction
        try:
            metadata_dict = self.get_book_metadata()
            # Ensure safety against None values
            meta_title = metadata_dict.get('book_title', 'Unknown')
            meta_author = metadata_dict.get('book_author', 'Unknown Author')
            meta_desc = metadata_dict.get('book_description', EPUB_STRINGS["default_no_description"])
            
            # Helper to Convert BeautifulSoup tags to string if needed
            def to_str(value):
                if value is None: return ""
                return value.get_text(strip=True) if hasattr(value, 'get_text') else str(value)

            self.book_title = to_str(meta_title)
            
            book_metadata = BookMetadata(
                book_title=self.book_title,
                book_author=to_str(meta_author),
                book_description=to_str(meta_desc),
                book_cover_link=to_str(metadata_dict.get('book_cover_link'))
            )
            
        except Exception as e:
            logger.error(f"[{self.class_name}] Critical failure fetching metadata: {e}", exc_info=True)
            raise e
        
        chapter_urls = self.get_chapters_link()
        total_to_download = len(chapter_urls)
        
        logger.info(f"[{self.class_name}] Metadata loaded: '{self.book_title}' | Total chapters: {total_to_download}")

        # 2. Download Cover Image (Optional)
        cover_bytes = None
        if book_metadata.book_cover_link and book_metadata.book_cover_link.startswith('http'):
            try:
                logger.info(f"[{self.class_name}] Downloading cover: {book_metadata.book_cover_link}")
                cover_res = self._session.get(book_metadata.book_cover_link, timeout=API_CONFIG["DEFAULT_TIMEOUT"])
                cover_res.raise_for_status()
                cover_bytes = cover_res.content
            except Exception as e:
                logger.warning(f"[{self.class_name}] Failed to download cover image: {e}")

        # 3. Parallel Chapter Download
        chapters: list[Chapter] = []
        # Create a list of None to store results in order
        chapters_data_results = [None] * total_to_download
        
        completed_count = 0
        checkpoints = {max(1, int(total_to_download * (i / 10))) for i in range(1, 11)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=API_CONFIG["MAX_WORKERS"]) as executor:
            future_to_index = {
                executor.submit(self._fetch_with_retry, url): i 
                for i, url in enumerate(chapter_urls)
            }
            
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    chapters_data_results[index] = result
                except Exception as e:
                    logger.error(f"[{self.class_name}] Error on chapter {index+1}: {e}")
                    chapters_data_results[index] = {
                        'chapter_title': f'Error Chapter {index+1}', 
                        'main_content': EPUB_STRINGS["error_content"]
                    }
                
                completed_count += 1
                if completed_count in checkpoints or completed_count == total_to_download:
                    percentage = (completed_count / total_to_download) * 100
                    logger.info(f"[{self.class_name}] Progress: {percentage:.0f}% ({completed_count}/{total_to_download})")

        # 4. Assemble Chapter Objects
        for i, data in enumerate(chapters_data_results):
            if not data: continue
            
            # Helper again
            def to_str(value):
                if value is None: return ""
                return value.get_text(strip=True) if hasattr(value, 'get_text') else str(value)
            
            title = to_str(data.get('chapter_title', f'Chapter {i + 1}'))
            content_node = data.get('main_content')
            raw_html = content_node.decode_contents() if hasattr(content_node, 'decode_contents') else str(content_node)

            chapters.append(Chapter(
                index=i+1,
                title=title,
                content=raw_html
            ))

        if not chapters:
            logger.critical(f"[{self.class_name}] Scrape failed: No chapters collected.")
            raise ValueError("No chapters found.")
            
        total_time = time.time() - start_time
        logger.info(f"[{self.class_name}] DONE: Scraped '{self.book_title}' in {total_time:.2f}s")

        return Novel(
            metadata=book_metadata,
            chapters=chapters,
            cover_image_bytes=cover_bytes
        )