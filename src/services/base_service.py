import cloudscraper
from abc import ABC, abstractmethod
from src.utils.logger import logger


class BaseService(ABC):
    """
    Abstract base class for all novel services.
    Provides shared networking (session/headers) and defines the service contract.
    """
    
    def __init__(self):
        # Child class name for precise logging (e.g., RoyalRoadService)
        self.service_name = self.__class__.__name__
        
        # Shared session using cloudscraper to bypass Cloudflare/Wordfence.
        # It ensures all requests from a service instance use the same headers.
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        
        # Depuration log to confirm the service was created successfully
        logger.debug(f"[{self.service_name}] Cloudscraper session initialized.")

    @abstractmethod
    def search(self, query: str) -> list:
        """
        Search for novels. Must be implemented by subclasses.
        """
        logger.info(f"[{self.service_name}] Starting search for query: '{query}'")
        pass

    @abstractmethod
    def get_book_instance(self, url: str, qty: int, start: int):
        """
        Returns an instance of a Book scraper (MyBook subclass).
        Must be implemented by subclasses to return their specific handler.
        """
        logger.info(f"[{self.service_name}] Creating book instance for URL: {url}")
        pass
