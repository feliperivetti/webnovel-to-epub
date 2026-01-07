import time
import os
import uvicorn
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.routes import book_routes, search_routes
from src.utils.logger import logger

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

# Initialize the FastAPI application with professional metadata
app = FastAPI(
    title="Novel Scraper API",
    description="Professional API for scraping novels, searching sources, and generating EPUB files.",
    version="1.0.0"
)

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
    
    print(f"⏱️  Path: {request.url.path} | Method: {request.method} | Duration: {process_time:.4f}s")
    
    return response

# --- ROUTE REGISTRATION ---
app.include_router(book_routes.router)
app.include_router(search_routes.router)

# --- HEALTH CHECK ROUTE ---
@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "message": "Novel Scraper API is running smoothly",
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
    proxy_url = os.environ.get("PROXY_URL")
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
    proxy = os.environ.get("PROXY_URL")
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
