import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.routes import book_routes, search_routes

# Initialize the FastAPI application with professional metadata
app = FastAPI(
    title="Novel Scraper API",
    description="Professional API for scraping novels, searching sources, and generating EPUB files.",
    version="1.0.0"
)

# --- CORS CONFIGURATION ---
# This allows browsers and the Swagger UI to communicate with your API without security blocks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PERFORMANCE MIDDLEWARE ---
# Automatically calculates and logs the processing time for every request
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    
    # Process the request
    response = await call_next(request)
    
    # Calculate duration
    process_time = time.perf_counter() - start_time
    
    # Add the duration to the response headers for debugging
    response.headers["X-Process-Time"] = f"{process_time:.4f} sec"
    
    # Console log for monitoring
    print(f"⏱️  Path: {request.url.path} | Method: {request.method} | Duration: {process_time:.4f}s")
    
    return response

# --- ROUTE REGISTRATION ---
# Registering modular routers to keep the code clean and scalable
app.include_router(book_routes.router)
app.include_router(search_routes.router)

# --- HEALTH CHECK ROUTE ---
@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "message": "Novel Scraper API is running smoothly",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
