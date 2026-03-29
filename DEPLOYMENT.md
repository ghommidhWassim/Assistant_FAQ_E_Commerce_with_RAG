# Deployment Guide

This document provides step-by-step instructions for deploying the RAG Chatbot.

## 📋 Prerequisites

- Docker 20.10+ (for containerized deployment)
- Python 3.9+ (for local deployment)
- Ollama with Granite model (`ollama pull granite3.3`)
- 4GB+ RAM recommended
- ~100MB disk space for FAISS index

---

## 🚀 Option 1: Local Deployment

### Step 1: Setup Environment

```bash
cd rag_chatbot

# Copy environment template
cp .env.example .env

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Install Data

```bash
# Data is pre-installed in data/ directory
# Add new documents as needed:
cp your_documents.json data/
```

### Step 3: Start Ollama (in separate terminal)

```bash
# Make sure Ollama is running and model is available
ollama serve
# In another terminal: ollama pull granite3.3
```

### Step 4: Start API

```bash
cd src
python app.py
```

**Output:**
```
[2026-03-29 12:00:00] * Running on http://0.0.0.0:5000
```

### Step 5: Test the API

```bash
# Health check
curl http://localhost:5000/health

# Sample question
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle est la politique de retour ?"}'
```

---

## 🐳 Option 2: Docker Deployment

### Step 1: Build Docker Image

From project root:

```bash
docker build -f src/dockerfile -t rag-chatbot:latest .
```

### Step 2: Configure Environment

Create `.env` file:

```env
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
LLM_MODEL=granite3.3
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### Step 3: Run Container

**Linux/Mac:**
```bash
docker run -d \
  --name rag-api \
  -p 5000:5000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/faiss_index:/app/faiss_index \
  rag-chatbot:latest
```

**Windows (PowerShell):**
```powershell
docker run -d `
  --name rag-api `
  -p 5000:5000 `
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 `
  -v ${PWD}/data:/app/data `
  -v ${PWD}/faiss_index:/app/faiss_index `
  rag-chatbot:latest
```

### Step 4: Verify Container

```bash
# Check running containers
docker ps

# Check logs
docker logs rag-api

# Test API from host
curl http://localhost:5000/health
```

### Step 5: Stop Container

```bash
docker stop rag-api
docker rm rag-api
```

---

## 🚢 Option 3: Docker Compose Deployment

### Step 1: Create docker-compose.yml

```yaml
version: '3.8'

services:
  rag-api:
    build:
      context: .
      dockerfile: src/dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_HOST=0.0.0.0
      - FLASK_PORT=5000
      - LLM_MODEL=granite3.3
      - OLLAMA_BASE_URL=http://localhost:11434
    volumes:
      - ./data:/app/data
      - ./faiss_index:/app/faiss_index
    depends_on:
      - ollama
    networks:
      - rag-network

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    volumes:
      - ollama-models:/root/.ollama
    networks:
      - rag-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  ollama-models:

networks:
  rag-network:
    driver: bridge
```

### Step 2: Start Services

```bash
docker-compose up -d

# Wait for services to start (30s)
sleep 30

# Pull model in Ollama
docker-compose exec ollama ollama pull granite3.3

# Test API
curl http://localhost:5000/health
```

### Step 3: Monitor

```bash
# View logs
docker-compose logs -f rag-api

# Check status
docker-compose ps
```

### Step 4: Stop Services

```bash
docker-compose down
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file with:

```env
# Flask API
FLASK_HOST=0.0.0.0          # API bind address
FLASK_PORT=5000             # API port
FLASK_DEBUG=False           # Enable debug mode

# LLM Configuration
LLM_MODEL=granite3.3        # Model name
OLLAMA_BASE_URL=http://localhost:11434

# Data paths
DATA_DIR=data               # Documents directory
VECTOR_STORE_PATH=faiss_index

