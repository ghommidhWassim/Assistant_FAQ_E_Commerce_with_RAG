# RAG Chatbot — E-commerce Support Assistant

A RAG (Retrieval-Augmented Generation) chatbot for accurate, source-backed e-commerce Q&A. Combines semantic document retrieval with Ollama's llama3 model to provide faithful, contextualized answers.

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   Client (HTTP REST + Swagger UI)   │
└────────────────┬────────────────────┘
                 │
        ┌────────┴────────┐
        │  POST /ask      │
        │  GET /health    │
        └────────┬────────┘
                 │
    ┌────────────▼──────────────┐
    │  FastAPI (app.py)         │
    │  - Input validation       │
    │  - Swagger UI docs        │
    │                           │
    └────────────┬──────────────┘
                 │
    ┌────────────▼─────────────────────┐
    │  RAG Handler (llm_rag.py)        │
    │  1. Semantic search              │
    │  2. Prompt engineering           │
    │  3. LLM inference (llama3)       │
    │  4. Post-processing              │
    └────────────┬─────────────────────┘
                 │
    ┌────────────▼─────────────────────┐
    │  Vector Store (vector_store.py)  │
    │  - ChromaDB indexing             │
    │  - Document chunking             │
    │  - Embeddings (Ollama)           │
    └────────────┬─────────────────────┘
                 │
        ┌────────┴─────────────┐
        │  data/               │
        │  - FAQ.json          │
        │  - Dataset.json      │
        └──────────────────────┘
```

## 🎯 Key Components

### 1. **Document Ingestion** (`vector_store.py`)
- Loads JSON, PDF, and text files
- Chunks with 500 token size, 50 token overlap
- Preserves source metadata

### 2. **Vectorization** (`vector_store.py`)
- Embeddings via Ollama (llama3)
- ChromaDB persistent indexing
- Semantic similarity search

### 3. **Retrieval** (`vector_store.py`)
- Query embedding
- Top-5 chunk retrieval
- Formatted with source metadata

### 4. **Generation** (`llm_rag.py`)
- System prompt with French instructions
- Chain-of-thought reasoning
- Source citation requirement
- Out-of-scope guardrails

### 5. **API** (`app.py`)
- `POST /ask` - Submit questions
- `GET /health` - Status check
- Error handling
- Pydantic validation

## 🚀 Quick Start

### Local Deployment

**1. Setup**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Start Ollama** (separate terminal)
```bash
ollama serve
# In another terminal:
ollama pull llama3
```

**3. Start API**
```bash
cd src
python app.py
```

Access at: **http://localhost:8000/docs**

### Docker Deployment

**1. Start services**
```bash
docker-compose up -d
sleep 10
docker-compose exec ollama ollama pull llama3
```

**2. Access**
- Swagger UI: http://localhost:8000/docs
- Health: `curl http://localhost:8000/health`
- Ask: `curl -X POST http://localhost:8000/ask ...`

See [DEPLOYMENT.md](DEPLOYMENT.md) for details.

## 📡 API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "message": "RAG API is running",
  "model": "llama3"
}
```

### Ask a Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is your return policy?"}'
```

Response:
```json
{
  "answer": "Returns accepted within 30 days with original receipt...",
  "sources": ["FAQ.json", "Ecommerce_FAQ_dataset.json"],
  "confidence": "high",
  "coverage": "complete"
}
```

### Out-of-Scope Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I make a chocolate cake?"}'
```

Response: Question not covered by available documents.

## 🛠️ Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| **LLM** | llama3 (Ollama) | Local execution, no data leakage, fast, free |
| **Vector Store** | ChromaDB | Built-in persistence, semantic search, lightweight |
| **Embeddings** | Ollama (llama3) | Same model, no external deps |
| **API Framework** | FastAPI | Modern, automatic docs, validation |
| **Chunking** | RecursiveCharacterSplitter | Preserves semantic structure |

## 📂 Project Structure

```
rag_chatbot/
├── src/
│   ├── app.py                  # FastAPI endpoints
│   ├── llm_rag.py              # RAG orchestration
│   ├── vector_store.py         # chromaDB + document processing
│   ├── conversation.py         # Chat history (optional)
│   └── dockerfile              # Docker image
├── data/                       # Document corpus
│   ├── FAQ.json
│   └── Ecommerce_FAQ_dataset.json
├── eval/                       # Evaluation tools
│   └── evaluation.py
├── docker-compose.yml          # Container setup
├── DEPLOYMENT.md               # Deployment guide
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── LICENSE                     # MIT
```
