"""
FastAPI REST API for RAG Chatbot with Swagger UI

Endpoints:
- GET /health: Check API status
- POST /ask: Submit question and get answer with sources
- GET /docs: Swagger UI documentation
- GET /redoc: ReDoc documentation
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from llm_rag import LLMRAGHandler
from pathlib import Path
import logging
import os
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set default USER_AGENT to avoid warnings
if not os.getenv('USER_AGENT'):
    os.environ['USER_AGENT'] = 'RAG-Chatbot/1.0'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize RAG handler (global instance)
rag_handler = None
documents_loaded = False  # Track document loading status


def load_documents_background():
    """Load documents in background thread (non-blocking)."""
    global documents_loaded
    try:
        data_dir = Path(os.getenv('DATA_DIR', 'data'))
        if data_dir.exists():
            logger.info("📚 Background: Loading documents from data...")
            documents = rag_handler.vector_store.load_documents(str(data_dir))
            if documents:
                logger.info(f"📚 Background: Found {len(documents)} documents, adding to vector store...")
                rag_handler.vector_store.add_documents(documents)
                logger.info(f"✅ Background: Documents loaded and indexed successfully!")
                documents_loaded = True
            else:
                logger.warning("📚 Background: No documents found in data directory")
        else:
            logger.warning(f"📚 Background: Data directory not found: {data_dir}")
    except Exception as e:
        logger.error(f"❌ Background: Error loading documents: {str(e)}")
        documents_loaded = False


def initialize_rag():
    """Initialize RAG handler (fast - doesn't load documents)."""
    global rag_handler
    if rag_handler is None:
        try:
            model = os.getenv('LLM_MODEL', 'llama3')
            logger.info(f"Initializing RAG handler with model: {model}")
            rag_handler = LLMRAGHandler(model=model)
            logger.info("✅ RAG handler initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG handler: {str(e)}")
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app startup and shutdown."""
    # Startup
    logger.info("🚀 Application starting up...")
    initialize_rag()
    
    # Start document loading in background thread (non-blocking)
    logger.info("📚 Starting background document loading...")
    doc_thread = threading.Thread(target=load_documents_background, daemon=True)
    doc_thread.start()
    
    logger.info("✅ Application ready to accept requests!")
    logger.info("📝 Note: Documents are loading in background (check logs for progress)")
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutting down...")


# Initialize FastAPI app with documentation and lifespan
app = FastAPI(
    title="RAG Chatbot API",
    description="E-commerce Support Assistant with Retrieval-Augmented Generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


class QuestionRequest(BaseModel):
    """Request model for asking questions."""
    question: str = Field(
        ..., 
        min_length=1, 
        max_length=1000,
        json_schema_extra={"example": "What is the return policy?"}
    )


class AnswerResponse(BaseModel):
    """Response model for answers."""
    answer: str = Field(..., json_schema_extra={"example": "Returns are accepted within 30 days..."})
    sources: list = Field(..., json_schema_extra={"example": ["FAQ.json"]})
    confidence: str = Field(..., pattern="^(high|medium|low)$", json_schema_extra={"example": "high"})
    coverage: str = Field(..., pattern="^(complete|partial|not_available)$", json_schema_extra={"example": "complete"})


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., json_schema_extra={"example": "ok"})
    message: str = Field(..., json_schema_extra={"example": "RAG API is running"})
    model: str = Field(..., json_schema_extra={"example": "llama3"})
    documents_loaded: bool = Field(..., json_schema_extra={"example": True})


@app.get('/health', response_model=HealthResponse, tags=["Health"])
async def health():
    """
    Check API health status.
    
    Returns:
        HealthResponse: Status of the API and current model
    """
    try:
        status = "ok"
        message = "RAG API is running"
        
        if not documents_loaded:
            message = "RAG API is running (documents loading in background, may take 30-60 seconds)"
        
        return HealthResponse(
            status=status,
            message=message,
            model=os.getenv('LLM_MODEL', 'llama3'),
            documents_loaded=documents_loaded
        )
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post('/ask', response_model=AnswerResponse, tags=["Chat"])
async def ask(request: QuestionRequest):
    """
    Ask a question to the RAG chatbot.
    
    The chatbot retrieves relevant documents from the vector store and generates
    an answer using the LLM, with sources and confidence metrics.
    
    Args:
        request: QuestionRequest object containing the question
    
    Returns:
        AnswerResponse: Answer with sources, confidence, and coverage information
    
    Raises:
        HTTPException: 400 if question is invalid, 404 if not covered by documents,
                      500 for internal errors
    """
    try:
        # Warn if documents still loading
        if not documents_loaded:
            logger.warning("⚠️ Documents still loading in background. Response may be incomplete.")
        
        question = request.question.strip()
        
        logger.info(f"Processing question: {question[:100]}")
        
        # Generate response
        result = rag_handler.generate_response(question)
        
        # Handle out-of-context responses
        if result['coverage'] == 'not_available':
            raise HTTPException(
                status_code=404,
                detail={
                    'message': 'Cette question n\'est pas couverte par les documents disponibles. '
                              'Veuillez vérifier que votre question est pertinente ou contactez le support.',
                    'coverage': result['coverage']
                }
            )
        
        return AnswerResponse(
            answer=result['answer'],
            sources=result['sources'],
            confidence=result['confidence'],
            coverage=result['coverage']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == '__main__':
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv('FASTAPI_HOST', '0.0.0.0')
    port = int(os.getenv('FASTAPI_PORT', 8000))
    
    logger.info(f"Starting FastAPI app on {host}:{port}")
    logger.info(f"📚 Swagger UI available at http://{host}:{port}/docs")
    logger.info(f"📖 ReDoc available at http://{host}:{port}/redoc")
    
    uvicorn.run(app, host=host, port=port)
