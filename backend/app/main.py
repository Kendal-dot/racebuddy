from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.v1.api import api_router
from db.session import init_db
import os
import logging

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
        description="Personalized training plans and AI coaching for Lidingoloppet"
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

            # Initialize database
            init_db()
            logger.info("Database initialized")

            # Ensure data directories exist
            os.makedirs("data", exist_ok=True)
            logger.info("Data directories created")

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
                "Race data and statistics",
                "Calendar integration (.ics export)"
            ]
        }

    return app


app = create_app()