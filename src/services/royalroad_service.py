from bs4 import BeautifulSoup
from src.services.base_service import BaseService
from src.classes.royalroad_book import MyRoyalRoadBook


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
        
        try:
            # Using self.session from BaseService instead of requests.get
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            items = soup.select('div.fiction-list-item')
            
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
            
            return results
        except Exception as e:
            print(f"❌ Royal Road Search Error: {e}")
            return []

    def get_book_instance(self, url: str, qty: int, start: int) -> MyRoyalRoadBook:
        """
        Implementation of the abstract factory method for Royal Road.
        """
        return MyRoyalRoadBook(url, qty, start)
