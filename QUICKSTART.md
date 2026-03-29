# QuickStart Guide ⚡

Get the RAG chatbot running in **3 minutes**.

## Prerequisites

✅ Ollama running: `ollama serve` (in terminal 1)
✅ Model pulled: `ollama pull granite3.3`
✅ Python 3.9+

## Start API (Terminal 2)

```bash
cd rag_chatbot

# Setup once
pip install -q -r requirements.txt
cd src

# Run
python app.py
```

Output:
```
Starting FastAPI app on 0.0.0.0:8000
📚 Swagger UI available at http://0.0.0.0:8000/docs
📖 ReDoc available at http://0.0.0.0:8000/redoc
```

## Access Swagger UI

Open your browser and navigate to:
```
http://localhost:8000/docs
```

This interactive UI allows you to:
- 🔍 Explore all available endpoints
- 📝 Try requests directly from the browser
- 📋 View request/response schemas
- 💬 Test the `/ask` endpoint with custom questions

## Test API (Terminal 3)

### Health Check
```bash
curl http://localhost:8000/health
```

### Ask a Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the return policy?"}'
```

## Sample Response

```json
{
  "answer": "Returns are accepted within 30 days...",
  "sources": ["FAQ.json"],
  "confidence": "high",
  "coverage": "complete"
}
```

## Next Steps

- 📖 [Read Full README](README.md)
- 🐳 [Docker Deployment](DEPLOYMENT.md)
- 🧪 [Run Evaluation](eval/README.md)
- 💭 [Prompt Engineering](reflection.md)

---

**Done! You have a working RAG chatbot with Swagger UI.** 🎉
