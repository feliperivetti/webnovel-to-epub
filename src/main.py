import time
import uvicorn
import requests
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from src.routes import book_routes, search_routes
from src.utils.logger import logger
from src.config import get_settings

# --- LOAD SETTINGS ---
settings = get_settings()

# --- JWT CONFIGURATION ---
from typing import Optional

# --- JWT CONFIGURATION ---
ALGORITHM = "HS256"
# Set auto_error=False to allow us to handle missing tokens manually in verify_internal_token
security = HTTPBearer(auto_error=False)

async def verify_internal_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    **JWT Validator for Internal Communication**

    This dependency verifies that the request includes a valid Bearer token signed by the Edge Function.
    
    - **Header**: `Authorization: Bearer <token>`
    - **Algorithm**: HS256
    - **Required Claims**: `sub`, `tier`, `action`
    
    Returns the decoded payload if valid.
    """
    if not settings.API_JWT_SECRET:
        logger.warning("API_JWT_SECRET not configured - skipping validation (dev mode)")
        return {"sub": "dev", "tier": "premium", "action": "generate-epub"}
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")

    token = credentials.credentials
    
    try:
        # Use settings.API_JWT_SECRET instead of global variable
        payload = jwt.decode(token, settings.API_JWT_SECRET, algorithms=[ALGORITHM])
        
        # Validate action (optional - for extra security)
        if payload.get("action") != "generate-epub":
            raise HTTPException(status_code=403, detail="Invalid action")
        
        logger.info(f"✅ Authenticated request from user {payload.get('sub')} (tier: {payload.get('tier')})")
        return payload
        
    except JWTError as e:
        logger.error(f"❌ JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.services.cleanup_service import cleanup_stale_files

# --- LIFESPAN MANAGER (Scheduler) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Scheduler
    scheduler = AsyncIOScheduler()
    # Run cleanup every hour (3600s)
    scheduler.add_job(cleanup_stale_files, 'interval', seconds=3600)
    scheduler.start()
    logger.info("🕒 Scheduler started: File cleanup job scheduled (every 1h).")
    
    yield
    
    # Shutdown: Stop Scheduler
    scheduler.shutdown()
    logger.info("🛑 Scheduler shut down.")

# Initialize the FastAPI application with professional metadata
tags_metadata = [
    {
        "name": "Books",
        "description": "**Protected Operations**. Scrape novels and generate EPUBs. **Requires JWT**.",
    },
    {
        "name": "Search",
        "description": "Public search operations for supported novel sources.",
    },
    {
        "name": "Health",
        "description": "System health and status checks.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    description="""
    # WebNovel to EPUB Service 📚

    Professional API for scraping novels, searching sources, and generating EPUB files.
    
    ## 🔐 Authentication
    
    Most endpoints in the `/books` namespace are **protected** and require an Internal JWT.
    You must include the token in the `Authorization` header:
    
    `Authorization: Bearer <your_token>`
    
    > **Note**: This service is designed to be called by the Supabase Edge Functions, which sign the tokens.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},  # Hide schemas sidebar for cleaner look
    lifespan=lifespan
)

# ... (middleware same) ...

# --- CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PERFORMANCE MIDDLEWARE ---
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    
    response = await call_next(request)
    
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f} sec"
    
    # Optional: only print if DEBUG is true, or keep always
    if settings.DEBUG:
        print(f"⏱️  Path: {request.url.path} | Method: {request.method} | Duration: {process_time:.4f}s")
    
    return response

# --- ROUTE REGISTRATION ---
# Pass the dependency to the router that needs protection
app.include_router(
    book_routes.router,
    dependencies=[Depends(verify_internal_token)]  # 🔐 Protected routes
)
app.include_router(search_routes.router)  # Search stays public

# --- HEALTH CHECK ROUTE ---
@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "message": f"{settings.APP_NAME} is running smoothly",
        "timestamp": time.time(),
        "docs": "/docs"
    }

# --- DEBUG PROXY ROUTE ---
@app.get("/debug-proxy", tags=["Debug"])
def debug_proxy():
    """
    Check which IP address is being used by the server. 
    Helps verify if the PROXY_URL is correctly applied on Render.
    """
    proxy_url = settings.PROXY_URL
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    } if proxy_url else None

    debug_data = {
        "proxy_configured": bool(proxy_url),
        "proxy_url_masked": f"{proxy_url[:15]}...{proxy_url[-5:]}" if proxy_url else None,
        "server_ip_check": "Checking...",
        "error": None
    }

    try:
        # We use a 3rd party API to see our outgoing IP
        response = requests.get(
            "https://api.ipify.org?format=json", 
            proxies=proxies, 
            timeout=10
        )
        debug_data["server_ip_check"] = response.json().get("ip")
    except Exception as e:
        logger.error(f"[Debug] Proxy check failed: {e}")
        debug_data["server_ip_check"] = "Failed"
        debug_data["error"] = str(e)

    return debug_data

@app.get("/debug-headers")
def debug_headers():
    import cloudscraper
    proxy = settings.PROXY_URL
    proxies = {"http": proxy, "https": proxy}
    
    # Usando cloudscraper com os mesmos headers do seu service
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    
    # Vamos forçar um User-Agent real aqui também
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    res = scraper.get("https://httpbin.org/headers", proxies=proxies, headers=headers)
    return res.json()

if __name__ == "__main__":
    # Ensure port is dynamic for Render and host is 0.0.0.0 for Docker
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
