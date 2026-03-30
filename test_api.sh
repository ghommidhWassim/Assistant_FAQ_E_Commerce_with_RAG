#!/bin/bash
# Test script for RAG Chatbot API

echo "🚀 RAG Chatbot API Testing Script"
echo "=================================="
echo ""

# Wait for server startup
echo "⏳ Waiting for server to initialize (45 seconds)..."
sleep 45

API_BASE="http://localhost:8000"

echo ""
echo "1️⃣ Testing Health Endpoint"
echo "─────────────────────────"
echo "Command: curl http://localhost:8000/health"
echo "Response:"
curl -s "$API_BASE/health" | python3 -m json.tool
echo ""

echo "2️⃣ Testing Ask Endpoint"
echo "──────────────────────"
echo "Command: curl -X POST http://localhost:8000/ask with question"
echo "Response:"
curl -s -X POST "$API_BASE/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the return policy?"}' | python3 -m json.tool
echo ""

echo "3️⃣ Testing Invalid Request (missing question)"
echo "─────────────────────────────────────────────"
curl -s -X POST "$API_BASE/ask" \
  -H "Content-Type: application/json" \
  -d '{ "question": "How to cook pasta?" }' | python3 -m json.tool
echo ""

echo "4️⃣ Accessing Swagger UI"
echo "──────────────────────"
echo "✅ Swagger UI is available at: http://localhost:8000/docs"
echo "✅ ReDoc is available at: http://localhost:8000/redoc"
echo ""

echo "📚 Available Endpoints:"
echo "  • GET  /health      - Health check"
echo "  • POST /ask         - Ask a question"
echo "  • GET  /docs        - Swagger UI"
echo "  • GET  /redoc       - ReDoc documentation"
echo "  • GET  /openapi.json - OpenAPI schema"
echo ""
echo "✅ All tests completed!"
