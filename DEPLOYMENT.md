# Deployment Guide

Simple deployment instructions for the RAG Chatbot with Ollama (llama3) and FAISS.

## Prerequisites

- Python 3.9+ (for local deployment)
- Docker & Docker Compose (for containerized deployment)
- Ollama installed locally (for local deployment)
- 4GB+ RAM

---

## Local Deployment

### 1. Setup Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Ollama (in a separate terminal)

```bash
ollama serve
```

In another terminal, pull the model:
```bash
ollama pull llama3
```

### 3. Start the API

```bash
cd src
python app.py
```

The API will start at `http://localhost:8000`

### 4. Access the Application

- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: `curl http://localhost:8000/health`
- **Ask a Question**:
  ```bash
  curl -X POST http://localhost:8000/ask \
    -H "Content-Type: application/json" \
    -d '{"question": "What is your return policy?"}'
  ```

---

## Docker Deployment

### 1. Build the Image

```bash
docker build -f src/dockerfile -t rag-chatbot:latest .
```



Start the services:

```bash
docker-compose up -d

# Wait for services to start
sleep 10

# Pull the llama3 model
docker-compose exec ollama ollama pull llama3
```

### 2. Access the Application

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: `curl http://localhost:8000/health`


### 4. Stop Services

```bash
docker-compose down
```