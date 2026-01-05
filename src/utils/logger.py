import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logger():
    """Configures the global logging system."""
    logger = logging.getLogger("novel_api")
    logger.setLevel(logging.INFO)

    # Prevent duplicate logs if setup is called multiple times
    if logger.hasHandlers():
        return logger

    # Format: 2024-03-20 10:00:00 | INFO | message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. Console Handler (To see in terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (Saves to logs/app.log)
    # RotatingFileHandler: keeps the file from getting too big (max 5MB, keeps 3 backups)
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log", 
        maxBytes=5*1024*1024, 
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Singleton instance
logger = setup_logger()