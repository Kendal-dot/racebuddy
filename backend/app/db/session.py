from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from settings import settings
from db.models import Base
import logging

# Create engine
engine = create_engine(
    settings.DB_URL,
    echo=settings.ENVIRONMENT == "development",  # Show SQL queries in development
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections after 5 minutes
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")
        raise

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()