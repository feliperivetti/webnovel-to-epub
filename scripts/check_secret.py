import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv  # noqa: E402
from src.config import get_settings  # noqa: E402

load_dotenv()
settings = get_settings()

print("Loaded Settings:")
print(f"API_JWT_SECRET: '{settings.API_JWT_SECRET}'")
print(f"Type: {type(settings.API_JWT_SECRET)}")
print(f"Value check: {bool(settings.API_JWT_SECRET)}")
