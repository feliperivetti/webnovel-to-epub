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
    
    # Real Browser User-Agents to bypass fingerprinting
    REAL_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]

    def __init__(self):
        super().__init__()
        # Force the cloudscraper to use a specific browser configuration
        # This helps in aligning the TLS fingerprint with the User-Agent
        self.session.browser = {
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }

    def search(self, query: str) -> list:
        """
        Performs a novel search using an advanced session warm-up technique,
        randomized User-Agents, and stealth headers to bypass 403 Forbidden errors.
        """
        search_url = f"{self.BASE_URL}/"
        params = {'s': query.strip()}
        
        # Select a random real User-Agent for this specific request
        current_ua = random.choice(self.REAL_USER_AGENTS)
        
        # Enhanced stealth headers to mimic a real Chrome browser
        headers = {
            "User-Agent": current_ua,
            "Referer": f"{self.BASE_URL}/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
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
        
        try:
            # 1. SESSION WARM-UP
            # Accessing the root domain first helps establish valid cookies and bypass Cloudflare
            if not self.session.cookies:
                logger.info(f"[{self.service_name}] Initializing fresh session warm-up for Central Novel...")
                warmup_response = self.session.get(self.BASE_URL, headers={"User-Agent": current_ua}, timeout=15)
                warmup_response.raise_for_status()
                
                # Human-like random delay
                delay = random.uniform(2.0, 4.0)
                logger.debug(f"[{self.service_name}] Warm-up successful. Waiting {delay:.2f}s before search.")
                time.sleep(delay)

            logger.info(f"[{self.service_name}] Executing search request for: '{query}'")

            # 2. ACTUAL SEARCH REQUEST
            response = self.session.get(
                search_url, 
                params=params, 
                headers=headers, 
                timeout=20
            )

            # Check for Cloudflare/Server block
            if response.status_code == 403:
                logger.error(f"[{self.service_name}] 403 Forbidden. Target site is blocking the Render environment.")
                return []

            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Identify article containers (Standard WordPress/Madara theme structure)
            articles = soup.find_all('article', class_='maindet')
            
            if not articles:
                logger.warning(f"[{self.service_name}] No articles found for: '{query}'. Site may have hidden the content.")
                return []

            for article in articles:
                title_tag = article.find('h2')
                link_tag = title_tag.find('a') if title_tag else None
                img_tag = article.find('img')
                chapter_span = article.find('span', class_='nchapter')

                if title_tag and link_tag:
                    # Preference for data-src due to lazy loading patterns
                    cover_url = img_tag.get('data-src') or img_tag.get('src') if img_tag else None
                    
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "url": link_tag.get('href'),
                        "cover": cover_url,
                        "chapters_count": chapter_span.get_text(strip=True) if chapter_span else "N/A"
                    })
            
            logger.info(f"[{self.service_name}] Successfully found {len(results)} results.")
            return results
            
        except Exception as e:
            logger.error(f"[{self.service_name}] Search failed: {str(e)}", exc_info=True)
            return []

    def get_book_instance(self, url: str, qty: int, start: int) -> MyCentralNovelBook:
        """
        Returns a specialized book instance for Central Novel.
        """
        logger.info(f"[{self.service_name}] Creating book instance for: {url}")
        return MyCentralNovelBook(url, qty, start)
    