"""
Evaluation script for RAG Chatbot using RAGAS metrics.

Metrics computed:
1. Faithfulness: How faithful is the answer to the retrieved context?
2. Answer Relevancy: Is the answer relevant to the question?
3. Context Relevancy: Is the retrieved context relevant to the question?
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_rag import LLMRAGHandler
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_relevancy


class RAGEvaluator:
    """Evaluator for RAG chatbot using RAGAS framework."""
    
    def __init__(self, model: str = "granite3.3"):
        """Initialize the evaluator with a RAG handler."""
        print("[INFO] Initializing RAG Evaluator...")
        self.rag_handler = LLMRAGHandler(model=model)
        self.results = []
        
    def load_test_questions(self, filepath: str = "eval/test_questions.json") -> List[Dict]:
        """Load test questions from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                questions = data if isinstance(data, list) else data.get('questions', [])
                print(f"[INFO] Loaded {len(questions)} test questions")
                return questions
        except FileNotFoundError:
            print(f"[ERROR] Test questions file not found: {filepath}")
            return []
    
    def evaluate_question(self, question: str, expected_answer: str = "") -> Dict:
        """
        Evaluate a single question.
        
        Args:
            question: The test question
            expected_answer: Ground truth answer (optional)
            
        Returns:
            Dict with evaluation metrics
        """
        try:
            print(f"\n[EVALUATING] {question[:80]}...")
            
            # Get response from RAG system
            result = self.rag_handler.generate_response(question)
            
            # Retrieve context for metric calculation
            retrieved_docs = self.rag_handler.retrieve(question, k=5)
            context = " ".join([doc.page_content for doc in retrieved_docs])
            
            return {
                'question': question,
                'answer': result['answer'],
                'context': context,
                'sources': result['sources'],
                'confidence': result['confidence'],
                'coverage': result['coverage'],
                'expected_answer': expected_answer,
                'num_contexts': len(retrieved_docs),
            }
        except Exception as e:
            print(f"[ERROR] Exception during evaluation: {str(e)}")
            return None
    
    def compute_ragas_metrics(self, evaluation_results: List[Dict]) -> Dict:
        """
        Compute RAGAS metrics on evaluation results.
        
        Args:
            evaluation_results: List of evaluation result dicts
            
        Returns:
            Dict with aggregate metrics
        """
        print("\n[INFO] Computing RAGAS metrics...")
        
        # Filter out None results
        valid_results = [r for r in evaluation_results if r is not None]
        
        if not valid_results:
            print("[ERROR] No valid results to evaluate")
            return {}
        
        try:
            # Prepare data for RAGAS
            eval_data = {
                'question': [r['question'] for r in valid_results],
                'answer': [r['answer'] for r in valid_results],
                'contexts': [[r['context']] for r in valid_results],  # RAGAS expects list of lists
                'ground_truth': [r.get('expected_answer', '') for r in valid_results]
            }
            
            dataset = Dataset.from_dict(eval_data)
            
            # Evaluate with RAGAS metrics
            print("[INFO] Running RAGAS evaluation (this may take a few minutes)...")
            ragas_results = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy, context_relevancy]
            )
            
            return {
                'faithfulness': float(ragas_results['faithfulness'].mean()),
                'answer_relevancy': float(ragas_results['answer_relevancy'].mean()),
                'context_relevancy': float(ragas_results['context_relevancy'].mean()),
                'sample_count': len(valid_results),
            }
        except Exception as e:
            print(f"[WARNING] RAGAS metrics computation failed: {str(e)}")
            print("[INFO] Returning custom metrics instead...")
            return self._compute_custom_metrics(valid_results)
    
    def _compute_custom_metrics(self, results: List[Dict]) -> Dict:
        """
        Compute custom metrics when RAGAS fails.
        
        Fallback implementation using simple heuristics.
        """
        if not results:
            return {}
        
        # Faithfulness: % of answers that cite sources
        faithful = sum(1 for r in results if r.get('sources')) / len(results)
        
        # Answer relevancy: % of non-empty answers
        relevant = sum(1 for r in results if len(r.get('answer', '')) > 50) / len(results)
        
        # Context relevancy: average documentation coverage
        coverage_scores = {
            'complete': 1.0,
            'partial': 0.6,
            'not_available': 0.0,
            'error': 0.0
        }
        context_rel = sum(
            coverage_scores.get(r.get('coverage', 'error'), 0) 
            for r in results
        ) / len(results)
        
        return {
            'faithfulness': faithful,
            'answer_relevancy': relevant,
            'context_relevancy': context_rel,
            'sample_count': len(results),
            'metric_type': 'custom_heuristic'
        }
    
    def generate_report(self, evaluation_results: List[Dict], 
                       ragas_metrics: Dict, output_file: str = "eval/results.json") -> None:
        """
        Generate evaluation report and save to file.
        
        Args:
            evaluation_results: List of evaluation results
            ragas_metrics: Computed RAGAS metrics
            output_file: Path to save report
        """
        valid_results = [r for r in evaluation_results if r is not None]
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_questions': len(evaluation_results),
                'successful_evaluations': len(valid_results),
                'failed_evaluations': len(evaluation_results) - len(valid_results),
            },
            'metrics': ragas_metrics,
            'detailed_results': [
                {
                    'question': r['question'],
                    'answer': r['answer'][:200] + '...' if len(r['answer']) > 200 else r['answer'],
                    'coverage': r['coverage'],
                    'confidence': r['confidence'],
                    'sources': r['sources'],
                    'num_contexts': r['num_contexts']
                }
                for r in valid_results[:10]  # First 10 for readability
            ]
        }
        
        # Save report
        Path(output_file).parent.mkdir(exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n[SUCCESS] Report saved to {output_file}")
        self._print_report_summary(report)
    
    def _print_report_summary(self, report: Dict) -> None:
        """Print a human-readable summary of the report."""
        summary = report['summary']
        metrics = report['metrics']
        
        print("\n" + "="*60)
        print("📊 EVALUATION REPORT SUMMARY")
        print("="*60)
        print(f"Questions evaluated: {summary['successful_evaluations']}/{summary['total_questions']}")
        print(f"Failed: {summary['failed_evaluations']}")
        print("\n📈 Metrics:")
        for key, value in metrics.items():
            if key != 'sample_count' and key != 'metric_type':
                print(f"  • {key.replace('_', ' ').title()}: {value:.2%}")
        print("="*60 + "\n")


def create_sample_test_file():
    """Create a sample test questions file."""
    sample_questions = [
        {
            "question": "Quelle est la politique de retour ?",
            "expected_answer": "Les retours sont acceptés under certain conditions"
        },
        {
            "question": "Quel est le délai de livraison standard ?",
            "expected_answer": "Standard delivery takes 5-7 business days"
        },
        {
            "question": "Comment puis-je suivre ma commande ?",
            "expected_answer": "You can track your order using the order number"
        },
        {
            "question": "Disposez-vous d'une garantie ?",
            "expected_answer": "Yes, products come with a warranty"
        },
        {
            "question": "Quelles sont les frais de livraison ?",
            "expected_answer": "Shipping costs depend on location"
        },
        {
            "question": "Puis-je modifier ma commande après l'avoir passée ?",
            "expected_answer": "Order modifications may be possible depending on status"
        },
        {
            "question": "Acceptez-vous les retours internationaux ?",
            "expected_answer": "International returns are subject to specific conditions"
        },
        {
            "question": "Y a-t-il une politique d'échange de produits ?",
            "expected_answer": "Product exchanges are available within the return period"
        },
        {
            "question": "Comment contactez-vous le service client ?",
            "expected_answer": "Customer support is available through email and chat"
        },
        {
            "question": "Offrez-vous une livraison gratuite ?",
            "expected_answer": "Free shipping is available for orders above a minimum amount"
        }
    ]
    
    output_path = Path("eval/test_questions.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_questions, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] Created sample test file: {output_path}")
    return sample_questions


def main():
    """Main evaluation entrypoint."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate RAG Chatbot")
    parser.add_argument('--questions', type=str, default="eval/test_questions.json",
                       help="Path to test questions JSON file")
    parser.add_argument('--output', type=str, default="eval/results.json",
                       help="Path to save evaluation results")
    parser.add_argument('--create-sample', action='store_true',
                       help="Create sample test questions file")
    
    args = parser.parse_args()
    
    # Create sample test file if requested
    if args.create_sample:
        create_sample_test_file()
    
    # Initialize evaluator
    evaluator = RAGEvaluator()
    
    # Load test questions
    test_questions = evaluator.load_test_questions(args.questions)
    if not test_questions:
        print("[ERROR] No test questions loaded. Use --create-sample to create sample file.")
        return
    
    # Evaluate each question
    evaluation_results = []
    for i, test_item in enumerate(test_questions, 1):
        question = test_item['question']
        expected = test_item.get('expected_answer', '')
        print(f"\n[{i}/{len(test_questions)}] Evaluating: {question}")
        
        result = evaluator.evaluate_question(question, expected)
        evaluation_results.append(result)
    
    # Compute RAGAS metrics
    ragas_metrics = evaluator.compute_ragas_metrics(evaluation_results)
    
    # Generate and save report
    evaluator.generate_report(evaluation_results, ragas_metrics, args.output)
    
    print("[INFO] Evaluation complete!")


if __name__ == "__main__":
    main()
