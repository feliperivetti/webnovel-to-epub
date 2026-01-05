from bs4 import BeautifulSoup
from src.services.base_service import BaseService
from src.classes.pandanovel_book import MyPandaNovelBook


class PandaNovelService(BaseService):
    SEARCH_URL = "https://pandanovel.co/ajax/searchLive"
    BASE_URL = "https://pandanovel.co"

    def __init__(self):
        super().__init__()

    def search(self, query: str) -> list:
        params = {"inputContent": query.strip()}
        
        try:
            # Now using self.session from BaseService
            response = self.session.get(
                self.SEARCH_URL, 
                params=params, 
                timeout=10
            )
            response.raise_for_status()

            raw_html = response.text.replace('\\/', '/').replace('\\"', '"')
            soup = BeautifulSoup(raw_html, 'html.parser')
            results = []
            
            items = soup.find_all("li")
            for item in items:
                link_tag = item.find("a")
                if not link_tag: continue

                path = link_tag.get("href", "").strip('"')
                full_url = path if path.startswith('http') else f"{self.BASE_URL}{path}"
                img_tag = item.find("img")
                cover_url = img_tag.get("src", "").strip('"') if img_tag else None
                
                title_tag = item.find("h4")
                chapters_tag = item.find("span")

                results.append({
                    "title": title_tag.get_text(strip=True) if title_tag else "Unknown",
                    "url": full_url,
                    "cover": cover_url if cover_url and cover_url.startswith('http') else f"{self.BASE_URL}{cover_url}",
                    "chapters_count": chapters_tag.get_text(strip=True) if chapters_tag else "N/A"
                })
            
            return results
        except Exception as e:
            print(f"❌ PandaNovel Search Error: {e}")
            return []

    def get_book_instance(self, url: str, qty: int, start: int) -> MyPandaNovelBook:
        return MyPandaNovelBook(url, qty, start)
    