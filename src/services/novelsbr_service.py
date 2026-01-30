import re
import sys
import os
from bs4 import BeautifulSoup
from src.services.base_service import BaseService
from src.services.registry import ScraperRegistry
from src.classes.novelsbr_book import MyNovelsBrBook
from src.utils.logger import logger

@ScraperRegistry.register("novels-br.com")
class NovelsBrService(BaseService):
    """
    Service responsible for interacting with Novels-BR.
    Handles HTML-based search results and book instantiation.
    """
    SEARCH_URL = "https://novels-br.com/novels"
    BASE_URL = "https://novels-br.com"

    def __init__(self):
        super().__init__()

    def search(self, query: str) -> list:
        """
        Searches for novels using the 'simplifiedField' parameter.
        Returns a list of dictionaries containing novel metadata.
        """
        params = {"simplifiedField": query.strip()}
        logger.info(f"[{self.service_name}] Starting search for: '{query}'")
        
        try:
            # Request using the session from BaseService
            response = self._session.get(
                self.SEARCH_URL, 
                params=params, 
                timeout=10
            )
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # Targeting the novel cards based on your HTML structure:
            # section#content -> .content-novel -> .container -> .row -> .col-sm-12
            items = soup.select('div.content-novel div.row.g-4 div.col-sm-12')

            if not items:
                logger.warning(f"[{self.service_name}] No results found for '{query}'. The site structure might have changed.")
                return []

            for item in items:
                # 1. Extract Title (h2.card-title)
                title_tag = item.select_one('h2.card-title')
                if not title_tag:
                    continue
                
                title = title_tag.get_text(strip=True)

                # 2. Extract Link (a.custom-link containing the "Ler Novel" button)
                link_tag = item.select_one('a.custom-link')
                path = link_tag.get("href", "") if link_tag else ""
                full_url = f"{self.BASE_URL}{path}" if path.startswith('/') else path

                # 3. Extract Cover Image (img.custom-card-img)
                img_tag = item.select_one('img.custom-card-img')
                cover_url = img_tag.get("src", "") if img_tag else None

                # 4. Extract Author (h3.card-text small)
                author_tag = item.select_one('h3.card-text small')
                author = author_tag.get_text(strip=True) if author_tag else "Unknown"

                results.append({
                    "title": title,
                    "url": full_url,
                    "cover": cover_url,
                    "author": author,
                    "chapters_count": "N/A" # Search page usually doesn't show the count
                })
            
            logger.info(f"[{self.service_name}] Search successful. Found {len(results)} items.")
            return results

        except Exception as e:
            logger.error(f"[{self.service_name}] Error during search for '{query}': {str(e)}", exc_info=True)
            return []

    def get_book_instance(self, url: str, qty: int, start: int) -> MyNovelsBrBook:
        """
        Returns a specialized MyNovelsBrBook instance.
        """
        logger.info(f"[{self.service_name}] Creating MyNovelsBrBook instance for: {url}")
        # Standard order: url, quantity, start
        return MyNovelsBrBook(url, qty, start)

if __name__ == "__main__":
    # Internal test block to verify the search parser
    # Add root to sys.path to handle absolute imports when running directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    
    service = NovelsBrService()
    test_query = "sombras"
    
    print(f"\n[TEST] Searching for: '{test_query}'...")
    search_results = service.search(test_query)
    
    if not search_results:
        print("No results found. Verify if selectors match the current site HTML.")
    else:
        for i, res in enumerate(search_results, 1):
            print(f"\n--- Result #{i} ---")
            print(f"Title:  {res['title']}")
            print(f"Author: {res['author']}")
            print(f"URL:    {res['url']}")
            print(f"Cover:  {res['cover']}")