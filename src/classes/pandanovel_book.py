from bs4 import BeautifulSoup
from .base_book import MyBook


class MyPandaNovelBook(MyBook):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        # SELECTORS CENTRALIZATION (Keeping your original selectors)
        self._selectors = {
            # Metadata selectors
            'meta_header': ('div', {'class': 'header-body container'}),
            'meta_info': ('div', {'class': 'novel-info'}),
            'meta_title': ('h1', {}),
            'meta_author': ('div', {'class': 'author'}),
            'meta_description': ('div', {'class': 'summary'}),
            'meta_total_chapters': ('div', {'class': 'header-stats'}),
            
            # Chapter content selectors
            'chap_title': ('span', {'class': 'chapter-title'}),
            'chap_content': ('div', {'id': 'content'})
        }

    def get_book_metadata(self) -> dict:
        """Extracts novel metadata using the shared session."""
        # Changed to self._session and removed self._headers
        response = self._session.get(self._main_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        header = soup.find(*self._selectors['meta_header'])
        if not header:
            raise ValueError("Could not find the novel header. The site layout might have changed.")

        info = header.find(*self._selectors['meta_info'])
        img_tag = header.find('img')
        cover_link = img_tag.get('data-src') or img_tag.get('src') if img_tag else None

        # Keeping your specific logic for titles and authors
        return {
            'book_title': info.find(*self._selectors['meta_title']).get_text(strip=True) if info else "Unknown Title",
            'book_author': info.find(*self._selectors['meta_author']).find('a')['title'] if info else "Unknown Author",
            'book_description': soup.find(*self._selectors['meta_description']) or "No description available.",
            'book_cover_link': cover_link
        }

    def get_chapters_link(self) -> list:
        """Generates chapter URLs based on the slug pattern."""
        chapter_urls = []
        slug = self._main_url.split('/')[-1]
        
        if self._start_chapter < 1:
            raise ValueError("Start chapter must be 1 or greater.")

        for i in range(self._chapters_quantity):
            current_chapter_num = i + self._start_chapter
            # Keeping your specific URL pattern
            url = f'https://novelfire.noveljk.org/book/{slug}/chapter-{current_chapter_num}'
            chapter_urls.append(url)
            
        return chapter_urls

    def get_chapter_content(self, url: str) -> dict:
        """Scrapes content from a specific chapter URL using the shared session."""
        # Changed to self._session
        response = self._session.get(url, timeout=10)
        
        if response.status_code == 404:
            raise ValueError(f"Chapter at URL {url} was not found (404).")
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        chapter_title_tag = soup.find(*self._selectors['chap_title'])
        main_content_div = soup.find(*self._selectors['chap_content'])

        return {    
            'chapter_title': chapter_title_tag.get_text(strip=True) if chapter_title_tag else "Untitled Chapter",
            'main_content': main_content_div # Returns the Tag object for the base class
        }