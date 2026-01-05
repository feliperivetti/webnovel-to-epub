import io
import time
import random
import requests
import concurrent.futures
from abc import ABC, abstractmethod
from ebooklib import epub
from src.utils.logger import logger


class MyBook(ABC):
    def __init__(self, main_url: str, chapters_quantity: int, start_chapter: int):
        self._main_url = main_url
        self._chapters_quantity = chapters_quantity
        self._start_chapter = start_chapter
        
        # Identify which subclass is running (e.g., MyPandaNovelBook)
        self.class_name = self.__class__.__name__
        
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        
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
        book_description = to_str(metadata.get('book_description', 'No description available.'))
        cover_url = to_str(metadata.get('book_cover_link'))
        
        chapter_urls = self.get_chapters_link()
        total_to_download = len(chapter_urls)
        
        logger.info(f"[{self.class_name}] Metadata loaded: '{self.book_title}' by '{book_author}' | Total chapters: {total_to_download}")

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
                cover_res = self._session.get(cover_url, timeout=15)
                cover_res.raise_for_status()
                book.set_cover("cover.jpg", cover_res.content)
            except Exception as e:
                logger.warning(f"[{self.class_name}] Failed to set cover image: {e}")

        # 4. Create Essential Pages
        # 4.1 Synopsis
        desc_page = epub.EpubHtml(title='Synopsis', file_name='synopsis.xhtml', lang='en')
        desc_page.set_content(f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Synopsis</title></head>
<body>
    <section>
        <h1>Synopsis</h1>
        <p>{book_description.replace(chr(10), '<br/>')}</p>
    </section>
</body>
</html>""".encode('utf-8'))
        book.add_item(desc_page)

        # 4.2 Disclaimer
        disclaimer_page = epub.EpubHtml(title='About this Project', file_name='disclaimer.xhtml', lang='en')
        disclaimer_page.set_content(f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>About this Project</title></head>
<body>
    <section>
        <h1>About this Project</h1>
        <p>This EPUB was generated automatically as a personal project.</p>
        <p><em>Disclaimer:</em> This book only utilizes publicly available data. All rights belong to the original authors.</p>
    </section>
</body>
</html>""".encode('utf-8'))
        book.add_item(disclaimer_page)

        # 5. Parallel Chapter Download
        chapters_data_results = [None] * total_to_download
        logger.info(f"[{self.class_name}] Starting parallel download (2 workers)...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_index = {
                executor.submit(self._fetch_with_retry, url): i 
                for i, url in enumerate(chapter_urls)
            }
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    chapters_data_results[index] = future.result()
                    logger.info(f"[{self.class_name}] Downloaded chapter {index + 1}/{total_to_download}")
                except Exception as e:
                    logger.error(f"[{self.class_name}] Permanent failure on chapter {index+1}: {e}")
                    chapters_data_results[index] = {
                        'chapter_title': f'Error Chapter {index+1}', 
                        'main_content': 'Content could not be downloaded.'
                    }

        # 6. Assemble EPUB Structure
        epub_chapters = []
        for i, data in enumerate(chapters_data_results):
            if not data: continue
            
            title = to_str(data.get('chapter_title', f'Chapter {i + 1}'))
            content_node = data.get('main_content')
            
            # Extract HTML content from BeautifulSoup node or string
            raw_html = content_node.decode_contents() if hasattr(content_node, 'decode_contents') else str(content_node)

            chapter = epub.EpubHtml(title=title, file_name=f'chap_{i + 1}.xhtml', lang='en')
            xhtml_body = f"""<!DOCTYPE html>
                            <html xmlns="http://www.w3.org/1999/xhtml">
                            <head><title>{title}</title></head>
                            <body>
                                <section>
                                    <h1>{title}</h1>
                                    <div>{raw_html}</div>
                                </section>
                            </body>
                            </html>"""
            chapter.set_content(xhtml_body.encode('utf-8'))
            book.add_item(chapter)
            epub_chapters.append(chapter)

        if not epub_chapters:
            logger.critical(f"[{self.class_name}] Generation failed: No chapters collected.")
            raise ValueError("No chapters found to build the EPUB.")

        # 7. Finalize TOC and Navigation
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
    