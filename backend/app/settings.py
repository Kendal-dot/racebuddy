# ./backend/app/settings.py

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    # Database
    DB_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"

    # Frontend
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    # Environment
    ENVIRONMENT: str = "development"

    # ChromaDB and Data paths
    CHROMADB_PATH: str = "data/chromadb"
    DATA_PATH: str = "data"
    CSV_DATA_FILE: str = "data/lidingo_full_data.csv"

    # RAG Settings
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_TOP_K_RESULTS: int = 5

    # Agent Settings
    AGENT_TEMPERATURE: float = 0.2
    AGENT_MAX_TOKENS: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
