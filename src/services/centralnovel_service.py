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
        Performs a novel search using a session warm-up technique to bypass 403 Forbidden errors.
        It first visits the Home Page to establish cookies and pass initial security checks.
        """
        import random
        import time

        search_url = f"{self.BASE_URL}/"
        params = {'s': query.strip()}
        
        # Comprehensive headers to simulate a real web browser
        headers = {
            "Referer": f"{self.BASE_URL}/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        try:
            # 1. SESSION WARM-UP
            # Check if session cookies are empty. If so, "step" on the home page first.
            if not self.session.cookies:
                logger.info(f"[{self.service_name}] New session detected. Performing warm-up on Home Page...")
                warmup_response = self.session.get(self.BASE_URL, timeout=10)
                warmup_response.raise_for_status()
                
                # Human-like random delay (between 1.5 to 3.5 seconds)
                time.sleep(random.uniform(1.5, 3.5))

            logger.info(f"[{self.service_name}] Searching for novels with query: '{query}'")

            # 2. ACTUAL SEARCH REQUEST
            # The session now carries valid cookies and the Referer simulates a legitimate origin
            response = self.session.get(
                search_url, 
                params=params, 
                headers=headers, 
                timeout=15
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Locate article containers (Commonly used in WordPress/Madara themes)
            articles = soup.find_all('article', class_='maindet')
            
            if not articles:
                logger.warning(f"[{self.service_name}] No articles found for query: '{query}'. Layout might have changed or no results exist.")
                return []

            for article in articles:
                title_tag = article.find('h2')
                link_tag = title_tag.find('a') if title_tag else None
                img_tag = article.find('img')
                chapter_span = article.find('span', class_='nchapter')

                if title_tag and link_tag:
                    # Check for data-src first (common in lazy-loading setups), fallback to src
                    cover_url = img_tag.get('data-src') or img_tag.get('src') if img_tag else None
                    
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "url": link_tag.get('href'),
                        "cover": cover_url,
                        "chapters_count": chapter_span.get_text(strip=True) if chapter_span else "N/A"
                    })
            
            logger.info(f"[{self.service_name}] Successfully found {len(results)} results for '{query}'")
            return results
            
        except Exception as e:
            # Error logging with traceback information
            logger.error(f"[{self.service_name}] Search failed for query '{query}': {str(e)}", exc_info=True)
            return []

    def get_book_instance(self, url: str, qty: int, start: int) -> MyCentralNovelBook:
        """
        Returns a specialized book instance for Central Novel.
        """
        logger.info(f"[{self.service_name}] Instantiating MyCentralNovelBook for URL: {url}")
        return MyCentralNovelBook(url, qty, start)
    