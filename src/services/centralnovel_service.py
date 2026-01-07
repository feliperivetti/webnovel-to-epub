import random
import time
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
        Performs a novel search using an advanced session warm-up technique 
        and stealth headers to bypass 403 Forbidden errors on hosted environments.
        """
        search_url = f"{self.BASE_URL}/"
        params = {'s': query.strip()}
        
        # Enhanced stealth headers to mimic a real Chrome 120+ browser
        # Note: 'User-Agent' is handled by cloudscraper, but we ensure consistency here
        headers = {
            "Referer": f"{self.BASE_URL}/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br", # Brotli is essential for stealth
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }
        
        try:
            # 1. ADVANCED SESSION WARM-UP
            # If the hosted environment is flagged, clearing cookies can sometimes help start fresh
            if not self.session.cookies:
                logger.info(f"[{self.service_name}] Initializing fresh session warm-up for Central Novel...")
                # First visit: Just the root domain to get security cookies
                warmup_response = self.session.get(self.BASE_URL, timeout=10)
                warmup_response.raise_for_status()
                
                # Human-like random delay before searching
                delay = random.uniform(2.0, 4.5)
                logger.debug(f"[{self.service_name}] Warm-up successful. Waiting {delay:.2f}s before search.")
                time.sleep(delay)

            logger.info(f"[{self.service_name}] Executing search request for: '{query}'")

            # 2. SEARCH REQUEST WITH STEALTH HEADERS
            response = self.session.get(
                search_url, 
                params=params, 
                headers=headers, 
                timeout=15
            )

            # Fallback for 403 on hosted environment
            if response.status_code == 403:
                logger.error(f"[{self.service_name}] 403 Forbidden detected on Render. Cloudflare may have flagged the JA3 fingerprint.")
                return []

            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Identify WordPress 'Madara' or 'Maindet' article containers
            articles = soup.find_all('article', class_='maindet')
            
            if not articles:
                logger.warning(f"[{self.service_name}] No articles found for: '{query}'. Site may have blocked the response content.")
                return []

            for article in articles:
                title_tag = article.find('h2')
                link_tag = title_tag.find('a') if title_tag else None
                img_tag = article.find('img')
                chapter_span = article.find('span', class_='nchapter')

                if title_tag and link_tag:
                    # data-src is preferred due to lazy loading patterns
                    cover_url = img_tag.get('data-src') or img_tag.get('src') if img_tag else None
                    
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "url": link_tag.get('href'),
                        "cover": cover_url,
                        "chapters_count": chapter_span.get_text(strip=True) if chapter_span else "N/A"
                    })
            
            logger.info(f"[{self.service_name}] Successfully retrieved {len(results)} results.")
            return results
            
        except Exception as e:
            logger.error(f"[{self.service_name}] Search process failed: {str(e)}", exc_info=True)
            return []

    def get_book_instance(self, url: str, qty: int, start: int) -> MyCentralNovelBook:
        """
        Returns a specialized book instance for Central Novel.
        """
        logger.info(f"[{self.service_name}] Creating book instance for: {url}")
        return MyCentralNovelBook(url, qty, start)
    