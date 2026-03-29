# Evaluation Suite 📊

This directory contains evaluation tools for the RAG chatbot using RAGAS metrics and custom heuristics.

## Quick Start

### 1. Create Sample Test Questions

```bash
cd /path/to/rag_chatbot
python eval/evaluation.py --create-sample
```

This generates 10 sample test questions in `eval/test_questions.json`.

### 2. Run Evaluation

```bash
python eval/evaluation.py \
  --questions eval/test_questions.json \
  --output eval/results.json
```

### 3. View Results

Results are saved to `eval/results.json` with metrics and detailed breakdowns.

---

## Metrics Explained

### 1. **Faithfulness** (0-1)
- Measures how well the LLM answer adheres to the retrieved context
- High faithfulness = answer doesn't hallucinate beyond what's in docs
- Target: > 0.85

### 2. **Answer Relevancy** (0-1)
- Measures if the generated answer is relevant to the question
- High relevancy = stays on topic, doesn't drift
- Target: > 0.80

### 3. **Context Relevancy** (0-1)
- Measures if retrieved contexts are relevant to the question
- High score = FAISS retrieval works well
- Target: > 0.75

---

## Example Usage

### Command Line

```bash
# Create sample tests
python eval/evaluation.py --create-sample

# Run full evaluation on sample
python eval/evaluation.py

# Use custom test questions
python eval/evaluation.py --questions my_questions.json --output my_results.json
```

### Programmatic Usage

```python
from evaluation import RAGEvaluator

evaluator = RAGEvaluator(model="granite3.3")
questions = evaluator.load_test_questions()

results = []
for q in questions:
    result = evaluator.evaluate_question(q['question'])
    results.append(result)

metrics = evaluator.compute_ragas_metrics(results)
print(f"Faithfulness: {metrics['faithfulness']:.2%}")
```

---

## Test Questions Format

Create `test_questions.json` with this structure:

```json
[
  {
    "question": "Quelle est la politique de retour ?",
    "expected_answer": "Returns are accepted within 30 days"
  },
  {
    "question": "Quel est le délai de livraison ?",
    "expected_answer": "Standard delivery is 5-7 business days"
  }
]
```

---

## Interpreting Results

### Sample Output

```json
{
  "timestamp": "2026-03-29 12:34:56",
  "summary": {
    "total_questions": 10,
    "successful_evaluations": 10,
    "failed_evaluations": 0
  },
  "metrics": {
    "faithfulness": 0.87,
    "answer_relevancy": 0.92,
    "context_relevancy": 0.79,
    "sample_count": 10
  },
  "detailed_results": [...]
}
```

### Interpreting Scores

| Metric | Excellent | Good | Fair | Poor |
|--------|-----------|------|------|------|
| **Faithfulness** | > 0.90 | 0.80-0.90 | 0.70-0.80 | < 0.70 |
| **Answer Relevancy** | > 0.90 | 0.80-0.90 | 0.70-0.80 | < 0.70 |
| **Context Relevancy** | > 0.85 | 0.75-0.85 | 0.65-0.75 | < 0.65 |

---

## Troubleshooting

### RAGAS Installation Issues

If RAGAS fails to import, use custom metrics:

```bash
pip install ragas --upgrade
```

The evaluation script falls back to custom heuristics if RAGAS fails.

### Slow Evaluation

- RAGAS metrics computation is slow (5-10 min for 10 questions)
- Consider using fewer test questions for quick iterations
- Batch evaluation results for batches > 50 questions

### Memory Issues

If running out of memory:
- Reduce question batch size
- Evaluate in separate runs
- Use smaller model or subset of documents

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: RAG Evaluation

on: [push, pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt
      - run: python eval/evaluation.py --output eval/ci_results.json
      - uses: actions/upload-artifact@v2
        with:
          name: evaluation-results
          path: eval/ci_results.json
```

---

## Advanced: Custom Metrics

To add custom metrics, extend `RAGEvaluator`:

```python
class CustomEvaluator(RAGEvaluator):
    def custom_metric(self, result: Dict) -> float:
        """Your custom metric logic."""
        return score
```

---

## References

- [RAGAS Documentation](https://docs.ragas.io/)
- [Faithfulness Metric](https://docs.ragas.io/en/latest/concepts/metrics/index.html#faithfulness)
- [Answer Relevancy](https://docs.ragas.io/en/latest/concepts/metrics/index.html#answer-relevancy)

---

**Last Updated**: 2026-03-29
