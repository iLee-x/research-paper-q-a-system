"""RAG (Retrieval-Augmented Generation) pipeline for Q&A."""

from typing import List, Dict, Any
from anthropic import Anthropic
from loguru import logger
from app.embeddings import EmbeddingGenerator
from app.vector_store import VectorStore
from app.config import Settings


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for answering questions."""

    def __init__(self, settings: Settings):
        """Initialize RAG pipeline.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
        self.embedding_generator = EmbeddingGenerator(settings.embedding_model)
        self.vector_store = VectorStore(
            persist_directory=settings.chroma_persist_directory
        )

        logger.info("RAG pipeline initialized successfully")

    def retrieve_context(self, question: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a question.

        Args:
            question: User's question
            top_k: Number of top results to retrieve (default from settings)

        Returns:
            List of relevant document chunks with metadata
        """
        if top_k is None:
            top_k = self.settings.top_k_results

        # Generate embedding for the question
        logger.info(f"Generating embedding for question: {question[:100]}...")
        question_embedding = self.embedding_generator.generate_single_embedding(question)

        # Search vector store for similar chunks
        results = self.vector_store.search(question_embedding, top_k=top_k)

        # Format results
        context_chunks = []
        for doc, distance, metadata in zip(
            results["documents"],
            results["distances"],
            results["metadatas"]
        ):
            context_chunks.append({
                "text": doc,
                "distance": distance,
                "metadata": metadata
            })

        logger.info(f"Retrieved {len(context_chunks)} relevant chunks")
        return context_chunks

    def generate_answer(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate an answer using Claude and retrieved context.

        Args:
            question: User's question
            context_chunks: Retrieved context chunks

        Returns:
            Dictionary containing answer and metadata
        """
        # Construct context from chunks
        context = "\n\n".join([
            f"[Context {i+1}]:\n{chunk['text']}"
            for i, chunk in enumerate(context_chunks)
        ])

        # Create prompt for Claude
        system_prompt = """You are an expert AI assistant specializing in the "Attention Is All You Need" paper by Vaswani et al.
Your role is to answer questions about the Transformer architecture, attention mechanisms, and related concepts described in this paper.

Guidelines:
1. Base your answers primarily on the provided context from the paper
2. Be precise and technical when appropriate
3. If the context doesn't contain enough information to answer fully, acknowledge this
4. Cite specific sections or concepts from the paper when relevant
5. Explain complex concepts clearly
6. If asked about something not in the paper, clarify that your knowledge is limited to the paper's content"""

        user_message = f"""Based on the following excerpts from the "Attention Is All You Need" paper, please answer the question.

Context from the paper:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above."""

        logger.info("Calling Claude API to generate answer")

        # Call Claude API
        response = self.anthropic_client.messages.create(
            model=self.settings.claude_model,
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        answer = response.content[0].text

        logger.info(f"Generated answer with {len(answer)} characters")

        return {
            "answer": answer,
            "model": self.settings.claude_model,
            "context_chunks_used": len(context_chunks),
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }

    async def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a question using the full RAG pipeline.

        Args:
            question: User's question

        Returns:
            Dictionary containing answer, context, and metadata
        """
        logger.info(f"Processing question: {question}")

        # Retrieve relevant context
        context_chunks = self.retrieve_context(question)

        if not context_chunks:
            logger.warning("No relevant context found")
            return {
                "answer": "I couldn't find relevant information in the paper to answer your question.",
                "context_chunks_used": 0,
                "context": []
            }

        # Generate answer
        result = self.generate_answer(question, context_chunks)

        # Add context information to result
        result["context"] = [
            {
                "text": chunk["text"][:200] + "...",  # Truncate for response
                "relevance_score": max(0.0, 1 - chunk["distance"])  # Convert distance to similarity score, ensuring non-negative
            }
            for chunk in context_chunks
        ]

        logger.info("Question answered successfully")
        return result
