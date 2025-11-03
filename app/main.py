"""FastAPI application for Q&A system over 'Attention Is All You Need' paper."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import sys

from app.config import get_settings
from app.models import (
    QuestionRequest,
    AnswerResponse,
    HealthResponse,
    StatusResponse,
    IndexResponse,
    ErrorResponse
)
from app.rag_pipeline import RAGPipeline
from app.pdf_processor import download_attention_paper, PDFProcessor
from app.embeddings import DocumentChunker, EmbeddingGenerator
from app.vector_store import VectorStore


# Global state
rag_pipeline = None
settings = get_settings()


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global rag_pipeline

    logger.info("Starting Q&A system...")

    try:
        # Initialize RAG pipeline
        rag_pipeline = RAGPipeline(settings)

        # Check if vector store is empty and needs initialization
        if rag_pipeline.vector_store.is_empty():
            logger.warning("Vector store is empty. Please call /index endpoint to initialize.")
        else:
            logger.info(f"Vector store loaded with {rag_pipeline.vector_store.count_documents()} documents")

        logger.info("Q&A system ready")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    logger.info("Shutting down Q&A system...")


# Initialize FastAPI app
app = FastAPI(
    title="Attention Is All You Need - Q&A System",
    description="A production-ready Q&A system over the 'Attention Is All You Need' research paper",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic information."""
    return HealthResponse(
        status="online",
        message="Q&A System for 'Attention Is All You Need' paper"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Service is running"
    )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system status and configuration."""
    if rag_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline not initialized"
        )

    return StatusResponse(
        documents_indexed=rag_pipeline.vector_store.count_documents(),
        embedding_model=settings.embedding_model,
        llm_model=settings.claude_model,
        vector_store_path=settings.chroma_persist_directory
    )


@app.post("/index", response_model=IndexResponse)
async def index_paper():
    """Download and index the 'Attention Is All You Need' paper.

    This endpoint will:
    1. Download the paper from arXiv (if not already downloaded)
    2. Extract text from the PDF
    3. Chunk the text into smaller pieces
    4. Generate embeddings for each chunk
    5. Store embeddings in the vector database
    """
    if rag_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline not initialized"
        )

    try:
        logger.info("Starting indexing process...")

        # Download paper
        pdf_path = await download_attention_paper()

        # Extract text
        pdf_processor = PDFProcessor(str(pdf_path))
        text = pdf_processor.extract_text()

        if not text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract text from PDF"
            )

        # Chunk text
        chunker = DocumentChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        chunks = chunker.chunk_text(text)

        # Generate embeddings
        embeddings = rag_pipeline.embedding_generator.generate_embeddings(chunks)

        # Reset and add to vector store
        rag_pipeline.vector_store.reset_collection()
        rag_pipeline.vector_store.add_documents(
            texts=chunks,
            embeddings=embeddings
        )

        logger.info("Indexing completed successfully")

        return IndexResponse(
            status="success",
            message="Paper indexed successfully",
            chunks_created=len(chunks),
            documents_indexed=rag_pipeline.vector_store.count_documents()
        )

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about the 'Attention Is All You Need' paper.

    The system will:
    1. Find relevant sections from the paper
    2. Use Claude to generate a comprehensive answer
    3. Return the answer with context and metadata
    """
    if rag_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline not initialized"
        )

    # Check if vector store has documents
    if rag_pipeline.vector_store.is_empty():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vector store is empty. Please call /index endpoint first."
        )

    try:
        # Override top_k if provided in request
        if request.top_k:
            original_top_k = settings.top_k_results
            settings.top_k_results = request.top_k

        # Get answer
        result = await rag_pipeline.answer_question(request.question)

        # Restore original top_k
        if request.top_k:
            settings.top_k_results = original_top_k

        return AnswerResponse(**result)

    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )
