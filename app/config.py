"""Configuration management for the Q&A system."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic API Configuration
    anthropic_api_key: str

    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # ChromaDB Configuration
    chroma_persist_directory: str = "./data/chroma_db"

    # Embedding Model
    embedding_model: str = "all-MiniLM-L6-v2"

    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5


    # Claude Configuration
    claude_model: str = "claude-3-haiku-20240307"
    max_tokens: int = 4096
    temperature: float = 0.7

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
