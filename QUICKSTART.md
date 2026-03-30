# QuickStart Guide ⚡

Get the RAG chatbot running in **3 minutes**.

## Prerequisites

✅ Ollama running: `ollama serve` (in terminal 1)
✅ Model pulled: `ollama pull llama3`
✅ Python 3.9+

## Start API (Terminal 2)

```bash
cd Assistant_FAQ_E_Commerce_with_RAG

# Setup once
pip install -r requirements.txt

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
  -d '{"question": "posez votre question"}'
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

