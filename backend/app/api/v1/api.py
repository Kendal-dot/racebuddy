from fastapi import APIRouter
from api.v1.endpoints import training, races, calendar, chat

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    training.router, 
    prefix="/training", 
    tags=["training"]
)

api_router.include_router(
    races.router, 
    prefix="/races", 
    tags=["races"]
)

api_router.include_router(
    calendar.router, 
    prefix="/calendar", 
    tags=["calendar"]
)

# NEW: Chat endpoints för AI-agenter
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat", "ai-agents"]
)

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "ok", "message": "RaceBuddy API is healthy"}

# NEW: Data management endpoints
@api_router.post("/admin/ingest-data")
async def trigger_data_ingestion():
    """Trigga data ingestion (för admin/development)"""
    from core.data_ingestion import data_ingestion
    
    try:
        result = data_ingestion.ingest_all_data()
        return {
            "status": "success",
            "message": "Data ingestion completed",
            "details": result
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Data ingestion failed: {str(e)}"
        }