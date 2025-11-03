"""Document chunking and embedding generation utilities."""

from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from loguru import logger
import re


class DocumentChunker:
    """Split documents into smaller chunks for processing."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize document chunker.

        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers and common artifacts
        text = re.sub(r'\n\d+\n', '\n', text)
        return text.strip()

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks.

        Args:
            text: Text to split into chunks

        Returns:
            List of text chunks
        """
        text = self._clean_text(text)
        chunks = []

        # Split by sentences first to avoid breaking mid-sentence
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())

                # Start new chunk with overlap from the end of previous chunk
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + " " + sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks


class EmbeddingGenerator:
    """Generate embeddings for text chunks using sentence transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding generator.

        Args:
            model_name: Name of the sentence-transformers model to use
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        logger.info(f"Embedding model loaded successfully")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()

    def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector
        """
        embedding = self.model.encode([text])[0]
        return embedding.tolist()

    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors.

        Returns:
            Dimension of embeddings
        """
        return self.model.get_sentence_embedding_dimension()
