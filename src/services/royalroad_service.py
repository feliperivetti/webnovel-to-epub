from bs4 import BeautifulSoup
from src.services.base_service import BaseService
from src.classes.royalroad_book import MyRoyalRoadBook
from src.utils.logger import logger

class RoyalRoadService(BaseService):
    """
    Service responsible for interacting with Royal Road website.
    Inherits from BaseService to use shared networking and session.
    """
    BASE_URL = "https://www.royalroad.com"

    def __init__(self):
        super().__init__()

    def search(self, query: str) -> list:
        """
        Searches for novels on Royal Road using the inherited session.
        Returns: list of dicts {'title': str, 'url': str, 'cover': str, 'chapters_count': str}
        """
        search_url = f"{self.BASE_URL}/fictions/search"
        params = {'title': query.strip()}
        
        logger.info(f"[{self.service_name}] Searching for: '{query}'")
        
        try:
            # Requisição via sessão compartilhada
            response = self._session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Selector para os itens da lista
            items = soup.select('div.fiction-list-item')
            
            if not items:
                logger.warning(f"[{self.service_name}] No results found for '{query}'. This might be a search with no matches or a change in the site's CSS selectors.")
                return []
            
            for item in items:
                # 1. Title and URL extraction
                title_tag = item.select_one('h2.fiction-title a')
                
                # 2. Cover image extraction
                img_tag = item.find('img')
                cover_url = None
                if img_tag:
                    cover_url = img_tag.get('src') or img_tag.get('data-src')

                # 3. Chapter count extraction (Logic: find list icon 'fa-list')
                chapters_count = "N/A"
                stats_div = item.select_one('.stats')
                if stats_div:
                    chapter_icon = stats_div.find('i', class_='fa-list')
                    if chapter_icon:
                        count_span = chapter_icon.find_next('span')
                        if count_span:
                            chapters_count = count_span.get_text(strip=True)

                if title_tag:
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "url": f"{self.BASE_URL}{title_tag.get('href')}",
                        "cover": cover_url,
                        "chapters_count": chapters_count
                    })
            
            logger.info(f"[{self.service_name}] Search successful. Found {len(results)} items.")
            return results

        except Exception as e:
            # exc_info=True garante que o Traceback completo apareça no log de erro
            logger.error(f"[{self.service_name}] Search error for query '{query}': {str(e)}", exc_info=True)
            return []

    def get_book_instance(self, url: str, qty: int, start: int) -> MyRoyalRoadBook:
        """
        Implementation of the abstract factory method for Royal Road.
        """
        logger.info(f"[{self.service_name}] Creating MyRoyalRoadBook instance for URL: {url}")
        return MyRoyalRoadBook(url, qty, start)
    