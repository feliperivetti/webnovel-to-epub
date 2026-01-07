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
    
    # Professional Real Browser User-Agents (Chrome 120+)
    REAL_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    ]

    def __init__(self):
        super().__init__()
        # Ensure the session starts with a clean Slate mimicking a Windows Desktop
        self.session.browser = {
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }

    def search(self, query: str) -> list:
        """
        Performs a novel search using session warm-up, randomized UAs, 
        and header sanitization to bypass cloudflare blocks on hosted environments.
        """
        search_url = f"{self.BASE_URL}/"
        params = {'s': query.strip()}
        current_ua = random.choice(self.REAL_USER_AGENTS)
        
        # Comprehensive headers mimicking a modern browser
        headers = {
            "User-Agent": current_ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": f"{self.BASE_URL}/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }

        # SANITIZATION: Remove any headers that identify the Render/AWS infrastructure
        # This is crucial for avoiding 403 blocks on PaaS.
        for header in ['X-Amzn-Trace-Id', 'Via', 'X-Forwarded-For', 'X-Real-Ip']:
            self.session.headers.pop(header, None)
        
        try:
            # 1. FORCED SESSION WARM-UP (Crucial for establishing cookies)
            # Even if cookies exist, a quick hit to home with the specific UA helps
            logger.info(f"[{self.service_name}] Warming up session for: {current_ua[:30]}...")
            self.session.get(self.BASE_URL, headers={"User-Agent": current_ua}, timeout=15)
            
            # Random wait to simulate human reading time
            time.sleep(random.uniform(2.5, 5.0))

            logger.info(f"[{self.service_name}] Executing search for: '{query}'")

            # 2. SEARCH REQUEST
            response = self.session.get(
                search_url, 
                params=params, 
                headers=headers, 
                timeout=20
            )

            if response.status_code == 403:
                logger.error(f"[{self.service_name}] 403 Forbidden - Fingerprint rejected by Central Novel.")
                return []

            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Select articles from the search results
            articles = soup.find_all('article', class_='maindet')
            
            if not articles:
                logger.warning(f"[{self.service_name}] No results found for '{query}'.")
                return []

            for article in articles:
                title_tag = article.find('h2')
                link_tag = title_tag.find('a') if title_tag else None
                img_tag = article.find('img')
                chapter_span = article.find('span', class_='nchapter')

                if title_tag and link_tag:
                    # Handle lazy-loaded images (common in WordPress)
                    cover_url = img_tag.get('data-src') or img_tag.get('src') if img_tag else None
                    
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "url": link_tag.get('href'),
                        "cover": cover_url,
                        "chapters_count": chapter_span.get_text(strip=True) if chapter_span else "N/A"
                    })
            
            logger.info(f"[{self.service_name}] Found {len(results)} results.")
            return results
            
        except Exception as e:
            logger.error(f"[{self.service_name}] Search failed: {str(e)}", exc_info=True)
            return []

    def get_book_instance(self, url: str, qty: int, start: int) -> MyCentralNovelBook:
        """
        Returns a specialized book instance for Central Novel.
        """
        logger.info(f"[{self.service_name}] Instantiating book for URL: {url}")
        return MyCentralNovelBook(url, qty, start)