"""
Flask REST API for RAG Chatbot

Endpoints:
- GET /health: Check API status
- POST /ask: Submit question and get answer with sources
"""

from flask import Flask, request, jsonify
from llm_rag import LLMRAGHandler
from pathlib import Path
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize RAG handler (global instance)
rag_handler = None


def initialize_rag():
    """Initialize RAG handler on first request."""
    global rag_handler
    if rag_handler is None:
        try:
            model = os.getenv('LLM_MODEL', 'llama3')
            logger.info(f"Initializing RAG handler with model: {model}")
            rag_handler = LLMRAGHandler(model=model)
            
            # Load initial data if available (non-blocking)
            data_dir = Path(os.getenv('DATA_DIR', 'data'))
            if data_dir.exists():
                try:
                    logger.info(f"Loading documents from {data_dir}")
                    documents = rag_handler.vector_store.load_documents(str(data_dir))
                    if documents:
                        logger.info(f"Found {len(documents)} documents to add")
                        rag_handler.vector_store.add_documents(documents)
                        logger.info(f"Successfully added documents to vector store")
                except Exception as e:
                    logger.warning(f"Could not load documents on startup: {str(e)}")
        except Exception as e:
            logger.error(f"Error initializing RAG handler: {str(e)}")
            raise


@app.before_request
def before_request():
    """Initialize RAG handler on first request (lazy initialization)."""
    initialize_rag()


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    
    Returns:
        JSON: Status of the API and vector store
    """
    try:
        return jsonify({
            'status': 'ok',
            'message': 'RAG API is running',
            'model': os.getenv('LLM_MODEL', 'llama3')
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/ask', methods=['POST'])
def ask():
    """
    Main endpoint for asking questions to the RAG chatbot.
    
    Request body:
    {
        "question": "Your question here"
    }
    
    Response:
    {
        "answer": "The answer to your question",
        "sources": ["document1.pdf", "document2.txt"],
        "confidence": "high/medium/low",
        "coverage": "complete/partial/not_available"
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'error': 'Missing required field: "question"'
            }), 400
        
        question = data['question'].strip()
        
        if not question:
            return jsonify({
                'error': 'Question cannot be empty'
            }), 400
        
        if len(question) > 1000:
            return jsonify({
                'error': 'Question too long (max 1000 characters)'
            }), 400
        
        logger.info(f"Processing question: {question[:100]}")
        
        # Generate response
        result = rag_handler.generate_response(question)
        
        # Handle out-of-context responses
        if result['coverage'] == 'not_available':
            return jsonify({
                'error': 'Cette question n\'est pas couverte par les documents disponibles. '
                        'Veuillez vérifier que votre question est pertinente ou contactez le support.',
                'coverage': result['coverage']
            }), 404
        
        return jsonify({
            'answer': result['answer'],
            'sources': result['sources'],
            'confidence': result['confidence'],
            'coverage': result['coverage']
        }), 200
        
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error: ' + str(e)
        }), 500


@app.route('/ask', methods=['OPTIONS'])
def ask_options():
    """Handle CORS preflight requests."""
    return '', 204


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'error': 'Method not allowed'
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask app on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