# Vector store parameters
CHUNK_SIZE=500              # Tokens per chunk
CHUNK_OVERLAP=50            # Token overlap between chunks
```

---

## ✅ Post-Deployment Verification

### 1. Health Check

```bash
curl -s http://localhost:5000/health | python -m json.tool
```

Expected response:
```json
{
  "status": "ok",
  "message": "RAG API is running",
  "model": "granite3.3"
}
```

### 2. Functional Test

```bash
curl -s -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle est la politique de retour ?"}' | python -m json.tool
```

### 3. Error Handling Test

```bash
# Test with invalid request
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
```

---

## 📊 Monitoring & Logs

### Local Deployment

```bash
# Follow logs
tail -f rag-api.log

# Check Ollama connectivity
curl http://localhost:11434/api/tags
```

### Docker Deployment

```bash
# View container logs
docker logs -f rag-api

# Check resource usage
docker stats rag-api

# Inspect container
docker inspect rag-api
```

---

## 🐛 Troubleshooting

### Issue: "No such file or directory: data/..."

**Solution:**
```bash
# Ensure data directory exists
mkdir -p data

# Copy resources
cp resources/*.json data/
```

### Issue: "Ollama connection refused"

**Solution:**
```bash
# Check Ollama is running
ollama serve

# Or in Docker, verify network communication
docker-compose ps
docker-compose logs ollama
```

### Issue: "FAISS index corrupted"

**Solution:**
```bash
# Rebuild FAISS index
rm -rf faiss_index/
python src/app.py
# API will auto-rebuild on first run
```

### Issue: "Out of memory"

**Solution:**
- Reduce chunk size: `CHUNK_SIZE=250`
- Reduce retrieval count: modify `k=3` in llm_rag.py
- Deploy on machine with more RAM

### Issue: "Slow responses"

**Solutions:**
- Use a faster model: try `mistral` instead of `granite3.3`
- Cache FAISS locally on faster disk
- Deploy Ollama on GPU machine

---

## 📈 Scaling

### Horizontal Scaling

For multiple API instances:

```yaml
# docker-compose.yml
services:
  rag-api-1:
    build: .
    ports:
      - "5000:5000"
  rag-api-2:
    build: .
    ports:
      - "5001:5000"
  # ... share same FAISS index and Ollama
  
  ollama:
    # shared instance
```

### Performance Tuning

1. **FAISS Index**
   - Use `IndexIVFFlat` for 1M+ documents
   - Use `faiss.gpu_resources.StandardGpuResources()` for GPU

2. **Ollama**
   - Enable GPU: `CUDA_VISIBLE_DEVICES=0 ollama serve`
   - Increase `num_thread`: `ollama serve --num-thread 8`

3. **Flask**
   - Use production WSGI server:
     ```bash
     pip install gunicorn
     gunicorn -w 4 -b 0.0.0.0:5000 app:app
     ```

---

## 📝 Maintenance

### Regular Tasks

**Daily:**
- Monitor API health: `curl /health`
- Check logs for errors

**Weekly:**
- Test with sample questions
- Monitor FAISS index size

**Monthly:**
- Add new documents: `cp new_docs.json data/`
- Rebuild FAISS index if needed
- Update Granite model: `ollama pull granite3.3`

---

## 🔐 Security Considerations

### Before Production

- [ ] Disable debug mode: `FLASK_DEBUG=False`
- [ ] Add authentication: API key validation
- [ ] Use HTTPS: reverse proxy with nginx/Apache
- [ ] Rate limiting: implement with Flask-Limiter
- [ ] Input validation: already done in app.py
- [ ] Sanitize log output: remove sensitive data

### Example: Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/ask', methods=['POST'])
@limiter.limit("5 per minute")
def ask():
    # ... existing code
```

---

## 📞 Support

For issues:
1. Check logs: `docker logs rag-api` or local terminal
2. Verify Ollama: `curl http://localhost:11434/api/tags`
3. Test connectivity: `curl -X POST http://localhost:5000/ask`
4. Review [reflection.md](../reflection.md) for design decisions

---

**Last Updated**: 2026-03-29
