import io, os, random, time
import cloudscraper
import requests
import concurrent.futures
from abc import ABC, abstractmethod

from src.utils.constants import EPUB_STRINGS
from src.utils.logger import logger
from src.config import get_settings
from src.schemas.novel_schema import Novel, Chapter, BookMetadata, ChapterContent
from src.services.metrics_service import benchmark_scraper


class BaseScraper(ABC):
    def __init__(self, main_url: str, chapters_quantity: int, start_chapter: int):
        self.settings = get_settings()
        
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
        if self.settings.PROXY_URL:
            self._session.proxies = {
                "http": self.settings.PROXY_URL,
                "https": self.settings.PROXY_URL
            }
            logger.info(f"[{self.class_name}] Proxy enabled from environment.")
        else:
            logger.warning(f"[{self.class_name}] No proxy detected. Using direct server IP.")
        
        self.book_title = "Unknown Title"
        logger.debug(f"[{self.class_name}] Instance initialized for: {main_url}")

    @abstractmethod
    def get_book_metadata(self) -> BookMetadata: 
        """Must return a BookMetadata object."""
        pass

    @abstractmethod
    def get_chapters_link(self) -> list: 
        """Must return a list of URLs for the chapters."""
        pass

    @abstractmethod
    def get_chapter_content(self, url: str) -> ChapterContent: 
        """Must return a ChapterContent object with title and content."""
        pass

    def _fetch_with_retry(self, url: str, max_retries: int = 3) -> ChapterContent:
        """Internal helper to fetch chapter content with exponential backoff."""
        for i in range(max_retries):
            try:
                data = self.get_chapter_content(url)
                if not data or not data.content:
                    raise ValueError("Main content is empty or not found.")
                return data
            except requests.exceptions.HTTPError as e:
                 if e.response.status_code == 404:
                     logger.error(f"[{self.class_name}] Chapter 404 Not Found: {url}")
                     raise e
                 # Special handling for Rate Limits (429) and IP Bans (403)
                 if e.response.status_code in [429, 403]:
                     # Only retry if we have retries left
                     if i < max_retries - 1:
                        # Reduced backoff: Assuming rotating proxy, we just need a new IP.
                        # For 403, we might want a slightly longer pause or just try again immediately if we trust the rotation.
                        wait_time = 3.0 * (i + 1) + random.uniform(0, 1)
                        status_msg = "Rate Limit" if e.response.status_code == 429 else "IP Block"
                        logger.warning(f"[{self.class_name}] {e.response.status_code} {status_msg}. Cooling down for {wait_time:.1f}s... (Attempt {i+1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                     # If last retry, fall through to re-raise logic
                     pass
                 raise e
                 raise e
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
                # Proxy Failover Logic
                if self.settings.PROXY_URL_FALLBACK and self.settings.PROXY_URL_FALLBACK != self.settings.PROXY_URL:
                    current_proxy = self._session.proxies.get("http")
                    # If we are currently using the main proxy, switch to fallback
                    if current_proxy == self.settings.PROXY_URL:
                        logger.warning(f"[{self.class_name}] Proxy failed ({e}). Switching to FALLBACK proxy.")
                        self._session.proxies = {
                            "http": self.settings.PROXY_URL_FALLBACK,
                            "https": self.settings.PROXY_URL_FALLBACK
                        }
                        # Give it a moment to switch context
                        time.sleep(1)
                        continue
                
                # Standard Retry Logic
                if i < max_retries - 1:
                    wait_time = (2 ** i) * 5 + random.uniform(1, 2)
                    logger.warning(f"[{self.class_name}] Retry {i+1}/{max_retries} for: {url} | Error: {e} | Waiting {wait_time:.2f}s")
                    time.sleep(wait_time)
                    continue
                logger.error(f"[{self.class_name}] Max retries reached for: {url}")
                raise e
            except Exception as e:
                # ... existing retry logic ...
                if i < max_retries - 1:
                    wait_time = (2 ** i) * 5 + random.uniform(1, 2)
                    logger.warning(f"[{self.class_name}] Retry {i+1}/{max_retries} for: {url} | Error: {e} | Waiting {wait_time:.2f}s")
                    time.sleep(wait_time)
                    continue
                logger.error(f"[{self.class_name}] Max retries reached for: {url}")
                raise e

    @benchmark_scraper
    def scrape_novel(self, progress_callback=None) -> Novel:
        """
        Main process to orchestrate scraping and return a Novel object.
        :param progress_callback: Optional async or sync function(progress: int) -> None
        """
        start_time = time.time()
        logger.info(f"[{self.class_name}] Starting Scrape for: {self._main_url}")

        if progress_callback:
            # Report initial progress
            progress_callback(5)

        # 1. Metadata Extraction
        logger.info(f"[{self.class_name}] Step 1: Fetching metadata...")
        try:
        # ... (metadata logic matches existing) ...
            # Now expects a Pydantic Model directly
            book_metadata = self.get_book_metadata()
            self.book_title = book_metadata.book_title
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                 logger.error(f"[{self.class_name}] Novel not found (404): {self._main_url}")
                 raise NovelNotFoundException(f"Novel not found at {self._main_url}")
            raise e
        except Exception as e:
            logger.error(f"[{self.class_name}] Critical failure fetching metadata: {e}", exc_info=True)
            raise e
        
        if progress_callback:
            progress_callback(10)

        # ... (chapters selection) ...
        try:
            logger.info(f"[{self.class_name}] Step 2: Fetching chapter links...")
            chapter_urls = self.get_chapters_link()
        except ValueError as e:
            # Often subclasses raise ValueError for invalid range/empty chapters
            raise ChapterLimitException(str(e))
        except Exception as e:
             raise e

        total_to_download = len(chapter_urls)
        
        logger.info(f"[{self.class_name}] Metadata loaded: '{self.book_title}' | Total chapters: {total_to_download}")

        if progress_callback:
            progress_callback(15)

        # 2. Download Cover Image (Optional)
        # ... (cover download logic) ...
        cover_bytes = None
        if book_metadata.book_cover_link and book_metadata.book_cover_link.startswith('http'):
            try:
                logger.info(f"[{self.class_name}] Downloading cover: {book_metadata.book_cover_link}")
                cover_res = self._session.get(book_metadata.book_cover_link, timeout=self.settings.DEFAULT_TIMEOUT)
                cover_res.raise_for_status()
                cover_bytes = cover_res.content
            except Exception as e:
                logger.warning(f"[{self.class_name}] Failed to download cover image: {e}")

        # 3. Parallel Chapter Download
        chapters: list[Chapter] = []
        chapters_data_results = [None] * total_to_download
        
        completed_count = 0
        # Calculate checkpoints for logging (every 10%)
        checkpoints = {max(1, int(total_to_download * (i / 10))) for i in range(1, 11)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.settings.MAX_WORKERS) as executor:
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
                    chapters_data_results[index] = ChapterContent(
                        title=f'Error Chapter {index+1}', 
                        content=EPUB_STRINGS["error_content"]
                    )
                
                completed_count += 1
                
                # Progress Logic
                # Scale from 15% to 95% based on chapter download
                # 15 + (count/total * 80)
                if total_to_download > 0:
                    current_pct = 15 + int((completed_count / total_to_download) * 80)
                    if progress_callback:
                        progress_callback(current_pct)

                if completed_count in checkpoints or completed_count == total_to_download:
                    percentage = (completed_count / total_to_download) * 100
                    logger.info(f"[{self.class_name}] Progress: {percentage:.0f}% ({completed_count}/{total_to_download})")

        # 4. Assemble Chapter Objects
        for i, data in enumerate(chapters_data_results):
            if not data: continue
            
            # Data is already ChapterContent, no need to parse dicts
            chapters.append(Chapter(
                index=i+1,
                title=data.title,
                content=data.content
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