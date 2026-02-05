import time
import tempfile
from pathlib import Path
from src.utils.logger import logger

def cleanup_stale_files(max_age_seconds: int = 3600):
    """
    Scans the system temp directory for .epub files created by this app 
    and deletes those older than max_age_seconds.
    """
    tmp_dir = tempfile.gettempdir()
    now = time.time()
    count = 0
    errors = 0
    
    logger.info("[Cleanup] Starting stale file cleanup scan...")
    
    try:
        # Scan system temp dir
        # Note: In production with high traffic, scanning the entire temp dir might be slow.
        # Ideally, we should keep track of created files in TaskManager or put them in a dedicated subdir.
        # For MVP, we'll scan carefully.
        
        # We only touch files that look like our random temp files or have .epub extension
        # Since tempfile.NamedTemporaryFile creates random names, we just look for .epub suffix if we set it.
        # In book_routes we used suffix=".epub".
        
        for p in Path(tmp_dir).glob("*.epub"):
            try:
                # Check modification time
                mtime = p.stat().st_mtime
                if now - mtime > max_age_seconds:
                    p.unlink()
                    count += 1
                    logger.debug(f"[Cleanup] Deleted stale file: {p.name}")
            except Exception:
                # Permission error or file in use
                errors += 1
                pass
                
        if count > 0:
            logger.info(f"[Cleanup] Removed {count} stale EPUB files. Errors: {errors}")
        else:
            logger.info("[Cleanup] No stale files found.")
            
    except Exception as e:
        logger.error(f"[Cleanup] Failed to run cleanup: {e}")
