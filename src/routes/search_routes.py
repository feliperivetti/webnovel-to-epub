from fastapi import APIRouter, HTTPException, Query

from src.schemas.novel_schema import SearchResponse
from src.utils.logger import logger

from src.services.centralnovel_service import CentralNovelService
from src.services.pandanovel_service import PandaNovelService
from src.services.royalroad_service import RoyalRoadService


router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/", response_model=SearchResponse)
def search_novel(
    source: str = Query(..., description="The source site (royal, panda, central)"),
    query: str = Query(..., min_length=2, description="The search term")
):
    """
    Unified search endpoint.
    Identifies the service provider, executes the search, and logs the process.
    """
    # Log the incoming request details
    logger.info(f"🔍 Incoming search request | Source: {source} | Query: {query}")
    
    source_key = source.lower().strip()
    
    # Mapping sources to their respective CLASSES
    providers = {
        "royal": RoyalRoadService,
        "panda": PandaNovelService,
        "central": CentralNovelService
    }

    # Validation for supported sources
    if source_key not in providers:
        available_sources = list(providers.keys())
        logger.warning(f"⚠️ Unsupported source requested: {source}. Available: {available_sources}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid source. Available options: {available_sources}"
        )

    try:
        # 1. Select the correct service class
        service_class = providers[source_key]
        
        # 2. Instantiate the service (initializes session and headers)
        service_instance = service_class()
        
        # 3. Execute search
        results = service_instance.search(query)
        
        # Log success with the number of results found
        logger.info(f"✅ Search successful | Source: {source_key} | Results found: {len(results)}")
        
        # 4. Return validated response matching the SearchResponse schema
        return {
            "source": source_key,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        # Log the error with full traceback (exc_info=True) for easier debugging
        logger.error(f"❌ Search Route Error for query '{query}': {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=500, 
            detail="An error occurred during search. Please check the logs for more details."
        )
