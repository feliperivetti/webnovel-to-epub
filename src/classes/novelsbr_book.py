import re
import time
from bs4 import BeautifulSoup
from src.classes.base_book import MyBook
from src.utils.logger import logger

class MyNovelsBrBook(MyBook):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        # Selectors using CSS syntax for select_one
        self._selectors = {
            'meta_header': 'section.navbar-novel',
            'meta_title': 'h1.mb-0',
            'meta_info': 'div#hero-novel',
            'meta_description': 'p[style*="text-align: justify"]',
            'meta_chapter_list_all': 'div.row.mt-3',
            
            'chap_title': 'h2.chapter-title',
            'chap_content': 'div.chapter-content'
        }
        
    def get_book_metadata(self) -> dict:
        logger.info(f"[{self.class_name}] Fetching metadata from: {self._main_url}")
        
        try:
            response = self._session.get(self._main_url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            # 1. Access the main header container (section.navbar-novel)
            header = soup.select_one(self._selectors['meta_header'])
            if not header:
                logger.error(f"[{self.class_name}] Could not find book header at {self._main_url}")
                raise ValueError("Could not find the book header. Check the URL.")

            # 2. Extract Title (h1.mb-0)
            title_element = header.select_one(self._selectors['meta_title'])
            title = title_element.get_text(strip=True) if title_element else "Unknown Title"

            # 3. Extract Author and Info from the hero-novel container
            info_content = header.select_one(self._selectors['meta_info'])
            # In Novels-BR, Author is in h3 and Chapters Count is in h6
            author_text = "Unknown Author"
            if info_content:
                author_tag = info_content.select_one('h3')
                if author_tag:
                    author_text = author_tag.get_text(strip=True)

            # 4. Extract Description (p with specific justify style)
            description_div = soup.select_one(self._selectors['meta_description'])
            
            # 5. Extract Cover Link (img with class header-img)
            # We look for the image inside the header context
            cover_img = header.select_one('img.header-img')
            cover_link = cover_img.get('src') if cover_img else None

            logger.info(f"[{self.class_name}] Metadata extracted for: {title}")

            return {
                'book_title': title,
                'book_author': author_text,
                'book_description': description_div or "No description available.",
                'book_cover_link': cover_link
            }
            
        except Exception as e:
            logger.error(f"[{self.class_name}] Failed to get metadata: {e}", exc_info=True)
            raise e
    
    def get_chapters_link(self) -> list:
        logger.info(f"[{self.class_name}] Fetching chapter links for range: {self._start_chapter} to {self._start_chapter + self._chapters_quantity - 1}")
        
        try:
            # 1. Fetch the main novel page
            response = self._session.get(self._main_url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            # 2. Locate the accordion container that holds all volumes and chapters
            # On Novels-BR, this is usually 'div#volumes'
            volume_accordion = soup.select_one('div#volumes')
            
            if not volume_accordion:
                logger.error(f"[{self.class_name}] Chapter accordion not found at {self._main_url}")
                raise ValueError("Could not find the chapter list container.")

            # 3. Extract all available chapter anchor tags from the lists
            all_links = volume_accordion.select('ol li a.custom-link')
            total_available = len(all_links)

            if total_available == 0:
                logger.error(f"[{self.class_name}] No chapter links extracted from the accordion.")
                raise ValueError("No chapters found on this page.")

            # 4. Calculate the slice based on requested start and quantity
            # We use (start - 1) because lists are 0-indexed (Chapter 1 is index 0)
            start_index = max(0, self._start_chapter - 1)
            end_index = min(start_index + self._chapters_quantity, total_available)
            
            selected_anchors = all_links[start_index : end_index]
            
            chapter_urls = []
            for anchor in selected_anchors:
                href = anchor.get('href')
                if href:
                    # Normalize relative URLs to absolute ones
                    full_url = f"https://novels-br.com{href}" if href.startswith('/') else href
                    chapter_urls.append(full_url)
            
            logger.info(f"[{self.class_name}] Successfully retrieved {len(chapter_urls)} absolute chapter links.")
            return chapter_urls

        except Exception as e:
            logger.error(f"[{self.class_name}] Failed to retrieve chapter links: {e}", exc_info=True)
            raise e
    
    def get_chapter_content(self, url: str) -> dict:
        # Fetch the chapter page
        response = self._session.get(url, timeout=10)
        
        if response.status_code == 429:
            logger.warning(f"[{self.class_name}] Rate limited (429) on {url}. Retrying after sleep...")
            time.sleep(2)
            response = self._session.get(url, timeout=10)

        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')

        # 1. Select the title and the main container
        # Note: Assuming self._selectors['chap_content'] is '.chapter-content'
        chapter_title = soup.select_one(self._selectors.get('chap_title', 'h1'))
        content_div = soup.select_one(self._selectors.get('chap_content', '.chapter-content'))

        if not content_div:
            # Fallback to general WordPress content div if primary fails
            content_div = soup.find('div', class_='entry-content')
            if content_div:
                logger.debug(f"[{self.class_name}] Primary content selector failed, used fallback for {url}")
            else:
                logger.error(f"[{self.class_name}] Content div not found for {url}")
                return {'chapter_title': 'Error', 'main_content': None}

        # 2. CLEANUP: Novels-BR specific junk removal
        # Decompose Ads and hidden SEO elements to keep only the story text
        
        # Remove Google Ads containers
        for ads in content_div.select('.google-auto-placed, ins, script'):
            ads.decompose()
            
        # Remove the hidden SEO link usually found in the first/second <p>
        # Pattern: <p style="display: none">Leia em https://...</p>
        for hidden_p in content_div.find_all('p', style=lambda s: s and 'display: none' in s):
            hidden_p.decompose()

        # Remove the internal link anchor that duplicates the title
        # Pattern: <a class="page-link" rel="nofollow" ...>
        for internal_link in content_div.find_all('a', class_='page-link'):
            internal_link.decompose()

        # 3. Return cleaned data
        return {
            'chapter_title': chapter_title.get_text(strip=True) if chapter_title else "Untitled",
            'main_content': content_div 
        }
    
if __name__ == "__main__":
    # 1. Setup parameters for testing
    # Replace this URL with a valid novel URL from Novels-BR
    test_url = "https://novels-br.com/novels/reincarnation-of-the-strongest-sword-god/"
    start_chap = 1
    quantity = 20
    
    # 2. Instantiate the class
    # Arguments: main_url, start_chapter, chapters_quantity, output_folder (dummy for test)
    book = MyNovelsBrBook(test_url, quantity, start_chap)

    print("\n" + "="*50)
    print("TESTING: get_book_metadata")
    print("="*50)
    try:
        metadata = book.get_book_metadata()
        print(f"Title:  {metadata['book_title']}")
        print(f"Author: {metadata['book_author']}")
        print(f"Cover:  {metadata['book_cover_link']}")
        # print(f"Description: {metadata['book_description'].get_text()[:100]}...")
    except Exception as e:
        print(f"Metadata Test Failed: {e}")

    print("\n" + "="*50)
    print("TESTING: get_chapters_link")
    print("="*50)
    links = []
    try:
        links = book.get_chapters_link()
        for idx, link in enumerate(links, 1):
            print(f"{idx}. {link}")
    except Exception as e:
        print(f"Chapter Links Test Failed: {e}")

    if links:
        print("\n" + "="*50)
        print(f"TESTING: get_chapter_content (First link)")
        print("="*50)
        try:
            content = book.get_chapter_content(links[0])
            print(f"Chapter Title: {content['chapter_title']}")
            
            # Show the first few cleaned paragraphs
            paragraphs = content['main_content'].find_all('p')
            print("\nContent Preview (First 3 clean paragraphs):")
            for p in paragraphs[:3]:
                text = p.get_text(strip=True)
                if text:
                    print(f"- {text}")
        except Exception as e:
            print(f"Chapter Content Test Failed: {e}")
