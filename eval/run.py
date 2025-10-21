#!/usr/bin/env python3
"""
Evaluation module for Food Recipes IR Pipeline.
Computes P@k, Recall@k, MAP, and NDCG@k metrics.

Author: Maroš Bednár (AIS ID: 116822)
"""

import argparse
import logging
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """Calculate IR evaluation metrics."""
    
    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: set, k: int) -> float:
        """
        Calculate Precision@k.
        
        P@k = (# relevant docs in top k) / k
        """
        if k == 0:
            return 0.0
        
        retrieved_at_k = retrieved[:k]
        relevant_in_k = sum(1 for doc_id in retrieved_at_k if doc_id in relevant)
        return relevant_in_k / k
    
    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: set, k: int) -> float:
        """
        Calculate Recall@k.
        
        R@k = (# relevant docs in top k) / (total # relevant docs)
        """
        if not relevant:
            return 0.0
        
        retrieved_at_k = retrieved[:k]
        relevant_in_k = sum(1 for doc_id in retrieved_at_k if doc_id in relevant)
        return relevant_in_k / len(relevant)
    
    @staticmethod
    def average_precision(retrieved: List[str], relevant: set) -> float:
        """
        Calculate Average Precision (AP).
        
        AP = (sum of P@k for each relevant doc) / (total # relevant docs)
        """
        if not relevant:
            return 0.0
        
        score = 0.0
        num_hits = 0
        
        for k, doc_id in enumerate(retrieved, 1):
            if doc_id in relevant:
                num_hits += 1
                precision_at_k = num_hits / k
                score += precision_at_k
        
        return score / len(relevant) if relevant else 0.0
    
    @staticmethod
    def dcg_at_k(retrieved: List[str], relevance: Dict[str, int], k: int) -> float:
        """
        Calculate Discounted Cumulative Gain@k.
        
        DCG@k = sum_{i=1}^{k} (2^{rel_i} - 1) / log_2(i + 1)
        """
        dcg = 0.0
        for i, doc_id in enumerate(retrieved[:k], 1):
            rel = relevance.get(doc_id, 0)
            dcg += (2 ** rel - 1) / math.log2(i + 1)
        return dcg
    
    @staticmethod
    def ndcg_at_k(retrieved: List[str], relevance: Dict[str, int], k: int) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain@k.
        
        nDCG@k = DCG@k / IDCG@k
        """
        dcg = EvaluationMetrics.dcg_at_k(retrieved, relevance, k)
        
        # Ideal DCG: sort by relevance descending
        ideal_retrieved = sorted(relevance.keys(), key=lambda x: relevance[x], reverse=True)
        idcg = EvaluationMetrics.dcg_at_k(ideal_retrieved, relevance, k)
        
        return dcg / idcg if idcg > 0 else 0.0


class RecipeEvaluator:
    """Main evaluation orchestrator."""
    
    def __init__(self, index_dir: str, queries_file: str, qrels_file: str, 
                 metrics_output: str, k_values: List[int] = None):
        self.index_dir = Path(index_dir)
        self.queries_file = Path(queries_file)
        self.qrels_file = Path(qrels_file)
        self.metrics_output = Path(metrics_output)
        self.k_values = k_values or [5, 10, 20]
        
        self.queries = self._load_queries()
        self.qrels = self._load_qrels()
        
        logger.info(f"Loaded {len(self.queries)} queries")
        logger.info(f"Loaded qrels for {len(self.qrels)} queries")
    
    def _load_queries(self) -> Dict[str, str]:
        """Load queries from TSV file."""
        queries = {}
        with open(self.queries_file, 'r', encoding='utf-8') as f:
            next(f)  # Skip header
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    qid, query = parts[0], parts[1]
                    queries[qid] = query
        return queries
    
    def _load_qrels(self) -> Dict[str, Dict[str, int]]:
        """Load relevance judgments from TSV file."""
        qrels = defaultdict(dict)
        with open(self.qrels_file, 'r', encoding='utf-8') as f:
            next(f)  # Skip header
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 3:
                    qid, doc_id, rel = parts[0], parts[1], int(parts[2])
                    qrels[qid][doc_id] = rel
        return dict(qrels)
    
    def _run_search(self, query: str, metric: str = 'bm25', k: int = 100) -> List[str]:
        """Run search and return ranked document IDs."""
        cmd = [
            'python3', 'search_cli/run.py',
            '--index', str(self.index_dir),
            '--metric', metric,
            '--q', query,
            '--k', str(k),
            '--quiet'  # Suppress output
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse output to extract document IDs in ranked order
            doc_ids = []
            for line in result.stdout.split('\n'):
                if line.strip() and line.startswith('   ID: '):
                    doc_id = line.replace('   ID:', '').strip()
                    doc_ids.append(doc_id)
            
            return doc_ids
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []
    
    def evaluate_query(self, qid: str, query: str, metric: str = 'bm25') -> Dict:
        """Evaluate a single query."""
        logger.info(f"Evaluating {qid}: '{query}'")
        
        # Get relevance judgments
        relevance = self.qrels.get(qid, {})
        if not relevance:
            logger.warning(f"No qrels found for {qid}")
            return {}
        
        # Get relevant documents (rel >= 1)
        relevant_docs = {doc_id for doc_id, rel in relevance.items() if rel >= 1}
        
        # Run search
        max_k = max(self.k_values)
        retrieved = self._run_search(query, metric, k=max_k * 2)  # Retrieve more than needed
        
        if not retrieved:
            logger.warning(f"No results retrieved for {qid}")
            return {}
        
        # Calculate metrics for each k
        results = {'qid': qid, 'query': query}
        
        for k in self.k_values:
            p_at_k = EvaluationMetrics.precision_at_k(retrieved, relevant_docs, k)
            r_at_k = EvaluationMetrics.recall_at_k(retrieved, relevant_docs, k)
            ndcg_at_k = EvaluationMetrics.ndcg_at_k(retrieved, relevance, k)
            
            results[f'P@{k}'] = p_at_k
            results[f'R@{k}'] = r_at_k
            results[f'NDCG@{k}'] = ndcg_at_k
        
        # Calculate MAP (over all retrieved)
        map_score = EvaluationMetrics.average_precision(retrieved, relevant_docs)
        results['MAP'] = map_score
        
        return results
    
    def evaluate_all(self, metric: str = 'bm25') -> List[Dict]:
        """Evaluate all queries."""
        all_results = []
        
        for qid in sorted(self.queries.keys()):
            query = self.queries[qid]
            results = self.evaluate_query(qid, query, metric)
            if results:
                all_results.append(results)
        
        return all_results
    
    def compute_macro_average(self, results: List[Dict]) -> Dict:
        """Compute macro-average across all queries."""
        if not results:
            return {}
        
        avg_results = {'qid': 'ALL', 'query': 'Macro Average'}
        
        # Collect all metric keys
        metric_keys = set()
        for r in results:
            metric_keys.update(k for k in r.keys() if k not in ['qid', 'query'])
        
        # Average each metric
        for key in sorted(metric_keys):
            values = [r[key] for r in results if key in r]
            avg_results[key] = sum(values) / len(values) if values else 0.0
        
        return avg_results
    
    def save_metrics(self, results: List[Dict], avg_results: Dict):
        """Save metrics to TSV file."""
        if not results:
            logger.warning("No results to save")
            return
        
        # Ensure output directory exists
        self.metrics_output.parent.mkdir(parents=True, exist_ok=True)
        
        # Get all metric columns
        all_keys = ['qid', 'query']
        for k in self.k_values:
            all_keys.extend([f'P@{k}', f'R@{k}', f'NDCG@{k}'])
        all_keys.append('MAP')
        
        with open(self.metrics_output, 'w', encoding='utf-8') as f:
            # Write header
            f.write('\t'.join(all_keys) + '\n')
            
            # Write per-query results
            for r in results:
                values = []
                for key in all_keys:
                    value = r.get(key, '')
                    if isinstance(value, float):
                        values.append(f'{value:.4f}')
                    else:
                        values.append(str(value))
                f.write('\t'.join(values) + '\n')
            
            # Write macro average
            if avg_results:
                values = []
                for key in all_keys:
                    value = avg_results.get(key, '')
                    if isinstance(value, float):
                        values.append(f'{value:.4f}')
                    else:
                        values.append(str(value))
                f.write('\t'.join(values) + '\n')
        
        logger.info(f"Metrics saved to {self.metrics_output}")
    
    def print_summary(self, results: List[Dict], avg_results: Dict):
        """Print evaluation summary."""
        print("\n" + "="*80)
        print("EVALUATION RESULTS SUMMARY")
        print("="*80)
        print()
        
        for r in results:
            print(f"{r['qid']}: {r['query']}")
            for k in self.k_values:
                print(f"  P@{k}={r.get(f'P@{k}', 0):.4f}  R@{k}={r.get(f'R@{k}', 0):.4f}  NDCG@{k}={r.get(f'NDCG@{k}', 0):.4f}")
            print(f"  MAP={r.get('MAP', 0):.4f}")
            print()
        
        print("-"*80)
        print("MACRO AVERAGE:")
        for k in self.k_values:
            print(f"  P@{k}={avg_results.get(f'P@{k}', 0):.4f}  R@{k}={avg_results.get(f'R@{k}', 0):.4f}  NDCG@{k}={avg_results.get(f'NDCG@{k}', 0):.4f}")
        print(f"  MAP={avg_results.get('MAP', 0):.4f}")
        print("="*80)
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate recipe search engine using P@k, Recall@k, MAP, and NDCG@k'
    )
    parser.add_argument(
        '--index',
        default='data/index/v1',
        help='Path to index directory (default: data/index/v1)'
    )
    parser.add_argument(
        '--queries',
        default='eval/queries.tsv',
        help='Path to queries TSV file (default: eval/queries.tsv)'
    )
    parser.add_argument(
        '--qrels',
        default='eval/qrels.tsv',
        help='Path to qrels TSV file (default: eval/qrels.tsv)'
    )
    parser.add_argument(
        '--output',
        default='eval/metrics.tsv',
        help='Path to output metrics TSV (default: eval/metrics.tsv)'
    )
    parser.add_argument(
        '--metric',
        choices=['tfidf', 'bm25'],
        default='bm25',
        help='Search metric to use (default: bm25)'
    )
    parser.add_argument(
        '--k',
        type=int,
        nargs='+',
        default=[5, 10, 20],
        help='K values for P@k, R@k, NDCG@k (default: 5 10 20)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.index).exists():
        logger.error(f"Index directory not found: {args.index}")
        sys.exit(1)
    
    if not Path(args.queries).exists():
        logger.error(f"Queries file not found: {args.queries}")
        sys.exit(1)
    
    if not Path(args.qrels).exists():
        logger.error(f"Qrels file not found: {args.qrels}")
        sys.exit(1)
    
    # Run evaluation
    evaluator = RecipeEvaluator(
        index_dir=args.index,
        queries_file=args.queries,
        qrels_file=args.qrels,
        metrics_output=args.output,
        k_values=args.k
    )
    
    results = evaluator.evaluate_all(metric=args.metric)
    avg_results = evaluator.compute_macro_average(results)
    
    evaluator.save_metrics(results, avg_results)
    evaluator.print_summary(results, avg_results)
    
    logger.info("Evaluation completed successfully")


if __name__ == '__main__':
    main()
