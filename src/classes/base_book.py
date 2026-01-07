import io, os, random, time
import cloudscraper
import concurrent.futures
from abc import ABC, abstractmethod
from ebooklib import epub

from src.utils.constants import API_CONFIG, EPUB_HTML_TEMPLATE, EPUB_STRINGS
from src.utils.logger import logger


class MyBook(ABC):
    def __init__(self, main_url: str, chapters_quantity: int, start_chapter: int):
        self._main_url = main_url
        self._chapters_quantity = chapters_quantity
        self._start_chapter = start_chapter
        
        # Identify which subclass is running (e.g., MyPandaNovelBook)
        self.class_name = self.__class__.__name__
        
        # Initialize cloudscraper to bypass Cloudflare/Wordfence
        self._session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        # Proxy configuration via Environment Variable
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
        """Must return a dict with book_title, book_author, book_description, book_cover_link."""
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
                    # Exponential backoff: 5s, 10s... + jitter
                    wait_time = (2 ** i) * 5 + random.uniform(1, 2)
                    logger.warning(f"[{self.class_name}] Retry {i+1}/{max_retries} for: {url} | Error: {e} | Waiting {wait_time:.2f}s")
                    time.sleep(wait_time)
                    continue
                
                logger.error(f"[{self.class_name}] Max retries reached for: {url}")
                raise e

    def create_epub_buffer(self) -> io.BytesIO:
        """Main process to orchestrate scraping and EPUB creation."""
        start_time = time.time()
        logger.info(f"[{self.class_name}] Starting EPUB generation for: {self._main_url}")

        # 1. Metadata Extraction
        try:
            metadata = self.get_book_metadata()
        except Exception as e:
            logger.error(f"[{self.class_name}] Critical failure fetching metadata: {e}", exc_info=True)
            raise e
        
        def to_str(value):
            if value is None: return ""
            return value.get_text(strip=True) if hasattr(value, 'get_text') else str(value)

        self.book_title = to_str(metadata.get('book_title', 'Unknown'))
        book_author = to_str(metadata.get('book_author', 'Unknown Author'))
        book_description = to_str(metadata.get('book_description', EPUB_STRINGS["default_no_description"]))
        cover_url = to_str(metadata.get('book_cover_link'))
        
        chapter_urls = self.get_chapters_link()
        total_to_download = len(chapter_urls)
        
        logger.info(f"[{self.class_name}] Metadata loaded: '{self.book_title}' | Total chapters: {total_to_download}")

        # 2. Initialize EPUB object
        book = epub.EpubBook()
        book.set_identifier(f"id_{int(time.time())}")
        book.set_title(self.book_title)
        book.set_language('en')
        book.add_author(book_author)
        book.add_metadata('DC', 'description', book_description)

        # 3. Handle Cover Image
        if cover_url and cover_url.startswith('http'):
            try:
                logger.info(f"[{self.class_name}] Downloading cover: {cover_url}")
                cover_res = self._session.get(cover_url, timeout=API_CONFIG["DEFAULT_TIMEOUT"])
                cover_res.raise_for_status()
                book.set_cover("cover.jpg", cover_res.content)
            except Exception as e:
                logger.warning(f"[{self.class_name}] Failed to set cover image: {e}")

        # 4. Create Essential Pages
        desc_page = epub.EpubHtml(title=EPUB_STRINGS["synopsis_title"], file_name='synopsis.xhtml', lang='en')
        desc_page.set_content(EPUB_HTML_TEMPLATE.format(
            title=EPUB_STRINGS["synopsis_title"],
            content=f"<p>{book_description.replace(chr(10), '<br/>')}</p>"
        ).encode('utf-8'))
        book.add_item(desc_page)

        disclaimer_page = epub.EpubHtml(title=EPUB_STRINGS["disclaimer_title"], file_name='disclaimer.xhtml', lang='en')
        disclaimer_page.set_content(EPUB_HTML_TEMPLATE.format(
            title=EPUB_STRINGS["disclaimer_title"],
            content=EPUB_STRINGS["disclaimer_content"]
        ).encode('utf-8'))
        book.add_item(disclaimer_page)

        # 5. Parallel Chapter Download with Progress Milestones
        chapters_data_results = [None] * total_to_download
        logger.info(f"[{self.class_name}] Starting parallel download: {total_to_download} chapters | Workers: {API_CONFIG['MAX_WORKERS']}")
        
        completed_count = 0
        errors_count = 0 

        # Define os marcos de progresso (ex: a cada 10%)
        # Usamos um set para evitar duplicatas e garantir busca O(1)
        checkpoints = {max(1, int(total_to_download * (i / 10))) for i in range(1, 11)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=API_CONFIG["MAX_WORKERS"]) as executor:
            future_to_index = {
                executor.submit(self._fetch_with_retry, url): i 
                for i, url in enumerate(chapter_urls)
            }
            
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    chapters_data_results[index] = future.result()
                except Exception as e:
                    errors_count += 1
                    logger.error(f"[{self.class_name}] Error on chapter {index+1}: {e}")
                    chapters_data_results[index] = {
                        'chapter_title': f'Error Chapter {index+1}', 
                        'main_content': EPUB_STRINGS["error_content"]
                    }
                
                # Incrementa o contador e verifica se atingiu um marco
                completed_count += 1
                if completed_count in checkpoints or completed_count == total_to_download:
                    percentage = (completed_count / total_to_download) * 100
                    logger.info(f"[{self.class_name}] Progress: {percentage:.0f}% ({completed_count}/{total_to_download})")

        # FINAL SUMMARY LOG
        if errors_count == 0:
            logger.info(f"[{self.class_name}] All chapters downloaded successfully.")
        else:
            logger.warning(f"[{self.class_name}] Download finished with {errors_count} errors.")

        # 6. Assemble EPUB Structure
        epub_chapters = []
        for i, data in enumerate(chapters_data_results):
            if not data: continue
            
            title = to_str(data.get('chapter_title', f'Chapter {i + 1}'))
            content_node = data.get('main_content')
            raw_html = content_node.decode_contents() if hasattr(content_node, 'decode_contents') else str(content_node)

            chapter = epub.EpubHtml(title=title, file_name=f'chap_{i + 1}.xhtml', lang='en')
            chapter.set_content(EPUB_HTML_TEMPLATE.format(
                title=title,
                content=raw_html
            ).encode('utf-8'))
            
            book.add_item(chapter)
            epub_chapters.append(chapter)

        if not epub_chapters:
            logger.critical(f"[{self.class_name}] Generation failed: No chapters collected.")
            raise ValueError("No chapters found to build the EPUB.")

        # 7. Structure TOC and Spine
        book.toc = (
            (epub.Section('Essential Information'), (desc_page, disclaimer_page)),
            (epub.Section('Table of Contents'), tuple(epub_chapters)),
        )
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ['nav', desc_page, disclaimer_page] + epub_chapters

        # 8. Save to Buffer
        buffer = io.BytesIO()
        epub.write_epub(buffer, book, {})
        buffer.seek(0)
        
        total_time = time.time() - start_time
        logger.info(f"[{self.class_name}] DONE: '{self.book_title}' generated in {total_time:.2f}s")
        
        return buffer
    