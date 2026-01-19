from bs4 import BeautifulSoup
from src.services.base_service import BaseService
from src.classes.pandanovel_book import MyPandaNovelBook
from src.utils.logger import logger

class PandaNovelService(BaseService):
    """
    Service responsible for interacting with PandaNovel.
    Handles AJAX-based live search and book instantiation.
    """
    SEARCH_URL = "https://pandanovel.co/ajax/searchLive"
    BASE_URL = "https://pandanovel.co"

    def __init__(self):
        super().__init__()

    def search(self, query: str) -> list:
        """
        Searches for novels using PandaNovel's AJAX endpoint.
        """
        params = {"inputContent": query.strip()}
        logger.info(f"[{self.service_name}] Starting AJAX search for: '{query}'")
        
        try:
            # Requisição usando a sessão da BaseService
            response = self._session.get(
                self.SEARCH_URL, 
                params=params, 
                timeout=10
            )
            response.raise_for_status()

            # Limpeza básica de caracteres escapados comuns em respostas AJAX
            raw_html = response.text.replace('\\/', '/').replace('\\"', '"')
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            results = []
            items = soup.find_all("li")
            
            if not items:
                logger.warning(f"[{self.service_name}] No results found for '{query}'. Site might have changed its AJAX response format.")
                return []

            for item in items:
                link_tag = item.find("a")
                if not link_tag: 
                    continue

                path = link_tag.get("href", "").strip('"')
                full_url = path if path.startswith('http') else f"{self.BASE_URL}{path}"
                
                img_tag = item.find("img")
                cover_url = img_tag.get("src", "").strip('"') if img_tag else None
                if cover_url and not cover_url.startswith('http'):
                    cover_url = f"{self.BASE_URL}{cover_url}"
                
                title_tag = item.find("h4")
                chapters_tag = item.find("span")

                results.append({
                    "title": title_tag.get_text(strip=True) if title_tag else "Unknown",
                    "url": full_url,
                    "cover": cover_url,
                    "chapters_count": chapters_tag.get_text(strip=True) if chapters_tag else "N/A"
                })
            
            logger.info(f"[{self.service_name}] Search successful. Found {len(results)} items.")
            return results

        except Exception as e:
            # O exc_info=True captura o erro de parsing ou de rede detalhadamente
            logger.error(f"[{self.service_name}] Error during AJAX search for '{query}': {str(e)}", exc_info=True)
            return []

    def get_book_instance(self, url: str, qty: int, start: int) -> MyPandaNovelBook:
        """
        Returns a specialized book instance for PandaNovel.
        """
        logger.info(f"[{self.service_name}] Creating MyPandaNovelBook instance for: {url}")
        return MyPandaNovelBook(url, qty, start)
    