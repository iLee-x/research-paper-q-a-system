"""Pydantic models for API request and response validation."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class QuestionRequest(BaseModel):
    """Request model for asking a question."""

    question: str = Field(
        ...,
        description="The question to ask about the paper",
        min_length=5,
        max_length=500,
        examples=["What is the Transformer architecture?"]
    )
    top_k: Optional[int] = Field(
        None,
        description="Number of context chunks to retrieve (overrides default)",
        ge=1,
        le=10
    )


class ContextChunk(BaseModel):
    """Model for a context chunk in the response."""

    text: str = Field(..., description="Truncated text of the context chunk")
    relevance_score: float = Field(
        ...,
        description="Relevance score (0-1, higher is more relevant)",
        ge=0,
        le=1
    )


class AnswerResponse(BaseModel):
    """Response model for question answers."""

    answer: str = Field(..., description="The generated answer")
    model: str = Field(..., description="Model used to generate the answer")
    context_chunks_used: int = Field(
        ...,
        description="Number of context chunks used"
    )
    context: List[ContextChunk] = Field(
        ...,
        description="List of context chunks used"
    )
    usage: Dict[str, int] = Field(
        ...,
        description="Token usage statistics"
    )


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Health check message")


class StatusResponse(BaseModel):
    """Response model for system status."""

    documents_indexed: int = Field(
        ...,
        description="Number of document chunks in vector store"
    )
    embedding_model: str = Field(..., description="Name of embedding model")
    llm_model: str = Field(..., description="Name of LLM model")
    vector_store_path: str = Field(..., description="Path to vector store")


class IndexResponse(BaseModel):
    """Response model for indexing operation."""

    status: str = Field(..., description="Indexing status")
    message: str = Field(..., description="Indexing result message")
    chunks_created: int = Field(..., description="Number of chunks created")
    documents_indexed: int = Field(
        ...,
        description="Number of documents added to index"
    )


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
