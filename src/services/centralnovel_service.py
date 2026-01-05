from bs4 import BeautifulSoup
from src.services.base_service import BaseService
from src.classes.centralnovel_book import MyCentralNovelBook


class CentralNovelService(BaseService):
    """
    Service responsible for interacting with Central Novel.
    Inherits from BaseService to use shared session and headers.
    """
    BASE_URL = "https://centralnovel.com"

    def __init__(self):
        super().__init__()

    def search(self, query: str) -> list:
        """
        Searches for novels using the standard WordPress query.
        Uses the inherited session from BaseService.
        """
        search_url = f"{self.BASE_URL}/"
        params = {'s': query.strip()}
        
        try:
            # Using self.session instead of requests.get
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            # Specific container for this theme's search results
            articles = soup.find_all('article', class_='maindet')
            
            for article in articles:
                title_tag = article.find('h2')
                link_tag = title_tag.find('a') if title_tag else None
                img_tag = article.find('img')
                chapter_span = article.find('span', class_='nchapter')

                if title_tag and link_tag:
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "url": link_tag.get('href'),
                        "cover": img_tag.get('src') if img_tag else None,
                        "chapters_count": chapter_span.get_text(strip=True) if chapter_span else "N/A"
                    })
            return results
            
        except Exception as e:
            print(f"❌ Central Novel Search Error: {e}")
            return []

    def get_book_instance(self, url: str, qty: int, start: int) -> MyCentralNovelBook:
        """
        Returns a specialized book instance for Central Novel.
        """
        return MyCentralNovelBook(url, qty, start)
