from typing import Type, Dict, Any, Optional
import importlib
import pkgutil
import inspect
import pathlib
from src.utils.logger import logger

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

    @classmethod
    def auto_discover(cls, package_path: str = "src.services"):
        """
        Automatically discovers and imports all modules in the specified package.
        This triggers the @register decorators in those files.
        """
        try:
            # Import the package to get its path
            import src.services as services_pkg
            
            # Use __path__ which is standard for packages (list of paths)
            package_paths = services_pkg.__path__
            
            logger.info(f"[Registry] Discovering services in: {package_paths}")

            count = 0
            for _, name, _ in pkgutil.iter_modules(package_paths):
                # Import the module
                full_module_name = f"{package_path}.{name}"
                try:
                    importlib.import_module(full_module_name)
                    count += 1
                except Exception as e:
                    logger.error(f"[Registry] Failed to import module {full_module_name}: {e}")
            
            logger.info(f"[Registry] Auto-discovery complete. Scanned {count} modules. Registered domains: {len(cls._registry)}")
            
        except ImportError as e:
            logger.error(f"[Registry] Auto-discovery failed: {e}")
        except Exception as e:
            logger.error(f"[Registry] Unexpected error during auto-discovery: {e}")

