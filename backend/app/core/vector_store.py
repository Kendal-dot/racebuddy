import chromadb
from chromadb.config import Settings
from pathlib import Path
import os
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from langchain_openai import OpenAIEmbeddings
import json

from settings import settings

logger = logging.getLogger(__name__)


class RaceBuddyVectorStore:
    """ChromaDB vector store for RaceBuddy RAG system"""

    def __init__(self):
        self.persist_directory = Path("data/chromadb")
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBED_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )

        # Collection names
        self.RACE_DATA_COLLECTION = "lidingo_race_data"
        self.TRAINING_COLLECTION = "training_guidelines"

        # Initialize collections
        self._init_collections()

    def _init_collections(self):
        """Initialize ChromaDB collections"""
        try:
            # Race data collection
            self.race_collection = self.client.get_or_create_collection(
                name=self.RACE_DATA_COLLECTION,
                metadata={
                    "description": "Lidingöloppet race data and statistics"}
            )

            # Training guidelines collection
            self.training_collection = self.client.get_or_create_collection(
                name=self.TRAINING_COLLECTION,
                metadata={"description": "Training guidelines and tips"}
            )

            logger.info("ChromaDB collections initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing ChromaDB collections: {e}")
            raise

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """Add documents to a collection"""
        try:
            collection = self.client.get_collection(collection_name)

            # Generate embeddings using OpenAI
            embeddings = []
            for doc in documents:
                embedding = self.embeddings.embed_query(doc)
                embeddings.append(embedding)

            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )

            logger.info(
                f"Added {len(documents)} documents to {collection_name}")

        except Exception as e:
            logger.error(f"Error adding documents to {collection_name}: {e}")
            raise

    def query_collection(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search in a collection"""
        try:
            collection = self.client.get_collection(collection_name)

            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query_text)

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )

            return results

        except Exception as e:
            logger.error(f"Error querying {collection_name}: {e}")
            raise

    def query_race_data(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Specific method for searching race data"""
        results = self.query_collection(
            self.RACE_DATA_COLLECTION,
            query,
            n_results
        )

        # Format results for easier use
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                    'distance': results['distances'][0][i] if results['distances'][0] else 0
                })

        return formatted_results

    def query_training_data(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Specific method for training data"""
        results = self.query_collection(
            self.TRAINING_COLLECTION,
            query,
            n_results
        )

        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                    'distance': results['distances'][0][i] if results['distances'][0] else 0
                })

        return formatted_results

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection"""
        try:
            collection = self.client.get_collection(collection_name)
            count = collection.count()

            return {
                "name": collection_name,
                "document_count": count,
                "metadata": collection.metadata
            }

        except Exception as e:
            logger.error(f"Error getting stats for {collection_name}: {e}")
            return {"name": collection_name, "error": str(e)}

    def reset_collection(self, collection_name: str):
        """Clear a collection (use with caution!)"""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")

            # Recreate collection
            if collection_name == self.RACE_DATA_COLLECTION:
                self.race_collection = self.client.create_collection(
                    name=self.RACE_DATA_COLLECTION,
                    metadata={
                        "description": "Lidingöloppet race data and statistics"}
                )
            elif collection_name == self.TRAINING_COLLECTION:
                self.training_collection = self.client.create_collection(
                    name=self.TRAINING_COLLECTION,
                    metadata={"description": "Training guidelines and tips"}
                )

            logger.info(f"Recreated collection: {collection_name}")

        except Exception as e:
            logger.error(f"Error resetting collection {collection_name}: {e}")
            raise


# Singleton instance
vector_store = RaceBuddyVectorStore()
