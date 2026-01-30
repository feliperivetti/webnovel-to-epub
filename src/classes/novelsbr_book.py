import time
from bs4 import BeautifulSoup
from src.classes.base_book import BaseScraper
from src.utils.logger import logger
from src.schemas.novel_schema import BookMetadata, ChapterContent

class MyNovelsBrBook(BaseScraper):
    """
    Scraper implementation for Novels-BR books.
    Handles metadata extraction and chapter list navigation within accordion menus.
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        # Selectors using CSS syntax for select/select_one
        self._selectors = {
            'meta_header': 'section.navbar-novel',
            'meta_title': 'h1.mb-0',
            'meta_info': 'div#hero-novel',
            'meta_description': 'p[style*="text-align: justify"]',
            'meta_chapter_list_all': 'div#volumes',
            
            'chap_title': 'h2.chapter-title',
            'chap_content': 'div.chapter-content'
        }
        
    def get_book_metadata(self) -> BookMetadata:
        """
        Extracts book title, author, description, and cover image from the main page.
        """
        logger.info(f"[{self.class_name}] Fetching metadata from: {self._main_url}")
        
        try:
            response = self._session.get(self._main_url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            # 1. Access the main header container
            header = soup.select_one(self._selectors['meta_header'])
            if not header:
                logger.error(f"[{self.class_name}] Could not find book header at {self._main_url}")
                raise ValueError("Could not find the book header. Check the URL.")

            # 2. Extract Title
            title_element = header.select_one(self._selectors['meta_title'])
            title = title_element.get_text(strip=True) if title_element else "Unknown Title"

            # 3. Extract Author and Info from hero section
            info_content = header.select_one(self._selectors['meta_info'])
            author_text = "Unknown Author"
            if info_content:
                author_tag = info_content.select_one('h3')
                if author_tag:
                    author_text = author_tag.get_text(strip=True)

            # 4. Extract Description
            description_element = soup.select_one(self._selectors['meta_description'])
            description_str = description_element.get_text(strip=True) if description_element else "No description available."

            # 5. Extract Cover Link
            cover_img = header.select_one('img.header-img')
            cover_link = cover_img.get('src') if cover_img else None

            logger.info(f"[{self.class_name}] Metadata successfully extracted for: {title}")

            return BookMetadata(
                book_title=title,
                book_author=author_text,
                book_description=description_str,
                book_cover_link=cover_link
            )
            
        except Exception as e:
            logger.error(f"[{self.class_name}] Failed to get metadata: {e}", exc_info=True)
            raise e
    
    def get_chapters_link(self) -> list:
        # Keeping this brief as logic remains same, just ensuring correct method bounds
        """
        Parses the accordion-style chapter list and returns absolute URLs for the requested range.
        """
        logger.info(f"[{self.class_name}] Fetching chapter links for range: {self._start_chapter} to {self._start_chapter + self._chapters_quantity - 1}")
        
        try:
            response = self._session.get(self._main_url, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            # 1. Locate the main accordion container (#volumes)
            volume_container = soup.select_one(self._selectors['meta_chapter_list_all'])
            
            if not volume_container:
                # Fallback to generic accordion class if ID is missing
                volume_container = soup.select_one('div.accordion')
                if not volume_container:
                    logger.error(f"[{self.class_name}] Chapter container not found at {self._main_url}")
                    return []

            # 2. Extract all chapter links using the specific accordion hierarchy
            # Path: div#volumes -> accordion-body -> ol -> li -> a
            all_links = volume_container.select('div.accordion-body ol li a.custom-link')
            total_available = len(all_links)
            
            logger.info(f"[{self.class_name}] Found {total_available} chapters available on the page.")

            if total_available == 0:
                logger.warning(f"[{self.class_name}] No links found with primary selector. Trying generic 'ol li a'.")
                all_links = volume_container.select('ol li a')
                total_available = len(all_links)

            # 3. Calculate slice range
            start_index = max(0, self._start_chapter - 1)
            end_index = start_index + self._chapters_quantity
            
            selected_anchors = all_links[start_index : end_index]
            
            chapter_urls = []
            for anchor in selected_anchors:
                href = anchor.get('href')
                if href:
                    # Normalize relative URLs to absolute
                    full_url = f"https://novels-br.com{href}" if href.startswith('/') else href
                    chapter_urls.append(full_url)
            
            logger.info(f"[{self.class_name}] Successfully retrieved {len(chapter_urls)} absolute chapter links.")
            return chapter_urls

        except Exception as e:
            logger.error(f"[{self.class_name}] Failed to retrieve chapter links: {e}", exc_info=True)
            return []
    
    def get_chapter_content(self, url: str) -> ChapterContent:
        """
        Fetches and cleans the main text content of a single chapter, 
        targeting pure paragraph tags within the content container.
        """
        logger.debug(f"[{self.class_name}] Scraping content from: {url}")
        
        try:
            response = self._session.get(url, timeout=15)
            
            # Handling potential rate limits
            if response.status_code == 429:
                logger.warning(f"[{self.class_name}] Rate limited (429). Waiting 2s before retry...")
                time.sleep(2)
                response = self._session.get(url, timeout=15)

            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            # 1. Select the title (often h1 or h2 with chapter-title class)
            chapter_title = soup.select_one('h1.mb-0, h2.chapter-title, .chapter-title')
            
            # 2. Select the main container
            container = soup.select_one(self._selectors.get('chap_content', 'div.chapter-content'))

            if not container:
                logger.error(f"[{self.class_name}] Main container 'div.chapter-content' not found at {url}")
                # Return empty content object
                return ChapterContent(title='Error', content='')

            # 3. CLEANUP: Remove known junk before extracting paragraphs
            for junk in container.select('.google-auto-placed, ins, script, .adsbygoogle, .page-link, style'):
                junk.decompose()

            # 4. EXTRACTION: Create a new container to hold only "pure" paragraphs
            cleaned_content = soup.new_tag("div")
            
            # Find all <p> tags that do NOT have classes or IDs (pure story text)
            paragraphs = container.find_all('p', recursive=True)
            
            valid_paragraphs_count = 0
            for p in paragraphs:
                # Filter out hidden SEO text or empty paragraphs
                style = p.get('style', '')
                if 'display: none' in style or 'visibility: hidden' in style:
                    continue
                
                # Filter out common "Support the author" or "Read at site" junk
                text = p.get_text(strip=True)
                if not text or len(text) < 3 or "Leia em https" in text:
                    continue
                
                # If it's a pure paragraph, append it to our cleaned container
                cleaned_content.append(p)
                valid_paragraphs_count += 1

            if valid_paragraphs_count == 0:
                logger.warning(f"[{self.class_name}] No valid paragraphs found. Falling back to full container text.")
                cleaned_content = container

            title = chapter_title.get_text(strip=True) if chapter_title else "Untitled Chapter"
            
            return ChapterContent(
                title=title,
                content=cleaned_content.decode_contents()
            )

        except Exception as e:
            logger.error(f"[{self.class_name}] Error fetching chapter content at {url}: {e}", exc_info=True)
            return ChapterContent(title='Error', content='')