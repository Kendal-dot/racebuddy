from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.v1.api import api_router
from db.session import init_db
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="RaceBuddy API",
        version="0.1.0",
        description="Personalized training plans and AI coaching for Lidingöloppet"
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production: specify domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router, prefix="/v1")

    # Static files for .ics files
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.on_event("startup")
    async def startup_event():
        """Initialization when the app starts"""
        try:
            logger.info("Starting RaceBuddy API...")

            # 1. Initialize database
            init_db()
            logger.info("Database initialized")

            # 2. Ensure data directories exist
            os.makedirs("data", exist_ok=True)
            os.makedirs("data/chromadb", exist_ok=True)
            logger.info("Data directories created")

            # 3. ALWAYS run data ingestion automatically
            csv_path = Path("data/lidingo_full_data.csv")
            if csv_path.exists():
                logger.info("CSV data file found, running data ingestion...")

                try:
                    from core.vector_store import vector_store
                    from core.data_ingestion import data_ingestion

                    # Check current state
                    race_stats = vector_store.get_collection_stats(
                        vector_store.RACE_DATA_COLLECTION)
                    training_stats = vector_store.get_collection_stats(
                        vector_store.TRAINING_COLLECTION)

                    total_docs = race_stats.get(
                        "document_count", 0) + training_stats.get("document_count", 0)
                    logger.info(
                        f"Current ChromaDB state: {total_docs} documents")

                    # Always run ingestion to ensure fresh data
                    if total_docs == 0:
                        logger.info(
                            "ChromaDB is empty, running full data ingestion...")
                    else:
                        logger.info(
                            "Refreshing ChromaDB with latest data...")
                        # Reset collections to ensure clean data
                        vector_store.reset_collection(
                            vector_store.RACE_DATA_COLLECTION)
                        vector_store.reset_collection(
                            vector_store.TRAINING_COLLECTION)

                    # Run ingestion
                    result = data_ingestion.ingest_all_data()
                    logger.info(f"Data ingestion completed successfully!")
                    logger.info(
                        f"Total documents: {result['total_documents']}")
                    logger.info(
                        f"Race documents: {result['race_documents_created']}")
                    logger.info(
                        f"Training documents: {result['training_documents_created']}")

                    # Verify final state
                    race_stats = vector_store.get_collection_stats(
                        vector_store.RACE_DATA_COLLECTION)
                    training_stats = vector_store.get_collection_stats(
                        vector_store.TRAINING_COLLECTION)
                    final_docs = race_stats.get(
                        "document_count", 0) + training_stats.get("document_count", 0)
                    logger.info(
                        f"ChromaDB now contains {final_docs} documents and is ready!")

                except Exception as e:
                    logger.error(
                        f"Data ingestion failed during startup: {e}")
                    logger.info(
                        "You can trigger data ingestion via /v1/admin/ingest-data endpoint")
                    # Don't crash the app, just continue without data

            else:
                logger.warning(
                    "CSV data file not found at data/lidingo_full_data.csv")
                logger.info(
                    "Please copy your CSV file to data/lidingo_full_data.csv and restart")
                logger.info("Expected path: /app/data/lidingo_full_data.csv")

            logger.info("RaceBuddy API startup completed!")

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            # Don't crash the app, just log the error

    @app.get("/")
    async def root():
        return {
            "message": "RaceBuddy API is running",
            "version": "0.1.0",
            "features": [
                "Personalized training plans",
                "AI coaching agents",
                "Race data and statistics",
                "Calendar integration (.ics export)"
            ]
        }

    return app


app = create_app()
