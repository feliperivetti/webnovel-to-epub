from fastapi import APIRouter, HTTPException
from src.classes.centralnovel_book import MyCentralNovelBook
from src.classes.royalroad_book import MyRoyalRoadBook
from src.classes.pandanovel_book import MyPandaNovelBook

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/")
def search_novel(source: str, query: str):
    """
    Search for novels in a specific source.
    Allowed sources: central, royal, panda
    """
    source_key = source.lower().strip()
    
    try:
        if "central" in source_key:
            results = MyCentralNovelBook.search(query)
        elif "royal" in source_key:
            results = MyRoyalRoadBook.search(query)
        elif "panda" in source_key:
            results = MyPandaNovelBook.search(query)
        else:
            raise HTTPException(status_code=400, detail="Invalid source. Use 'central', 'royal' or 'panda'.")
            
        return {
            "source": source_key,
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Search Route Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
