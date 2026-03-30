"""
100% LOCAL RAG Evaluation (Ollama) + Benchmark Multi-Models
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict
import numpy as np

# Add src
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_rag import LLMRAGHandler
from langchain_ollama.embeddings import OllamaEmbeddings
from sklearn.metrics.pairwise import cosine_similarity


class LocalRAGEvaluator:
    def __init__(self, model: str):
        print(f"\n🚀 Initializing model: {model}")
        self.model = model
        self.rag = LLMRAGHandler(model=model)
        self.embedder = OllamaEmbeddings(model=model)

        self._load_documents()

    def _load_documents(self):
        data_dir = Path("data")

        docs = self.rag.vector_store.load_documents(str(data_dir))
        self.rag.vector_store.add_documents(docs)

        print(f"📚 Loaded {len(docs)} documents")

    # -------------------------
    # 🧠 Metrics
    # -------------------------

    def _embedding_similarity(self, text1: str, text2: str) -> float:
        emb1 = self.embedder.embed_query(text1)
        emb2 = self.embedder.embed_query(text2)

        return cosine_similarity([emb1], [emb2])[0][0]

    def compute_metrics(self, result: Dict, question: str, expected: str) -> Dict:
        answer = result["answer"]

        # ✅ Relevance
        relevance = self._embedding_similarity(question, answer)

        # ✅ Faithfulness (proxy)
        faithfulness = 1.0 if result["sources"] else 0.0

        # ✅ Context usage
        coverage_map = {
            "complete": 1.0,
            "partial": 0.6,
            "not_available": 0.0
        }
        context_score = coverage_map.get(result["coverage"], 0)

        # ✅ Answer vs expected (if provided)
        expected_score = (
            self._embedding_similarity(answer, expected)
            if expected else 0.0
        )

        return {
            "relevance": relevance,
            "faithfulness": faithfulness,
            "context_score": context_score,
            "expected_match": expected_score
        }

    # -------------------------
    # 📊 Evaluation
    # -------------------------

    def evaluate(self, questions: List[Dict]) -> Dict:
        results = []

        for q in questions:
            question = q["question"]
            expected = q.get("expected_answer", "")

            start = time.time()
            response = self.rag.generate_response(question)
            latency = time.time() - start

            metrics = self.compute_metrics(response, question, expected)

            results.append({
                "question": question,
                "latency": latency,
                **metrics
            })

        return self._aggregate(results)

    def _aggregate(self, results: List[Dict]) -> Dict:
        return {
            "avg_relevance": np.mean([r["relevance"] for r in results]),
            "avg_faithfulness": np.mean([r["faithfulness"] for r in results]),
            "avg_context": np.mean([r["context_score"] for r in results]),
            "avg_expected_match": np.mean([r["expected_match"] for r in results]),
            "avg_latency": np.mean([r["latency"] for r in results]),
        }


# -------------------------
# 🔥 BENCHMARK MULTI-MODELS
# -------------------------

def benchmark(models: List[str], questions: List[Dict]):
    all_results = {}

    for model in models:
        evaluator = LocalRAGEvaluator(model)
        metrics = evaluator.evaluate(questions)

        all_results[model] = metrics

    return all_results


# -------------------------
# 🧪 MAIN
# -------------------------

def main():
    models = ["llama3", "mistral", "granite3.3"]

    with open("eval/test_questions.json") as f:
        questions = json.load(f)

    results = benchmark(models, questions)

    print("\n📊 BENCHMARK RESULTS")
    print("=" * 50)

    for model, metrics in results.items():
        print(f"\n🤖 {model}")
        for k, v in metrics.items():
            print(f"  {k}: {v:.3f}")

    # Save
    with open("eval/benchmark.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()