from typing import Type, Dict, Any, Optional

class ScraperRegistry:
    _registry: Dict[str, Type] = {}

    @classmethod
    def register(cls, *domains: str):
        """
        Decorator to register a service class for one or multiple domains.
        Usage:
            @ScraperRegistry.register("domain.com", "another-domain.com")
            class MyService(BaseService):
                ...
        """
        def wrapper(service_cls: Type):
            for domain in domains:
                # Normalize domain to lowercase for consistent lookup
                cls._registry[domain.lower()] = service_cls
            return service_cls
        return wrapper

    @classmethod
    def get_service(cls, url: str) -> Optional[Type]:
        """
        Finds the correct service class for a given URL by checking if any registered 
        domain is a substring of the URL.
        """
        normalized_url = url.lower()
        for domain, service_cls in cls._registry.items():
            if domain in normalized_url:
                return service_cls
        return None

    @classmethod
    def get_registered_domains(cls) -> list[str]:
        return list(cls._registry.keys())
