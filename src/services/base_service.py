import requests
from abc import ABC, abstractmethod


class BaseService(ABC):
    """
    Abstract base class for all novel services.
    Provides shared networking (session/headers) and defines the service contract.
    """
    
    def __init__(self):
        # Shared session ensures all requests from a service instance 
        # use the same headers and connection pool.
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })

    @abstractmethod
    def search(self, query: str) -> list:
        """
        Search for novels. Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def get_book_instance(self, url: str, qty: int, start: int):
        """
        Returns an instance of a Book scraper (MyBook subclass).
        Must be implemented by subclasses to return their specific handler.
        """
        pass
