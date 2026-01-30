from bs4 import BeautifulSoup
from src.classes.base_book import BaseScraper
from src.utils.logger import logger
from src.schemas.novel_schema import BookMetadata, ChapterContent
from src.utils.exceptions import ScraperParsingException, NovelNotFoundException

class MyPandaNovelBook(BaseScraper):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        # SELECTORS CENTRALIZATION
        self._selectors = {
            'meta_header': ('div', {'class': 'header-body container'}),
            'meta_info': ('div', {'class': 'novel-info'}),
            'meta_title': ('h1', {}),
            'meta_author': ('div', {'class': 'author'}),
            'meta_description': ('div', {'class': 'summary'}),
            'meta_total_chapters': ('div', {'class': 'header-stats'}),
            
            'chap_title': ('span', {'class': 'chapter-title'}),
            'chap_content': ('div', {'id': 'content'})
        }

    def get_book_metadata(self) -> BookMetadata:
        """Extracts novel metadata using the shared session with logging."""
        
        try:
            response = self._session.get(self._main_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')

            header = soup.find(*self._selectors['meta_header'])
            if not header:
                logger.error(f"[{self.class_name}] Header not found. Site layout might have changed at {self._main_url}")
                raise ScraperParsingException("Could not find the novel header.")

            info = header.find(*self._selectors['meta_info'])
            img_tag = header.find('img')
            
            # Logging cover discovery
            cover_link = img_tag.get('data-src') or img_tag.get('src') if img_tag else None
            if not cover_link:
                logger.warning(f"[{self.class_name}] No cover image found for this novel.")

            title = info.find(*self._selectors['meta_title']).get_text(strip=True) if info else "Unknown Title"
            author = info.find(*self._selectors['meta_author']).find('a')['title'] if info else "Unknown Author"
            
            desc_tag = soup.find(*self._selectors['meta_description'])
            description_str = desc_tag.get_text(strip=True) if desc_tag else "No description available."

            logger.info(f"[{self.class_name}] Metadata successfully extracted: {title}")
            
            return BookMetadata(
                book_title=title,
                book_author=author,
                book_description=description_str,
                book_cover_link=cover_link
            )

        except Exception as e:
            logger.error(f"[{self.class_name}] Critical error during metadata extraction: {e}", exc_info=True)
            raise e

    def get_chapters_link(self) -> list:
        """Generates chapter URLs and logs the range."""
        slug = self._main_url.split('/')[-1]
        
        if self._start_chapter < 1:
            logger.error(f"[{self.class_name}] Invalid start chapter: {self._start_chapter}")
            raise ValueError("Start chapter must be 1 or greater.")
        
        # Ensure only integer part of chapter quantity is used
        try:
            qty = int(self._chapters_quantity)
        except ValueError:
            qty = 1

        logger.info(f"[{self.class_name}] Generating {qty} links starting from chapter {self._start_chapter}")
        
        chapter_urls = []
        for i in range(qty):
            current_chapter_num = i + self._start_chapter
            # Panda/Novelfire specific URL pattern
            url = f'https://novelfire.noveljk.org/book/{slug}/chapter-{current_chapter_num}'
            chapter_urls.append(url)
            
        return chapter_urls

    def get_chapter_content(self, url: str) -> ChapterContent:
        """Scrapes chapter content with detailed error logging."""
        response = self._session.get(url, timeout=10)
        
        if response.status_code == 404:
            logger.error(f"[{self.class_name}] Chapter 404 Not Found: {url}")
            raise NovelNotFoundException(f"Chapter at URL {url} was not found (404).")
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        chapter_title_tag = soup.find(*self._selectors['chap_title'])
        main_content_div = soup.find(*self._selectors['chap_content'])

        if not main_content_div:
            logger.warning(f"[{self.class_name}] Content div empty for chapter: {url}")
            content_str = ""
        else:
            content_str = main_content_div.decode_contents()

        title = chapter_title_tag.get_text(strip=True) if chapter_title_tag else "Untitled Chapter"

        return ChapterContent(
            title=title,
            content=content_str
        )