"""Vector database management using ChromaDB."""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from loguru import logger
from pathlib import Path


class VectorStore:
    """Manage vector storage and retrieval using ChromaDB."""

    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "attention_paper"
    ):
        """Initialize ChromaDB vector store.

        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection to use
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        logger.info(f"Initializing ChromaDB at {persist_directory}")

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Attention Is All You Need paper chunks"}
        )

        logger.info(f"Vector store initialized with collection: {collection_name}")

    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add documents to the vector store.

        Args:
            texts: List of text chunks
            embeddings: List of embedding vectors
            metadatas: Optional metadata for each chunk
        """
        if not texts:
            logger.warning("No texts provided to add_documents")
            return

        # Generate IDs for each chunk
        ids = [f"chunk_{i}" for i in range(len(texts))]

        # Add metadata if not provided
        if metadatas is None:
            metadatas = [{"chunk_id": i} for i in range(len(texts))]

        logger.info(f"Adding {len(texts)} documents to vector store")

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        logger.info(f"Successfully added {len(texts)} documents")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Search for similar documents using a query embedding.

        Args:
            query_embedding: Embedding vector of the query
            top_k: Number of top results to return

        Returns:
            Dictionary containing documents, distances, and metadata
        """
        logger.info(f"Searching for top {top_k} similar documents")

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        return {
            "documents": results["documents"][0],
            "distances": results["distances"][0],
            "metadatas": results["metadatas"][0]
        }

    def count_documents(self) -> int:
        """Get the number of documents in the collection.

        Returns:
            Number of documents
        """
        return self.collection.count()

    def reset_collection(self) -> None:
        """Delete all documents from the collection."""
        logger.warning(f"Resetting collection: {self.collection_name}")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Attention Is All You Need paper chunks"}
        )
        logger.info("Collection reset successfully")

    def is_empty(self) -> bool:
        """Check if the collection is empty.

        Returns:
            True if collection has no documents, False otherwise
        """
        return self.collection.count() == 0
