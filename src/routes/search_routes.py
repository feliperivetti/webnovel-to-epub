from fastapi import APIRouter, HTTPException, Query

from src.schemas.novel_schema import SearchResponse
from src.services.centralnovel_service import CentralNovelService
from src.services.pandanovel_service import PandaNovelService
from src.services.royalroad_service import RoyalRoadService


router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/", response_model=SearchResponse) # <--- Validação e Docs automática
def search_novel(
    source: str = Query(..., description="The source site (royal, panda, central)"),
    query: str = Query(..., min_length=2, description="The search term")
):
    """
    Unified search endpoint. 
    Instantiates the correct service and returns a validated SearchResponse.
    """
    source_key = source.lower().strip()
    
    # Mapping sources to their respective CLASSES
    providers = {
        "royal": RoyalRoadService,
        "panda": PandaNovelService,
        "central": CentralNovelService
    }

    if source_key not in providers:
        available = list(providers.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid source. Available options: {available}"
        )

    try:
        # 1. Get the class from the dictionary
        service_class = providers[source_key]
        
        # 2. Instantiate the service (this runs __init__ and sets up the session)
        service_instance = service_class()
        
        # 3. Call the search method
        results = service_instance.search(query)
        
        # 4. Return as a dictionary that matches the SearchResponse schema
        return {
            "source": source_key,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        # Standardized error reporting
        print(f"❌ Search Route Error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="An error occurred during search. Please try again later."
        )