import re
import time
from bs4 import BeautifulSoup
from .base_book import BaseScraper
from src.utils.logger import logger

class MyCentralNovelBook(BaseScraper):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        # Selectors using CSS syntax for select_one
        self._selectors = {
            'meta_header': 'div.bigcontent',
            'meta_title': 'h1.entry-title',
            'meta_info': 'div.info-content',
            'meta_description': 'div.entry-content',
            'meta_chapter_list_all': 'div.eplister',
            
            'chap_title': 'div.cat-series',
            'chap_content': 'div.epcontent.entry-content'
        }

    def get_book_metadata(self) -> dict:
        logger.info(f"[{self.class_name}] Fetching metadata from: {self._main_url}")
        
        try:
            response = self._session.get(self._main_url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            header = soup.select_one(self._selectors['meta_header'])
            if not header:
                logger.error(f"[{self.class_name}] Could not find book header at {self._main_url}")
                raise ValueError("Could not find the book header. Check the URL.")

            info_content = header.select_one(self._selectors['meta_info'])
            author_spans = info_content.find_all('span') if info_content else []
            author_text = author_spans[2].get_text(strip=True) if len(author_spans) > 2 else "Unknown Author"

            description_div = soup.select_one(self._selectors['meta_description'])
            title = header.select_one(self._selectors['meta_title']).get_text(strip=True)

            logger.info(f"[{self.class_name}] Metadata extracted for: {title}")

            return {
                'book_title': title,
                'book_author': author_text,
                'book_description': description_div or "No description available.",
                'book_cover_link': header.find('img').get('src') if header.find('img') else None
            }
        except Exception as e:
            logger.error(f"[{self.class_name}] Failed to get metadata: {e}", exc_info=True)
            raise e

    def get_chapters_link(self) -> list:
        logger.info(f"[{self.class_name}] Generating chapter URLs for range: {self._start_chapter} to {self._start_chapter + self._chapters_quantity - 1}")
        
        response = self._session.get(self._main_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        all_eplisters = soup.select(self._selectors['meta_chapter_list_all'])
        total_available = sum(len(block.find_all('a')) for block in all_eplisters)

        if total_available == 0:
            logger.error(f"[{self.class_name}] No chapters found on the page.")
            raise ValueError("No chapters found.")

        raw_slug = self._main_url.strip('/').split('/')[-1]
        clean_slug = re.sub(r'-\d+$', '', raw_slug)
        
        chapter_urls = []
        end_chapter = min(self._start_chapter + self._chapters_quantity - 1, total_available)
        
        for i in range(self._start_chapter, end_chapter + 1):
            url = f"https://centralnovel.com/{clean_slug}-capitulo-{i}/"
            chapter_urls.append(url)
            
        logger.info(f"[{self.class_name}] Successfully generated {len(chapter_urls)} chapter links.")
        return chapter_urls

    def get_chapter_content(self, url: str) -> dict:
        # Note: The log of "Downloading chapter..." is handled by BaseBook in ThreadPool
        response = self._session.get(url, timeout=10)
        
        if response.status_code == 429:
            logger.warning(f"[{self.class_name}] Rate limited (429) on {url}. Retrying after sleep...")
            time.sleep(2)
            response = self._session.get(url, timeout=10)

        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        chapter_title = soup.select_one(self._selectors['chap_title'])
        content_div = soup.select_one(self._selectors['chap_content'])

        if not content_div:
            # Fallback selector
            content_div = soup.find('div', class_='entry-content')
            if content_div:
                logger.debug(f"[{self.class_name}] Primary content selector failed, used fallback for {url}")
            else:
                logger.error(f"[{self.class_name}] Content div not found for {url}")

        # Cleanup specific to Central Novel (removal of AI notices)
        if content_div:
            first_p = content_div.find('p')
            if first_p and "Inteligência Artificial" in first_p.get_text():
                first_p.decompose()
                logger.debug(f"[{self.class_name}] Removed AI disclaimer from {url}")

        return {
            'chapter_title': chapter_title.get_text(strip=True) if chapter_title else "Untitled",
            'main_content': content_div 
        }
    