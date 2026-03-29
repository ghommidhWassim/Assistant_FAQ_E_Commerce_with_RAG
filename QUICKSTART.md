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
 * Running on http://0.0.0.0:5000
```

## Test API (Terminal 3)

### Health Check
```bash
curl http://localhost:5000/health
```

### Ask a Question
```bash
curl -X POST http://localhost:5000/ask \
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

**Done! You have a working RAG chatbot.** 🎉
