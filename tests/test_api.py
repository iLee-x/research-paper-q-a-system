"""Tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "Q&A System" in data["message"]


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_status_endpoint():
    """Test status endpoint returns system information."""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "documents_indexed" in data
    assert "embedding_model" in data
    assert "llm_model" in data


def test_ask_question_invalid_request():
    """Test ask endpoint with invalid question."""
    # Question too short
    response = client.post("/ask", json={"question": "Hi"})
    assert response.status_code == 422

    # Missing question
    response = client.post("/ask", json={})
    assert response.status_code == 422


def test_ask_question_empty_vector_store():
    """Test ask endpoint when vector store is empty."""
    response = client.post("/ask", json={"question": "What is the Transformer?"})
    # Should return 400 if vector store is empty
    assert response.status_code in [400, 200]


@pytest.mark.asyncio
async def test_chunker():
    """Test document chunker functionality."""
    from app.embeddings import DocumentChunker

    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    text = "This is a test sentence. " * 50
    chunks = chunker.chunk_text(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)


@pytest.mark.asyncio
async def test_embedding_generator():
    """Test embedding generator functionality."""
    from app.embeddings import EmbeddingGenerator

    generator = EmbeddingGenerator()
    text = "This is a test sentence."
    embedding = generator.generate_single_embedding(text)

    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, float) for x in embedding)
