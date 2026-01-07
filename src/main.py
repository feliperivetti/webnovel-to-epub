import time
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.routes import book_routes, search_routes

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

if __name__ == "__main__":
    # Garante que a porta seja dinâmica para o Render e o host seja 0.0.0.0 para o Docker
    port = int(os.environ.get("PORT", 8000))
    # Importante: ao usar uvicorn.run com string "src.main:app", o reload funciona melhor em desenvolvimento
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
