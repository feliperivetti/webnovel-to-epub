import os
import cloudscraper
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from src.utils.logger import logger


class BaseService(ABC):
    """
    Abstract base class for all novel services.
    Provides shared networking (session/headers) and defines the service contract.
    """
    
    def __init__(self):
        # Load variables from .env file into os.environ
        load_dotenv()

        # Child class name for precise logging (e.g., RoyalRoadService)
        self.service_name = self.__class__.__name__
        
        # Shared session using cloudscraper to bypass Cloudflare/Wordfence.
        self._session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        # Proxy configuration via Environment Variable
        proxy_url = os.environ.get("PROXY_URL")
        if proxy_url:
            self._session.proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            logger.info(f"[{self.service_name}] Proxy enabled for search service.")
        else:
            logger.warning(f"[{self.service_name}] No proxy detected for search. Using direct IP.")
        
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
