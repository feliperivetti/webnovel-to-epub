import os
import sys
import time
from unittest.mock import patch

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.registry import ScraperRegistry  # noqa: E402
from src.config import get_settings  # noqa: E402

# Import services to trigger registration

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

# --- CONFIGURATIONS TO TEST ---
TEST_CONFIGS = [
    {
        "name": "Fixed Proxy (2 Workers)",
        "PROXY_URL": "http://zplnmdym:rk0w6ii0pa4a@31.59.20.176:6754/",
        "MAX_WORKERS": 2
    },
    {
        "name": "Rotating Proxy (2 Workers)",
        "PROXY_URL": "http://zplnmdym-rotate:rk0w6ii0pa4a@p.webshare.io:80/",
        "MAX_WORKERS": 2
    },
]

# --- QUANTITIES TO TEST ---
TEST_QUANTITIES = [
    {"label": "Low", "qty": 10},
    {"label": "Medium", "qty": 100},
    {"label": "High", "qty": 350}
]

# --- PASTE LINKS HERE (Fixed Syntax) ---
TEST_URLS = [
    "https://novelfire.net/book/shadow-slave",
    "https://novelfire.net/book/kill-the-sun",
    "https://www.royalroad.com/fiction/36735/the-perfect-run",
    "https://www.royalroad.com/fiction/92820/phantom-star"
]

START_CHAPTER = 1

def run_benchmarks():
    if not TEST_URLS:
        print("Please add URLs to TEST_URLS list in scripts/run_benchmarks.py")
        return

    print("Starting Benchmark Runner")
    print(f"URLs: {len(TEST_URLS)} | Configs: {len(TEST_CONFIGS)} | Quantities: {len(TEST_QUANTITIES)}")
    print("="*80)

    for url in TEST_URLS:
        print(f"\nTargeting: {url}")
        
        service_class = ScraperRegistry.get_service(url)
        if not service_class:
            print(f"Skipping unsupported URL: {url}")
            continue

        for qty_conf in TEST_QUANTITIES:
            qty_label = qty_conf["label"]
            qty = qty_conf["qty"]
            
            print(f"\n  [ {qty_label} Load: {qty} chapters ]")
            
            for config in TEST_CONFIGS:
                print(f"    > Running {config['name']} ... ", end="", flush=True)
                
                # Strategy: Patch os.environ and clear lru_cache of get_settings
                # This ensures Pydantic re-reads config from our injected env vars
                
                # Prepare Env Vars
                env_update = {
                    "MAX_WORKERS": str(config['MAX_WORKERS'])
                }
                if config['PROXY_URL']:
                    env_update["PROXY_URL"] = config['PROXY_URL']
                else:
                    # If None, we want to remove it or set to empty. 
                    # But Pydantic Optional[str] = None might treat "" as "".
                    # Best to set it to "" or ensure it's not set. 
                    # patch.dict allows us to set, but removing is trickier if we want to restore.
                    # Actually patch.dict supports clear=False so we can overwrite.
                    # We will set it to empty string if None, assuming config logic handles it.
                    # Looking at src/classes/base_book.py: if self.settings.PROXY_URL:
                    # An empty string is falsy, so it works.
                    env_update["PROXY_URL"] = ""

                # Apply Patch
                with patch.dict(os.environ, env_update):
                    # Clear cache to force reload
                    get_settings.cache_clear()
                    
                    try:
                        # Instantiate Scraper (will trigger get_settings() which reads fresh env)
                        service = service_class()
                        scraper = service.get_book_instance(url, qty, START_CHAPTER)
                        
                        # Run Scrape (Decorated with @benchmark_scraper)
                        scraper.scrape_novel()
                        print("DONE ✅")
                    except Exception as e:
                        print(f"FAILED ❌ ({e})")
                    
                    # Cleanup cache again just in case
                    get_settings.cache_clear()
                
                # Cool down to avoid ban between configs
                time.sleep(2)

    print("\nAll benchmarks completed. Run 'python scripts/benchmark_viewer.py' to see results.")

if __name__ == "__main__":
    run_benchmarks()
