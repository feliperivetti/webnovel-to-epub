import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
from src.config import get_settings

load_dotenv()
settings = get_settings()

print(f"Loaded Settings:")
print(f"API_JWT_SECRET: '{settings.API_JWT_SECRET}'")
print(f"Type: {type(settings.API_JWT_SECRET)}")
print(f"Value check: {bool(settings.API_JWT_SECRET)}")
