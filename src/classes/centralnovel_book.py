import re
from bs4 import BeautifulSoup
from .base_book import MyBook

class MyCentralNovelBook(MyBook):
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
        # IMPORTANTE: Usando self._session em vez de requests
        response = self._session.get(self._main_url, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')

        header = soup.select_one(self._selectors['meta_header'])
        if not header:
            raise ValueError("Could not find the book header. Check the URL.")

        info_content = header.select_one(self._selectors['meta_info'])
        author_spans = info_content.find_all('span') if info_content else []
        author_text = author_spans[2].get_text(strip=True) if len(author_spans) > 2 else "Unknown Author"

        description_div = soup.select_one(self._selectors['meta_description'])

        return {
            'book_title': header.select_one(self._selectors['meta_title']).get_text(strip=True),
            'book_author': author_text,
            'book_description': description_div or "No description available.",
            'book_cover_link': header.find('img').get('src') if header.find('img') else None
        }

    def get_chapters_link(self) -> list:
        # IMPORTANTE: Usando self._session
        response = self._session.get(self._main_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        all_eplisters = soup.select(self._selectors['meta_chapter_list_all'])
        total_available = sum(len(block.find_all('a')) for block in all_eplisters)

        if total_available == 0:
            raise ValueError("No chapters found.")

        raw_slug = self._main_url.strip('/').split('/')[-1]
        clean_slug = re.sub(r'-\d+$', '', raw_slug)
        
        chapter_urls = []
        end_chapter = min(self._start_chapter + self._chapters_quantity - 1, total_available)
        
        for i in range(self._start_chapter, end_chapter + 1):
            url = f"https://centralnovel.com/{clean_slug}-capitulo-{i}/"
            chapter_urls.append(url)
            
        return chapter_urls

    def get_chapter_content(self, url: str) -> dict:
        # IMPORTANTE: Usando self._session
        response = self._session.get(url, timeout=10)
        
        if response.status_code == 429:
            print(f"⚠️ Warning: Being rate limited on {url}. Waiting 2 seconds...")
            import time
            time.sleep(2)
            response = self._session.get(url, timeout=10)

        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        chapter_title = soup.select_one(self._selectors['chap_title'])
        content_div = soup.select_one(self._selectors['chap_content'])

        if not content_div:
            content_div = soup.find('div', class_='entry-content')

        # Cleanup
        if content_div:
            first_p = content_div.find('p')
            if first_p and "Inteligência Artificial" in first_p.get_text():
                first_p.decompose()

        return {
            'chapter_title': chapter_title.get_text(strip=True) if chapter_title else "Untitled",
            'main_content': content_div # Retorna a tag para o decode_contents da base
        }