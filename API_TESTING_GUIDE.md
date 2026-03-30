# API Access & Testing Guide

## ⚠️ Why Browser Connection Refused?

When you tried accessing `http://localhost:8000/docs` immediately after starting the app, you got `ERR_CONNECTION_REFUSED` because:

### The Problem
1. **Initialization Phase** - When the app starts, it initializes the RAG handler:
   - Loads Ollama model
   - Loads ChromaDB
   - Reads documents from `data/` directory
   - Creates vector embeddings
   - This process can take **30-60 seconds**

2. **Server Status** 
   - The Uvicorn server listens on port 8000
   - But the app's startup event completes only after initialization
   - Browser attempts to connect before initialization finishes
   - Connection gets refused

### The Solution
**Wait 45-60 seconds after the app starts** before opening the browser. You'll know it's ready when you see:
```
✅ Application ready to accept requests
```

---

## 🚀 Proper Startup Process

### Terminal 1 (Ollama)
```bash
ollama serve
```

### Terminal 2 (RAG API)
```bash
cd /home/gass/Desktop/test/rag_chatbot
source venv/bin/activate
python3 src/app.py
```

**Wait for these logs to appear:**
```
🚀 Application starting up...
Initializing RAG handler with model: llama3
Loading documents from data
[... document loading logs ...]
✅ Application ready to accept requests
```

---

## 📈 Startup Timeline

```
Time  | Event
------|----------------------------------
0s    | App starts, listening on 0.0.0.0:8000
5s    | Initializing RAG handler with model
15s   | ChromaDB initialized
25s   | Documents loaded (113 chunks)
45s   | ✅ Application ready to accept requests
```

**After ~45 seconds**, the app is ready!

---

## ✅ GET /health Endpoint

**Purpose:** Check if the API is running and ready to accept requests

### How to Test

**Via curl:**
```bash
curl http://localhost:8000/health
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "message": "RAG API is running",
  "model": "llama3"
}
```

**What it tells you:**
- ✅ `status: "ok"` — API is operational
- ✅ `message` — Human-readable status message
- ✅ `model: "llama3"` — Current LLM model in use

**Error Response (500):**
```json
{
  "error": "Internal server error: [details]"
}
```

---

## 💬 POST /ask Endpoint

**Purpose:** Submit a question and get an answer with sources

### Request Format

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelle est la politique de retour ?"
  }'
```

### Success Response (200 OK)

```json
{
  "answer": "La politique de retour est de 30 jours pour tout produit non utilisé...",
  "sources": ["FAQ.json", "Ecommerce_FAQ_Chatbot_dataset.json"],
  "confidence": "high",
  "coverage": "complete"
}
```

**Response fields:**
- `answer` — The AI-generated answer based on documents
- `sources` — Which document(s) contain the relevant information
- `confidence` — `"high"` | `"medium"` | `"low"` — How confident is the answer?
- `coverage` — `"complete"` | `"partial"` | `"not_available"`

### Error Response: Question Out of Context (404)

```bash
curl -X POST http://localhost:8000/ask \
  -d '{"question": "How to build a rocket?"}'
```

**Response:**
```json
{
  "detail": {
    "message": "Cette question n'est pas couverte par les documents disponibles. Veuillez vérifier que votre question est pertinente ou contactez le support.",
    "coverage": "not_available"
  }
}
```

### Error Response: Invalid Request (422)

```bash
curl -X POST http://localhost:8000/ask \
  -d '{}'  # Missing required "question" field
```

**Response:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "question"],
      "msg": "Field required"
    }
  ]
}
```

---

## 🎨 Using Swagger UI (Interactive Testing)

### Access Swagger UI
Open your browser and navigate to:
```
http://localhost:8000/docs
```

### Step-by-Step Guide

1. **Open Swagger UI**
   - Navigate to `http://localhost:8000/docs`
   - Wait 45+ seconds if app just started

2. **Test Health Endpoint**
   - Click on `GET /health`
   - Click "Try it out"
   - Click "Execute"
   - View the response (should be 200 OK with status details)

3. **Test Ask Endpoint**
   - Click on `POST /ask`
   - Click "Try it out"
   - Enter a question in the `question` field (e.g., "What is the return policy?")
   - Click "Execute"
   - View the response with answer and sources

### Swagger UI Features
- 🔍 See request/response schemas
- 📝 Built-in documentation
- 🧪 Try endpoints without curl
- 💬 See actual HTTP requests/responses

---

## 🧪 Testing Scenarios

### Scenario : Healthy System
```bash
# Check health
curl http://localhost:8000/health

# Ask a question covered by documents
curl -X POST http://localhost:8000/ask \
  -d '{"question": "What is the return policy?"}'

# Expected: 200 OK with answer
```
---

## 🔧 Testing Script

Run the provided test script:

```bash
# Make it executable
chmod +x test_api.sh

# Run tests (wait for app to initialize first!)
./test_api.sh
```

This script:
- ⏳ Waits 45 seconds for initialization
- ✅ Tests `/health` endpoint
- ✅ Tests `/ask` endpoint
- ✅ Tests error handling
- 📝 Shows all available endpoints

---

## 🚀 Quick Test Commands

**After waiting 45+ seconds for initialization:**

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "c est quoi la politique de retour?"}'

# 3. Open Swagger UI in browser
open http://localhost:8000/docs  

```

---

## 📱 API Endpoints Summary

| Method | Endpoint | Purpose | Requires |
|--------|----------|---------|----------|
| GET | `/health` | Health check | Nothing |
| POST | `/ask` | Ask question | `{"question": "..."}`  |
| GET | `/docs` | Swagger UI | Nothing |

---

## 🐛 Troubleshooting

### Issue: Connection Refused
**Cause:** App still initializing  
**Solution:** Wait 45+ seconds 

### Issue: 404 Not Found
**Cause:** Question not in document database  
**Solution:** Ask about e-commerce FAQ topics

### Issue: 422 Validation Error
**Cause:** Invalid request format  
**Solution:** Ensure JSON is valid and `question` field exists

### Issue: 500 Server Error
**Cause:** RAG handler crashed  
**Solution:** Check logs, restart app

---

## 📝 Example Requests/Responses

### Successful Query
```bash
$ curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle est la politique de retour ?"}'
```

**Response:**
```json
{
  "answer": "La politique de retour pour nos produits...",
  "sources": ["FAQ.json"],
  "confidence": "high",
  "coverage": "complete"
}
```

### Out-of-Context Query
```bash
$ curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How to build quantum computers?"}'
```

**Response:**
```json
{
  "detail": {
    "message": "Cette question n'est pas couverte par les documents disponibles. Veuillez vérifier que votre question est pertinente ou contactez le support.",
    "coverage": "not_available"
  }
}
```

---

**Ready to test? Start with the health endpoint first!** 
