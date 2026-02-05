import json
import os
import time
import functools
from datetime import datetime
from src.config import get_settings

class MetricsService:
    FILE_PATH = "benchmarks.jsonl"

    @classmethod
    def record_scrape_metric(cls, 
                             url: str, 
                             chapters_count: int, 
                             duration_seconds: float, 
                             status: str, 
                             error: str = None):
        """Appends a benchmark record to the JSONL file."""
        settings = get_settings()
        
        # Determine config context (Simplified)
        config_snapshot = {
            "workers": settings.MAX_WORKERS,
            "proxy_mode": "rotating" if "rotate" in (settings.PROXY_URL or "") else "fixed" if settings.PROXY_URL else "direct",
            "timestamp": datetime.now().isoformat()
        }
        
        rate = 0
        if duration_seconds > 0:
            rate = round(chapters_count / duration_seconds, 2)

        record = {
            "version": "1.0",
            "timestamp": time.time(),
            "target_url": url,
            "chapters_count": chapters_count,
            "duration_s": round(duration_seconds, 2),
            "chapters_per_second": rate,
            "status": status,
            "error": error,
            "config": config_snapshot
        }
        
        try:
            with open(cls.FILE_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[MetricsService] Failed to record metric: {e}")

    @classmethod
    def get_recent_benchmarks(cls, limit: int = 10):
        if not os.path.exists(cls.FILE_PATH):
            return []
        data = []
        try:
            with open(cls.FILE_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        data.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            return []
        return list(reversed(data))

def benchmark_scraper(func):
    """
    Decorator to measure execution time and record metrics for scrape_novel.
    Assuming func is method of a class with `_main_url`.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        url = getattr(self, "_main_url", "unknown")
        
        try:
            result_novel = func(self, *args, **kwargs)
            
            # Success
            duration = time.time() - start_time
            chapters_count = len(result_novel.chapters) if result_novel and result_novel.chapters else 0
            
            MetricsService.record_scrape_metric(
                url=url,
                chapters_count=chapters_count,
                duration_seconds=duration,
                status="success"
            )
            return result_novel
            
        except Exception as e:
            # Failure
            duration = time.time() - start_time
            MetricsService.record_scrape_metric(
                url=url,
                chapters_count=0,
                duration_seconds=duration,
                status="failed",
                error=str(e)
            )
            raise e
            
    return wrapper
