from bs4 import BeautifulSoup
from src.services.base_service import BaseService
from src.classes.centralnovel_book import MyCentralNovelBook
from src.utils.logger import logger

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
        
        logger.info(f"[{self.service_name}] Searching for novels with query: '{query}'")
        
        try:
            # Realizando a requisição via sessão herdada
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Buscando o container dos artigos
            articles = soup.find_all('article', class_='maindet')
            
            if not articles:
                logger.warning(f"[{self.service_name}] No articles found for query: '{query}'. The site layout might have changed or no results exist.")
                return []

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
            
            logger.info(f"[{self.service_name}] Found {len(results)} results for '{query}'")
            return results
            
        except Exception as e:
            # exc_info=True salvará o rastro completo do erro no arquivo app.log
            logger.error(f"[{self.service_name}] Search error for query '{query}': {str(e)}", exc_info=True)
            return []

    def get_book_instance(self, url: str, qty: int, start: int) -> MyCentralNovelBook:
        """
        Returns a specialized book instance for Central Novel.
        """
        logger.info(f"[{self.service_name}] Instantiating MyCentralNovelBook for URL: {url}")
        return MyCentralNovelBook(url, qty, start)
    