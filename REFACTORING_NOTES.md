# Refactoring Notes: Flask → FastAPI Migration

## Overview
Successfully migrated the RAG Chatbot API from Flask to FastAPI with improved developer experience via built-in Swagger UI documentation.

---

## 📊 Changes Summary

### 1. **Dependencies Updated** (`requirements.txt`)

**Removed:**
- `flask==3.0.0` - Flask framework
- `streamlit==1.44.1` - Streamlit web UI
- `ragas==0.1.15` - Evaluation package
- `datasets==2.18.0` - Dataset utilities
- `scipy==1.12.0` - Scientific computing

**Added:**
- `fastapi==0.109.0` - Modern async API framework
- `uvicorn==0.27.0` - ASGI server for FastAPI

**Result:** Cleaner, lighter dependencies focused on API-only functionality

---

### 2. **API Rewrite** (`src/app.py`)

#### Before (Flask):
```python
from flask import Flask, request, jsonify

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    # Manual validation
    if not data or 'question' not in data:
        return jsonify({'error': '...'}), 400
```

#### After (FastAPI):
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)

@app.post('/ask', response_model=AnswerResponse)
async def ask(request: QuestionRequest):
    # Automatic validation & type checking
```

#### Key Improvements:
- ✅ **Automatic request validation** via Pydantic
- ✅ **Built-in Swagger UI** at `/docs`
- ✅ **ReDoc documentation** at `/redoc`
- ✅ **Async support** for better concurrency
- ✅ **OpenAPI schema** auto-generation
- ✅ **Type hints** for better IDE support

---

### 3. **Server Configuration**

| Aspect | Flask | FastAPI |
|--------|-------|---------|
| Default Port | 5000 | 8000 |
| Debug Mode | Manual `debug=True` | Built into uvicorn |
| Env Variable | `FLASK_HOST/PORT` | `FASTAPI_HOST/PORT` |
| Documentation | Manual setup needed | Auto-generated at `/docs` |

---

### 4. **Removed Components**

#### `src/chat_ui.py` (Streamlit Interface)
- ❌ Removed: Streamlit web interface
- ✅ Reason: API-only architecture with Swagger UI
- 📝 File remains but **no longer used**

#### `src/conversation.py` (Conversation Manager)
- ❌ Removed: Local conversation persistence
- ✅ Reason: Stateless API design (each request is independent)
- 📝 File remains but **no longer used**

---

### 5. **Documentation Updates**

#### `README.md`
```diff
- │      Flask REST API (app.py)         │
+ │      FastAPI REST API (app.py)       │
```
- Updated architecture diagram
- Updated framework description

#### `QUICKSTART.md`
```diff
- Output:
-  * Running on http://0.0.0.0:5000
+ Output:
+ Starting FastAPI app on 0.0.0.0:8000
+ 📚 Swagger UI available at http://0.0.0.0:8000/docs
+ 📖 ReDoc available at http://0.0.0.0:8000/redoc
```
- Added Swagger UI access instructions
- Updated port from 5000 → 8000
- Added browser-based testing section

#### `DEPLOYMENT.md`
- Updated environment variables: `FLASK_*` → `FASTAPI_*`
- Updated all port references: `5000` → `8000`
- Updated Docker configuration
- Updated docker-compose.yml
- Added Swagger UI access in post-deployment instructions

#### `src/dockerfile`
```diff
- ENV FLASK_HOST=0.0.0.0 FLASK_PORT=5000
+ ENV FASTAPI_HOST=0.0.0.0 FASTAPI_PORT=8000

- EXPOSE 5000
+ EXPOSE 8000

- CMD ["python", "app.py"]  # Uses uvicorn now
+ CMD ["python", "app.py"]  # Uses uvicorn now
```

---

## 🚀 Quick Start After Migration

### Local Development
```bash
cd rag_chatbot/src
python app.py
# Opens: http://localhost:8000/docs
```

### Testing with Swagger UI
1. Open http://localhost:8000/docs
2. Click "Try it out" on `/ask` endpoint
3. Enter your question
4. See formatted response with sources

### Testing with curl
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the return policy?"}'
```

### Docker
```bash
docker build -f src/dockerfile -t rag-chatbot:latest .
docker run -p 8000:8000 rag-chatbot:latest
# Opens: http://localhost:8000/docs
```

---

## ✨ Benefits of Migration

### For Users:
- 🎨 Interactive Swagger UI for testing
- 📖 Auto-generated API documentation
- 🔍 Better error messages with validation details
- ⚡ Faster response times (async support)

### For Developers:
- 🔒 Type-safe request/response validation
- 🛠️ Better IDE autocomplete
- 📝 Self-documenting code (Pydantic models)
- 🧪 Easier to write tests
- 🚀 Modern Python async/await support

### For DevOps:
- 📦 Smaller Docker image (no Streamlit)
- ⚙️ Lighter memory footprint
- 🎯 Cleaner dependency management
- 🔧 Standard ASGI deployment options

---

## ⚠️ Migration Checklist

- [x] Replace Flask imports with FastAPI
- [x] Convert routes to FastAPI endpoints
- [x] Add Pydantic models for requests/responses
- [x] Update requirements.txt
- [x] Update PORT (5000 → 8000)
- [x] Update ENV variables (FLASK_* → FASTAPI_*)
- [x] Update dockerfile
- [x] Update docker-compose.yml
- [x] Update all documentation (.md files)
- [x] Add async event handlers
- [x] Add comprehensive docstrings

---

## 📝 API Endpoints

### GET `/health`
Health check endpoint

**Response:**
```json
{
  "status": "ok",
  "message": "RAG API is running",
  "model": "llama3"
}
```

### POST `/ask`
Submit question to RAG chatbot

**Request:**
```json
{
  "question": "What is the return policy?"
}
```

**Response:**
```json
{
  "answer": "Returns are accepted within 30 days...",
  "sources": ["FAQ.json"],
  "confidence": "high",
  "coverage": "complete"
}
```

### GET `/docs`
Interactive Swagger UI documentation

### GET `/redoc`
ReDoc API documentation

---

## 🔮 Future Improvements

1. **WebSocket Support** - Real-time streaming responses
2. **Request Caching** - Redis integration for frequently asked questions
3. **Authentication** - API key or JWT-based access control
4. **Rate Limiting** - Prevent abuse with per-user/IP limits
5. **Monitoring** - Prometheus metrics integration
6. **Async Document Loading** - Background processing for new documents
7. **Multi-language Support** - Dynamic language selection per request

---

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [OpenAPI Specification](https://www.openapis.org/)

---

**Migration Date:** March 29, 2026  
**Status:** ✅ Complete and Tested
