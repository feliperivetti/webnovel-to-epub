import os
import sys
import time
from unittest.mock import patch

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.registry import ScraperRegistry  # noqa: E402
from src.config import get_settings  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

# --- INITIALIZATION ---
load_dotenv()
ScraperRegistry.auto_discover()
settings = get_settings()

# --- CONFIGURATIONS TO TEST ---
# We dynamicallly build this from environment or defaults
TEST_CONFIGS = [
    {
        "name": "Direct (No Proxy)",
        "PROXY_URL": None,
        "MAX_WORKERS": settings.MAX_WORKERS
    }
]

# Add Main Proxy if configured
if settings.PROXY_URL:
    TEST_CONFIGS.append({
        "name": "Primary Proxy",
        "PROXY_URL": settings.PROXY_URL,
        "MAX_WORKERS": settings.MAX_WORKERS
    })

# Add Fallback Proxy if different
if settings.PROXY_URL_FALLBACK and settings.PROXY_URL_FALLBACK != settings.PROXY_URL:
    TEST_CONFIGS.append({
        "name": "Fallback Proxy",
        "PROXY_URL": settings.PROXY_URL_FALLBACK,
        "MAX_WORKERS": settings.MAX_WORKERS
    })

# --- QUANTITIES TO TEST ---
TEST_QUANTITIES = [
    {"label": "Low", "qty": 10},
    {"label": "Medium", "qty": 100},
    # {"label": "High", "qty": 350} # Slow for regular runs
]

# --- TEST TARGETS ---
TEST_URLS = [
    "https://novelfire.net/book/shadow-slave",
    "https://www.royalroad.com/fiction/36735/the-perfect-run",
]

START_CHAPTER = 1

def run_benchmarks():
    if not TEST_URLS:
        print("Please add URLs to TEST_URLS list.")
        return

    print("🚀 Starting Benchmark Runner")
    print(f"URLs: {len(TEST_URLS)} | Configs: {len(TEST_CONFIGS)} | Quantities: {len(TEST_QUANTITIES)}")
    print("="*80)

    total_start = time.time()

    for url in TEST_URLS:
        print(f"\n📂 Targeting: {url}")
        
        service_class = ScraperRegistry.get_service(url)
        if not service_class:
            print(f"❌ Skipping unsupported URL: {url}")
            continue

        for qty_conf in TEST_QUANTITIES:
            qty_label = qty_conf["label"]
            qty = qty_conf["qty"]
            
            print(f"\n  [ {qty_label} Load: {qty} chapters ]")
            
            for config in TEST_CONFIGS:
                print(f"    > {config['name']:<20} ... ", end="", flush=True)
                
                run_start = time.time()
                env_update = {"MAX_WORKERS": str(config['MAX_WORKERS'])}
                env_update["PROXY_URL"] = config['PROXY_URL'] or ""

                with patch.dict(os.environ, env_update):
                    get_settings.cache_clear()
                    
                    try:
                        service = service_class()
                        scraper = service.get_book_instance(url, qty, START_CHAPTER)
                        scraper.scrape_novel()
                        
                        elapsed = time.time() - run_start
                        print(f"DONE ✅ ({elapsed:.2f}s)")
                    except Exception as e:
                        print(f"FAILED ❌ ({e})")
                    
                    get_settings.cache_clear()
                
                time.sleep(1) # Brief pause

    total_elapsed = time.time() - total_start
    print("\n" + "="*80)
    print(f"✅ All benchmarks completed in {total_elapsed/60:.2f} minutes.")
    print("Run 'python scripts/benchmark_viewer.py' to see analysis.")

    print("\nAll benchmarks completed. Run 'python scripts/benchmark_viewer.py' to see results.")

if __name__ == "__main__":
    run_benchmarks()
