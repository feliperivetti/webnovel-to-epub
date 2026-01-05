from bs4 import BeautifulSoup
from .base_book import MyBook

class MyRoyalRoadBook(MyBook):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        # SELECTORS CENTRALIZATION (Keeping your original tuples)
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
        # Changed to self._session and removed manual headers
        response = self._session.get(self._main_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        header = soup.find(*self._selectors['meta_header'])
        if not header:
            raise ValueError("Could not find the book header. The site layout might have changed.")

        # Cover image extraction
        img_tag = header.find('img')
        cover_link = img_tag.get('src') if img_tag else None

        return {
            'book_title': header.find(*self._selectors['meta_title']).get_text(strip=True),
            'book_author': header.find(*self._selectors['meta_author']).get_text(strip=True),
            'book_description': soup.find(*self._selectors['meta_description']) or "No description available.",
            'book_cover_link': cover_link
        }

    def get_chapters_link(self) -> list:
        """Retrieves real chapter links and validates the requested range."""
        # Changed to self._session
        response = self._session.get(self._main_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get all rows from the chapters table
        all_rows = soup.find_all(*self._selectors['chap_table_rows'])
        total_available = len(all_rows)

        # VALIDATION
        if self._start_chapter > total_available:
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
                # Prepending domain to relative links
                chapter_urls.append(f'https://www.royalroad.com{relative_url}')
        
        return chapter_urls

    def get_chapter_content(self, url: str) -> dict:
        """Scrapes the title and body text of a specific chapter."""
        # Changed to self._session
        response = self._session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Unpacking the tuple (tag, attributes) for the find method
        chapter_title_tag = soup.find(*self._selectors['chap_title_tag'])
        content_div = soup.find(*self._selectors['chap_content'])

        # print(f"Content div: {content_div}")

        return {    
            'chapter_title': chapter_title_tag.get_text(strip=True) if chapter_title_tag else "Untitled Chapter",
            'main_content': content_div # Returns the Tag object for the base class assembly
        }